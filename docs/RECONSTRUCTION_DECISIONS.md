# Reconstruction Decisions

This log records every methodological choice that cannot be recovered historically or that is intentionally changed in the reconstructed analysis.

No scientific decisions are recorded yet.

## Decision Statuses

- `OPEN`: Decision is identified but unresolved.
- `UNDER_REVIEW`: Candidate decision is being evaluated.
- `FROZEN`: Decision is approved and fixed for the reconstruction.
- `SUPERSEDED`: Decision was replaced by a later decision.

## Decision Template

| Field | Entry |
|---|---|
| Decision ID |  |
| Scientific Question |  |
| Historical Method |  |
| Historical Evidence Level |  |
| Reconstruction Decision |  |
| Scientific Justification |  |
| Affected Data |  |
| Affected Results |  |
| Affected Paper Sections |  |
| Status |  |
| Date Frozen |  |

## DEC-001

| Field | Entry |
|---|---|
| Decision ID | DEC-001 |
| Scientific Question | Should the exponential reference time tp be fitted independently together with the exponential amplitude? |
| Historical Method | The historical manuscript writes the exponential contribution as `B exp[-(t - tp)/tau]` and describes tp as an onset/reference time. The exact numerical treatment of tp in the historical fitting implementation is not recoverable. |
| Historical Evidence Level | D for the exact numerical treatment of tp. |
| Reconstruction Decision | Do not fit tp as an independent free parameter. The reconstructed exponential model will use a fixed reference time and an amplitude defined relative to that fixed reference time. |
| Scientific Justification | The exponential term satisfies `B exp[-(t - tp)/tau] = (B exp[tp/tau]) exp[-t/tau]`. Therefore amplitude and time shift are structurally degenerate in this parameterization. A free tp cannot be independently identified from the amplitude using this functional form alone. Fixing the reference time removes this redundant degree of freedom and gives the exponential amplitude an explicit reference epoch. |
| Affected Data | None directly. This is a model-parameterization decision. |
| Affected Results | Future reconstructed exponential fits, parameter counts, information criteria, tau estimates, amplitudes, classifications, diagnostics, and derived tables/figures. |
| Affected Paper Sections | Framework and Methodology; Fitting Procedure; Results; Discussion; Appendices; Abstract/Conclusions where reconstructed model results are summarized. |
| Status | FROZEN |
| Date Frozen | 2026-09-23 |

DEC-001 freezes only the identifiability requirement. The definition and numerical value of the fixed exponential reference time remain an OPEN future reconstruction decision.
