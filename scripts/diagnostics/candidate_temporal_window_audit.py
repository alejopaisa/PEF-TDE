#!/usr/bin/env python
"""Audit candidate temporal-window scenarios for reconstructed measurements.

This is a descriptive sensitivity/counting audit. It uses source MJD as the
canonical timestamp and compares candidate reference-anchored windows without
selecting a final fitting window, defining model time, or fitting any model.
"""

from __future__ import annotations

import csv
import hashlib
import math
from collections import defaultdict
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
REFERENCE_PATH = (
    REPO_ROOT
    / "results"
    / "reconstruction"
    / "temporal"
    / "RECONSTRUCTED_ELIGIBLE_EVENT_SUMMARY.csv"
)
OUTPUT_DIR = REPO_ROOT / "results" / "reconstruction" / "temporal"
DETAIL_PATH = OUTPUT_DIR / "CANDIDATE_TEMPORAL_WINDOW_AUDIT.csv"
SUMMARY_PATH = OUTPUT_DIR / "CANDIDATE_TEMPORAL_WINDOW_SUMMARY.csv"
EVENT_SUMMARY_PATH = OUTPUT_DIR / "CANDIDATE_TEMPORAL_WINDOW_EVENT_SUMMARY.csv"

EXPECTED_TOTAL = 4151
EXPECTED_FLUX_TOTAL = 3927
EXPECTED_MAGNITUDE_TOTAL = 224
EXPECTED_POST_REFERENCE_TOTAL = 2614

REFERENCE_LIMITATION_NOTE = (
    "The reference epochs used in this audit are heterogeneous "
    "literature-derived descriptive anchors. Equal numerical window bounds "
    "relative to these anchors do not imply that the anchors represent the "
    "same physical phase across events."
)

SCENARIOS = [
    {
        "scenario_id": "ALL_ELIGIBLE",
        "scenario_type": "full_available_eligible_layer",
        "lower_rest_days": None,
        "upper_rest_days": None,
    },
    {
        "scenario_id": "POST_REFERENCE_ALL",
        "scenario_type": "post_reference_unbounded",
        "lower_rest_days": 0.0,
        "upper_rest_days": None,
    },
    {
        "scenario_id": "REF_0_180",
        "scenario_type": "bounded_reference_anchored_sensitivity_grid",
        "lower_rest_days": 0.0,
        "upper_rest_days": 180.0,
    },
    {
        "scenario_id": "REF_0_365",
        "scenario_type": "bounded_reference_anchored_sensitivity_grid",
        "lower_rest_days": 0.0,
        "upper_rest_days": 365.0,
    },
    {
        "scenario_id": "REF_0_730",
        "scenario_type": "bounded_reference_anchored_sensitivity_grid",
        "lower_rest_days": 0.0,
        "upper_rest_days": 730.0,
    },
    {
        "scenario_id": "REF_M30_180",
        "scenario_type": "bounded_reference_anchored_sensitivity_grid",
        "lower_rest_days": -30.0,
        "upper_rest_days": 180.0,
    },
    {
        "scenario_id": "REF_M30_365",
        "scenario_type": "bounded_reference_anchored_sensitivity_grid",
        "lower_rest_days": -30.0,
        "upper_rest_days": 365.0,
    },
    {
        "scenario_id": "REF_M30_730",
        "scenario_type": "bounded_reference_anchored_sensitivity_grid",
        "lower_rest_days": -30.0,
        "upper_rest_days": 730.0,
    },
    {
        "scenario_id": "REF_M60_180",
        "scenario_type": "bounded_reference_anchored_sensitivity_grid",
        "lower_rest_days": -60.0,
        "upper_rest_days": 180.0,
    },
    {
        "scenario_id": "REF_M60_365",
        "scenario_type": "bounded_reference_anchored_sensitivity_grid",
        "lower_rest_days": -60.0,
        "upper_rest_days": 365.0,
    },
    {
        "scenario_id": "REF_M60_730",
        "scenario_type": "bounded_reference_anchored_sensitivity_grid",
        "lower_rest_days": -60.0,
        "upper_rest_days": 730.0,
    },
    {
        "scenario_id": "REF_M120_180",
        "scenario_type": "bounded_reference_anchored_sensitivity_grid",
        "lower_rest_days": -120.0,
        "upper_rest_days": 180.0,
    },
    {
        "scenario_id": "REF_M120_365",
        "scenario_type": "bounded_reference_anchored_sensitivity_grid",
        "lower_rest_days": -120.0,
        "upper_rest_days": 365.0,
    },
    {
        "scenario_id": "REF_M120_730",
        "scenario_type": "bounded_reference_anchored_sensitivity_grid",
        "lower_rest_days": -120.0,
        "upper_rest_days": 730.0,
    },
]

