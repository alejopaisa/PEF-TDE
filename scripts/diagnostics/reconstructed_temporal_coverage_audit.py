#!/usr/bin/env python
"""Audit temporal coverage of the DEC-006 eligible measurement layer.

This descriptive audit reads reconstructed eligible measurements through their
manifest, uses source MJD as the canonical timestamp, and reports temporal
coverage relative to existing heterogeneous publication/reference epochs. It
does not choose a fitting window, define model time, fit models, or select
modeling parameters.
"""

from __future__ import annotations

import csv
import hashlib
import math
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = (
    REPO_ROOT
    / "data"
    / "metadata"
    / "RECONSTRUCTED_ELIGIBLE_MEASUREMENT_MANIFEST.csv"
)
REDSHIFT_PATH = (
    REPO_ROOT / "data" / "metadata" / "RECONSTRUCTION_REDSHIFT_PROVENANCE.csv"
)
REFERENCE_PROVENANCE_PATH = (
    REPO_ROOT / "data" / "metadata" / "RECONSTRUCTION_REFERENCE_EPOCH_PROVENANCE.csv"
)
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
OUTPUT_DIR = REPO_ROOT / "results" / "reconstruction" / "temporal"
COVERAGE_PATH = OUTPUT_DIR / "RECONSTRUCTED_ELIGIBLE_TEMPORAL_COVERAGE.csv"
EVENT_SUMMARY_PATH = OUTPUT_DIR / "RECONSTRUCTED_ELIGIBLE_EVENT_SUMMARY.csv"

EXPECTED_TOTAL = 4151
EXPECTED_FLUX_TOTAL = 3927
EXPECTED_MAGNITUDE_TOTAL = 224

COVERAGE_FIELDS = [
    "event",
    "band",
    "measurement_mode",
    "N",
    "redshift_adopted",
    "mjd_min",
    "mjd_max",
    "span_observer_days",
    "span_rest_days",
    "publication_reference_mjd",
    "reference_epoch_type",
    "reference_epoch_provenance_status",
    "N_pre_reference",
    "N_at_reference",
    "N_post_reference",
    "fraction_pre_reference",
    "fraction_post_reference",
    "first_minus_reference_observer_days",
    "last_minus_reference_observer_days",
    "first_minus_reference_rest_days",
    "last_minus_reference_rest_days",
    "median_positive_cadence_observer_days",
    "median_positive_cadence_rest_days",
    "p90_positive_cadence_observer_days",
    "p90_positive_cadence_rest_days",
    "max_gap_observer_days",
    "max_gap_rest_days",
    "max_gap_start_mjd",
    "max_gap_end_mjd",
    "first_post_reference_mjd",
    "last_pre_reference_mjd",
    "temporal_window_applied",
    "model_time_defined",
    "historical_N",
    "reconstructed_N",
    "historical_mjd_min",
    "historical_mjd_max",
    "historical_span_observer_days",
    "reconstructed_minus_historical_N",
    "earliest_newly_retained_mjd",
    "latest_newly_retained_mjd",
    "newly_retained_pre_reference_N",
    "newly_retained_post_reference_N",
    "has_pre_reference_data",
    "has_post_reference_data",
    "contains_multi_year_span",
    "notes",
]

EVENT_FIELDS = [
    "event",
    "redshift_adopted",
    "bands_N",
    "measurements_N",
    "event_mjd_min",
    "event_mjd_max",
    "event_span_observer_days",
    "event_span_rest_days",
    "publication_reference_mjd",
    "reference_epoch_type",
    "reference_epoch_provenance_status",
    "measurements_pre_reference_N",
    "measurements_post_reference_N",
    "bands_with_pre_reference_data_N",
    "bands_with_post_reference_data_N",
    "earliest_minus_reference_observer_days",
    "latest_minus_reference_observer_days",
    "earliest_minus_reference_rest_days",
    "latest_minus_reference_rest_days",
    "longest_band_span_observer_days",
    "longest_band_span_rest_days",
    "largest_single_band_gap_observer_days",
    "largest_single_band_gap_rest_days",
    "largest_gap_band",
    "temporal_window_applied",
    "model_time_defined",
    "notes",
]


def fnum(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value == 0.0:
            return "0"
        return repr(value)
    return str(value)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: Iterable[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: fnum(row.get(field)) for field in fields})


