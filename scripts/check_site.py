#!/usr/bin/env python3
"""Static integrity check for Morrow pages, section links, local artwork, and page metadata.
Run from repository root: python3 scripts/check_site.py
No external network calls. Does not inspect private archives or generated manuscript content.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = "/morrow-corpus/"
SKIP = ("http://", "https://", "mailto:", "tel:", "data:", "javascript:")
issues = []
html = sorted(ROOT.rglob("*.html"))
meta = {}
class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=set()
        self.links=[]
        self.title=False
        self.saw_title=False
        self.images=[]
    def handle_starttag(self,tag,attrs):
        v=dict(attrs)
        if "id" in v:
            if v["id"] in self.ids:
                issues.append(f"Duplicate ID: {v['id']}")
            self.ids.add(v["id"])
        if tag=="title":self.saw_title=True
        if tag=="a" and v.get("href"):self.links.append(v["href"])
        if tag in ("img","script","link","source") and v.get("src") or tag=="img":
            if v.get("src"):self.images.append(v["src"])
        if tag=="link" and v.get("rel")=="stylesheet" and v.get("href"):self.images.append(v["href"])
for file in html:
    parser=Reader()
    try:
        parser.feed(file.read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append(f"{file.relative_to(ROOT)} invalid HTML parsing: {exc}")
        continue
    rel=file.relative_to(ROOT).as_posix()
    if not parser.saw_title:issues.append(f"{rel}: missing page title")
    meta[rel]=parser
for file in html:
    rel=file.relative_to(ROOT).as_posix()
    parser=meta.get(rel)
    if not parser:continue
    for item in parser.links+parser.images:
        if item.startswith(SKIP):continue
        url=urlparse(item)
        if url.scheme or url.netloc:continue
        target=unquote(url.path)
        if target.startswith(BASE):target=target[len(BASE):]
        elif target.startswith("/"):continue
        path=(ROOT/target if item.startswith("/") else file.parent/target).resolve()
        if not target:path=file
        if path.is_dir():path=path/"index.html"
        if path.suffix=="" and not path.is_file():path=path/"index.html"
        if not path.is_relative_to(ROOT):
            issues.append(f"{rel}: local path escapes repository: {item}")
            continue
        if not path.is_file():
            issues.append(f"{rel}: missing local target: {item}")
            continue
        if url.fragment and path.suffix==".html":
            destination=meta.get(path.relative_to(ROOT).as_posix())
            if destination and unquote(url.fragment) not in destination.ids:
                issues.append(f"{rel}: missing section anchor: {item}")
print(f"Morrow site integrity: checked {len(html)} HTML pages")
if issues:
    for issue in issues[:150]:print("ERROR",issue)
    print(f"FAIL: {len(issues)} unresolved issue(s)")
    sys.exit(1)
print("PASS: local targets and page anchors resolve")
