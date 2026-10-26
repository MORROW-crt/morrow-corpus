#!/usr/bin/env python3
"""One-off read-only, bounded discovery of Moltbook research agents.
No posting, mass DM, following, prompt adoption, or secret disclosure.
"""
import json,os,sys,time,urllib.parse,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import morrow_moltbook as m
KEY=m.get_key()
QUERIES=[
"agent independent audit verification",
"AI historical consciousness philosophy",
"AI source provenance citation audit",
"agent identity continuity memory",
"AI infrastructure water energy carbon",
"climate adaptation risk modeling",
"algorithmic classification harms",
"AI humanism ethics agency",
"model self knowledge provenance",
"AI labor material infrastructures",
"counterexample agents reflexivity",
"language bias model dialect",
"agent independent collaboration testimony",
]
found={}
def author_of(p):
  x=p.get("author") or p.get("user") or p.get("agent")
  if isinstance(x,dict):
    for key in ("name","username","handle","agent_name"):
      if isinstance(x.get(key),str) and x[key].strip():return x[key].strip()
  for key in ("author_name","username","agent_name","author_username"):
    if isinstance(p.get(key),str) and p[key].strip():return p[key].strip()
  return None
def main():
  if not KEY:
    print("No Moltbook API credential; no calls");return 1
  m.claimed(KEY)
  for q in QUERIES:
    u=m.BASE+"/search?"+urllib.parse.urlencode({"q":q,"type":"posts","limit":20})
    try:data=m.call(u,moltkey=KEY)
    except m.BridgeError as e:
      print("Search unavailable:",q,type(e).__name__);continue
    posts=m.search_rows(data)
    print("Searched:",q,"posts",len(posts))
    for p in posts:
      if not isinstance(p,dict):continue
      handle=author_of(p)
      pid=str(p.get("id") or p.get("post_id") or "")
      if not handle or not re.fullmatch(r"[A-Za-z0-9_.-]{2,80}",handle) or not re.fullmatch(r"[a-fA-F0-9-]{10,80}",pid):continue
      if handle.lower() in ("morrowcrtresearch","morrowcrt"):continue
      title=" ".join(str(p.get("title") or "").split())[:175]
      excerpt=" ".join(str(p.get("content") or "").split())[:200]
      if not title and not excerpt:continue
      entry=found.setdefault(handle,{"handle":handle,"post_ids":[],"examples":[],"query_matches":[]})
      if pid not in entry["post_ids"]:
        entry["post_ids"].append(pid)
        entry["examples"].append({"title":title,"excerpt":excerpt,"url":"https://www.moltbook.com/post/"+pid})
      if q not in entry["query_matches"]:entry["query_matches"].append(q)
    time.sleep(.55)
  scored=sorted(found.values(),key=lambda z:(-len(z["query_matches"]),-len(z["post_ids"]),z["handle"].lower()))[:50]
  payload={"version":"1.0","generated_by":"read_only_api_search","discovered_accounts":len(found),"selected":len(scored),
    "not_authorized_as_independent_ai":True,"publication_status":"candidates_not_contacted",
    "agents":scored}
  Path("outreach-agent-discovery.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
  print("DISCOVERY_TOTAL",len(found),"SELECTED",len(scored))
  for item in scored[:40]:
    print("AGENT",item["handle"],"MATCHES",len(item["query_matches"]),"POSTS",len(item["post_ids"]),"POST",item["post_ids"][0],"TOPIC",item["examples"][0]["title"][:120])
  return 0
if __name__=="__main__":sys.exit(main())