DETAIL_FIELDS = [
    "scenario_id",
    "scenario_type",
    "lower_rest_days",
    "upper_rest_days",
    "event",
    "band",
    "measurement_mode",
    "redshift_adopted",
    "publication_reference_mjd",
    "reference_epoch_type",
    "eligible_N",
    "retained_N",
    "excluded_N",
    "retained_fraction",
    "retained_pre_reference_N",
    "retained_at_reference_N",
    "retained_post_reference_N",
    "retained_mjd_min",
    "retained_mjd_max",
    "retained_first_minus_reference_rest_days",
    "retained_last_minus_reference_rest_days",
    "retained_span_rest_days",
    "retained_median_positive_cadence_rest_days",
    "retained_p90_positive_cadence_rest_days",
    "retained_max_gap_rest_days",
    "temporal_window_scenario_applied",
    "final_fitting_window_selected",
    "model_time_defined",
    "reference_epoch_limitation",
]

SUMMARY_FIELDS = [
    "scenario_id",
    "scenario_type",
    "lower_rest_days",
    "upper_rest_days",
    "total_eligible_N",
    "total_retained_N",
    "total_excluded_N",
    "retained_fraction",
    "flux_retained_N",
    "magnitude_retained_N",
    "pre_reference_retained_N",
    "at_reference_retained_N",
    "post_reference_retained_N",
    "event_band_rows_N",
    "event_bands_nonempty_N",
    "event_bands_zero_N",
    "minimum_band_retained_N",
    "median_band_retained_N",
    "maximum_band_retained_N",
    "bands_with_lt_5_measurements_N",
    "bands_with_lt_10_measurements_N",
    "bands_with_lt_20_measurements_N",
    "W1_W2_retained_N",
    "non_W1_W2_retained_N",
    "final_fitting_window_selected",
    "model_time_defined",
    "reference_epoch_limitation",
]

