#!/usr/bin/env python
"""Audit local light-curve behavior around candidate decline-phase anchors.

This diagnostic is model-independent. It compares reconstructed eligible
measurements around current verified reference epochs and published alternative
epochs without selecting an anchor, selecting a fitting window, defining model
time, or fitting any model.
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
CURRENT_REFERENCE_PATH = (
    REPO_ROOT / "data" / "metadata" / "RECONSTRUCTION_REFERENCE_EPOCH_PROVENANCE.csv"
)
ALTERNATIVE_REFERENCE_PATH = (
    REPO_ROOT / "data" / "metadata" / "RECONSTRUCTION_REFERENCE_EPOCH_ALTERNATIVES.csv"
)
REDSHIFT_PATH = (
    REPO_ROOT / "data" / "metadata" / "RECONSTRUCTION_REDSHIFT_PROVENANCE.csv"
)
MANIFEST_PATH = (
    REPO_ROOT
    / "data"
    / "metadata"
    / "RECONSTRUCTED_ELIGIBLE_MEASUREMENT_MANIFEST.csv"
)
OUTPUT_DIR = REPO_ROOT / "results" / "reconstruction" / "temporal"
DETAIL_PATH = OUTPUT_DIR / "DECLINE_PHASE_ANCHOR_AUDIT.csv"
EVENT_SUMMARY_PATH = OUTPUT_DIR / "DECLINE_PHASE_ANCHOR_EVENT_SUMMARY.csv"

DIAGNOSTIC_HALF_WIDTHS_REST_DAYS = [30.0, 60.0, 120.0]
EXPECTED_CURRENT_MJDS = {
    "AT2018hyz": 58429.0,
    "AT2019qiz": 58764.0,
    "AT2020wey": 59152.0,
    "AT2020ysg": 59122.64,
    "AT2020yue": 59179.44,
    "AT2020zso": 59184.0,
}

REFERENCE_HETEROGENEITY_NOTE = (
    "The anchor candidates represent heterogeneous literature definitions "
    "including bolometric, single-band, and fitted multiband epochs. This audit "
    "compares local observational behavior relative to them but does not assume "
    "they represent one homogeneous physical quantity."
)

DETAIL_NOTE = (
    "Diagnostic local-neighborhood measurement summary only. The brightest "
    "observed local measurement may be sensitive to cadence, noise, or outliers "
    "and is not interpreted as a true peak, physical peak, fitted peak, decline "
    "anchor, or model-time origin."
)

DETAIL_FIELDS = [
    "anchor_source",
    "anchor_id",
    "event",
    "band",
    "measurement_mode",
    "anchor_mjd",
    "anchor_definition",
    "anchor_source_authors",
    "anchor_source_year",
    "anchor_doi",
    "anchor_source_location",
    "anchor_provenance_note",
    "redshift_adopted",
    "diagnostic_half_width_rest_days",
    "eligible_N",
    "local_N",
    "local_pre_anchor_N",
    "local_at_anchor_N",
    "local_post_anchor_N",
    "nearest_pre_anchor_mjd",
    "nearest_pre_anchor_rest_days",
    "nearest_post_anchor_mjd",
    "nearest_post_anchor_rest_days",
    "local_mjd_min",
    "local_mjd_max",
    "local_span_rest_days",
    "local_brightest_observed_mjd",
    "local_brightest_offset_rest_days",
    "local_brightest_has_pre_measurement",
    "local_brightest_has_post_measurement",
    "pre_adjacent_steps_N",
    "pre_rising_steps_N",
    "pre_declining_steps_N",
    "pre_tied_steps_N",
    "pre_rising_step_fraction",
    "post_adjacent_steps_N",
    "post_rising_steps_N",
    "post_declining_steps_N",
    "post_tied_steps_N",
    "post_declining_step_fraction",
    "final_decline_anchor_selected",
    "final_fitting_window_selected",
    "model_time_defined",
    "notes",
]

EVENT_FIELDS = [
    "anchor_source",
    "anchor_id",
    "event",
    "anchor_mjd",
    "anchor_definition",
    "diagnostic_half_width_rest_days",
    "bands_N",
    "bands_with_local_data_N",
    "bands_with_pre_anchor_data_N",
    "bands_with_post_anchor_data_N",
    "bands_with_both_sides_N",
    "bands_with_brightest_before_anchor_N",
    "bands_with_brightest_at_anchor_N",
    "bands_with_brightest_after_anchor_N",
    "median_brightest_offset_rest_days",
    "minimum_brightest_offset_rest_days",
    "maximum_brightest_offset_rest_days",
    "bands_with_pre_step_diagnostic_N",
    "bands_with_post_step_diagnostic_N",
    "median_pre_rising_step_fraction",
    "median_post_declining_step_fraction",
    "final_decline_anchor_selected",
    "final_fitting_window_selected",
    "model_time_defined",
    "reference_heterogeneity_note",
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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_current_anchors() -> list[dict[str, object]]:
    rows = read_csv(CURRENT_REFERENCE_PATH)
    if len(rows) != 6:
        raise RuntimeError(f"Expected 6 current reference rows, found {len(rows)}")

    anchors: list[dict[str, object]] = []
    seen: set[str] = set()
    for row in rows:
        event = row["event"]
        if event in seen:
            raise RuntimeError(f"Duplicate current reference event {event}")
        seen.add(event)
        reference_mjd = finite_float(row["reference_mjd"], f"{event} reference MJD")
        if reference_mjd != EXPECTED_CURRENT_MJDS[event]:
            raise RuntimeError(
                f"Unexpected current reference MJD for {event}: {reference_mjd!r}"
            )
        if row["value_verification_status"] != "VERIFIED_EXACT":
            raise RuntimeError(f"Unexpected current reference status for {event}")
        if row["absolute_mjd_status"] != "ABSOLUTE_MJD_NOT_DIVIDED_BY_1_PLUS_Z":
            raise RuntimeError(f"Unexpected absolute MJD status for {event}")
        definition = row["reference_epoch_type"].strip()
        if not definition:
            raise RuntimeError(f"Blank current reference definition for {event}")
        anchors.append(
            {
                "anchor_source": "CURRENT",
                "anchor_id": "CURRENT",
                "event": event,
                "anchor_mjd": reference_mjd,
                "anchor_definition": definition,
                "anchor_source_authors": row["source_authors"],
                "anchor_source_year": row["source_year"],
                "anchor_doi": row["doi"],
                "anchor_source_location": row["source_location"],
                "anchor_provenance_note": row["notes"],
            }
        )

    if set(seen) != set(EXPECTED_CURRENT_MJDS):
        raise RuntimeError("Current reference events do not match expected six events")
    return sorted(anchors, key=lambda item: str(item["event"]))


def read_alternative_anchors() -> list[dict[str, object]]:
    rows = read_csv(ALTERNATIVE_REFERENCE_PATH)
    if len(rows) != 10:
        raise RuntimeError(f"Expected 10 alternative reference rows, found {len(rows)}")

    anchors: list[dict[str, object]] = []
    seen: set[tuple[str, float]] = set()
    for row in rows:
        event = row["event"]
        alternative_mjd = finite_float(row["alternative_mjd"], f"{event} alternative MJD")
        key = (event, alternative_mjd)
        if key in seen:
            raise RuntimeError(f"Duplicate alternative event/MJD pair {event} {alternative_mjd!r}")
        seen.add(key)
        definition = row["alternative_definition"].strip()
        if not definition:
            raise RuntimeError(f"Blank alternative reference definition for {event}")
        anchor_id = "ALT_" + fnum(alternative_mjd).replace(".", "p")
        anchors.append(
            {
                "anchor_source": "PUBLISHED_ALTERNATIVE",
                "anchor_id": anchor_id,
                "event": event,
                "anchor_mjd": alternative_mjd,
                "anchor_definition": definition,
                "anchor_source_authors": row["source_authors"],
                "anchor_source_year": row["source_year"],
                "anchor_doi": row["doi"],
                "anchor_source_location": row["source_location"],
                "anchor_provenance_note": row["provenance_note"],
            }
        )
    return sorted(
        anchors,
        key=lambda item: (str(item["event"]), float(item["anchor_mjd"]), str(item["anchor_id"])),
    )


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
    if len(out) != 6:
        raise RuntimeError(f"Expected 6 adopted redshifts, found {len(out)}")
    return out


def read_manifest() -> list[dict[str, str]]:
    rows = read_csv(MANIFEST_PATH)
    if len(rows) != 27:
        raise RuntimeError(f"Expected 27 manifest rows, found {len(rows)}")
    keys = [(row["event"], row["band"]) for row in rows]
    if len(set(keys)) != 27:
        raise RuntimeError("Manifest event-band keys are not unique")

    total = sum(int(row["reconstructed_eligible_N"]) for row in rows)
    flux_total = sum(
        int(row["reconstructed_eligible_N"])
        for row in rows
        if row["measurement_mode"] == "FLUX"
    )
    magnitude_total = sum(
        int(row["reconstructed_eligible_N"])
        for row in rows
        if row["measurement_mode"] == "MAGNITUDE"
    )
    if total != 4151:
        raise RuntimeError(f"Expected 4151 eligible measurements, found {total}")
    if flux_total != 3927:
        raise RuntimeError(f"Expected 3927 eligible flux measurements, found {flux_total}")
    if magnitude_total != 224:
        raise RuntimeError(
            f"Expected 224 eligible magnitude measurements, found {magnitude_total}"
        )
    return rows


def read_measurements(manifest_row: dict[str, str]) -> list[dict[str, object]]:
    event = manifest_row["event"]
    band = manifest_row["band"]
    mode = manifest_row["measurement_mode"]
    path = REPO_ROOT / manifest_row["output_file"]
    rows: list[dict[str, object]] = []
    for raw in read_csv(path):
        mjd = finite_float(raw["mjd"], f"{event} {band} source MJD")
        if mode == "FLUX":
            brightness = finite_float(raw["flux"], f"{event} {band} flux")
        elif mode == "MAGNITUDE":
            brightness = -finite_float(raw["magnitude"], f"{event} {band} magnitude")
        else:
            raise RuntimeError(f"Unexpected measurement mode {mode!r}")
        rows.append(
            {
                "mjd": mjd,
                "source_row_index": int(raw["source_row_index"]),
                "brightness_orientation": brightness,
            }
        )
    rows.sort(key=lambda row: (float(row["mjd"]), int(row["source_row_index"])))
    expected = int(manifest_row["reconstructed_eligible_N"])
    if len(rows) != expected:
        raise RuntimeError(f"Manifest count mismatch for {event} {band}")
    return rows


def adjacent_step_counts(rows: list[dict[str, object]]) -> dict[str, object]:
    adjacent = 0
    rising = 0
    declining = 0
    tied = 0
    for index in range(1, len(rows)):
        delta_mjd = float(rows[index]["mjd"]) - float(rows[index - 1]["mjd"])
        # Zero-time pairs do not represent temporal evolution.
        if delta_mjd <= 0.0:
            continue
        adjacent += 1
        delta = float(rows[index]["brightness_orientation"]) - float(
            rows[index - 1]["brightness_orientation"]
        )
        if delta > 0.0:
            rising += 1
        elif delta < 0.0:
            declining += 1
        else:
            tied += 1
    if rising + declining + tied != adjacent:
        raise RuntimeError("Adjacent-step count mismatch")
    return {
        "adjacent": adjacent,
        "rising": rising,
        "declining": declining,
        "tied": tied,
    }


def build_detail_row(
    anchor: dict[str, object],
    manifest_row: dict[str, str],
    measurements: list[dict[str, object]],
    redshifts: dict[str, float],
    half_width_rest: float,
) -> dict[str, object]:
    event = str(anchor["event"])
    z = redshifts[event]
    rest_factor = 1.0 + z
    anchor_mjd = float(anchor["anchor_mjd"])
    local = [
        row
        for row in measurements
        if abs((float(row["mjd"]) - anchor_mjd) / rest_factor) <= half_width_rest
    ]
    pre_rows = [row for row in local if float(row["mjd"]) < anchor_mjd]
    at_rows = [row for row in local if float(row["mjd"]) == anchor_mjd]
    post_rows = [row for row in local if float(row["mjd"]) > anchor_mjd]
    pre_steps = adjacent_step_counts(pre_rows)
    post_steps = adjacent_step_counts(post_rows)

    local_mjds = [float(row["mjd"]) for row in local]
    brightest = None
    if local:
        brightest = sorted(
            local,
            key=lambda row: (
                -float(row["brightness_orientation"]),
                float(row["mjd"]),
                int(row["source_row_index"]),
            ),
        )[0]

    nearest_pre = max(pre_rows, key=lambda row: float(row["mjd"])) if pre_rows else None
    nearest_post = min(post_rows, key=lambda row: float(row["mjd"])) if post_rows else None
    brightest_mjd = float(brightest["mjd"]) if brightest else None

    return {
        "anchor_source": anchor["anchor_source"],
        "anchor_id": anchor["anchor_id"],
        "event": event,
        "band": manifest_row["band"],
        "measurement_mode": manifest_row["measurement_mode"],
        "anchor_mjd": anchor_mjd,
        "anchor_definition": anchor["anchor_definition"],
        "anchor_source_authors": anchor["anchor_source_authors"],
        "anchor_source_year": anchor["anchor_source_year"],
        "anchor_doi": anchor["anchor_doi"],
        "anchor_source_location": anchor["anchor_source_location"],
        "anchor_provenance_note": anchor["anchor_provenance_note"],
        "redshift_adopted": z,
        "diagnostic_half_width_rest_days": half_width_rest,
        "eligible_N": len(measurements),
        "local_N": len(local),
        "local_pre_anchor_N": len(pre_rows),
        "local_at_anchor_N": len(at_rows),
        "local_post_anchor_N": len(post_rows),
        "nearest_pre_anchor_mjd": nearest_pre["mjd"] if nearest_pre else None,
        "nearest_pre_anchor_rest_days": (
            (float(nearest_pre["mjd"]) - anchor_mjd) / rest_factor if nearest_pre else None
        ),
        "nearest_post_anchor_mjd": nearest_post["mjd"] if nearest_post else None,
        "nearest_post_anchor_rest_days": (
            (float(nearest_post["mjd"]) - anchor_mjd) / rest_factor
            if nearest_post
            else None
        ),
        "local_mjd_min": min(local_mjds) if local_mjds else None,
        "local_mjd_max": max(local_mjds) if local_mjds else None,
        "local_span_rest_days": (
            (max(local_mjds) - min(local_mjds)) / rest_factor if local_mjds else None
        ),
        "local_brightest_observed_mjd": brightest_mjd,
        "local_brightest_offset_rest_days": (
            (brightest_mjd - anchor_mjd) / rest_factor if brightest_mjd is not None else None
        ),
        "local_brightest_has_pre_measurement": (
            any(float(row["mjd"]) < brightest_mjd for row in local)
            if brightest_mjd is not None
            else None
        ),
        "local_brightest_has_post_measurement": (
            any(float(row["mjd"]) > brightest_mjd for row in local)
            if brightest_mjd is not None
            else None
        ),
        "pre_adjacent_steps_N": pre_steps["adjacent"],
        "pre_rising_steps_N": pre_steps["rising"],
        "pre_declining_steps_N": pre_steps["declining"],
        "pre_tied_steps_N": pre_steps["tied"],
        "pre_rising_step_fraction": (
            pre_steps["rising"] / float(pre_steps["adjacent"])
            if pre_steps["adjacent"]
            else None
        ),
        "post_adjacent_steps_N": post_steps["adjacent"],
        "post_rising_steps_N": post_steps["rising"],
        "post_declining_steps_N": post_steps["declining"],
        "post_tied_steps_N": post_steps["tied"],
        "post_declining_step_fraction": (
            post_steps["declining"] / float(post_steps["adjacent"])
            if post_steps["adjacent"]
            else None
        ),
        "final_decline_anchor_selected": False,
        "final_fitting_window_selected": False,
        "model_time_defined": False,
        "notes": DETAIL_NOTE,
    }


def nullable_median(values: list[float]) -> float | None:
    return median(values) if values else None


def build_event_summary_row(
    anchor: dict[str, object],
    half_width_rest: float,
    detail_rows: list[dict[str, object]],
) -> dict[str, object]:
    offsets = [
        float(row["local_brightest_offset_rest_days"])
        for row in detail_rows
        if row["local_brightest_offset_rest_days"] is not None
    ]
    pre_fractions = [
        float(row["pre_rising_step_fraction"])
        for row in detail_rows
        if row["pre_rising_step_fraction"] is not None
    ]
    post_fractions = [
        float(row["post_declining_step_fraction"])
        for row in detail_rows
        if row["post_declining_step_fraction"] is not None
    ]
    return {
        "anchor_source": anchor["anchor_source"],
        "anchor_id": anchor["anchor_id"],
        "event": anchor["event"],
        "anchor_mjd": anchor["anchor_mjd"],
        "anchor_definition": anchor["anchor_definition"],
        "diagnostic_half_width_rest_days": half_width_rest,
        "bands_N": len(detail_rows),
        "bands_with_local_data_N": sum(1 for row in detail_rows if int(row["local_N"]) > 0),
        "bands_with_pre_anchor_data_N": sum(
            1 for row in detail_rows if int(row["local_pre_anchor_N"]) > 0
        ),
        "bands_with_post_anchor_data_N": sum(
            1 for row in detail_rows if int(row["local_post_anchor_N"]) > 0
        ),
        "bands_with_both_sides_N": sum(
            1
            for row in detail_rows
            if int(row["local_pre_anchor_N"]) > 0 and int(row["local_post_anchor_N"]) > 0
        ),
        "bands_with_brightest_before_anchor_N": sum(
            1
            for row in detail_rows
            if row["local_brightest_offset_rest_days"] is not None
            and float(row["local_brightest_offset_rest_days"]) < 0.0
        ),
        "bands_with_brightest_at_anchor_N": sum(
            1
            for row in detail_rows
            if row["local_brightest_offset_rest_days"] is not None
            and float(row["local_brightest_offset_rest_days"]) == 0.0
        ),
        "bands_with_brightest_after_anchor_N": sum(
            1
            for row in detail_rows
            if row["local_brightest_offset_rest_days"] is not None
            and float(row["local_brightest_offset_rest_days"]) > 0.0
        ),
        "median_brightest_offset_rest_days": nullable_median(offsets),
        "minimum_brightest_offset_rest_days": min(offsets) if offsets else None,
        "maximum_brightest_offset_rest_days": max(offsets) if offsets else None,
        "bands_with_pre_step_diagnostic_N": sum(
            1 for row in detail_rows if int(row["pre_adjacent_steps_N"]) > 0
        ),
        "bands_with_post_step_diagnostic_N": sum(
            1 for row in detail_rows if int(row["post_adjacent_steps_N"]) > 0
        ),
        "median_pre_rising_step_fraction": nullable_median(pre_fractions),
        "median_post_declining_step_fraction": nullable_median(post_fractions),
        "final_decline_anchor_selected": False,
        "final_fitting_window_selected": False,
        "model_time_defined": False,
        "reference_heterogeneity_note": REFERENCE_HETEROGENEITY_NOTE,
    }


def validate_outputs(
    detail_rows: list[dict[str, object]],
    event_summary_rows: list[dict[str, object]],
) -> None:
    if len(detail_rows) != 213:
        raise RuntimeError(f"Expected 213 detail rows, found {len(detail_rows)}")
    detail_keys = {
        (
            row["anchor_source"],
            row["anchor_id"],
            row["event"],
            row["band"],
            row["diagnostic_half_width_rest_days"],
        )
        for row in detail_rows
    }
    if len(detail_keys) != 213:
        raise RuntimeError("Detail keys are not unique")
    if len(event_summary_rows) != 48:
        raise RuntimeError(f"Expected 48 event-summary rows, found {len(event_summary_rows)}")
    summary_keys = {
        (
            row["anchor_source"],
            row["anchor_id"],
            row["event"],
            row["diagnostic_half_width_rest_days"],
        )
        for row in event_summary_rows
    }
    if len(summary_keys) != 48:
        raise RuntimeError("Event-summary keys are not unique")

    grouped: dict[tuple[object, object, object, object], dict[float, int]] = defaultdict(dict)
    for row in detail_rows:
        local_n = int(row["local_N"])
        eligible_n = int(row["eligible_N"])
        if local_n > eligible_n:
            raise RuntimeError("Local count exceeds eligible count")
        if (
            int(row["local_pre_anchor_N"])
            + int(row["local_at_anchor_N"])
            + int(row["local_post_anchor_N"])
            != local_n
        ):
            raise RuntimeError("Pre/at/post local counts do not sum to local_N")
        if (
            int(row["pre_rising_steps_N"])
            + int(row["pre_declining_steps_N"])
            + int(row["pre_tied_steps_N"])
            != int(row["pre_adjacent_steps_N"])
        ):
            raise RuntimeError("Pre-anchor step counts do not sum")
        if (
            int(row["post_rising_steps_N"])
            + int(row["post_declining_steps_N"])
            + int(row["post_tied_steps_N"])
            != int(row["post_adjacent_steps_N"])
        ):
            raise RuntimeError("Post-anchor step counts do not sum")
        for field in ["pre_rising_step_fraction", "post_declining_step_fraction"]:
            if row[field] is not None and not (0.0 <= float(row[field]) <= 1.0):
                raise RuntimeError(f"Fraction out of range for {field}")
        if local_n == 0:
            blank_fields = [
                "local_mjd_min",
                "local_mjd_max",
                "local_span_rest_days",
                "local_brightest_observed_mjd",
                "local_brightest_offset_rest_days",
                "local_brightest_has_pre_measurement",
                "local_brightest_has_post_measurement",
                "pre_rising_step_fraction",
                "post_declining_step_fraction",
            ]
            if any(row[field] is not None for field in blank_fields):
                raise RuntimeError("Local-empty row contains measurement-dependent values")
        else:
            offset = float(row["local_brightest_offset_rest_days"])
            half_width = float(row["diagnostic_half_width_rest_days"])
            if abs(offset) > half_width:
                raise RuntimeError("Brightest local measurement lies outside neighborhood")
        if row["final_decline_anchor_selected"] or row["final_fitting_window_selected"]:
            raise RuntimeError("Selection flags must remain False")
        if row["model_time_defined"]:
            raise RuntimeError("model_time_defined must remain False")

        grouped[
            (row["anchor_source"], row["anchor_id"], row["event"], row["band"])
        ][float(row["diagnostic_half_width_rest_days"])] = local_n

    for key, values in grouped.items():
        counts = [values[half_width] for half_width in DIAGNOSTIC_HALF_WIDTHS_REST_DAYS]
        if counts != sorted(counts):
            raise RuntimeError(f"Local-N monotonicity failed for {key}: {counts}")

    for row in event_summary_rows:
        if row["final_decline_anchor_selected"] or row["final_fitting_window_selected"]:
            raise RuntimeError("Event-summary selection flags must remain False")
        if row["model_time_defined"]:
            raise RuntimeError("Event-summary model_time_defined must remain False")
        if row["reference_heterogeneity_note"] != REFERENCE_HETEROGENEITY_NOTE:
            raise RuntimeError("Missing required reference heterogeneity note")


def distribution(values: list[float]) -> tuple[float | None, float | None, float | None]:
    if not values:
        return None, None, None
    return min(values), median(values), max(values)


def main() -> int:
    current_anchors = read_current_anchors()
    alternative_anchors = read_alternative_anchors()
    anchors = current_anchors + alternative_anchors
    if len(anchors) != 16:
        raise RuntimeError(f"Expected 16 combined anchors, found {len(anchors)}")

    events = {str(anchor["event"]) for anchor in anchors}
    redshifts = read_redshifts(events)
    manifest = read_manifest()
    manifest_by_event: dict[str, list[dict[str, str]]] = defaultdict(list)
    measurements_by_key = {}
    for row in manifest:
        manifest_by_event[row["event"]].append(row)
        measurements_by_key[(row["event"], row["band"])] = read_measurements(row)

    detail_rows: list[dict[str, object]] = []
    for anchor in anchors:
        event = str(anchor["event"])
        for manifest_row in sorted(manifest_by_event[event], key=lambda item: item["band"]):
            measurements = measurements_by_key[(event, manifest_row["band"])]
            for half_width in DIAGNOSTIC_HALF_WIDTHS_REST_DAYS:
                detail_rows.append(
                    build_detail_row(anchor, manifest_row, measurements, redshifts, half_width)
                )

    detail_by_summary_key: dict[tuple[object, object, object, float], list[dict[str, object]]] = (
        defaultdict(list)
    )
    for row in detail_rows:
        detail_by_summary_key[
            (
                row["anchor_source"],
                row["anchor_id"],
                row["event"],
                float(row["diagnostic_half_width_rest_days"]),
            )
        ].append(row)

    anchor_by_summary_key = {
        (
            anchor["anchor_source"],
            anchor["anchor_id"],
            anchor["event"],
            half_width,
        ): anchor
        for anchor in anchors
        for half_width in DIAGNOSTIC_HALF_WIDTHS_REST_DAYS
    }
    event_summary_rows = [
        build_event_summary_row(anchor_by_summary_key[key], key[3], rows)
        for key, rows in sorted(
            detail_by_summary_key.items(),
            key=lambda item: (str(item[0][2]), str(item[0][0]), str(item[0][1]), item[0][3]),
        )
    ]

    validate_outputs(detail_rows, event_summary_rows)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(DETAIL_PATH, detail_rows, DETAIL_FIELDS)
    write_csv(EVENT_SUMMARY_PATH, event_summary_rows, EVENT_FIELDS)

    local_zero_by_horizon = {
        half_width: sum(
            1
            for row in detail_rows
            if float(row["diagnostic_half_width_rest_days"]) == half_width
            and int(row["local_N"]) == 0
        )
        for half_width in DIAGNOSTIC_HALF_WIDTHS_REST_DAYS
    }
    pre_step_by_horizon = {
        half_width: sum(
            1
            for row in detail_rows
            if float(row["diagnostic_half_width_rest_days"]) == half_width
            and int(row["pre_adjacent_steps_N"]) > 0
        )
        for half_width in DIAGNOSTIC_HALF_WIDTHS_REST_DAYS
    }
    post_step_by_horizon = {
        half_width: sum(
            1
            for row in detail_rows
            if float(row["diagnostic_half_width_rest_days"]) == half_width
            and int(row["post_adjacent_steps_N"]) > 0
        )
        for half_width in DIAGNOSTIC_HALF_WIDTHS_REST_DAYS
    }
    brightest_by_horizon = {}
    for half_width in DIAGNOSTIC_HALF_WIDTHS_REST_DAYS:
        offsets = [
            float(row["local_brightest_offset_rest_days"])
            for row in detail_rows
            if float(row["diagnostic_half_width_rest_days"]) == half_width
            and row["local_brightest_offset_rest_days"] is not None
        ]
        brightest_by_horizon[half_width] = distribution(offsets)

    print(f"current anchors = {len(current_anchors)}")
    print(f"published alternative anchors = {len(alternative_anchors)}")
    print(f"combined anchors = {len(anchors)}")
    print(f"detail rows = {len(detail_rows)}")
    print(
        "detail unique keys = "
        + str(
            len(
                {
                    (
                        row["anchor_source"],
                        row["anchor_id"],
                        row["event"],
                        row["band"],
                        row["diagnostic_half_width_rest_days"],
                    )
                    for row in detail_rows
                }
            )
        )
    )
    print(f"event-summary rows = {len(event_summary_rows)}")
    print(
        "event-summary unique keys = "
        + str(
            len(
                {
                    (
                        row["anchor_source"],
                        row["anchor_id"],
                        row["event"],
                        row["diagnostic_half_width_rest_days"],
                    )
                    for row in event_summary_rows
                }
            )
        )
    )
    print("eligible measurements = 4151")
    print("flux eligible measurements = 3927")
    print("magnitude eligible measurements = 224")
    print("local-N monotonicity across horizons = PASS")
    print("step-count consistency = PASS")
    print("fraction range validation = PASS")
    print("detail rows with local_N = 0 by horizon:")
    for half_width in DIAGNOSTIC_HALF_WIDTHS_REST_DAYS:
        print(f"  +/-{fnum(half_width)} rest days: {local_zero_by_horizon[half_width]}")
    print("event-band rows with usable pre-step diagnostics by horizon:")
    for half_width in DIAGNOSTIC_HALF_WIDTHS_REST_DAYS:
        print(f"  +/-{fnum(half_width)} rest days: {pre_step_by_horizon[half_width]}")
    print("event-band rows with usable post-step diagnostics by horizon:")
    for half_width in DIAGNOSTIC_HALF_WIDTHS_REST_DAYS:
        print(f"  +/-{fnum(half_width)} rest days: {post_step_by_horizon[half_width]}")
    print("local_brightest_offset_rest_days distribution by horizon:")
    for half_width in DIAGNOSTIC_HALF_WIDTHS_REST_DAYS:
        values = brightest_by_horizon[half_width]
        print(
            f"  +/-{fnum(half_width)} rest days: "
            f"min={fnum(values[0])}, median={fnum(values[1])}, max={fnum(values[2])}"
        )
    print("final_decline_anchor_selected = False for all rows")
    print("final_fitting_window_selected = False for all rows")
    print("model_time_defined = False for all rows")
    print("No fitting, AIC/AICc/BIC, ranking, anchor selection, fitting-window selection, or model-time definition was performed.")
    print(f"detail sha256 = {file_sha256(DETAIL_PATH)}")
    print(f"event summary sha256 = {file_sha256(EVENT_SUMMARY_PATH)}")
    print(f"wrote {DETAIL_PATH.relative_to(REPO_ROOT)}")
    print(f"wrote {EVENT_SUMMARY_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
