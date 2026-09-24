#!/usr/bin/env python
"""Audit sampling-structure sensitivity of decline-anchor diagnostics.

This script summarizes the validated decline-phase anchor diagnostic under
three structural band-availability subsets. It performs no fitting, weighting,
ranking, anchor selection, temporal-window selection, or model-time definition.
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
INPUT_PATH = (
    REPO_ROOT / "results" / "reconstruction" / "temporal" / "DECLINE_PHASE_ANCHOR_AUDIT.csv"
)
OUTPUT_PATH = (
    REPO_ROOT
    / "results"
    / "reconstruction"
    / "temporal"
    / "DECLINE_ANCHOR_SAMPLING_SENSITIVITY.csv"
)

SUBSETS = ["LOCAL_DATA", "BOTH_SIDES", "BIDIRECTIONAL_STEPS"]
HORIZONS = ["30.0", "60.0", "120.0"]

FIELDS = [
    "anchor_source",
    "anchor_id",
    "event",
    "anchor_mjd",
    "anchor_definition",
    "diagnostic_half_width_rest_days",
    "sampling_subset",
    "event_bands_total_N",
    "bands_in_subset_N",
    "bands_excluded_from_subset_N",
    "included_bands",
    "excluded_bands",
    "total_local_measurements_in_subset",
    "minimum_local_N_in_subset",
    "median_local_N_in_subset",
    "maximum_local_N_in_subset",
    "bands_with_brightest_before_anchor_N",
    "bands_with_brightest_at_anchor_N",
    "bands_with_brightest_after_anchor_N",
    "minimum_brightest_offset_rest_days",
    "median_brightest_offset_rest_days",
    "maximum_brightest_offset_rest_days",
    "bands_with_pre_step_diagnostic_N",
    "bands_with_post_step_diagnostic_N",
    "median_pre_rising_step_fraction",
    "median_post_declining_step_fraction",
    "final_decline_anchor_selected",
    "final_fitting_window_selected",
    "model_time_defined",
    "notes",
]

NOTES = {
    "LOCAL_DATA": (
        "Structural sensitivity subset: includes bands with at least one local "
        "measurement. This is not a quality threshold and does not select an anchor."
    ),
    "BOTH_SIDES": (
        "Structural sensitivity subset: includes bands with local measurements "
        "on both sides of the anchor. This is not a fitting-window rule and does "
        "not select an anchor."
    ),
    "BIDIRECTIONAL_STEPS": (
        "Structural sensitivity subset: includes bands with positive-time "
        "adjacent-step diagnostics on both sides of the anchor. This is not a "
        "minimum-N, cadence, instrument, or model-quality rule and does not select an anchor."
    ),
}


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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def maybe_float(value: str) -> float | None:
    return float(value) if value != "" else None


def subset_includes(row: dict[str, str], subset: str) -> bool:
    if subset == "LOCAL_DATA":
        return int(row["local_N"]) > 0
    if subset == "BOTH_SIDES":
        return int(row["local_pre_anchor_N"]) > 0 and int(row["local_post_anchor_N"]) > 0
    if subset == "BIDIRECTIONAL_STEPS":
        return int(row["pre_adjacent_steps_N"]) > 0 and int(row["post_adjacent_steps_N"]) > 0
    raise RuntimeError(f"Unexpected sampling subset {subset!r}")


def sorted_bands(rows: list[dict[str, str]]) -> list[str]:
    return sorted(row["band"] for row in rows)


def join_bands(bands: list[str]) -> str:
    return ";".join(bands)


def summary_stats(values: list[float]) -> tuple[float | None, float | None, float | None]:
    if not values:
        return None, None, None
    return min(values), median(values), max(values)


def build_subset_row(
    key: tuple[str, str, str, str],
    rows: list[dict[str, str]],
    subset: str,
) -> dict[str, object]:
    included = [row for row in rows if subset_includes(row, subset)]
    excluded = [row for row in rows if not subset_includes(row, subset)]
    local_counts = [int(row["local_N"]) for row in included]
    offsets = [
        float(row["local_brightest_offset_rest_days"])
        for row in included
        if row["local_brightest_offset_rest_days"] != ""
    ]
    pre_fractions = [
        float(row["pre_rising_step_fraction"])
        for row in included
        if row["pre_rising_step_fraction"] != ""
    ]
    post_fractions = [
        float(row["post_declining_step_fraction"])
        for row in included
        if row["post_declining_step_fraction"] != ""
    ]
    offset_min, offset_median, offset_max = summary_stats(offsets)

    exemplar = rows[0]
    return {
        "anchor_source": key[0],
        "anchor_id": key[1],
        "event": key[2],
        "anchor_mjd": exemplar["anchor_mjd"],
        "anchor_definition": exemplar["anchor_definition"],
        "diagnostic_half_width_rest_days": key[3],
        "sampling_subset": subset,
        "event_bands_total_N": len(rows),
        "bands_in_subset_N": len(included),
        "bands_excluded_from_subset_N": len(excluded),
        "included_bands": join_bands(sorted_bands(included)),
        "excluded_bands": join_bands(sorted_bands(excluded)),
        "total_local_measurements_in_subset": sum(local_counts),
        "minimum_local_N_in_subset": min(local_counts) if local_counts else None,
        "median_local_N_in_subset": median(local_counts) if local_counts else None,
        "maximum_local_N_in_subset": max(local_counts) if local_counts else None,
        "bands_with_brightest_before_anchor_N": sum(
            1
            for row in included
            if row["local_brightest_offset_rest_days"] != ""
            and float(row["local_brightest_offset_rest_days"]) < 0.0
        ),
        "bands_with_brightest_at_anchor_N": sum(
            1
            for row in included
            if row["local_brightest_offset_rest_days"] != ""
            and float(row["local_brightest_offset_rest_days"]) == 0.0
        ),
        "bands_with_brightest_after_anchor_N": sum(
            1
            for row in included
            if row["local_brightest_offset_rest_days"] != ""
            and float(row["local_brightest_offset_rest_days"]) > 0.0
        ),
        "minimum_brightest_offset_rest_days": offset_min,
        "median_brightest_offset_rest_days": offset_median,
        "maximum_brightest_offset_rest_days": offset_max,
        "bands_with_pre_step_diagnostic_N": sum(
            1 for row in included if int(row["pre_adjacent_steps_N"]) > 0
        ),
        "bands_with_post_step_diagnostic_N": sum(
            1 for row in included if int(row["post_adjacent_steps_N"]) > 0
        ),
        "median_pre_rising_step_fraction": median(pre_fractions)
        if pre_fractions
        else None,
        "median_post_declining_step_fraction": median(post_fractions)
        if post_fractions
        else None,
        "final_decline_anchor_selected": False,
        "final_fitting_window_selected": False,
        "model_time_defined": False,
        "notes": NOTES[subset],
    }


def validate_input(rows: list[dict[str, str]]) -> None:
    if len(rows) != 213:
        raise RuntimeError(f"Expected 213 decline-anchor detail rows, found {len(rows)}")
    keys = {
        (
            row["anchor_source"],
            row["anchor_id"],
            row["event"],
            row["band"],
            row["diagnostic_half_width_rest_days"],
        )
        for row in rows
    }
    if len(keys) != 213:
        raise RuntimeError("Decline-anchor detail keys are not unique")
    if len({(row["anchor_source"], row["anchor_id"], row["event"]) for row in rows}) != 16:
        raise RuntimeError("Expected 16 anchor/event combinations")


def validate_output(rows: list[dict[str, object]]) -> None:
    if len(rows) != 144:
        raise RuntimeError(f"Expected 144 sampling-sensitivity rows, found {len(rows)}")
    keys = {
        (
            row["anchor_source"],
            row["anchor_id"],
            row["event"],
            row["diagnostic_half_width_rest_days"],
            row["sampling_subset"],
        )
        for row in rows
    }
    if len(keys) != 144:
        raise RuntimeError("Sampling-sensitivity keys are not unique")

    by_anchor_horizon: dict[tuple[object, object, object, object], dict[str, dict[str, object]]] = (
        defaultdict(dict)
    )
    for row in rows:
        if row["final_decline_anchor_selected"] or row["final_fitting_window_selected"]:
            raise RuntimeError("Selection flags must remain False")
        if row["model_time_defined"]:
            raise RuntimeError("model_time_defined must remain False")
        if int(row["bands_in_subset_N"]) + int(row["bands_excluded_from_subset_N"]) != int(
            row["event_bands_total_N"]
        ):
            raise RuntimeError("Included/excluded band counts do not sum to total")
        by_anchor_horizon[
            (
                row["anchor_source"],
                row["anchor_id"],
                row["event"],
                row["diagnostic_half_width_rest_days"],
            )
        ][str(row["sampling_subset"])] = row

    if len(by_anchor_horizon) != 48:
        raise RuntimeError(f"Expected 48 anchor/horizon groups, found {len(by_anchor_horizon)}")

    for key, subsets in by_anchor_horizon.items():
        if set(subsets) != set(SUBSETS):
            raise RuntimeError(f"Missing subset rows for {key}")
        local = set(str(subsets["LOCAL_DATA"]["included_bands"]).split(";")) - {""}
        both = set(str(subsets["BOTH_SIDES"]["included_bands"]).split(";")) - {""}
        bidir = set(str(subsets["BIDIRECTIONAL_STEPS"]["included_bands"]).split(";")) - {""}
        if not bidir <= both <= local:
            raise RuntimeError(f"Subset nesting failed for {key}")
        counts = [
            int(subsets["BIDIRECTIONAL_STEPS"]["bands_in_subset_N"]),
            int(subsets["BOTH_SIDES"]["bands_in_subset_N"]),
            int(subsets["LOCAL_DATA"]["bands_in_subset_N"]),
        ]
        if counts != sorted(counts):
            raise RuntimeError(f"Subset count nesting failed for {key}: {counts}")


def sign(value: float | None) -> int | None:
    if value is None:
        return None
    if value > 0.0:
        return 1
    if value < 0.0:
        return -1
    return 0


def main() -> int:
    input_rows = read_csv(INPUT_PATH)
    validate_input(input_rows)

    grouped: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in input_rows:
        grouped[
            (
                row["anchor_source"],
                row["anchor_id"],
                row["event"],
                row["diagnostic_half_width_rest_days"],
            )
        ].append(row)

    output_rows: list[dict[str, object]] = []
    for key in sorted(grouped):
        rows = sorted(grouped[key], key=lambda item: item["band"])
        for subset in SUBSETS:
            output_rows.append(build_subset_row(key, rows, subset))

    validate_output(output_rows)
    write_csv(OUTPUT_PATH, output_rows, FIELDS)

    by_key = {
        (
            row["anchor_source"],
            row["anchor_id"],
            row["event"],
            row["diagnostic_half_width_rest_days"],
            row["sampling_subset"],
        ): row
        for row in output_rows
    }
    median_changes = []
    sign_changes = 0
    for key in sorted(grouped):
        local = by_key[(*key, "LOCAL_DATA")]
        bidir = by_key[(*key, "BIDIRECTIONAL_STEPS")]
        local_median = local["median_brightest_offset_rest_days"]
        bidir_median = bidir["median_brightest_offset_rest_days"]
        if local_median is None or bidir_median is None:
            continue
        diff = float(bidir_median) - float(local_median)
        if diff != 0.0:
            median_changes.append((abs(diff), diff, key, local_median, bidir_median))
        if sign(float(local_median)) != sign(float(bidir_median)):
            sign_changes += 1

    zero_subset_rows = sum(1 for row in output_rows if int(row["bands_in_subset_N"]) == 0)

    print(f"input detail rows = {len(input_rows)}")
    print(
        "input detail unique keys = "
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
                    for row in input_rows
                }
            )
        )
    )
    print(f"output rows = {len(output_rows)}")
    print(
        "output unique keys = "
        + str(
            len(
                {
                    (
                        row["anchor_source"],
                        row["anchor_id"],
                        row["event"],
                        row["diagnostic_half_width_rest_days"],
                        row["sampling_subset"],
                    )
                    for row in output_rows
                }
            )
        )
    )
    print("subset nesting = PASS")
    print("final_decline_anchor_selected = False for all rows")
    print("final_fitting_window_selected = False for all rows")
    print("model_time_defined = False for all rows")
    print("No fitting, AIC/AICc/BIC, weighting, ranking, anchor selection, or fitting-window selection was performed.")
    print(
        "median brightest-offset changes LOCAL_DATA vs BIDIRECTIONAL_STEPS = "
        + str(len(median_changes))
    )
    if median_changes:
        largest = max(median_changes, key=lambda item: (item[0], item[2]))
        print(
            "largest absolute median brightest-offset change = "
            f"{largest[0]!r} ({largest[2][2]} {largest[2][0]} {largest[2][1]} "
            f"+/-{largest[2][3]} rest days: LOCAL_DATA={largest[3]!r}, "
            f"BIDIRECTIONAL_STEPS={largest[4]!r})"
        )
    else:
        print("largest absolute median brightest-offset change = 0")
    print(f"median brightest-offset sign changes = {sign_changes}")
    print(f"subset rows with zero included bands = {zero_subset_rows}")
    print(f"sha256 = {file_sha256(OUTPUT_PATH)}")
    print(f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