def finite_float(value: object, context: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Cannot interpret {context}: {value!r}") from exc
    if not math.isfinite(number):
        raise RuntimeError(f"Non-finite {context}: {value!r}")
    return number


def positive_differences(sorted_mjds: list[float]) -> list[tuple[float, float, float]]:
    gaps = []
    for index in range(1, len(sorted_mjds)):
        start = sorted_mjds[index - 1]
        end = sorted_mjds[index]
        diff = end - start
        if diff > 0.0:
            gaps.append((diff, start, end))
    return gaps


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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_redshifts(events: set[str]) -> dict[str, float]:
    rows = read_csv(REDSHIFT_PATH)
    out: dict[str, float] = {}
    seen: set[str] = set()
    for row in rows:
        event = row["event"]
        if event in seen:
            raise RuntimeError(f"Duplicate redshift row for {event}")
        seen.add(event)
        if event not in events:
            continue
        if row["adoption_status"] != "ADOPTED_LITERATURE_VALUE":
            raise RuntimeError(f"Unexpected redshift adoption status for {event}")
        out[event] = finite_float(
            row["adopted_reconstruction_redshift"], f"{event} adopted redshift"
        )
    missing = sorted(events - set(out))
    if missing:
        raise RuntimeError("Missing adopted redshift(s): " + ", ".join(missing))
    return out


def read_reference_epochs(events: set[str]) -> dict[str, dict[str, object]]:
    rows = read_csv(REFERENCE_PROVENANCE_PATH)
    out: dict[str, dict[str, object]] = {}
    seen: set[str] = set()
    for row in rows:
        event = row["event"]
        if event in seen:
            raise RuntimeError(f"Duplicate reference epoch row for {event}")
        seen.add(event)
        if event not in events:
            raise RuntimeError(f"Unexpected reference epoch event {event}")
        if row["value_verification_status"] != "VERIFIED_EXACT":
            raise RuntimeError(f"Unexpected reference epoch verification status for {event}")
        if row["absolute_mjd_status"] != "ABSOLUTE_MJD_NOT_DIVIDED_BY_1_PLUS_Z":
            raise RuntimeError(f"Unexpected absolute MJD status for {event}")
        reference_type = row["reference_epoch_type"].strip()
        if not reference_type:
            raise RuntimeError(f"Blank reference epoch type for {event}")
        if event not in events:
            continue
        out[event] = {
            "mjd": finite_float(row["reference_mjd"], f"{event} reference MJD"),
            "type": reference_type,
            "provenance": row["value_verification_status"],
        }
    missing = sorted(events - set(out))
    if missing:
        raise RuntimeError("Missing reference epoch(s): " + ", ".join(missing))
    return out


def processed_path(event: str, band: str) -> Path:
    return PROCESSED_DIR / f"{event}_{band}_clean_lightcurve.csv"


def historical_rows(event: str, band: str, mode: str) -> list[dict[str, float]]:
    rows = read_csv(processed_path(event, band))
    out = []
    for row in rows:
        if mode == "FLUX":
            out.append(
                {
                    "mjd": finite_float(
                        row["time_original_mjd"], f"{event} {band} historical MJD"
                    ),
                    "flux": finite_float(row["flux"], f"{event} {band} historical flux"),
                    "flux_err": finite_float(
                        row["flux_err"], f"{event} {band} historical flux_err"
                    ),
                }
            )
        else:
            out.append(
                {
                    "mjd": finite_float(
                        row["time_original"], f"{event} {band} historical MJD"
                    ),
                    "magnitude": finite_float(
                        row["magnitude"], f"{event} {band} historical magnitude"
                    ),
                    "magnitude_error": finite_float(
                        row["magnitude_error"],
                        f"{event} {band} historical magnitude_error",
                    ),
                }
            )
    return out


def new_rows_against_historical(
    reconstructed: list[dict[str, object]], historical: list[dict[str, float]], mode: str
) -> list[dict[str, object]]:
    if mode == "FLUX":
        historical_keys = Counter(
            (row["mjd"], row["flux"], row["flux_err"]) for row in historical
        )
        new_rows = []
        for row in reconstructed:
            key = (
                row["mjd"],
                row["flux"],
                row["flux_err"],
            )
            if historical_keys[key] > 0:
                historical_keys[key] -= 1
            else:
                new_rows.append(row)
        if sum(historical_keys.values()):
            raise RuntimeError("Historical flux rows not recovered by reconstructed layer")
        return new_rows

    historical_keys = Counter(
        (row["mjd"], row["magnitude"], row["magnitude_error"]) for row in historical
    )
    new_rows = []
    for row in reconstructed:
        key = (row["mjd"], row["magnitude"], row["magnitude_error"])
        if historical_keys[key] > 0:
            historical_keys[key] -= 1
        else:
            new_rows.append(row)
    if sum(historical_keys.values()):
        raise RuntimeError("Historical magnitude rows not recovered by reconstructed layer")
    return new_rows


def coverage_row(
    manifest_row: dict[str, str],
    redshifts: dict[str, float],
    references: dict[str, dict[str, object]],
) -> dict[str, object]:
    event = manifest_row["event"]
    band = manifest_row["band"]
    mode = manifest_row["measurement_mode"]
    path = REPO_ROOT / manifest_row["output_file"]
    rows_raw = read_csv(path)
    rows = [
        {
            **row,
            "mjd": finite_float(row["mjd"], f"{event} {band} reconstructed MJD"),
            "source_row_index": int(row["source_row_index"]),
            "flux": finite_float(row["flux"], f"{event} {band} flux")
            if row["flux"]
            else None,
            "flux_err": finite_float(row["flux_err"], f"{event} {band} flux_err")
            if row["flux_err"]
            else None,
            "magnitude": finite_float(row["magnitude"], f"{event} {band} magnitude")
            if row["magnitude"]
            else None,
            "magnitude_error": finite_float(
                row["magnitude_error"], f"{event} {band} magnitude_error"
            )
            if row["magnitude_error"]
            else None,
        }
        for row in rows_raw
    ]
    rows.sort(key=lambda row: (row["mjd"], row["source_row_index"]))
    if len(rows) != int(manifest_row["reconstructed_eligible_N"]):
        raise RuntimeError(f"Manifest count mismatch for {event} {band}")

    z = redshifts[event]
    reference = references[event]
    reference_mjd = float(reference["mjd"])
    mjds = [row["mjd"] for row in rows]
    mjd_min = min(mjds)
    mjd_max = max(mjds)
    span = mjd_max - mjd_min
    rest_factor = 1.0 + z
    gaps = positive_differences(mjds)
    gap_values = [gap[0] for gap in gaps]
    max_gap = max(gaps, key=lambda item: item[0]) if gaps else None

    pre_rows = [row for row in rows if row["mjd"] < reference_mjd]
    at_rows = [row for row in rows if row["mjd"] == reference_mjd]
    post_rows = [row for row in rows if row["mjd"] > reference_mjd]
    first_post = min((row["mjd"] for row in post_rows), default=None)
    last_pre = max((row["mjd"] for row in pre_rows), default=None)

    historical = historical_rows(event, band, mode)
    historical_mjds = [row["mjd"] for row in historical]
    new_rows = new_rows_against_historical(rows, historical, mode)
    new_mjds = [row["mjd"] for row in new_rows]
    newly_pre = sum(1 for row in new_rows if row["mjd"] < reference_mjd)
    newly_post = sum(1 for row in new_rows if row["mjd"] > reference_mjd)

    cadence_median = median(gap_values) if gap_values else None
    cadence_p90 = quantile(gap_values, 0.9)
    insufficient_note = (
        " Positive cadence/gap metrics are blank because fewer than two distinct MJDs exist."
        if not gap_values
        else ""
    )
    return {
        "event": event,
        "band": band,
        "measurement_mode": mode,
        "N": len(rows),
        "redshift_adopted": z,
        "mjd_min": mjd_min,
        "mjd_max": mjd_max,
        "span_observer_days": span,
        "span_rest_days": span / rest_factor,
        "publication_reference_mjd": reference_mjd,
        "reference_epoch_type": reference["type"],
        "reference_epoch_provenance_status": reference["provenance"],
        "N_pre_reference": len(pre_rows),
        "N_at_reference": len(at_rows),
        "N_post_reference": len(post_rows),
        "fraction_pre_reference": len(pre_rows) / float(len(rows)),
        "fraction_post_reference": len(post_rows) / float(len(rows)),
        "first_minus_reference_observer_days": mjd_min - reference_mjd,
        "last_minus_reference_observer_days": mjd_max - reference_mjd,
        "first_minus_reference_rest_days": (mjd_min - reference_mjd) / rest_factor,
        "last_minus_reference_rest_days": (mjd_max - reference_mjd) / rest_factor,
        "median_positive_cadence_observer_days": cadence_median,
        "median_positive_cadence_rest_days": cadence_median / rest_factor
        if cadence_median is not None
        else None,
        "p90_positive_cadence_observer_days": cadence_p90,
        "p90_positive_cadence_rest_days": cadence_p90 / rest_factor
        if cadence_p90 is not None
        else None,
        "max_gap_observer_days": max_gap[0] if max_gap else None,
        "max_gap_rest_days": max_gap[0] / rest_factor if max_gap else None,
        "max_gap_start_mjd": max_gap[1] if max_gap else None,
        "max_gap_end_mjd": max_gap[2] if max_gap else None,
        "first_post_reference_mjd": first_post,
        "last_pre_reference_mjd": last_pre,
        "temporal_window_applied": False,
        "model_time_defined": False,
        "historical_N": len(historical),
        "reconstructed_N": len(rows),
        "historical_mjd_min": min(historical_mjds),
        "historical_mjd_max": max(historical_mjds),
        "historical_span_observer_days": max(historical_mjds) - min(historical_mjds),
        "reconstructed_minus_historical_N": len(rows) - len(historical),
        "earliest_newly_retained_mjd": min(new_mjds) if new_mjds else None,
        "latest_newly_retained_mjd": max(new_mjds) if new_mjds else None,
        "newly_retained_pre_reference_N": newly_pre,
        "newly_retained_post_reference_N": newly_post,
        "has_pre_reference_data": bool(pre_rows),
        "has_post_reference_data": bool(post_rows),
        "contains_multi_year_span": span >= 365.0,
        "notes": (
            "Publication/reference epochs are heterogeneous descriptive anchors, "
            "not disruption time, fallback time, t0, t_ref, C_event, or model zero. "
            "No temporal fitting window or model time is defined."
            + insufficient_note
        ),
    }


def build_event_summary(
    event: str,
    event_rows: list[dict[str, object]],
    redshifts: dict[str, float],
    references: dict[str, dict[str, object]],
) -> dict[str, object]:
    z = redshifts[event]
    rest_factor = 1.0 + z
    reference = references[event]
    reference_mjd = float(reference["mjd"])
    measurements_n = sum(int(row["N"]) for row in event_rows)
    event_min = min(float(row["mjd_min"]) for row in event_rows)
    event_max = max(float(row["mjd_max"]) for row in event_rows)
    span = event_max - event_min
    largest_span = max(event_rows, key=lambda row: float(row["span_observer_days"]))
    gap_rows = [row for row in event_rows if row["max_gap_observer_days"] is not None]
    largest_gap = (
        max(gap_rows, key=lambda row: float(row["max_gap_observer_days"]))
        if gap_rows
        else None
    )
    pre = sum(int(row["N_pre_reference"]) for row in event_rows)
    post = sum(int(row["N_post_reference"]) for row in event_rows)
    return {
        "event": event,
        "redshift_adopted": z,
        "bands_N": len(event_rows),
        "measurements_N": measurements_n,
        "event_mjd_min": event_min,
        "event_mjd_max": event_max,
        "event_span_observer_days": span,
        "event_span_rest_days": span / rest_factor,
        "publication_reference_mjd": reference_mjd,
        "reference_epoch_type": reference["type"],
        "reference_epoch_provenance_status": reference["provenance"],
        "measurements_pre_reference_N": pre,
        "measurements_post_reference_N": post,
        "bands_with_pre_reference_data_N": sum(
            1 for row in event_rows if int(row["N_pre_reference"]) > 0
        ),
        "bands_with_post_reference_data_N": sum(
            1 for row in event_rows if int(row["N_post_reference"]) > 0
        ),
        "earliest_minus_reference_observer_days": event_min - reference_mjd,
        "latest_minus_reference_observer_days": event_max - reference_mjd,
        "earliest_minus_reference_rest_days": (event_min - reference_mjd) / rest_factor,
        "latest_minus_reference_rest_days": (event_max - reference_mjd) / rest_factor,
        "longest_band_span_observer_days": largest_span["span_observer_days"],
        "longest_band_span_rest_days": largest_span["span_rest_days"],
        "largest_single_band_gap_observer_days": largest_gap["max_gap_observer_days"]
        if largest_gap
        else None,
        "largest_single_band_gap_rest_days": largest_gap["max_gap_rest_days"]
        if largest_gap
        else None,
        "largest_gap_band": largest_gap["band"] if largest_gap else None,
        "temporal_window_applied": False,
        "model_time_defined": False,
        "notes": (
            "The reconstructed eligible layer contains heterogeneous temporal "
            "coverage relative to literature reference epochs. Some event-band "
            "datasets contain multi-year baselines and/or large temporal gaps. "
            "No fitting window is selected."
        ),
    }


def main() -> int:
    manifest = read_csv(MANIFEST_PATH)
    if len(manifest) != 27:
        raise RuntimeError(f"Expected 27 manifest rows, found {len(manifest)}")
    keys = [(row["event"], row["band"]) for row in manifest]
    if len(set(keys)) != 27:
        raise RuntimeError("Manifest event-band keys are not unique")
    events = {row["event"] for row in manifest}
    if len(events) != 6:
        raise RuntimeError(f"Expected 6 events, found {len(events)}")

    redshifts = read_redshifts(events)
    references = read_reference_epochs(events)

    coverage_rows = [coverage_row(row, redshifts, references) for row in manifest]
    event_rows = [
        build_event_summary(
            event,
            [row for row in coverage_rows if row["event"] == event],
            redshifts,
            references,
        )
        for event in sorted(events)
    ]

    total = sum(int(row["N"]) for row in coverage_rows)
    flux_total = sum(
        int(row["N"]) for row in coverage_rows if row["measurement_mode"] == "FLUX"
    )
    magnitude_total = sum(
        int(row["N"])
        for row in coverage_rows
        if row["measurement_mode"] == "MAGNITUDE"
    )
    if total != EXPECTED_TOTAL:
        raise RuntimeError(f"Expected {EXPECTED_TOTAL} measurements, found {total}")
    if flux_total != EXPECTED_FLUX_TOTAL:
        raise RuntimeError(f"Expected {EXPECTED_FLUX_TOTAL} flux measurements, found {flux_total}")
    if magnitude_total != EXPECTED_MAGNITUDE_TOTAL:
        raise RuntimeError(
            f"Expected {EXPECTED_MAGNITUDE_TOTAL} magnitude measurements, found {magnitude_total}"
        )
    for row in coverage_rows:
        manifest_n = next(
            int(item["reconstructed_eligible_N"])
            for item in manifest
            if item["event"] == row["event"] and item["band"] == row["band"]
        )
        if int(row["N"]) != manifest_n:
            raise RuntimeError(f"Coverage/manifest N mismatch for {row['event']} {row['band']}")

    write_csv(COVERAGE_PATH, coverage_rows, COVERAGE_FIELDS)
    write_csv(EVENT_SUMMARY_PATH, event_rows, EVENT_FIELDS)

    coverage_hash = file_sha256(COVERAGE_PATH)
    event_hash = file_sha256(EVENT_SUMMARY_PATH)

    print(f"coverage rows = {len(coverage_rows)}")
    print(f"event-summary rows = {len(event_rows)}")
    print(f"unique event-band keys = {len(set(keys))}")
    print(f"total eligible measurements = {total}")
    print(f"flux-based eligible measurements = {flux_total}")
    print(f"magnitude-based eligible measurements = {magnitude_total}")
    print("temporal_window_applied = False for 27/27")
    print("model_time_defined = False for 27/27")
    print("No t_model, C_event, t0, t_ref, fitting window, or model fitting was introduced.")
    print("five longest event-band spans:")
    for row in sorted(
        coverage_rows, key=lambda item: float(item["span_observer_days"]), reverse=True
    )[:5]:
        print(f"  {row['event']} {row['band']}: {row['span_observer_days']!r} d")
    print("five largest single-band gaps:")
    for row in sorted(
        [item for item in coverage_rows if item["max_gap_observer_days"] is not None],
        key=lambda item: float(item["max_gap_observer_days"]),
        reverse=True,
    )[:5]:
        print(
            f"  {row['event']} {row['band']}: {row['max_gap_observer_days']!r} d "
            f"({row['max_gap_start_mjd']!r} to {row['max_gap_end_mjd']!r})"
        )
    print("event-level earliest/latest relative to reference:")
    for row in event_rows:
        print(
            f"  {row['event']}: {row['earliest_minus_reference_observer_days']!r} d, "
            f"{row['latest_minus_reference_observer_days']!r} d"
        )
    print(f"coverage sha256 = {coverage_hash}")
    print(f"event summary sha256 = {event_hash}")
    print(f"wrote {COVERAGE_PATH.relative_to(REPO_ROOT)}")
    print(f"wrote {EVENT_SUMMARY_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
