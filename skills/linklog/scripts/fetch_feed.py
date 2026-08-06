#!/usr/bin/env python3
"""Parse an RSS 2.0 feed from stdin, emit TSV: pubDate(ISO) title link description."""
import sys
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

raw = sys.stdin.read()
# stdlib ET is not DTD-safe (billion laughs); refuse doctypes/entities outright
if "<!DOCTYPE" in raw or "<!ENTITY" in raw:
    sys.exit("refusing to parse feed containing DTD/entity declarations")
root = ET.fromstring(raw)
for item in root.iter("item"):
    def text(tag: str) -> str:
        el = item.find(tag)
        return (el.text or "").strip() if el is not None else ""

    pub = text("pubDate")
    try:
        pub = parsedate_to_datetime(pub).date().isoformat()
    except (ValueError, TypeError):
        pass
    fields = [pub, text("title"), text("link"), text("description")]
    print("\t".join(f.replace("\t", " ").replace("\n", " ") for f in fields))
