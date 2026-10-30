#!/usr/bin/env node
// Condense `osv-scanner scan source --format json` output into a triage table.
// Usage: node summarize.ts <osv.json> [--json]
// Zero dependencies; Node >= 23.6 runs .ts directly (type stripping).

import { readFileSync, existsSync } from "node:fs";
import { dirname, join, basename } from "node:path";

type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN";
type Bump = "patch" | "minor" | "major" | "none" | "unknown";

interface Row {
  ecosystem: string;
  name: string;
  version: string;
  lockfile: string;
  direct: boolean | null;
  severity: Severity;
  maxScore: number | null;
  vulnCount: number;
  ids: string[];
  fixVersion: string | null;
  bump: Bump;
  unfixable: string[];
}

const SEVERITY_ORDER: Severity[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"];

function scoreToSeverity(score: number | null): Severity {
  if (score === null) return "UNKNOWN";
  if (score >= 9) return "CRITICAL";
  if (score >= 7) return "HIGH";
  if (score >= 4) return "MEDIUM";
  if (score > 0) return "LOW";
  return "UNKNOWN";
}

function parseVersion(v: string): number[] {
  return v
    .replace(/^v/, "")
    .split(/[.+-]/)
    .slice(0, 3)
    .map((p) => Number.parseInt(p, 10))
    .map((n) => (Number.isNaN(n) ? 0 : n));
}

function compareVersions(a: string, b: string): number {
  const pa = parseVersion(a);
  const pb = parseVersion(b);
  for (let i = 0; i < 3; i++) {
    const d = (pa[i] ?? 0) - (pb[i] ?? 0);
    if (d !== 0) return d;
  }
  return 0;
}

function bumpType(from: string, to: string | null): Bump {
  if (to === null) return "unknown";
  const a = parseVersion(from);
  const b = parseVersion(to);
  // Pre-1.0 semver: a minor bump is breaking, treat it as major.
  if (a[0] !== b[0] || (a[0] === 0 && a[1] !== b[1])) return "major";
  if (a[1] !== b[1]) return "minor";
  if (a[2] !== b[2]) return "patch";
  return "none";
}

// Smallest "fixed" version above the installed one, for this package's ranges.
function fixedFor(vuln: any, name: string, ecosystem: string, installed: string): string | null {
  const candidates: string[] = [];
  for (const aff of vuln.affected ?? []) {
    if (aff.package?.name !== name || aff.package?.ecosystem !== ecosystem) continue;
    for (const range of aff.ranges ?? []) {
      for (const ev of range.events ?? []) {
        if (ev.fixed && compareVersions(ev.fixed, installed) > 0) candidates.push(ev.fixed);
      }
    }
  }
  candidates.sort(compareVersions);
  return candidates[0] ?? null;
}

const MANIFESTS = [
  "package.json",
  "go.mod",
  "Cargo.toml",
  "pyproject.toml",
  "requirements.txt",
  "Gemfile",
  "composer.json",
  "pom.xml",
  "build.gradle",
];
const manifestCache = new Map<string, string | null>();

// Heuristic: a package named in a sibling manifest is a direct dependency.
function isDirect(lockfile: string, name: string): boolean | null {
  const dir = dirname(lockfile);
  if (!manifestCache.has(dir)) {
    const texts = MANIFESTS.map((m) => join(dir, m))
      .filter((p) => existsSync(p))
      .map((p) => readFileSync(p, "utf8"));
    manifestCache.set(dir, texts.length ? texts.join("\n") : null);
  }
  const text = manifestCache.get(dir);
  if (text == null) return null;
  const escaped = name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`(^|["'\\s/=])${escaped}(["'\\s=<>~^@]|$)`, "m").test(text);
}

