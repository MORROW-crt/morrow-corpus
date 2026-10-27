#!/usr/bin/env python3
"""Read-only Moltbook post diagnostic and GitHub Models availability check."""
import json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import morrow_moltbook as m
PID="92eca4d3-9f23-41cc-8f52-be83a745995d"
def main():
  key=m.get_key()
  if not key:
    print("DIAGNOSTIC no moltbook key");return 2
  for endpoint in ("/agents/status","/agents/me","/posts/"+PID,"/home"):
    try:
      data=m.call(m.BASE+endpoint,moltkey=key)
      obj=data.get("post") or data.get("agent") or data.get("data") or data
      if not isinstance(obj,dict):obj={}
      print("CHECK",endpoint,"fields",sorted(list(obj.keys()))[:45],"status",obj.get("verification_status") or obj.get("status"),"has_verification",bool(obj.get("verification") or data.get("verification")))
      if endpoint.startswith("/posts/"):print("POST_ID_MATCH",str(obj.get("id"))==PID,"TITLE",str(obj.get("title"))[:120],"VISIBILITY",obj.get("is_published"),"COMMENTS",obj.get("comments_count"))
    except m.BridgeError as e:
      print("CHECK",endpoint,"error",str(e))
  token=os.environ.get("GH_MODELS_TOKEN","").strip()
  if token:
    try:
      result=m.call(m.MODEL,method="POST",modeltoken=token,payload={"model":"openai/gpt-4o-mini","temperature":0,"max_tokens":32,"messages":[{"role":"system","content":"Answer the integer expression; respond with only the number."},{"role":"user","content":"(13 * 7) - 23 = ?"}]})
      content=result["choices"][0]["message"]["content"].strip()
      print("MODEL_PROBE", "valid" if content=="68" else "unexpected_answer", "has_model", bool(result.get("model")))
    except (m.BridgeError,KeyError,TypeError,IndexError) as e:print("MODEL_PROBE error",str(e)[:120])
  else:print("MODEL_PROBE not_configured")
  return 0
if __name__=="__main__":sys.exit(main())
