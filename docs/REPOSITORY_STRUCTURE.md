# PEF-TDE Repository Structure

This repository is organized to support reproducible scientific development for the PEF-TDE project. Existing scientific files should stay in place until a reviewed migration plan is approved.

## Root files

- `README.md`: project overview.
- `LICENSE`: repository license.
- `.gitignore`: local, cache, environment, editor, and build-output ignore rules.
- `REPOSITORY_AUDIT.md`: current repository audit and preparation notes.

## `data/`

Stores scientific input data and derived data products.

- `data/raw/`: original raw light-curve packages and raw observational inputs.
- `data/processed/`: processed datasets used by analysis scripts and paper outputs.
- `data/metadata/`: filter wavelength metadata, data dictionaries, provenance files, and machine-readable metadata needed for reproducibility.

## `results/`

Stores generated scientific outputs that are part of the reproducible record.

- `results/model_selection/`: AICc tables, model comparison outputs, and selection summaries.
- `results/residuals/`: residual diagnostics and related validation outputs.
- `results/robustness/`: robustness checks and sensitivity-analysis outputs.
- `results/multistart/`: multistart validation outputs, including AT2019qiz and related fit-stability products.

## `figures/`

Stores figures intended for inspection, reporting, or publication.

- `figures/main/`: main paper or presentation figures.
- `figures/diagnostics/`: diagnostic plots, residual plots, robustness plots, and supporting visual checks.

## `tables/`

Stores reproducible tables used by the manuscript, appendices, diagnostics, and validation summaries.

## `scripts/`

Stores Python scripts and related reproducibility code for preparing data, fitting models, generating results, making figures, and building tables.

## `paper/`

Stores manuscript source files, compiled manuscript PDFs, bibliography files, and paper-specific assets. Existing manuscript files remain in this directory.

## `docs/`

Stores repository documentation, reproducibility notes, workflow descriptions, and development guidance.

## `archive/`

Stores externally prepared packages or historical materials that should be preserved but not mixed directly into the active analysis layout until reviewed.

Potential future archive inputs include:

- `PEF_TDE_complete_repo_package.zip`
- `PEF_TDE_raw_lightcurves_package_v2.zip`
- `AT2019qiz_multistart_validation.zip`
- `PEF_TDE_multistart_analysis_outputs.zip`

Do not unpack or reorganize archived scientific packages without a reviewed plan.
