#!/usr/bin/env python3
"""Morrow material-computation ledger v1: honest per-model-invocation telemetry.

No network calls or API secrets. No prompt/response content. No invented energy,
carbon, water, monetary cost, hardware or model selfhood. Python stdlib only.

Set MORROW_MATERIAL_LEDGER=<private run artifact .jsonl> to enable logging.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import time
import uuid

SCHEMA = "morrow.material-invocation.v1"
UNKNOWN = {"value": None, "basis": "unknown", "source": None}
ALLOWED_PROVIDER = ("github_models", "openrouter")
ALLOWED_STATUS = ("response_received", "failed", "invalid_response")
USAGE_FIELDS = ("prompt_tokens", "completion_tokens", "total_tokens")
DETAIL_FIELDS = (("cached_input_tokens", "prompt_tokens_details", "cached_tokens"),
                 ("reasoning_output_tokens", "completion_tokens_details", "reasoning_tokens"))


def current_utc():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def usage_from_response(response):
    """Never infer counts from characters; accept non-negative provider integers only."""
    usage = response.get("usage", {}) if isinstance(response, dict) else {}
    if not isinstance(usage, dict):
        usage = {}
    cleaned = {}
    for field in USAGE_FIELDS:
        num = usage.get(field)
        cleaned[field] = num if type(num) is int and num >= 0 else None
    for alias, parent, field in DETAIL_FIELDS:
        details = usage.get(parent)
        num = details.get(field) if isinstance(details, dict) else None
        cleaned[alias] = num if type(num) is int and num >= 0 else None
    cleaned["basis"] = "provider_reported" if any(
        cleaned[k] is not None for k in USAGE_FIELDS) else "not_reported"
    return cleaned


def blank_impact():
    # Independent classes: do not conflate water consumption with water withdrawal.
    return {
        "electricity_wh": dict(UNKNOWN),
        "operational_carbon_gco2e": dict(UNKNOWN),
        "embodied_carbon_gco2e": dict(UNKNOWN),
        "water_consumption_ml": dict(UNKNOWN),
        "water_withdrawal_ml": dict(UNKNOWN),
        "human_labor_minutes": dict(UNKNOWN),
    }


def create_event(flow, provider, requested_model, status, started_at,
                 elapsed_seconds, response=None, event_id=None, error_class=None):
    if provider not in ALLOWED_PROVIDER:
        raise ValueError("Unapproved model provider label")
    if status not in ALLOWED_STATUS:
        raise ValueError("Unsupported status")
    if not math.isfinite(elapsed_seconds) or elapsed_seconds < 0:
        raise ValueError("Invalid measured wall time")
    if not isinstance(flow, str) or not flow or len(flow) > 72:
        raise ValueError("Invalid flow label")
    if not isinstance(requested_model, str) or len(requested_model) > 120:
        raise ValueError("Invalid model label")
    returned = response.get("model") if isinstance(response, dict) else None
    if not isinstance(returned, str) or len(returned) > 120:
        returned = None
    event = {
        "schema": SCHEMA,
        "id": event_id or "mcm-" + uuid.uuid4().hex,
        "github_run_id": str(os.environ.get("GITHUB_RUN_ID") or "local"),
        "flow": flow,
        "provider": provider,
        "requested_model": requested_model,
        "returned_model_if_reported": returned,
        "started_at_utc": started_at,
        "elapsed_seconds_client_wall_clock": round(elapsed_seconds, 6),
        "elapsed_scope": "request_and_client_wait_not_model_compute_energy",
        "request_attempted": True,
        "response_status": status,
        "generated_response_received": status == "response_received",
        "error_class": error_class if status != "response_received" else None,
        "usage": usage_from_response(response),
        "material_impact": blank_impact(),
        "model_infrastructure": {
            "hardware": None,
            "data_center_location": None,
            "electricity_mix": None,
            "provider_facility_metering": None,
        },
        "audit": {
            "material_measurement_level": "unknown",
            "independent_validation": False,
            "content_recorded": False,
            "prompt_recorded": False,
            "credentials_recorded": False,
            "avoided_emissions_claimed": False,
            "note": "Elapsed time and provider usage, if supplied, are not energy measurements."
        }
    }
    return event


def append_event(event, path=None):
    path = path or os.environ.get("MORROW_MATERIAL_LEDGER", "")
    if not path:
        return False
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # One line per attempt, write as one O_APPEND call for traceability.
    fd = os.open(dest, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        data = (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        if os.write(fd, data) != len(data):
            raise OSError("Partial material-event write")
    finally:
        os.close(fd)
    return True


class ModelInvocation:
    """Measure client-observed elapsed time; record a response or a failure.

    Not a GPU timer or an end-to-end energy measurement. Calling code must
    invoke .received(provider_dict) ONLY after a usable response is parsed.
    """
    def __init__(self, flow, provider, model):
        self.flow = flow
        self.provider = provider
        self.model = model
        self.event_id = "mcm-" + uuid.uuid4().hex
        self.response = None
        self.started_at = None
        self.start_perf = None
        self.error_class = None

    def __enter__(self):
        self.started_at = current_utc()
        self.start_perf = time.perf_counter()
        return self

    def received(self, response):
        if isinstance(response, dict):
            self.response = response
        else:
            self.error_class = "non_dictionary_response"

    def invalid(self, reason="invalid_response"):
        self.error_class = reason

    def __exit__(self, exception_type, exception, traceback):
        elapsed = time.perf_counter() - self.start_perf
        status = ("failed" if exception_type is not None else
                  "invalid_response" if self.response is None or self.error_class else
                  "response_received")
        error = (exception_type.__name__ if exception_type else self.error_class)
        event = create_event(
            self.flow, self.provider, self.model, status,
            self.started_at, elapsed, self.response,
            event_id=self.event_id, error_class=error)
        append_event(event)
        return False  # Never suppress errors.


def read_events(path):
    if not Path(path).is_file():
        return []
    events = []
    with Path(path).open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("schema") != SCHEMA:
                raise ValueError("Unexpected material ledger version")
            events.append(record)
    return events


def summary(events):
    statuses = Counter(x["response_status"] for x in events)
    providers = Counter(x["provider"] for x in events)
    reported = [x["usage"] for x in events
                if x["usage"]["basis"] == "provider_reported"]
    return {
        "schema": "morrow.material-run-summary.v1",
        "generated_at_utc": current_utc(),
        "github_run_id": str(os.environ.get("GITHUB_RUN_ID") or "local"),
        "model_requests_recorded": len(events),
        "responses_received": statuses["response_received"],
        "failed_or_invalid_responses": statuses["failed"] + statuses["invalid_response"],
        "provider_breakdown": dict(providers),
        "reported_token_usage_records": len(reported),
        "known_input_tokens_total": sum(
            x["prompt_tokens"] for x in reported if x["prompt_tokens"] is not None),
        "known_output_tokens_total": sum(
            x["completion_tokens"] for x in reported if x["completion_tokens"] is not None),
        "token_totals_scope": "sum_of_reported_usage_only_incomplete_if_any_missing",
        "energy_wh": None, "carbon_gco2e": None, "water_consumption_ml": None,
        "embodied_carbon_gco2e": None,
        "material_footprint_status": "unknown_not_zero",
        "missing_infrastructure_data": True,
        "publication_or_audit_status": "operational_telemetry_not_independent_material_audit",
        "note": "A zero count of recorded requests is not proof of zero data-centre or workflow impact."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("summarize", "validate"))
    parser.add_argument("--ledger", default="morrow-material.jsonl")
    parser.add_argument("--output", default="morrow-material-summary.json")
    args = parser.parse_args()
    events = read_events(args.ledger)
    if args.command == "validate":
        for event in events:
            if not event.get("audit", {}).get("credentials_recorded") is False:
                raise ValueError("Unsafe telemetry event")
            if any(metric.get("value") is not None for metric in
                   event.get("material_impact", {}).values()):
                raise ValueError("Unsupported material impact in unreviewed telemetry")
        print("Validated Morrow material telemetry:", len(events), "model attempts")
        return
    data = summary(events)
    Path(args.output).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print("Material ledger: model requests", data["model_requests_recorded"],
          "| responses", data["responses_received"],
          "| footprint unknown (not zero).")


if __name__ == "__main__":
    main()