function summarize(data: any): Row[] {
  const rows: Row[] = [];
  for (const result of data.results ?? []) {
    const lockfile: string = result.source?.path ?? "?";
    for (const pkg of result.packages ?? []) {
      const { name, version, ecosystem } = pkg.package;
      const vulnsById = new Map<string, any>();
      for (const v of pkg.vulnerabilities ?? []) vulnsById.set(v.id, v);

      let maxScore: number | null = null;
      const ids: string[] = [];
      const fixes: string[] = [];
      const unfixable: string[] = [];
      let dbSeverity: Severity | null = null;

      for (const group of pkg.groups ?? []) {
        const score = Number.parseFloat(group.max_severity);
        if (!Number.isNaN(score)) maxScore = Math.max(maxScore ?? 0, score);
        const primary: string =
          (group.aliases ?? []).find((a: string) => a.startsWith("CVE-")) ?? group.ids[0];
        ids.push(primary);
        let groupFix: string | null = null;
        for (const id of group.ids) {
          const v = vulnsById.get(id);
          if (!v) continue;
          const s = String(v.database_specific?.severity ?? "").toUpperCase();
          if (s === "MODERATE") dbSeverity ??= "MEDIUM";
          else if (SEVERITY_ORDER.includes(s as Severity)) {
            const cur = dbSeverity ? SEVERITY_ORDER.indexOf(dbSeverity) : 99;
            if (SEVERITY_ORDER.indexOf(s as Severity) < cur) dbSeverity = s as Severity;
          }
          groupFix ??= fixedFor(v, name, ecosystem, version);
        }
        if (groupFix) fixes.push(groupFix);
        else unfixable.push(primary);
      }

      // The version that clears every fixable advisory is the highest per-group fix.
      fixes.sort(compareVersions);
      const fixVersion = fixes[fixes.length - 1] ?? null;
      let severity = scoreToSeverity(maxScore);
      if (severity === "UNKNOWN" && dbSeverity) severity = dbSeverity;

      rows.push({
        ecosystem,
        name,
        version,
        lockfile,
        direct: isDirect(lockfile, name),
        severity,
        maxScore,
        vulnCount: (pkg.groups ?? []).length,
        ids,
        fixVersion,
        bump: bumpType(version, fixVersion),
        unfixable,
      });
    }
  }
  rows.sort(
    (a, b) =>
      SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity) ||
      (b.maxScore ?? 0) - (a.maxScore ?? 0),
  );
  return rows;
}

function render(rows: Row[]): string {
  if (rows.length === 0) return "No vulnerable packages.";
  const counts = SEVERITY_ORDER.map((s) => `${s}=${rows.filter((r) => r.severity === s).length}`);
  const lockfiles = [...new Set(rows.map((r) => r.lockfile))];
  const lines = [
    `Vulnerable packages: ${rows.length} | advisories: ${rows.reduce((n, r) => n + r.vulnCount, 0)} | ${counts.join(" ")}`,
    `Lockfiles: ${lockfiles.join(", ")}`,
    "",
    "| Sev | Score | Package | Installed | Fix | Bump | Direct | Advisories | No fix |",
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
  ];
  for (const r of rows) {
    const direct = r.direct === null ? "?" : r.direct ? "yes" : "no";
    const shown = r.ids.slice(0, 3).join(", ") + (r.ids.length > 3 ? ` +${r.ids.length - 3}` : "");
    lines.push(
      `| ${r.severity} | ${r.maxScore ?? "-"} | ${r.ecosystem}:${r.name} | ${r.version} | ${r.fixVersion ?? "none"} | ${r.bump} | ${direct} | ${shown} | ${r.unfixable.join(", ") || "-"} |`,
    );
  }
  if (lockfiles.length > 1) {
    lines.push("", "Lockfile per package:");
    for (const r of rows) lines.push(`- ${r.ecosystem}:${r.name} → ${basename(dirname(r.lockfile))}/${basename(r.lockfile)}`);
  }
  return lines.join("\n");
}

const [file, flag] = process.argv.slice(2);
if (!file) {
  console.error("usage: node summarize.ts <osv.json> [--json]");
  process.exit(2);
}
const rows = summarize(JSON.parse(readFileSync(file, "utf8")));
console.log(flag === "--json" ? JSON.stringify(rows, null, 2) : render(rows));
