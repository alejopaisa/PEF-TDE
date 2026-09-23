#!/usr/bin/env python
"""Audit recovered historical preprocessing against raw source measurements.

This script is descriptive provenance infrastructure only. It compares the
27-row historical analysis sample against raw JSON measurements and recovered
processed light curves. It performs no fitting, optimization, model selection,
classification, or reconstruction sample-rule choice.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_PATH = REPO_ROOT / "data" / "metadata" / "HISTORICAL_ANALYSIS_SAMPLE.csv"
RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
OUTPUT_DIR = REPO_ROOT / "results" / "reconstruction" / "preprocessing"
AUDIT_PATH = OUTPUT_DIR / "HISTORICAL_PREPROCESSING_AUDIT.csv"

FLUX_EVENTS = {"AT2020wey", "AT2020ysg", "AT2020yue", "AT2020zso"}
MAGNITUDE_EVENTS = {"AT2018hyz", "AT2019qiz"}

FLUX_FILTER_MAP = {
    "B": "B.uvot",
    "U": "U.uvot",
    "UVM2": "UVM2.uvot",
    "UVW1": "UVW1.uvot",
    "UVW2": "UVW2.uvot",
    "W1": "W1.wise",
    "W2": "W2.wise",
    "g": "g.ztf",
    "i": "i.ztf",
    "r": "r.ztf",
}

REFERENCE_EPOCHS = {
    "AT2018hyz": 58429.0,
    "AT2019qiz": 58764.0,
    "AT2020wey": 59152.0,
    "AT2020ysg": 59122.64,
    "AT2020yue": 59179.44,
    "AT2020zso": 59184.0,
}

EXPECTED_2020_COUNTS = {
    ("AT2020wey", "W1"): (20, 8),
    ("AT2020wey", "W2"): (20, 10),
    ("AT2020wey", "g"): (683, 428),
    ("AT2020wey", "r"): (801, 433),
    ("AT2020ysg", "W1"): (21, 16),
    ("AT2020ysg", "W2"): (21, 14),
    ("AT2020ysg", "g"): (421, 327),
    ("AT2020ysg", "i"): (79, 67),
    ("AT2020ysg", "r"): (531, 421),
    ("AT2020yue", "W1"): (21, 10),
    ("AT2020yue", "W2"): (21, 13),
    ("AT2020yue", "g"): (218, 168),
    ("AT2020yue", "r"): (282, 230),
    ("AT2020zso", "B"): (18, 14),
    ("AT2020zso", "U"): (18, 15),
    ("AT2020zso", "UVM2"): (17, 17),
    ("AT2020zso", "UVW1"): (18, 18),
    ("AT2020zso", "UVW2"): (18, 18),
    ("AT2020zso", "W1"): (21, 10),
    ("AT2020zso", "W2"): (21, 11),
    ("AT2020zso", "g"): (269, 162),
    ("AT2020zso", "i"): (64, 40),
    ("AT2020zso", "r"): (324, 232),
}

FIELDS = [
    "event",
    "band",
    "raw_band",
    "data_mode",
    "historical_N",
    "processed_N",
    "raw_candidate_N",
    "finite_flux_error_N",
    "positive_flux_positive_error_N",
    "processed_rule_match",
    "processed_rows_exactly_matched",
    "raw_nonpositive_flux_N",
    "raw_nonpositive_error_N",
    "fraction_retained",
    "finite_magnitude_N",
    "upper_limit_N",
    "non_upperlimit_finite_magnitude_N",
    "finite_positive_magnitude_error_N",
    "processed_unmatched_N",
    "selected_raw_unmatched_N",
    "excluded_source_rows_N",
    "raw_positive_flux_N",
    "raw_zero_flux_N",
    "raw_negative_flux_N",
    "raw_flux_median",
    "positive_only_flux_median",
    "raw_flux_mean",
    "positive_only_flux_mean",
    "pre_reference_N",
    "pre_reference_positive_N",
    "pre_reference_zero_N",
    "pre_reference_negative_N",
    "pre_reference_raw_flux_median",
    "pre_reference_positive_only_flux_median",
    "pre_reference_raw_flux_mean",
    "pre_reference_positive_only_flux_mean",
    "publication_reference_mjd",
    "preprocessing_class",
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


def finite_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: fnum(row.get(field)) for field in fields})


def processed_path(event: str, band: str) -> Path:
    return PROCESSED_DIR / f"{event}_{band}_clean_lightcurve.csv"


def count_flux(values: list[float]) -> dict[str, object]:
    positives = [value for value in values if value > 0.0]
    pre = {
        "raw_positive_flux_N": sum(1 for value in values if value > 0.0),
        "raw_zero_flux_N": sum(1 for value in values if value == 0.0),
        "raw_negative_flux_N": sum(1 for value in values if value < 0.0),
        "raw_flux_median": median(values) if values else None,
        "positive_only_flux_median": median(positives) if positives else None,
        "raw_flux_mean": mean(values) if values else None,
        "positive_only_flux_mean": mean(positives) if positives else None,
    }
    return pre


def match_counter(
    selected_keys: Counter[tuple[float, ...]], processed_keys: list[tuple[float, ...]]
) -> tuple[int, int]:
    remaining = selected_keys.copy()
    unmatched_processed = 0
    for key in processed_keys:
        if remaining[key] > 0:
            remaining[key] -= 1
        else:
            unmatched_processed += 1
    unmatched_selected = sum(remaining.values())
    return unmatched_processed, unmatched_selected


def audit_flux_event_band(event: str, band: str, historical_n: int) -> dict[str, object]:
    if band not in FLUX_FILTER_MAP:
        raise RuntimeError(f"No raw filter mapping for {event} {band}")

    raw_path = RAW_DIR / f"{event}.json"
    if not raw_path.exists():
        raise FileNotFoundError(raw_path)
    with raw_path.open(encoding="utf-8") as handle:
        raw_payload = json.load(handle)

    processed = read_csv(processed_path(event, band))
    raw_band = FLUX_FILTER_MAP[band]
    raw_rows = [
        {
            "mjd": float(row[0]),
            "flux": float(row[2]),
            "flux_err": float(row[3]),
        }
        for row in raw_payload["lightcurve"]["data"]
        if row[1] == raw_band
    ]

    finite_rows = [
        row
        for row in raw_rows
        if math.isfinite(row["flux"]) and math.isfinite(row["flux_err"])
    ]
    selected_rows = [
        row for row in finite_rows if row["flux"] > 0.0 and row["flux_err"] > 0.0
    ]

    selected_keys = Counter(
        (row["mjd"], row["flux"], row["flux_err"]) for row in selected_rows
    )
    processed_keys = [
        (
            float(row["time_original_mjd"]),
            float(row["flux"]),
            float(row["flux_err"]),
        )
        for row in processed
    ]
    unmatched_processed, unmatched_selected = match_counter(selected_keys, processed_keys)
    if unmatched_processed or unmatched_selected:
        raise RuntimeError(
            f"Unmatched processed/source rows for {event} {band}: "
            f"processed={unmatched_processed} selected_raw={unmatched_selected}"
        )

    expected = EXPECTED_2020_COUNTS.get((event, band))
    if expected and expected != (len(raw_rows), len(selected_rows)):
        raise RuntimeError(
            f"Count discrepancy for {event} {band}: expected {expected[0]} -> "
            f"{expected[1]}, found {len(raw_rows)} -> {len(selected_rows)}"
        )

    reference = REFERENCE_EPOCHS[event]
    raw_fluxes = [row["flux"] for row in raw_rows if math.isfinite(row["flux"])]
    pre_rows = [row for row in raw_rows if row["mjd"] < reference]
    pre_fluxes = [row["flux"] for row in pre_rows if math.isfinite(row["flux"])]

    stats = count_flux(raw_fluxes)
    pre_stats = count_flux(pre_fluxes)
    raw_has_positive_and_negative = (
        stats["raw_positive_flux_N"] > 0 and stats["raw_negative_flux_N"] > 0
    )

    return {
        "event": event,
        "band": band,
        "raw_band": raw_band,
        "data_mode": "flux",
        "historical_N": historical_n,
        "processed_N": len(processed),
        "raw_candidate_N": len(raw_rows),
        "finite_flux_error_N": len(finite_rows),
        "positive_flux_positive_error_N": len(selected_rows),
        "processed_rule_match": len(processed) == len(selected_rows),
        "processed_rows_exactly_matched": True,
        "raw_nonpositive_flux_N": sum(
            1 for row in finite_rows if row["flux"] <= 0.0
        ),
        "raw_nonpositive_error_N": sum(
            1 for row in finite_rows if row["flux_err"] <= 0.0
        ),
        "fraction_retained": len(processed) / float(len(raw_rows)),
        "finite_magnitude_N": None,
        "upper_limit_N": None,
        "non_upperlimit_finite_magnitude_N": None,
        "finite_positive_magnitude_error_N": None,
        "processed_unmatched_N": unmatched_processed,
        "selected_raw_unmatched_N": unmatched_selected,
        "excluded_source_rows_N": len(raw_rows) - len(selected_rows),
        **stats,
        "pre_reference_N": len(pre_rows),
        "pre_reference_positive_N": pre_stats["raw_positive_flux_N"],
        "pre_reference_zero_N": pre_stats["raw_zero_flux_N"],
        "pre_reference_negative_N": pre_stats["raw_negative_flux_N"],
        "pre_reference_raw_flux_median": pre_stats["raw_flux_median"],
        "pre_reference_positive_only_flux_median": pre_stats[
            "positive_only_flux_median"
        ],
        "pre_reference_raw_flux_mean": pre_stats["raw_flux_mean"],
        "pre_reference_positive_only_flux_mean": pre_stats[
            "positive_only_flux_mean"
        ],
        "publication_reference_mjd": reference,
        "preprocessing_class": (
            "POSITIVE_FLUX_TRUNCATION_VERIFIED"
            if raw_has_positive_and_negative
            else "POSITIVE_FLUX_SELECTION_VERIFIED"
        ),
        "notes": (
            "The historical preprocessing can be reproduced as a positive-flux "
            "selection for the affected 2020 flux-based datasets. "
            "Positive-only truncation can shift the retained flux distribution "
            "upward relative to the underlying raw measurements."
        ),
    }


def audit_magnitude_event_band(
    event: str, band: str, historical_n: int
) -> dict[str, object]:
    raw_path = RAW_DIR / f"{event}.json"
    if not raw_path.exists():
        raise FileNotFoundError(raw_path)
    with raw_path.open(encoding="utf-8") as handle:
        raw_payload = json.load(handle)[event]

    processed = read_csv(processed_path(event, band))
    raw_rows = [row for row in raw_payload["photometry"] if row.get("band") == band]
    finite_mag_rows = [
        row for row in raw_rows if finite_float(row.get("magnitude")) is not None
    ]
    upper_limit_rows = [row for row in finite_mag_rows if row.get("upperlimit")]
    non_upperlimit_rows = [
        row for row in finite_mag_rows if not row.get("upperlimit")
    ]
    selected_rows = [
        row
        for row in non_upperlimit_rows
        if finite_float(row.get("e_magnitude")) is not None
        and float(row["e_magnitude"]) > 0.0
    ]

    selected_keys = Counter(
        (
            float(row["time"]),
            float(row["magnitude"]),
            float(row["e_magnitude"]),
        )
        for row in selected_rows
    )
    processed_keys = [
        (
            float(row["time_original"]),
            float(row["magnitude"]),
            float(row["magnitude_error"]),
        )
        for row in processed
    ]
    unmatched_processed, unmatched_selected = match_counter(selected_keys, processed_keys)
    if unmatched_processed or unmatched_selected:
        raise RuntimeError(
            f"Unmatched processed/source rows for {event} {band}: "
            f"processed={unmatched_processed} selected_raw={unmatched_selected}"
        )

    notes = (
        "Magnitude-derived historical band verified by finite magnitude, "
        "non-upper-limit selection with finite positive magnitude errors."
    )
    if event == "AT2019qiz" and band == "g":
        notes += " Optical g is audited separately from Gaia G."

    return {
        "event": event,
        "band": band,
        "raw_band": band,
        "data_mode": "magnitude",
        "historical_N": historical_n,
        "processed_N": len(processed),
        "raw_candidate_N": len(raw_rows),
        "finite_flux_error_N": None,
        "positive_flux_positive_error_N": None,
        "processed_rule_match": len(processed) == len(selected_rows),
        "processed_rows_exactly_matched": True,
        "raw_nonpositive_flux_N": None,
        "raw_nonpositive_error_N": None,
        "fraction_retained": len(processed) / float(len(raw_rows)),
        "finite_magnitude_N": len(finite_mag_rows),
        "upper_limit_N": len(upper_limit_rows),
        "non_upperlimit_finite_magnitude_N": len(non_upperlimit_rows),
        "finite_positive_magnitude_error_N": len(selected_rows),
        "processed_unmatched_N": unmatched_processed,
        "selected_raw_unmatched_N": unmatched_selected,
        "excluded_source_rows_N": len(raw_rows) - len(selected_rows),
        "raw_positive_flux_N": None,
        "raw_zero_flux_N": None,
        "raw_negative_flux_N": None,
        "raw_flux_median": None,
        "positive_only_flux_median": None,
        "raw_flux_mean": None,
        "positive_only_flux_mean": None,
        "pre_reference_N": None,
        "pre_reference_positive_N": None,
        "pre_reference_zero_N": None,
        "pre_reference_negative_N": None,
        "pre_reference_raw_flux_median": None,
        "pre_reference_positive_only_flux_median": None,
        "pre_reference_raw_flux_mean": None,
        "pre_reference_positive_only_flux_mean": None,
        "publication_reference_mjd": REFERENCE_EPOCHS[event],
        "preprocessing_class": "MAGNITUDE_SELECTION_VERIFIED",
        "notes": notes,
    }


def main() -> int:
    sample = read_csv(SAMPLE_PATH)
    if len(sample) != 27:
        raise RuntimeError(f"Expected 27 historical event-band rows, found {len(sample)}")

    rows: list[dict[str, object]] = []
    for sample_row in sample:
        event = sample_row["event"]
        band = sample_row["band"]
        historical_n = int(sample_row["N"])

        path = processed_path(event, band)
        if not path.exists():
            raise FileNotFoundError(path)

        if event in FLUX_EVENTS:
            row = audit_flux_event_band(event, band, historical_n)
        elif event in MAGNITUDE_EVENTS:
            row = audit_magnitude_event_band(event, band, historical_n)
        else:
            raise RuntimeError(f"Unsupported event {event}")

        if row["processed_N"] != historical_n:
            raise RuntimeError(
                f"Historical N mismatch for {event} {band}: "
                f"sample={historical_n} processed={row['processed_N']}"
            )
        if not row["processed_rule_match"]:
            raise RuntimeError(f"Preprocessing rule mismatch for {event} {band}")
        rows.append(row)

    write_csv(AUDIT_PATH, rows, FIELDS)

    flux_rows = [row for row in rows if row["data_mode"] == "flux"]
    mag_rows = [row for row in rows if row["data_mode"] == "magnitude"]
    print(f"historical event-band rows = {len(rows)}")
    print(f"flux-rule rows = {len(flux_rows)}")
    print(f"magnitude-selection rows = {len(mag_rows)}")
    print(
        "positive-flux rule matches = "
        f"{sum(1 for row in flux_rows if row['processed_rule_match'])}/"
        f"{len(flux_rows)} PASS"
    )
    print(
        "magnitude-selection rule matches = "
        f"{sum(1 for row in mag_rows if row['processed_rule_match'])}/"
        f"{len(mag_rows)} PASS"
    )
    print("No fitting, optimization, model selection, or classification was performed.")
    print(f"wrote {AUDIT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
