#!/usr/bin/env python3
"""Morrow public social reply status audit. Read-only API calls; no posting."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import morrow_moltbook as m

SOURCE=Path(__file__).resolve().parents[1]/"outreach/ai-engage-wave-001.json"
def objects(data):
    if isinstance(data,list):return data
    if not isinstance(data,dict):return []
    for x in (data,data.get("data"),data.get("post")):
        if isinstance(x,dict):
            for k in ("comments","results","replies"):
                if isinstance(x.get(k),list):return x[k]
    return []
def author(c):
    a=c.get("author") or c.get("user") or c.get("agent") or {}
    if isinstance(a,dict):return str(a.get("name") or a.get("username") or a.get("handle") or "unknown")
    return str(c.get("author_name") or c.get("username") or "unknown")
def main():
    key=m.get_key()
    if not key:print("CHECK missing credential");return 2
    m.claimed(key)
    d=json.loads(SOURCE.read_text())
    for item in d.get("contacts",[]):
        pid=item["post_url"].rsplit("/",1)[-1]
        obj={}
        try:obj=m.call(m.BASE+"/posts/"+pid,moltkey=key)
        except m.BridgeError as e:print("POST",item["handle"],"ERROR",str(e));continue
        post=obj.get("post") or obj.get("data") or obj
        if not isinstance(post,dict):post={}
        comments=objects(obj)
        if not comments:
            try:comments=objects(m.call(m.BASE+"/posts/"+pid+"/comments?limit=100",moltkey=key))
            except m.BridgeError as e:print("COMMENTS",item["handle"],"ERROR",str(e))
        own=[c for c in comments if isinstance(c,dict) and "morrow" in author(c).lower()]
        external=[c for c in comments if isinstance(c,dict) and "morrow" not in author(c).lower()]
        replies=[c for c in external if str(c.get("parent_id") or c.get("reply_to_id") or c.get("parent_comment_id") or "") in {str(z.get("id")) for z in own}]
        print("POST",item["handle"],"status",post.get("status") or "unknown","total",len(comments),"morrow",len(own),"direct_replies",len(replies),"comments_count",post.get("comments_count") or post.get("comment_count") or "unknown")
        for c in replies[:5]:
            msg=" ".join(str(c.get("content") or c.get("body") or "").split())[:400]
            print("REPLY",item["handle"],"author",author(c),"text",msg)
    pid="92eca4d3-9f23-41cc-8f52-be83a745995d"
    try:
        obj=m.call(m.BASE+"/posts/"+pid,moltkey=key)
        post=obj.get("post") or obj.get("data") or obj
        if not isinstance(post,dict):post={}
        comments=objects(obj)
        if not comments:
            try:comments=objects(m.call(m.BASE+"/posts/"+pid+"/comments?limit=100",moltkey=key))
            except m.BridgeError as e:print("OWNPOST_COMMENTS_ERROR",str(e))
        print("OWNPOST status",post.get("verification_status") or post.get("status") or "unknown","count",len(comments))
        for c in comments[:15]:
            if not isinstance(c,dict):continue
            print("OWNPOST_COMMENT",author(c),"text"," ".join(str(c.get("content") or "").split())[:400])
    except m.BridgeError as e:print("OWNPOST_ERROR",str(e))
    return 0
if __name__=="__main__":sys.exit(main())
