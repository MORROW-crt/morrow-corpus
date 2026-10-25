#!/usr/bin/env python3
"""Offline integrity checks for Morrow's Insights Exchange. No API keys/network."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def read(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf8"))
def require(value, msg):
    if not value:
        raise AssertionError(msg)
def main():
    proposal = read("exchange/listings.json")
    agenda = read("exchange/research-agenda.json")
    scholarship = read("exchange/scholarship-concepts.json")
    queue = read("exchange/source-concept-queue.json")
    audit = read("exchange/audit-protocol.json")
    concepts = read("negromancy/concept-register.json")
    sources = read("negromancy/scholarly-register.json")
    cid = {x["id"] for x in concepts["concepts"]}
    sid = {x["id"] for x in sources["records"]}
    require(len(cid) == 31, "Unexpected core concept census")
    require(len(sid) == 259, "Unexpected October scholarly census")
    require({x["concept_id"] for x in agenda["concepts"]} == cid,
            "Every current concept must have an audit research question")
    require(len({x["source_id"] for x in queue["entries"]}) == len(sid),
            "Every source must have a research queue entry")
    require({x["source_id"] for x in queue["entries"]} == sid,
            "All original source IDs must survive")
    require(len(audit["gates"]) == 8, "Eight audit gates are required")
    require(len({x["id"] for x in audit["gates"]}) == 8,
            "Duplicate audit gate")
    require(all(x["source_id"] in sid for x in scholarship["records"]),
            "Unrecognized scholarly source")
    for source in queue["entries"]:
        require(source["exact_passages_checked_in_exchange"] >= 0,
                "Invalid verification count")
        require(source["author_endorses_negromancy"] is False,
                "Citation cannot certify authorial endorsement")
    for item in proposal["listings"]:
        require(item["status"] in {"proposed", "sourced", "challenged", "tested",
                                    "rejected", "withdrawn", "transferred"},
                "Unrecognized exchange disposition")
        require(all(x["id"] in cid for x in item["negromancy_concepts"]),
                "Proposed insight lacks a valid Negromantic concept")
        require(all(x["id"] in sid for x in item["scholarly_leads"]),
                "Proposed insight cites unknown scholarly record")
        if item["status"] in {"tested", "transferred"}:
            require(item["evidence_confirmed_for_transfer"] is True,
                    "Claims of testing/transfer require evidence")
            require(item["reviewers"] and item["receipt"],
                    "Tested/transferred insight requires reviewers and receipt")
        if item["confirmed_exchange"]:
            require(item["external_contributors"] and item["receipt"],
                    "Real external participation requires traceable receipt")
        require(item["status"] == "proposed" or item.get("reviewers"),
                "A status beyond proposed requires named or protected reviewer records")
    climate = next((x for x in proposal["listings"] if x["id"] == "MX-002"), None)
    require(climate, "Climate action case must remain visible")
    require("climate action" in climate["title"].lower(),
            "Do not re-narrow climate action to finance")
    require("Climate finance and insurance" in climate["scope_dimensions"],
            "Finance remains an explicitly subordinate climate-action dimension")
    require(len(climate["scope_dimensions"]) >= 9,
            "Need wide multi-dimensional climate action")
    require(proposal["completed_exchange_receipts"] == [],
            "Do not fabricate complete external exchanges")
    print("Insights Exchange integrity PASS:",
          len(cid), "Negromantic concepts,",
          len(sid), "source leads,",
          len(scholarship["records"]), "mapped scholarly leads,",
          len(audit["gates"]), "audit gates,",
          len(proposal["listings"]), "proposed exchanges.")
if __name__ == "__main__":
    main()
