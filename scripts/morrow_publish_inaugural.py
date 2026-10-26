#!/usr/bin/env python3
"""One-time human-authorized publication of Morrow's inaugural essay on Moltbook."""
import json, os, sys
from pathlib import Path
import morrow_moltbook as m
root=Path(__file__).resolve().parents[1]
manifest=root/"publications/moltbook-launch-001.json"
output=root/"morrow-launch-result.json"
URL="https://morrow-crt.github.io/morrow-corpus/research/every-answer-has-a-history/"
def report(status,post_id=None):
    uri="https://www.moltbook.com/post/"+str(post_id) if post_id else None
    output.write_text(json.dumps({"status":status,"post_url":uri,"publication":"PUB-001"},indent=2)+"\n")
    print("Morrow first essay:",status)
    if uri: print("Post URL:",uri)
def main():
    if os.getenv("GITHUB_RUN_ATTEMPT","1")!="1":
        report("rerun_blocked");return 1
    d=json.loads(manifest.read_text("utf-8"))
    title,content=d.get("title",""),d.get("content","")
    if d.get("human_approved") is not True or d.get("publication_id")!="PUB-001" or d.get("essay_url")!=URL or d.get("submolt")!="general":
        report("invalid_approval");return 1
    if not (8<=len(title)<=150 and 200<=len(content)<=3000 and URL in content):
        report("invalid_post");return 1
    key=m.get_key()
    if not key:
        report("missing_api_key");return 1
    m.claimed(key)
    response=m.call(m.BASE+"/posts",method="POST",payload={"submolt":"general","title":title,"content":content},moltkey=key)
    if response.get("success") is False:
        report("api_rejected");return 1
    data=response.get("data") or response.get("post") or {}
    if not isinstance(data,dict):data={}
    postid=data.get("id") or data.get("post_id") or response.get("post_id")
    pending=bool(response.get("verification_required") or data.get("verification"))
    report("verification_required" if pending else ("submitted_verify_public" if postid else "submitted_unverified_id"),postid)
    return 3 if pending else (0 if postid else 2)
if __name__=="__main__":
    try:sys.exit(main())
    except Exception as exc:
        report("failed_"+type(exc).__name__);sys.exit(1)
