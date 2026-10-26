#!/usr/bin/env python3
"""Read-only inspection of a single already-submitted inaugural Moltbook post."""
import json
import morrow_moltbook as m
ID="92eca4d3-9f23-41cc-8f52-be83a745995d"
def main():
    key=m.get_key()
    if not key:
        print("Moltbook status: missing credential");return 2
    data=m.call(m.BASE+"/posts/"+ID,moltkey=key)
    p=data.get("post") or data.get("data") or data
    if not isinstance(p,dict):p={}
    print("Moltbook status:",json.dumps({
        "found":bool(p.get("id") or p.get("title")),
        "post_id":p.get("id"),
        "status":p.get("verification_status") or p.get("status"),
        "title":p.get("title"),
        "has_challenge":bool(p.get("verification") or data.get("verification")),
        "challenge_text":(p.get("verification") or data.get("verification") or {}).get("challenge_text") if isinstance(p.get("verification") or data.get("verification") or {},dict) else None
    },ensure_ascii=False))
    return 0
if __name__=="__main__":main()