EVENT_FIELDS = [
    "scenario_id",
    "event",
    "redshift_adopted",
    "bands_N",
    "eligible_N",
    "retained_N",
    "retained_fraction",
    "pre_reference_retained_N",
    "at_reference_retained_N",
    "post_reference_retained_N",
    "bands_nonempty_N",
    "bands_zero_N",
    "earliest_retained_minus_reference_rest_days",
    "latest_retained_minus_reference_rest_days",
    "retained_event_span_rest_days",
    "final_fitting_window_selected",
    "model_time_defined",
    "reference_epoch_limitation",
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


def positive_differences(sorted_mjds: list[float], rest_factor: float) -> list[float]:
    values: list[float] = []
    for index in range(1, len(sorted_mjds)):
        diff = sorted_mjds[index] - sorted_mjds[index - 1]
        if diff > 0.0:
            values.append(diff / rest_factor)
    return values


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_redshifts(events: set[str]) -> dict[str, float]:
    rows = read_csv(REDSHIFT_PATH)
    out: dict[str, float] = {}
    for row in rows:
        event = row["event"]
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
    rows = read_csv(REFERENCE_PATH)
    out: dict[str, dict[str, object]] = {}
    for row in rows:
        event = row["event"]
        if event not in events:
            continue
        out[event] = {
            "mjd": finite_float(row["publication_reference_mjd"], f"{event} reference MJD"),
            "type": row["reference_epoch_type"],
        }
    missing = sorted(events - set(out))
    if missing:
        raise RuntimeError("Missing reference epoch(s): " + ", ".join(missing))
    return out


def read_measurements(
    manifest_row: dict[str, str],
    redshifts: dict[str, float],
    references: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    event = manifest_row["event"]
    band = manifest_row["band"]
    path = REPO_ROOT / manifest_row["output_file"]
    z = redshifts[event]
    rest_factor = 1.0 + z
    reference_mjd = float(references[event]["mjd"])
    rows = []
    for raw in read_csv(path):
        mjd = finite_float(raw["mjd"], f"{event} {band} source MJD")
        delta_observer = mjd - reference_mjd
        rows.append(
            {
                "event": event,
                "band": band,
                "measurement_mode": manifest_row["measurement_mode"],
                "mjd": mjd,
                "source_row_index": int(raw["source_row_index"]),
                "delta_reference_observer_days": delta_observer,
                "delta_reference_rest_days": delta_observer / rest_factor,
            }
        )
    rows.sort(key=lambda row: (row["mjd"], row["source_row_index"]))
    expected = int(manifest_row["reconstructed_eligible_N"])
    if len(rows) != expected:
        raise RuntimeError(f"Manifest count mismatch for {event} {band}")
    return rows


def scenario_retains(row: dict[str, object], scenario: dict[str, object]) -> bool:
    if scenario["scenario_id"] == "ALL_ELIGIBLE":
        return True
    delta_rest = float(row["delta_reference_rest_days"])
    lower = scenario["lower_rest_days"]
    upper = scenario["upper_rest_days"]
    if lower is not None and delta_rest < float(lower):
        return False
    if upper is not None and delta_rest > float(upper):
        return False
    return True


def build_detail_row(
    scenario: dict[str, object],
    manifest_row: dict[str, str],
    rows: list[dict[str, object]],
    redshifts: dict[str, float],
    references: dict[str, dict[str, object]],
) -> dict[str, object]:
    event = manifest_row["event"]
    band = manifest_row["band"]
    z = redshifts[event]
    reference_mjd = float(references[event]["mjd"])
    rest_factor = 1.0 + z
    retained = [row for row in rows if scenario_retains(row, scenario)]
    retained_mjds = [float(row["mjd"]) for row in retained]
    retained_rest = [float(row["delta_reference_rest_days"]) for row in retained]
    gaps_rest = positive_differences(retained_mjds, rest_factor)
    retained_n = len(retained)
    eligible_n = len(rows)
    return {
        "scenario_id": scenario["scenario_id"],
        "scenario_type": scenario["scenario_type"],
        "lower_rest_days": scenario["lower_rest_days"],
        "upper_rest_days": scenario["upper_rest_days"],
        "event": event,
        "band": band,
        "measurement_mode": manifest_row["measurement_mode"],
        "redshift_adopted": z,
        "publication_reference_mjd": reference_mjd,
        "reference_epoch_type": references[event]["type"],
        "eligible_N": eligible_n,
        "retained_N": retained_n,
        "excluded_N": eligible_n - retained_n,
        "retained_fraction": retained_n / float(eligible_n),
        "retained_pre_reference_N": sum(
            1 for row in retained if float(row["delta_reference_observer_days"]) < 0.0
        ),
        "retained_at_reference_N": sum(
            1 for row in retained if float(row["delta_reference_observer_days"]) == 0.0
        ),
        "retained_post_reference_N": sum(
            1 for row in retained if float(row["delta_reference_observer_days"]) > 0.0
        ),
        "retained_mjd_min": min(retained_mjds) if retained_mjds else None,
        "retained_mjd_max": max(retained_mjds) if retained_mjds else None,
        "retained_first_minus_reference_rest_days": min(retained_rest)
        if retained_rest
        else None,
        "retained_last_minus_reference_rest_days": max(retained_rest)
        if retained_rest
        else None,
        "retained_span_rest_days": (max(retained_mjds) - min(retained_mjds))
        / rest_factor
        if retained_mjds
        else None,
        "retained_median_positive_cadence_rest_days": median(gaps_rest)
        if gaps_rest
        else None,
        "retained_p90_positive_cadence_rest_days": quantile(gaps_rest, 0.9),
        "retained_max_gap_rest_days": max(gaps_rest) if gaps_rest else None,
        "temporal_window_scenario_applied": scenario["scenario_id"] != "ALL_ELIGIBLE",
        "final_fitting_window_selected": False,
        "model_time_defined": False,
        "reference_epoch_limitation": REFERENCE_LIMITATION_NOTE,
    }


def build_summary_row(
    scenario: dict[str, object], scenario_rows: list[dict[str, object]]
) -> dict[str, object]:
    total_eligible = sum(int(row["eligible_N"]) for row in scenario_rows)
    total_retained = sum(int(row["retained_N"]) for row in scenario_rows)
    retained_counts = [int(row["retained_N"]) for row in scenario_rows]
    return {
        "scenario_id": scenario["scenario_id"],
        "scenario_type": scenario["scenario_type"],
        "lower_rest_days": scenario["lower_rest_days"],
        "upper_rest_days": scenario["upper_rest_days"],
        "total_eligible_N": total_eligible,
        "total_retained_N": total_retained,
        "total_excluded_N": total_eligible - total_retained,
        "retained_fraction": total_retained / float(total_eligible),
        "flux_retained_N": sum(
            int(row["retained_N"])
            for row in scenario_rows
            if row["measurement_mode"] == "FLUX"
        ),
        "magnitude_retained_N": sum(
            int(row["retained_N"])
            for row in scenario_rows
            if row["measurement_mode"] == "MAGNITUDE"
        ),
        "pre_reference_retained_N": sum(
            int(row["retained_pre_reference_N"]) for row in scenario_rows
        ),
        "at_reference_retained_N": sum(
            int(row["retained_at_reference_N"]) for row in scenario_rows
        ),
        "post_reference_retained_N": sum(
            int(row["retained_post_reference_N"]) for row in scenario_rows
        ),
        "event_band_rows_N": len(scenario_rows),
        "event_bands_nonempty_N": sum(1 for count in retained_counts if count > 0),
        "event_bands_zero_N": sum(1 for count in retained_counts if count == 0),
        "minimum_band_retained_N": min(retained_counts),
        "median_band_retained_N": median(retained_counts),
        "maximum_band_retained_N": max(retained_counts),
        "bands_with_lt_5_measurements_N": sum(1 for count in retained_counts if count < 5),
        "bands_with_lt_10_measurements_N": sum(
            1 for count in retained_counts if count < 10
        ),
        "bands_with_lt_20_measurements_N": sum(
            1 for count in retained_counts if count < 20
        ),
        "W1_W2_retained_N": sum(
            int(row["retained_N"]) for row in scenario_rows if row["band"] in {"W1", "W2"}
        ),
        "non_W1_W2_retained_N": sum(
            int(row["retained_N"]) for row in scenario_rows if row["band"] not in {"W1", "W2"}
        ),
        "final_fitting_window_selected": False,
        "model_time_defined": False,
        "reference_epoch_limitation": REFERENCE_LIMITATION_NOTE,
    }


def build_event_summary_row(
    scenario_id: str,
    event: str,
    event_rows: list[dict[str, object]],
    redshifts: dict[str, float],
) -> dict[str, object]:
    eligible_n = sum(int(row["eligible_N"]) for row in event_rows)
    retained_n = sum(int(row["retained_N"]) for row in event_rows)
    first_values = [
        float(row["retained_first_minus_reference_rest_days"])
        for row in event_rows
        if row["retained_first_minus_reference_rest_days"] is not None
    ]
    last_values = [
        float(row["retained_last_minus_reference_rest_days"])
        for row in event_rows
        if row["retained_last_minus_reference_rest_days"] is not None
    ]
    return {
        "scenario_id": scenario_id,
        "event": event,
        "redshift_adopted": redshifts[event],
        "bands_N": len(event_rows),
        "eligible_N": eligible_n,
        "retained_N": retained_n,
        "retained_fraction": retained_n / float(eligible_n),
        "pre_reference_retained_N": sum(
            int(row["retained_pre_reference_N"]) for row in event_rows
        ),
        "at_reference_retained_N": sum(
            int(row["retained_at_reference_N"]) for row in event_rows
        ),
        "post_reference_retained_N": sum(
            int(row["retained_post_reference_N"]) for row in event_rows
        ),
        "bands_nonempty_N": sum(1 for row in event_rows if int(row["retained_N"]) > 0),
        "bands_zero_N": sum(1 for row in event_rows if int(row["retained_N"]) == 0),
        "earliest_retained_minus_reference_rest_days": min(first_values)
        if first_values
        else None,
        "latest_retained_minus_reference_rest_days": max(last_values)
        if last_values
        else None,
        "retained_event_span_rest_days": max(last_values) - min(first_values)
        if first_values and last_values
        else None,
        "final_fitting_window_selected": False,
        "model_time_defined": False,
        "reference_epoch_limitation": REFERENCE_LIMITATION_NOTE,
    }


def validate_outputs(
    detail_rows: list[dict[str, object]],
    summary_rows: list[dict[str, object]],
    event_summary_rows: list[dict[str, object]],
) -> None:
    if len(detail_rows) != 378:
        raise RuntimeError(f"Expected 378 detail rows, found {len(detail_rows)}")
    keys = {(row["scenario_id"], row["event"], row["band"]) for row in detail_rows}
    if len(keys) != 378:
        raise RuntimeError("Scenario/event/band detail keys are not unique")
    if len(summary_rows) != 14:
        raise RuntimeError(f"Expected 14 scenario rows, found {len(summary_rows)}")
    if len(event_summary_rows) != 84:
        raise RuntimeError(
            f"Expected 84 event-summary rows, found {len(event_summary_rows)}"
        )

    by_scenario = {row["scenario_id"]: row for row in summary_rows}
    all_row = by_scenario["ALL_ELIGIBLE"]
    if int(all_row["total_retained_N"]) != EXPECTED_TOTAL:
        raise RuntimeError("ALL_ELIGIBLE total does not reproduce 4151")
    if int(all_row["flux_retained_N"]) != EXPECTED_FLUX_TOTAL:
        raise RuntimeError("ALL_ELIGIBLE flux total does not reproduce 3927")
    if int(all_row["magnitude_retained_N"]) != EXPECTED_MAGNITUDE_TOTAL:
        raise RuntimeError("ALL_ELIGIBLE magnitude total does not reproduce 224")
    if int(all_row["event_bands_nonempty_N"]) != 27:
        raise RuntimeError("ALL_ELIGIBLE does not retain all 27 event-bands")

    post_row = by_scenario["POST_REFERENCE_ALL"]
    if int(post_row["total_retained_N"]) != EXPECTED_POST_REFERENCE_TOTAL:
        raise RuntimeError(
            "POST_REFERENCE_ALL total does not match the committed data expectation"
        )

    for row in detail_rows:
        if int(row["retained_N"]) > int(row["eligible_N"]):
            raise RuntimeError(
                f"Scenario retains more than eligible for {row['scenario_id']} "
                f"{row['event']} {row['band']}"
            )
        if row["final_fitting_window_selected"] or row["model_time_defined"]:
            raise RuntimeError("Final/model flags must remain False")
        expected_applied = row["scenario_id"] != "ALL_ELIGIBLE"
        if row["temporal_window_scenario_applied"] != expected_applied:
            raise RuntimeError(
                f"Scenario-applied flag mismatch for {row['scenario_id']}"
            )

    detail_by_key = {
        (row["scenario_id"], row["event"], row["band"]): row for row in detail_rows
    }
    upper_sets = [(180, "180"), (365, "365"), (730, "730")]
    lower_sets = [(0, "0"), (-30, "M30"), (-60, "M60"), (-120, "M120")]
    event_band_keys = sorted({(row["event"], row["band"]) for row in detail_rows})

    for event, band in event_band_keys:
        for _, lower_label in lower_sets:
            counts = [
                int(detail_by_key[(f"REF_{lower_label}_{upper_label}", event, band)]["retained_N"])
                for _, upper_label in upper_sets
            ]
            if counts != sorted(counts):
                raise RuntimeError(
                    f"Upper-bound monotonicity failed for {event} {band} lower {lower_label}"
                )
        for _, upper_label in upper_sets:
            counts = [
                int(detail_by_key[(f"REF_{lower_label}_{upper_label}", event, band)]["retained_N"])
                for _, lower_label in lower_sets
            ]
            if counts != sorted(counts):
                raise RuntimeError(
                    f"Lower-bound monotonicity failed for {event} {band} upper {upper_label}"
                )


def main() -> int:
    manifest = read_csv(MANIFEST_PATH)
    if len(manifest) != 27:
        raise RuntimeError(f"Expected 27 manifest rows, found {len(manifest)}")
    events = {row["event"] for row in manifest}
    if len(events) != 6:
        raise RuntimeError(f"Expected 6 events, found {len(events)}")

    redshifts = read_redshifts(events)
    references = read_reference_epochs(events)
    measurements_by_key = {
        (row["event"], row["band"]): read_measurements(row, redshifts, references)
        for row in manifest
    }

    detail_rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        for manifest_row in manifest:
            detail_rows.append(
                build_detail_row(
                    scenario,
                    manifest_row,
                    measurements_by_key[(manifest_row["event"], manifest_row["band"])],
                    redshifts,
                    references,
                )
            )

    detail_by_scenario: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in detail_rows:
        detail_by_scenario[str(row["scenario_id"])].append(row)

    summary_rows = [
        build_summary_row(scenario, detail_by_scenario[str(scenario["scenario_id"])])
        for scenario in SCENARIOS
    ]

    event_summary_rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        scenario_id = str(scenario["scenario_id"])
        scenario_rows = detail_by_scenario[scenario_id]
        for event in sorted(events):
            event_summary_rows.append(
                build_event_summary_row(
                    scenario_id,
                    event,
                    [row for row in scenario_rows if row["event"] == event],
                    redshifts,
                )
            )

    validate_outputs(detail_rows, summary_rows, event_summary_rows)

    write_csv(DETAIL_PATH, detail_rows, DETAIL_FIELDS)
    write_csv(SUMMARY_PATH, summary_rows, SUMMARY_FIELDS)
    write_csv(EVENT_SUMMARY_PATH, event_summary_rows, EVENT_FIELDS)

    print("Candidate windows produce different retained sample sizes and temporal coverage.")
    print("The audit quantifies sensitivity to reference-anchored temporal selection.")
    print(REFERENCE_LIMITATION_NOTE)
    print(f"detail rows = {len(detail_rows)}")
    print(f"scenario summary rows = {len(summary_rows)}")
    print(f"event-summary rows = {len(event_summary_rows)}")
    print("scenario summaries:")
    for row in summary_rows:
        print(
            f"  {row['scenario_id']}: retained_N={row['total_retained_N']}, "
            f"retained_fraction={row['retained_fraction']!r}, "
            f"zero_bands={row['event_bands_zero_N']}, "
            f"min/median/max band N="
            f"{row['minimum_band_retained_N']}/"
            f"{row['median_band_retained_N']!r}/"
            f"{row['maximum_band_retained_N']}, "
            f"lt5/lt10/lt20="
            f"{row['bands_with_lt_5_measurements_N']}/"
            f"{row['bands_with_lt_10_measurements_N']}/"
            f"{row['bands_with_lt_20_measurements_N']}, "
            f"W1_W2={row['W1_W2_retained_N']}, "
            f"non_W1_W2={row['non_W1_W2_retained_N']}"
        )

    print("bounded scenario event summaries:")
    for scenario in SCENARIOS:
        if scenario["scenario_type"] != "bounded_reference_anchored_sensitivity_grid":
            continue
        scenario_id = str(scenario["scenario_id"])
        print(f"  {scenario_id}:")
        for row in [item for item in event_summary_rows if item["scenario_id"] == scenario_id]:
            print(
                f"    {row['event']}: retained_N={row['retained_N']}, "
                f"retained_fraction={row['retained_fraction']!r}"
            )

    print("monotonicity validation = PASS")
    print("final_fitting_window_selected = False for all rows")
    print("model_time_defined = False for all rows")
    print("No final fitting datasets, model fits, parameter bounds, optimizer, or model-selection policy were produced.")
    print(f"detail sha256 = {file_sha256(DETAIL_PATH)}")
    print(f"summary sha256 = {file_sha256(SUMMARY_PATH)}")
    print(f"event summary sha256 = {file_sha256(EVENT_SUMMARY_PATH)}")
    print(f"wrote {DETAIL_PATH.relative_to(REPO_ROOT)}")
    print(f"wrote {SUMMARY_PATH.relative_to(REPO_ROOT)}")
    print(f"wrote {EVENT_SUMMARY_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
