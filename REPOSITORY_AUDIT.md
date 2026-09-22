# PEF-TDE Repository Audit

## Git status

Repository inspected on branch `main`.

Current status after configuration cleanup:

```text
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  modified:   .gitignore

Untracked files:
  REPOSITORY_AUDIT.md
```

The local `.idea/` directory is now ignored by Git and no longer appears as an untracked directory.

## GitHub remote

Configured remote:

```text
origin  https://github.com/alejopaisa/PEF-TDE.git (fetch)
origin  https://github.com/alejopaisa/PEF-TDE.git (push)
```

Main branch:

```text
* main 91d3094 [origin/main] Add files via upload
```

No `git push`, `git add`, or `git commit` was executed during this audit.

## Repository structure

Current summarized structure, excluding `.git/` internals and ignoring local `.idea/` project files:

```text
PEF-TDE/
  .gitignore
  LICENSE
  README.md
  REPOSITORY_AUDIT.md
  data/
    processed/
      .gitkeep
    raw/
      .gitkeep
  figures/
    .gitkeep
  paper/
    .gitkeep
    PEF_TDE_main_revision_major_integrated (1).pdf
    PEF_TDE_main_revision_major_integrated (1).tex
  scripts/
    .gitkeep
```

Tracked files before this audit:

```text
.gitignore
LICENSE
README.md
data/processed/.gitkeep
data/raw/.gitkeep
figures/.gitkeep
paper/.gitkeep
paper/PEF_TDE_main_revision_major_integrated (1).pdf
paper/PEF_TDE_main_revision_major_integrated (1).tex
scripts/.gitkeep
```

Directories requested for inspection:

- `data/`: present, with `raw/` and `processed/` placeholders only.
- `figures/`: present, placeholder only.
- `paper/`: present, contains one LaTeX source and one PDF manuscript.
- `scripts/`: present, placeholder only.
- `tables/`: not present.
- `results/`: not present.
- `robustness/`: not present.
- `docs/`: not present.

## Scientific assets found

Counts exclude `.git/` internals and ignored local `.idea/` files.

- Python scripts: 0
- CSV: 0
- JSON: 0
- LaTeX: 1
- PDF: 1
- PNG/JPG: 0
- ZIP: 0
- manifests: 0
- README/documentation: 1 README, 1 LICENSE, this audit report
- `.gitkeep` placeholders: 5

Scientific files currently found:

- `paper/PEF_TDE_main_revision_major_integrated (1).tex`
- `paper/PEF_TDE_main_revision_major_integrated (1).pdf`

## Potential issues

- `.idea/` was untracked because the root `.gitignore` did not contain a valid `.idea/` rule. The file ended with a corrupted null-byte version of `.idea/`, which Git did not interpret.
- `.idea/.gitignore` existed locally, but that only ignores selected files inside `.idea/`; it does not prevent `.idea/` itself from appearing as untracked at the repository root.
- The manuscript filename includes ` (1)`, which suggests it may be a downloaded or duplicated copy. This was not changed.
- `scripts/`, `figures/`, `data/raw/`, and `data/processed/` currently contain only `.gitkeep` placeholders. No computational pipeline is present yet.
- `tables/`, `results/`, `robustness/`, and `docs/` are not yet present.
- No dependency manifest was found (`requirements.txt`, `environment.yml`, `pyproject.toml`, `uv.lock`, `poetry.lock`, etc.).
- No reproducibility entry point was found, such as a main analysis script, Makefile, Snakemake workflow, or notebook index.
- No tests or validation scripts were found.
- Git reports a line-ending notice for `.gitignore`: `LF will be replaced by CRLF the next time Git touches it`. This is not blocking, but adding a future `.gitattributes` may make line endings explicit.

No files were deleted, moved, renamed, or scientifically modified.

## Recommended repository structure

A suitable reproducible scientific layout for PEF-TDE would be:

```text
PEF-TDE/
  README.md
  LICENSE
  CITATION.cff
  .gitignore
  .gitattributes
  requirements.txt or environment.yml
  data/
    raw/
    processed/
    README.md
  scripts/
    00_prepare_data.py
    01_fit_models.py
    02_make_figures.py
    03_make_tables.py
  notebooks/
  results/
    README.md
  figures/
  tables/
  paper/
    PEF_TDE_main.tex
    references.bib
  docs/
    reproducibility.md
  robustness/
  tests/
```

Recommended principles:

- Keep reproducible scientific inputs, scripts, figures, tables, PDFs, TeX, CSV, JSON, ZIP archives, and manifests versionable unless there is a size, privacy, or licensing reason not to.
- Ignore local environments, IDE metadata, caches, Python bytecode, temporary editor files, OS metadata, and LaTeX auxiliary build outputs.
- Add a dependency file before the first large scientific commit.
- Add a short reproduction guide that explains how to regenerate figures, tables, and the paper.
- Use Git LFS only if large binary scientific assets exceed practical GitHub repository limits.

## Git changes made

Only `.gitignore` was changed.

Changes made:

- Enabled `.idea/` so the entire local PyCharm project folder is ignored.
- Removed corrupted null-byte `.idea/` text that Git could not interpret.
- Added `.venv/` explicitly in addition to the existing `.venv` rule.
- Added local editor and OS ignores:
  - `.vscode/`
  - `.DS_Store`
  - `Thumbs.db`
  - `Desktop.ini`
- Added Python/local runtime ignores:
  - `*.pyo`
  - `*.pyd`
  - `*.swp`
  - `*.swo`
- Added LaTeX auxiliary build-output ignores while keeping `.tex` and `.pdf` versionable:
  - `*.aux`
  - `*.bbl`
  - `*.bcf`
  - `*.blg`
  - `*.fdb_latexmk`
  - `*.fls`
  - `*.lof`
  - `*.log`
  - `*.lot`
  - `*.out`
  - `*.run.xml`
  - `*.synctex.gz`
  - `*.toc`
- Removed automatic ignores for `MANIFEST` and `*.manifest` so scientific or reproducibility manifests remain visible to Git.

Rules were checked so that these are not automatically ignored:

- `*.csv`
- `*.json`
- `*.tex`
- `*.pdf`
- `*.png`
- `*.zip`
- Python scripts
- manifests

## Next recommended step

Before the first large commit, review this audit and decide the intended reproducibility layout. The next practical step should be to add a minimal reproducibility scaffold without moving existing scientific files yet:

- dependency manifest (`requirements.txt`, `environment.yml`, or `pyproject.toml`);
- `docs/reproducibility.md`;
- `data/README.md`;
- optional `.gitattributes` for line endings and large binary handling;
- a clear decision about whether the current manuscript filename should be renamed later.
