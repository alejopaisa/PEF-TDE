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

## DEC-002

| Field | Entry |
|---|---|
| Decision ID | DEC-002 |
| Scientific Question | Should alternative functional forms such as broken power laws or stretched exponentials participate directly in the definition of the PEF–TDE phenomenological class labels? |
| Historical Method | The historical analysis defines Standard, Floor, and Exponential as the minimal PEF–TDE comparison while also containing expanded comparisons with more flexible alternative functional forms. The historical presentation does not always maintain a sufficiently explicit separation between these two comparison levels. |
| Historical Evidence Level | A for the existence of the three-model core taxonomy in the surviving manuscript and classification evidence. Historical expanded comparisons also survive at varying provenance levels, but their exact implementation is not being frozen by this decision. |
| Reconstruction Decision | The reconstructed PEF–TDE analysis will define Standard, Floor, and Exponential as the core classification model space. Alternative functional forms will be evaluated separately as robustness or model-adequacy comparisons. An alternative model that provides a better statistical description will not silently redefine the PEF–TDE class labels. |
| Scientific Justification | The purpose of the core PEF–TDE comparison is to provide a deliberately small and interpretable observational taxonomy. Expanded models answer a different scientific question: whether the minimal taxonomy is sufficient to describe the observed light curve or whether additional functional flexibility is required. Separating these levels prevents the classification definition from changing whenever a new alternative model is introduced and makes the scope of the taxonomy reproducible. |
| Affected Data | None directly. |
| Affected Results | Future core classifications, expanded-model comparisons, model-adequacy flags, robustness results, tables, figures, and summary statements. |
| Affected Paper Sections | Framework and Methodology; Model Selection; Results; Robustness; Discussion; Appendices; Abstract/Conclusions where classifications are summarized. |
| Status | FROZEN |
| Date Frozen | 2026-09-23 |

DEC-002 freezes the separation between the core classification space and expanded robustness/model-adequacy comparisons. It does not choose the statistical selection criterion, information-criterion thresholds, goodness-of-fit thresholds, or the specific alternative models to be used.
