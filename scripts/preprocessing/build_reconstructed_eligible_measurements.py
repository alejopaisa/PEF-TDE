#!/usr/bin/env python
"""Build DEC-006 eligible measurement CSVs from recovered raw source data.

This materializes measurement-level observations eligible under DEC-006. It
does not apply temporal fitting windows, create model time coordinates, fit
models, choose parameter treatments, or define model-ready fitting samples.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_PATH = REPO_ROOT / "data" / "metadata" / "HISTORICAL_ANALYSIS_SAMPLE.csv"
RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
OUTPUT_DIR = REPO_ROOT / "data" / "reconstructed" / "eligible"
MANIFEST_PATH = (
    REPO_ROOT
    / "data"
    / "metadata"
    / "RECONSTRUCTED_ELIGIBLE_MEASUREMENT_MANIFEST.csv"
)

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

EXPECTED_FLUX_COUNTS = {
    ("AT2020wey", "W1"): 20,
    ("AT2020wey", "W2"): 20,
    ("AT2020wey", "g"): 683,
    ("AT2020wey", "r"): 801,
    ("AT2020ysg", "W1"): 21,
    ("AT2020ysg", "W2"): 21,
    ("AT2020ysg", "g"): 421,
    ("AT2020ysg", "i"): 79,
    ("AT2020ysg", "r"): 531,
    ("AT2020yue", "W1"): 21,
    ("AT2020yue", "W2"): 21,
    ("AT2020yue", "g"): 218,
    ("AT2020yue", "r"): 282,
    ("AT2020zso", "B"): 18,
    ("AT2020zso", "U"): 18,
    ("AT2020zso", "UVM2"): 17,
    ("AT2020zso", "UVW1"): 18,
    ("AT2020zso", "UVW2"): 18,
    ("AT2020zso", "W1"): 21,
    ("AT2020zso", "W2"): 21,
    ("AT2020zso", "g"): 269,
    ("AT2020zso", "i"): 64,
    ("AT2020zso", "r"): 324,
}

EXPECTED_MAGNITUDE_COUNTS = {
    ("AT2018hyz", "g"): 79,
    ("AT2019qiz", "g"): 55,
    ("AT2019qiz", "i"): 29,
    ("AT2019qiz", "r"): 61,
}

EXPECTED_TOTAL = 4151
EXPECTED_FLUX_TOTAL = 3927
EXPECTED_MAGNITUDE_TOTAL = 224

MEASUREMENT_FIELDS = [
    "event",
    "band",
    "mjd",
    "measurement_mode",
    "flux",
    "flux_err",
    "magnitude",
    "magnitude_error",
    "upper_limit",
    "source_raw_file",
    "source_row_index",
    "eligibility_rule",
    "eligible",
    "notes",
]

MANIFEST_FIELDS = [
    "event",
    "band",
    "measurement_mode",
    "historical_processed_N",
    "reconstructed_eligible_N",
    "delta_N",
    "positive_flux_N",
    "zero_flux_N",
    "negative_flux_N",
    "source_raw_file",
    "output_file",
    "eligibility_rule",
    "temporal_window_applied",
    "model_ready",
    "notes",
]

FLUX_RULE = "finite(flux) AND finite(flux_err) AND flux_err > 0"
MAG_RULE = (
    "finite(magnitude) AND finite(magnitude_error) AND "
    "magnitude_error > 0 AND non-upper-limit where available"
)


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


def finite_float(value: object, context: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Cannot interpret numeric value for {context}: {value!r}") from exc
    if not math.isfinite(number):
        raise RuntimeError(f"Non-finite numeric value for {context}: {value!r}")
    return number


def optional_finite_float(value: object) -> float | None:
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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def processed_path(event: str, band: str) -> Path:
    return PROCESSED_DIR / f"{event}_{band}_clean_lightcurve.csv"


def output_path(event: str, band: str) -> Path:
    return OUTPUT_DIR / f"{event}_{band}_eligible_measurements.csv"


def read_sample() -> list[dict[str, str]]:
    sample = read_csv(SAMPLE_PATH)
    if len(sample) != 27:
        raise RuntimeError(f"Expected 27 historical sample rows, found {len(sample)}")
    keys = [(row["event"], row["band"]) for row in sample]
    duplicates = [key for key, count in Counter(keys).items() if count > 1]
    if duplicates:
        raise RuntimeError(f"Duplicate historical sample rows: {duplicates}")
    return sample


def load_raw(event: str) -> object:
    path = RAW_DIR / f"{event}.json"
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def compare_counter(
    expected_keys: Counter[tuple[float, ...]], observed_keys: list[tuple[float, ...]]
) -> tuple[int, int]:
    remaining = expected_keys.copy()
    unmatched_observed = 0
    for key in observed_keys:
        if remaining[key] > 0:
            remaining[key] -= 1
        else:
            unmatched_observed += 1
    return unmatched_observed, sum(remaining.values())


def historical_flux_keys(event: str, band: str) -> list[tuple[float, float, float]]:
    processed = read_csv(processed_path(event, band))
    return [
        (
            finite_float(row["time_original_mjd"], f"{event} {band} processed MJD"),
            finite_float(row["flux"], f"{event} {band} processed flux"),
            finite_float(row["flux_err"], f"{event} {band} processed flux_err"),
        )
        for row in processed
    ]


def historical_magnitude_keys(event: str, band: str) -> list[tuple[float, float, float]]:
    processed = read_csv(processed_path(event, band))
    return [
        (
            finite_float(row["time_original"], f"{event} {band} processed MJD"),
            finite_float(row["magnitude"], f"{event} {band} processed magnitude"),
            finite_float(
                row["magnitude_error"], f"{event} {band} processed magnitude_error"
            ),
        )
        for row in processed
    ]


def build_flux_dataset(
    event: str, band: str, historical_processed_n: int
) -> tuple[list[dict[str, object]], dict[str, object]]:
    if band not in FLUX_FILTER_MAP:
        raise RuntimeError(f"No deterministic raw filter mapping for {event} {band}")

    raw_payload = load_raw(event)
    raw_file = f"{event}.json"
    raw_band = FLUX_FILTER_MAP[band]
    if "lightcurve" not in raw_payload or "data" not in raw_payload["lightcurve"]:
        raise RuntimeError(f"Missing lightcurve data in {raw_file}")

    candidates = []
    for source_row_index, source_row in enumerate(raw_payload["lightcurve"]["data"]):
        if len(source_row) < 4:
            raise RuntimeError(f"Cannot interpret raw lightcurve row {source_row_index}")
        if source_row[1] != raw_band:
            continue
        candidates.append(
            {
                "source_row_index": source_row_index,
                "mjd": finite_float(source_row[0], f"{event} {band} raw MJD"),
                "flux": finite_float(source_row[2], f"{event} {band} raw flux"),
                "flux_err": finite_float(source_row[3], f"{event} {band} raw flux_err"),
            }
        )

    if not candidates:
        raise RuntimeError(f"No raw source rows found for {event} {band} ({raw_band})")

    eligible = [row for row in candidates if row["flux_err"] > 0.0]
    eligible.sort(key=lambda row: (row["mjd"], row["source_row_index"]))

    expected_n = EXPECTED_FLUX_COUNTS.get((event, band))
    if expected_n is None:
        raise RuntimeError(f"No expected flux count registered for {event} {band}")
    if len(eligible) != expected_n:
        raise RuntimeError(
            f"Eligible count discrepancy for {event} {band}: "
            f"expected {expected_n}, found {len(eligible)}"
        )

    positive_rows = [row for row in eligible if row["flux"] > 0.0]
    positive_keys = Counter(
        (row["mjd"], row["flux"], row["flux_err"]) for row in positive_rows
    )
    unmatched_processed, unmatched_positive = compare_counter(
        positive_keys, historical_flux_keys(event, band)
    )
    if unmatched_processed or unmatched_positive:
        raise RuntimeError(
            f"Historical positive subset mismatch for {event} {band}: "
            f"processed={unmatched_processed} positive_raw={unmatched_positive}"
        )

    positive_n = sum(1 for row in eligible if row["flux"] > 0.0)
    zero_n = sum(1 for row in eligible if row["flux"] == 0.0)
    negative_n = sum(1 for row in eligible if row["flux"] < 0.0)
    delta_n = len(eligible) - historical_processed_n
    if delta_n != zero_n + negative_n:
        raise RuntimeError(
            f"Newly retained rows are not exactly nonpositive flux rows for "
            f"{event} {band}: delta={delta_n}, zero+negative={zero_n + negative_n}"
        )

    rows = [
        {
            "event": event,
            "band": band,
            "mjd": row["mjd"],
            "measurement_mode": "FLUX",
            "flux": row["flux"],
            "flux_err": row["flux_err"],
            "magnitude": None,
            "magnitude_error": None,
            "upper_limit": None,
            "source_raw_file": raw_file,
            "source_row_index": row["source_row_index"],
            "eligibility_rule": FLUX_RULE,
            "eligible": True,
            "notes": (
                "Measurement-level observation eligible under DEC-006; "
                "no temporal fitting window applied."
            ),
        }
        for row in eligible
    ]

    out_path = output_path(event, band)
    manifest = {
        "event": event,
        "band": band,
        "measurement_mode": "FLUX",
        "historical_processed_N": historical_processed_n,
        "reconstructed_eligible_N": len(rows),
        "delta_N": delta_n,
        "positive_flux_N": positive_n,
        "zero_flux_N": zero_n,
        "negative_flux_N": negative_n,
        "source_raw_file": raw_file,
        "output_file": str(out_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "eligibility_rule": FLUX_RULE,
        "temporal_window_applied": False,
        "model_ready": False,
        "notes": (
            "Sign-neutral DEC-006 eligible measurement layer; additional "
            "temporal and modeling choices remain unresolved."
        ),
    }
    return rows, manifest


def build_magnitude_dataset(
    event: str, band: str, historical_processed_n: int
) -> tuple[list[dict[str, object]], dict[str, object]]:
    raw_payload = load_raw(event)
    raw_file = f"{event}.json"
    if event not in raw_payload or "photometry" not in raw_payload[event]:
        raise RuntimeError(f"Missing catalog photometry in {raw_file}")

    candidates = []
    for source_row_index, source_row in enumerate(raw_payload[event]["photometry"]):
        if source_row.get("band") != band:
            continue
        magnitude = optional_finite_float(source_row.get("magnitude"))
        magnitude_error = optional_finite_float(source_row.get("e_magnitude"))
        if magnitude is None:
            continue
        if source_row.get("upperlimit"):
            continue
        if magnitude_error is None or magnitude_error <= 0.0:
            continue
        mjd = finite_float(source_row.get("time"), f"{event} {band} raw MJD")
        candidates.append(
            {
                "source_row_index": source_row_index,
                "mjd": mjd,
                "magnitude": magnitude,
                "magnitude_error": magnitude_error,
                "upper_limit": bool(source_row.get("upperlimit", False)),
            }
        )

    candidates.sort(key=lambda row: (row["mjd"], row["source_row_index"]))

    expected_n = EXPECTED_MAGNITUDE_COUNTS.get((event, band))
    if expected_n is None:
        raise RuntimeError(f"No expected magnitude count registered for {event} {band}")
    if len(candidates) != expected_n:
        raise RuntimeError(
            f"Eligible count discrepancy for {event} {band}: "
            f"expected {expected_n}, found {len(candidates)}"
        )
    if len(candidates) != historical_processed_n:
        raise RuntimeError(
            f"Magnitude historical count mismatch for {event} {band}: "
            f"historical={historical_processed_n}, eligible={len(candidates)}"
        )

    selected_keys = Counter(
        (row["mjd"], row["magnitude"], row["magnitude_error"]) for row in candidates
    )
    unmatched_processed, unmatched_selected = compare_counter(
        selected_keys, historical_magnitude_keys(event, band)
    )
    if unmatched_processed or unmatched_selected:
        raise RuntimeError(
            f"Historical magnitude subset mismatch for {event} {band}: "
            f"processed={unmatched_processed} selected_raw={unmatched_selected}"
        )

    rows = [
        {
            "event": event,
            "band": band,
            "mjd": row["mjd"],
            "measurement_mode": "MAGNITUDE",
            "flux": None,
            "flux_err": None,
            "magnitude": row["magnitude"],
            "magnitude_error": row["magnitude_error"],
            "upper_limit": row["upper_limit"],
            "source_raw_file": raw_file,
            "source_row_index": row["source_row_index"],
            "eligibility_rule": MAG_RULE,
            "eligible": True,
            "notes": (
                "Native magnitude measurement eligible under DEC-006; "
                "no magnitude-to-flux conversion or temporal fitting window applied."
            ),
        }
        for row in candidates
    ]

    out_path = output_path(event, band)
    manifest = {
        "event": event,
        "band": band,
        "measurement_mode": "MAGNITUDE",
        "historical_processed_N": historical_processed_n,
        "reconstructed_eligible_N": len(rows),
        "delta_N": 0,
        "positive_flux_N": None,
        "zero_flux_N": None,
        "negative_flux_N": None,
        "source_raw_file": raw_file,
        "output_file": str(out_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "eligibility_rule": MAG_RULE,
        "temporal_window_applied": False,
        "model_ready": False,
        "notes": (
            "Native magnitude DEC-006 eligible measurement layer; additional "
            "temporal, transformation, and modeling choices remain unresolved."
        ),
    }
    return rows, manifest


def main() -> int:
    sample = read_sample()
    manifests = []
    output_paths = []

    for sample_row in sample:
        event = sample_row["event"]
        band = sample_row["band"]
        historical_processed_n = int(sample_row["N"])
        if not processed_path(event, band).exists():
            raise FileNotFoundError(processed_path(event, band))

        if event in FLUX_EVENTS:
            rows, manifest = build_flux_dataset(event, band, historical_processed_n)
        elif event in MAGNITUDE_EVENTS:
            rows, manifest = build_magnitude_dataset(
                event, band, historical_processed_n
            )
        else:
            raise RuntimeError(f"Unsupported event in sample: {event}")

        path = output_path(event, band)
        write_csv(path, rows, MEASUREMENT_FIELDS)
        output_paths.append(path)
        manifests.append(manifest)

    write_csv(MANIFEST_PATH, manifests, MANIFEST_FIELDS)

    if len(output_paths) != 27:
        raise RuntimeError(f"Expected 27 output files, wrote {len(output_paths)}")
    if len(manifests) != 27:
        raise RuntimeError(f"Expected 27 manifest rows, wrote {len(manifests)}")

    unique_keys = {(row["event"], row["band"]) for row in manifests}
    if len(unique_keys) != 27:
        raise RuntimeError(f"Expected 27 unique event-band keys, found {len(unique_keys)}")

    flux_total = sum(
        int(row["reconstructed_eligible_N"])
        for row in manifests
        if row["measurement_mode"] == "FLUX"
    )
    mag_total = sum(
        int(row["reconstructed_eligible_N"])
        for row in manifests
        if row["measurement_mode"] == "MAGNITUDE"
    )
    total = flux_total + mag_total
    if flux_total != EXPECTED_FLUX_TOTAL:
        raise RuntimeError(f"Expected flux total {EXPECTED_FLUX_TOTAL}, found {flux_total}")
    if mag_total != EXPECTED_MAGNITUDE_TOTAL:
        raise RuntimeError(
            f"Expected magnitude total {EXPECTED_MAGNITUDE_TOTAL}, found {mag_total}"
        )
    if total != EXPECTED_TOTAL:
        raise RuntimeError(f"Expected total {EXPECTED_TOTAL}, found {total}")

    hashes = [file_sha256(path) for path in sorted(output_paths)] + [
        file_sha256(MANIFEST_PATH)
    ]
    combined_hash = hashlib.sha256("".join(hashes).encode("ascii")).hexdigest()

    print(f"event-band files = {len(output_paths)}")
    print(f"manifest rows = {len(manifests)}")
    print(f"unique event-band keys = {len(unique_keys)}")
    print(f"total eligible measurements = {total}")
    print(f"flux-based eligible measurements = {flux_total}")
    print(f"magnitude-based eligible measurements = {mag_total}")
    print(
        "newly retained zero/negative flux measurements = "
        f"{sum(int(row['delta_N']) for row in manifests if row['measurement_mode'] == 'FLUX')}"
    )
    print("historical positive flux subsets = 23/23 PASS")
    print("historical magnitude selections = 4/4 PASS")
    print("temporal_window_applied = False for 27/27")
    print("model_ready = False for 27/27")
    print("No fitting, optimization, model selection, t_model, C_event, t0, or t_ref was introduced.")
    print(f"combined output hash = {combined_hash}")
    print(f"wrote {MANIFEST_PATH.relative_to(REPO_ROOT)}")
    print(f"wrote {OUTPUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
