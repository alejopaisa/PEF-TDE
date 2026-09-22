# Reproducibility Workflow

The required reconstruction chain is:

```text
raw data
-> preprocessing script
-> reconstructed dataset
-> analysis script
-> machine-readable result
-> generated table/figure
-> LaTeX manuscript
-> compiled PDF
```

A quantitative scientific claim cannot receive `FINAL` status unless its provenance can be traced through the applicable parts of this chain.

## Authority and Generation Policy

- Machine-readable result files are authoritative over manually typed manuscript numbers.
- Tables should be generated from result files whenever practical.
- Figures should be generated from result files.
- PDFs must never be manually edited.
- Scientific manuscript changes occur in LaTeX.
- The reconstructed PDF must be compiled from reconstructed LaTeX.

## Paper Policy

Historical paper:

- `paper/PEF_TDE_main_revision_major_integrated (1).tex`
- `paper/PEF_TDE_main_revision_major_integrated (1).pdf`

These files are frozen historical artifacts.

Future reconstructed manuscript:

- `paper/reconstructed/PEF_TDE_reconstructed.tex`
- `paper/reconstructed/PEF_TDE_reconstructed.pdf`

Do not create the reconstructed manuscript yet. It will be created only after validated scientific support begins to accumulate.

