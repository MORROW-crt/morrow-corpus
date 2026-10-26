#!/usr/bin/env python3
"""Reject mislabeled/unverifiable Morrow run artifacts before archiving.
Not a substitute for historical, scholarly or independent human audit.
"""
import argparse
import json
from pathlib import Path
import sys

GATES = ("provenance", "concept_genealogy", "scene_mechanism",
         "reciprocal_counterreading", "evidence_reproducibility",
         "opacity_authority", "bearing_outcomes", "independent_scrutiny")
TRACKS = ("conceptual-conjuration", "situational-conjuration",
          "prodigal-theory", "prodigal-outcomes", "witness-testimony")
ALLOWED = ("NOT_ASSESSED", "NEEDS_EVIDENCE", "DISPUTED", "PASSED_WITH_SCOPE")


def audit(payload):
    faults = []
    if payload.get("schema") != "morrow.research-cycle.v0.1":
        faults.append("Incorrect research cycle schema")
    if payload.get("publications_created") != 0 or payload.get("outreach_sent") != 0:
        faults.append("Automated research must not claim external action")
    if payload.get("independent_contributors") != 0:
        faults.append("Internal agent cannot claim independent contributions")
    if len(payload.get("records", [])) > 2:
        faults.append("Too many commissions in one cycle")
    for i, rec in enumerate(payload.get("records", [])):
        p = str(i)
        if rec.get("track") not in TRACKS:
            faults.append(p + ": unsupported research track")
        if rec.get("authorization") != "internal_draft_only":
            faults.append(p + ": unapproved public artifact")
        if rec.get("independent_review") is not False:
            faults.append(p + ": false independent audit")
        if rec.get("publications_created") != 0:
            faults.append(p + ": unexpected publication")
        gates = rec.get("eight_gate_audit") or {}
        if set(gates) != set(GATES):
            faults.append(p + ": incomplete eight-gate audit")
        for key, gate in gates.items():
            if not isinstance(gate, dict) or gate.get("status") not in ALLOWED:
                faults.append(p + ": invalid audit gate " + key)
            if gate.get("status") == "PASSED_WITH_SCOPE":
                faults.append(p + ": automated audit cannot self-certify " + key)
        outcome = rec.get("computational_outcome") or {}
        if outcome.get("ecological_savings_claimed") is not False:
            faults.append(p + ": unverified ecological benefit")
        if any(outcome.get(name) is not None for name in
               ("energy_kwh", "water_litres", "emissions_kg")):
            faults.append(p + ": model invocation has no audited footprint")
        if (rec.get("evidence") or {}).get("evidence_level") != "LEAD_ONLY":
            faults.append(p + ": source lead misclassified as evidence")
    return faults


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    payload = json.loads(Path(args.path).read_text("utf-8"))
    findings = audit(payload)
    if findings:
        for item in findings:
            print("AUDIT BLOCK:", item)
        raise SystemExit(1)
    print("Morrow structural audit PASSED (not an independent historical audit).")


if __name__ == "__main__":
    main()
