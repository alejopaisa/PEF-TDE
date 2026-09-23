#!/usr/bin/env python
"""Reproduce the PEF-TDE temporal-coordinate audit artifacts.

This script is descriptive/provenance infrastructure only. It reads the
historical 27-row analysis sample and processed light curves, verifies the
historical band-relative time coordinate, and writes deterministic CSV audit
outputs. It performs no fitting, optimization, model selection, or temporal
methodology choice.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_PATH = REPO_ROOT / "data" / "metadata" / "HISTORICAL_ANALYSIS_SAMPLE.csv"
REDSHIFT_PROVENANCE_PATH = (
    REPO_ROOT / "data" / "metadata" / "RECONSTRUCTION_REDSHIFT_PROVENANCE.csv"
)
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
OUTPUT_DIR = REPO_ROOT / "results" / "reconstruction" / "temporal"

REFERENCE_EPOCHS = {
    "AT2018hyz": {
        "mjd": 58429.0,
        "type": "bolometric_peak",
        "provenance": "PENDING_LITERATURE_VERIFICATION",
    },
    "AT2019qiz": {
        "mjd": 58764.0,
        "type": "bolometric_peak",
        "provenance": "PENDING_LITERATURE_VERIFICATION",
    },
    "AT2020wey": {
        "mjd": 59152.0,
        "type": "r_band_peak",
        "provenance": "PENDING_LITERATURE_VERIFICATION",
    },
    "AT2020ysg": {
        "mjd": 59122.64,
        "type": "fitted_lightcurve_peak",
        "provenance": "PENDING_LITERATURE_VERIFICATION",
    },
    "AT2020yue": {
        "mjd": 59179.44,
        "type": "fitted_rest_frame_g_band_peak",
        "provenance": "PENDING_LITERATURE_VERIFICATION",
    },
    "AT2020zso": {
        "mjd": 59184.0,
        "type": "bolometric_peak",
        "provenance": "PENDING_LITERATURE_VERIFICATION",
    },
}

AUDIT_FIELDS = [
    "event",
    "band",
    "N",
    "mjd_first",
    "mjd_last",
    "baseline_days",
    "historical_zero_mjd",
    "historical_time_days_verified",
    "historical_time_days_max_error",
    "event_common_zero_mjd",
    "band_offset_from_event_zero_days",
    "cadence_q25_days",
    "cadence_median_days",
    "cadence_q75_days",
    "cadence_q90_days",
    "publication_reference_mjd",
    "publication_reference_type",
    "publication_reference_provenance_status",
    "delta_first_from_reference",
    "delta_last_from_reference",
    "N_pre_reference",
    "N_post_reference",
    "fraction_pre_reference",
    "fraction_post_reference",
    "redshift",
    "redshift_provenance_status",
    "baseline_rest_days",
]

EVENT_FIELDS = [
    "event",
    "number_of_analyzed_bands",
    "earliest_mjd",
    "latest_mjd",
    "full_event_span_days",
    "spread_of_band_zero_dates_days",
    "publication_reference_mjd",
    "publication_reference_type",
    "publication_reference_provenance_status",
    "redshift",
    "redshift_provenance_status",
    "observer_frame_span_days",
    "rest_frame_span_days",
    "notes",
]

NOTES = (
    "Historical per-band zero is the first retained observation in each band; "
    "publication reference retained from accepted prior audit and remains "
    "pending literature-provenance verification; redshift taken from the "
    "frozen reconstruction redshift provenance table."
)


def fnum(value: float | int | bool | str) -> str:
    """Return deterministic Python-compatible string formatting for CSV cells."""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value == 0.0:
            return "0"
        return repr(value)
    return str(value)


def quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def read_sample() -> list[dict[str, str]]:
    with SAMPLE_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_processed(event: str, band: str) -> list[dict[str, float]]:
    path = PROCESSED_DIR / f"{event}_{band}_clean_lightcurve.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"No rows found in {path}")
    if "time_original_mjd" in rows[0]:
        time_column = "time_original_mjd"
    elif "time_original" in rows[0]:
        time_column = "time_original"
    else:
        raise ValueError(f"No original MJD column found in {path}")
    out = []
    for row in rows:
        out.append(
            {
                "mjd": float(row[time_column]),
                "time_days": float(row["time_days"]),
            }
        )
    return sorted(out, key=lambda item: item["mjd"])


def read_adopted_redshifts(expected_events: list[str]) -> dict[str, dict[str, object]]:
    with REDSHIFT_PROVENANCE_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    expected = set(expected_events)
    seen: set[str] = set()
    redshifts: dict[str, dict[str, object]] = {}

    for row in rows:
        event = row["event"]
        if event in seen:
            raise RuntimeError(f"Duplicate redshift provenance row for {event}")
        seen.add(event)

        if event not in expected:
            raise RuntimeError(f"Unexpected redshift provenance event {event}")

        redshift = row["adopted_reconstruction_redshift"].strip()
        if not redshift:
            raise RuntimeError(f"Missing adopted reconstruction redshift for {event}")

        status = row["adoption_status"].strip()
        if not status:
            raise RuntimeError(f"Missing redshift adoption status for {event}")

        redshifts[event] = {
            "redshift": float(redshift),
            "provenance_status": status,
        }

    missing = sorted(expected - seen)
    if missing:
        raise RuntimeError(
            "Missing redshift provenance row(s) for " + ", ".join(missing)
        )

    if len(redshifts) != len(expected_events):
        raise RuntimeError(
            f"Expected {len(expected_events)} redshift provenance rows, "
            f"found {len(redshifts)}"
        )

    return redshifts


def max_abs_time_error(rows: list[dict[str, float]], mjd_min: float) -> float:
    return max(abs((row["mjd"] - mjd_min) - row["time_days"]) for row in rows)


def as_csv_row(row: dict[str, object], fields: Iterable[str]) -> dict[str, str]:
    return {field: fnum(row[field]) for field in fields}


def main() -> int:
    sample = read_sample()
    if len(sample) != 27:
        raise RuntimeError(f"Expected 27 historical event-band rows, found {len(sample)}")

    band_data = []
    for sample_row in sample:
        event = sample_row["event"]
        band = sample_row["band"]
        expected_n = int(sample_row["N"])
        rows = read_processed(event, band)
        if len(rows) != expected_n:
            raise RuntimeError(
                f"N check failed for {event} {band}: processed={len(rows)} sample={expected_n}"
            )
        band_data.append(
            {
                "event": event,
                "band": band,
                "expected_n": expected_n,
                "rows": rows,
            }
        )

    events = sorted({row["event"] for row in sample})
    if len(events) != 6:
        raise RuntimeError(f"Expected 6 events, found {len(events)}")

    event_common_zero = {}
    event_latest = {}
    for event in events:
        all_mjds = [
            point["mjd"]
            for item in band_data
            if item["event"] == event
            for point in item["rows"]
        ]
        event_common_zero[event] = min(all_mjds)
        event_latest[event] = max(all_mjds)

    redshifts = read_adopted_redshifts(events)

    audit_rows = []
    pass_n = 0
    pass_time = 0
    global_max_error = 0.0

    for item in band_data:
        event = item["event"]
        band = item["band"]
        rows = item["rows"]
        n = len(rows)
        if n == item["expected_n"]:
            pass_n += 1

        mjds = [row["mjd"] for row in rows]
        mjd_first = min(mjds)
        mjd_last = max(mjds)
        baseline = mjd_last - mjd_first
        time_error = max_abs_time_error(rows, mjd_first)
        global_max_error = max(global_max_error, time_error)
        verified = time_error <= 1e-8
        if verified:
            pass_time += 1

        cadences = [mjds[index] - mjds[index - 1] for index in range(1, len(mjds))]
        reference = REFERENCE_EPOCHS[event]
        reference_mjd = reference["mjd"]
        pre = sum(1 for mjd in mjds if mjd - reference_mjd < 0.0)
        post = sum(1 for mjd in mjds if mjd - reference_mjd >= 0.0)
        redshift = redshifts[event]["redshift"]
        redshift_status = redshifts[event]["provenance_status"]

        audit_rows.append(
            {
                "event": event,
                "band": band,
                "N": n,
                "mjd_first": mjd_first,
                "mjd_last": mjd_last,
                "baseline_days": baseline,
                "historical_zero_mjd": mjd_first,
                "historical_time_days_verified": verified,
                "historical_time_days_max_error": time_error,
                "event_common_zero_mjd": event_common_zero[event],
                "band_offset_from_event_zero_days": mjd_first - event_common_zero[event],
                "cadence_q25_days": quantile(cadences, 0.25),
                "cadence_median_days": quantile(cadences, 0.5),
                "cadence_q75_days": quantile(cadences, 0.75),
                "cadence_q90_days": quantile(cadences, 0.9),
                "publication_reference_mjd": reference_mjd,
                "publication_reference_type": reference["type"],
                "publication_reference_provenance_status": reference["provenance"],
                "delta_first_from_reference": mjd_first - reference_mjd,
                "delta_last_from_reference": mjd_last - reference_mjd,
                "N_pre_reference": pre,
                "N_post_reference": post,
                "fraction_pre_reference": pre / float(n),
                "fraction_post_reference": post / float(n),
                "redshift": redshift,
                "redshift_provenance_status": redshift_status,
                "baseline_rest_days": baseline / (1.0 + redshift),
            }
        )

    event_rows = []
    for event in events:
        event_bands = [row for row in audit_rows if row["event"] == event]
        zero_dates = [row["historical_zero_mjd"] for row in event_bands]
        earliest = min(zero_dates)
        latest = max(row["mjd_last"] for row in event_bands)
        span = latest - earliest
        redshift = redshifts[event]["redshift"]
        redshift_status = redshifts[event]["provenance_status"]
        reference = REFERENCE_EPOCHS[event]
        event_rows.append(
            {
                "event": event,
                "number_of_analyzed_bands": len(event_bands),
                "earliest_mjd": earliest,
                "latest_mjd": latest,
                "full_event_span_days": span,
                "spread_of_band_zero_dates_days": max(zero_dates) - min(zero_dates),
                "publication_reference_mjd": reference["mjd"],
                "publication_reference_type": reference["type"],
                "publication_reference_provenance_status": reference["provenance"],
                "redshift": redshift,
                "redshift_provenance_status": redshift_status,
                "observer_frame_span_days": span,
                "rest_frame_span_days": span / (1.0 + redshift),
                "notes": NOTES,
            }
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    audit_path = OUTPUT_DIR / "TEMPORAL_COORDINATE_AUDIT.csv"
    event_path = OUTPUT_DIR / "TEMPORAL_EVENT_SUMMARY.csv"

    with audit_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in audit_rows:
            writer.writerow(as_csv_row(row, AUDIT_FIELDS))

    with event_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=EVENT_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in event_rows:
            writer.writerow(as_csv_row(row, EVENT_FIELDS))

    print(f"event-band rows = {len(audit_rows)}")
    print(f"event rows = {len(event_rows)}")
    print(f"N checks = {pass_n}/27 PASS")
    print(f"historical time_days checks = {pass_time}/27 PASS")
    print(f"maximum reconstruction error = {global_max_error!r}")
    print("No fitting, optimization, or model selection was performed.")
    print(f"wrote {audit_path.relative_to(REPO_ROOT)}")
    print(f"wrote {event_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
