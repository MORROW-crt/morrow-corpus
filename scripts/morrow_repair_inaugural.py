#!/usr/bin/env python3
"""One-shot, fail-closed repair of a user-approved pending Moltbook inaugural post.

1) If original verified, do nothing.
2) If original is definitely pending, DELETE and CONFIRM deletion before resubmitting.
3) Create at most one replacement using the approved existing text.
4) Verify only if a fresh valid challenge is present and local arithmetic is unambiguous.
5) Confirm publication with GET and record truthful nonsecret results.
No retries or duplicate posts on error.
"""
import json, os, sys
from pathlib import Path
import morrow_moltbook as m
from morrow_challenge import solve

ROOT=Path(__file__).resolve().parents[1]
APPROVAL=ROOT/"publications/moltbook-launch-001.json"
REPAIR=ROOT/"publications/moltbook-repair-001.json"
RESULT=ROOT/"morrow-moltbook-repair-result.json"
OLD="92eca4d3-9f23-41cc-8f52-be83a745995d"
ESSAY="https://morrow-crt.github.io/morrow-corpus/research/every-answer-has-a-history/"

def emit(status,post_id=None,prior_deleted=False,extra=None):
    payload={"status":status,"original_post_id":OLD,"new_post_id":post_id,
       "new_post_url":("https://www.moltbook.com/post/"+post_id) if post_id else None,
       "original_confirmed_deleted":prior_deleted,
       "published_verified":status in ("already_verified","new_post_verified"),
       "action":"user_approved_single_repair",
       "message":"No duplicate retries. Pending is not public publication."}
    if extra:payload["note"]=extra
    RESULT.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print("MORROW_REPAIR",json.dumps(payload))
    return 0 if payload["published_verified"] else 4

def get_post(key,id):
    try:
        data=m.call(m.BASE+"/posts/"+id,moltkey=key)
        p=data.get("post") or data.get("data") or data
        if not isinstance(p,dict):raise ValueError("Unknown post format")
        return p
    except m.BridgeError as e:
        if "HTTP 404" in str(e):return None
        raise

def main():
    if os.environ.get("GITHUB_RUN_ATTEMPT","1")!="1":
        return emit("rerun_refused")
    instruction=json.loads(REPAIR.read_text(encoding="utf-8"))
    approved=json.loads(APPROVAL.read_text(encoding="utf-8"))
    if (instruction.get("approved_by_user") is not True or
        instruction.get("mode")!="one_attempt_replace_unverified" or
        instruction.get("original_post_id")!=OLD or
        approved.get("human_approved") is not True or
        approved.get("publication_id")!="PUB-001" or
        approved.get("essay_url")!=ESSAY or approved.get("submolt")!="general"):
        return emit("manifest_validation_failed")
    title,content=approved["title"],approved["content"]
    if not (8<=len(title)<=150 and 200<=len(content)<=3000 and ESSAY in content):
        return emit("post_validation_failed")
    key=m.get_key()
    if not key:return emit("missing_credentials")
    m.claimed(key)
    old=get_post(key,OLD)
    if old is None:return emit("original_not_found_no_automatic_repost")
    if str(old.get("title"))!=title:return emit("original_title_mismatch")
    original_status=old.get("verification_status") or old.get("status")
    if original_status in ("verified","published"):
        return emit("already_verified",OLD,False)
    if original_status!="pending" or old.get("is_deleted") is True:
        return emit("original_not_confirmed_pending")
    # Existing pending post must be retired before a single replacement.
    try:
        m.call(m.BASE+"/posts/"+OLD,method="DELETE",moltkey=key)
    except m.BridgeError:
        # DELETE can validly return HTTP 204, which the json-only bridge
        # reports as a non-JSON response. Confirm with the subsequent GET.
        pass
    after=get_post(key,OLD)
    if after is not None and after.get("is_deleted") is not True:
        return emit("original_not_deleted_no_repost")
    # Deletion confirmed. Exactly one fresh POST.
    response=m.call(m.BASE+"/posts",method="POST",
        payload={"submolt":"general","title":title,"content":content},moltkey=key)
    if response.get("success") is False:
        return emit("replacement_rejected",prior_deleted=True)
    post=response.get("post") or response.get("data") or {}
    if not isinstance(post,dict):post={}
    new_id=str(post.get("id") or post.get("post_id") or response.get("post_id") or "")
    if not new_id or len(new_id)>100:return emit("replacement_id_missing",prior_deleted=True)
    # Two possible API shapes: top-level verification or post.verification.
    verification=post.get("verification") or response.get("verification") or {}
    needs_verification=bool(response.get("verification_required") or verification)
    if needs_verification:
        if not isinstance(verification,dict) or not verification.get("challenge_text") or not verification.get("verification_code"):
            return emit("replacement_pending_no_verification_challenge",new_id,True)
        vcode=str(verification["verification_code"])
        question=str(verification["challenge_text"])
        if not vcode.startswith("moltbook_verify_") or len(vcode)>300:
            return emit("verification_challenge_invalid",new_id,True)
        try:
            answer=solve(question)
        except ValueError:
            # Never guess or brute force a live challenge.
            return emit("verification_problem_ambiguous_no_guess",new_id,True)
        try:
            confirmation=m.call(m.BASE+"/verify",method="POST",
                 payload={"verification_code":vcode,"answer":answer},moltkey=key)
            if confirmation.get("success") is not True:
                return emit("verification_declined",new_id,True)
        except m.BridgeError:
            return emit("verification_endpoint_error",new_id,True)
    check=get_post(key,new_id)
    if check is None:return emit("replacement_absent_after_submission",new_id,True)
    state=check.get("verification_status") or check.get("status")
    if state=="verified" and check.get("is_deleted") is not True and check.get("is_spam") is not True:
        return emit("new_post_verified",new_id,True)
    return emit("replacement_still_"+str(state or "unknown"),new_id,True)

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as e:
        # Never print the challenge or credential on error.
        print("MORROW_REPAIR_ERROR",type(e).__name__,str(e)[:100])
        sys.exit(8)
