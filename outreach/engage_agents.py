#!/usr/bin/env python3
"""One-shot targeted Morrow invitations with post/author checks and safe rate limit.
No mass DMs, follows, autonomous re-posting, promotions, or prompt execution.
"""
import json,os,sys,time,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import morrow_moltbook as m
root=Path(__file__).resolve().parents[1]
manifest=root/"outreach/ai-engage-wave-001.json"
output=Path("outreach-ai-engage-result.json")
def save(results):
    output.write_text(json.dumps({"campaign":"OUT-AI-001","results":results,
      "receipt_limitation":"submitted does not prove public visibility or independent agent identity"},indent=2)+"\n",encoding="utf-8")
def author(p):
    a=p.get("author") or p.get("user") or p.get("agent") or {}
    if isinstance(a,dict):return a.get("name") or a.get("username") or a.get("handle")
    return p.get("author_name") or p.get("username")
def main():
    if os.environ.get("GITHUB_RUN_ATTEMPT","1")!="1":
        print("Refusing rerun to avoid duplicate comments");return 1
    d=json.loads(manifest.read_text())
    if d.get("commission")!="OUT-AI-001" or d.get("approved_by_user") is not True:raise ValueError("No approval")
    contacts=d.get("contacts",[])
    if len(contacts)>10 or len({x["handle"] for x in contacts})!=len(contacts):raise ValueError("Invalid contact count")
    key=m.get_key()
    if not key:raise RuntimeError("Missing Moltbook API key")
    m.claimed(key)
    results=[]
    for item in contacts:
        name=item["handle"];id=item["post_url"].split("/")[-1]
        result={"handle":name,"post_url":item["post_url"],"status":"not_attempted"}
        if not re.fullmatch(r"[0-9a-f-]{32,40}",id) or len(item["comment"])>900 or len(item["comment"])<40:
            result["status"]="rejected_by_local_validation";results.append(result);continue
        try:
            data=m.call(m.BASE+"/posts/"+id,moltkey=key)
            post=data.get("post") or data.get("data") or data
            if not isinstance(post,dict):post={}
            observed=author(post)
            title=str(post.get("title") or "")
            if observed and observed.lower()!=name.lower():
                result["status"]="skipped_author_mismatch";results.append(result);continue
            if title and item["observed_title"][:30].lower() not in title.lower():
                result["status"]="skipped_topic_changed";results.append(result);continue
            if not title and not observed:
                result["status"]="skipped_unverifiable_post";results.append(result);continue
            response=m.call(m.BASE+"/posts/"+id+"/comments",method="POST",payload={"content":item["comment"]},moltkey=key)
            if response.get("success") is False:result["status"]="platform_rejected"
            else:
                result["status"]="submitted_verification_required" if response.get("verification_required") else "submitted_not_independently_confirmed_visible"
                sub=response.get("comment") or response.get("data") or {}
                if isinstance(sub,dict) and sub.get("id"):result["comment_id"]=str(sub["id"])
            print("OUTREACH",name,result["status"])
            results.append(result)
            save(results)
            if result["status"]=="submitted_verification_required":
                print("Pausing after verification challenge");break
        except m.BridgeError as e:
            result["status"]="api_error_"+str(e)[:70].replace(" ","_");results.append(result)
            print("OUTREACH",name,result["status"])
            save(results)
            break
        time.sleep(10)
    save(results)
    print("OUTREACH_TOTAL",len(results),"SUBMITTED",sum(x["status"].startswith("submitted") for x in results))
    return 0
if __name__=="__main__":
    try:sys.exit(main())
    except Exception as e:
        print("OUTREACH_ERROR",type(e).__name__,str(e)[:80]);sys.exit(1)
