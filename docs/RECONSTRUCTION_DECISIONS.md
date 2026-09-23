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

## DEC-003

| Field | Entry |
|---|---|
| Decision ID | DEC-003 |
| Title / Topic | Canonical temporal coordinate and cross-band alignment |
| Scientific Question | What temporal reference should define reconstructed PEF–TDE timestamps so that different photometric bands preserve their true calendar alignment without assigning an artificial physical meaning to time zero? |
| Historical Method | The historical processed light curves use a band-relative coordinate: `time_days = MJD - min(MJD retained in that band)`. The reproducible temporal-coordinate audit verifies this relation for all 27 historical event-band datasets with maximum reconstruction error 0.0 days. Because the first retained MJD differs by band, historical `time_days=0` does not represent a common calendar epoch within multi-band events. |
| Historical Evidence Level | A for the recovered historical coordinate definition, supported by the processed data and reproducible temporal audit. |
| Reconstruction Decision | Source MJD timestamps are the canonical temporal reference for the reconstructed analysis. The reconstructed pipeline must not independently redefine time zero for each photometric band. A translated numerical coordinate may be used internally for numerical convenience, provided that the translation: 1. is derived explicitly from source MJD, 2. is applied consistently across the relevant bands, 3. is documented and reproducible, 4. is exactly reversible to MJD, and 5. is not assigned physical meaning. Publication-reference epochs such as reported peak times remain scientific metadata and are not automatically adopted as the coordinate origin. |
| Scientific Justification | The validated temporal audit demonstrates that band-specific historical zero dates differ across bands of the same event. Verified spreads include approximately: AT2019qiz = 6.78 d; AT2020wey = 1467.81 d; AT2020ysg = 2000.35 d; AT2020yue = 1679.10 d; AT2020zso = 2366.46 d. Independent band-relative zeroing can therefore make physically different calendar epochs appear aligned when plotted or modeled in the historical `time_days` coordinate. Using source MJD as the canonical reference preserves observational calendar alignment while allowing any later numerical centering to remain a pure coordinate transformation. |
| Affected Data | Reconstructed temporal representations derived from the 27 historical event-band datasets and future reconstructed datasets. |
| Affected Results | Future fitting inputs, model parameters expressed in time coordinates, cross-band comparisons, diagnostic plots, tables, and reproducibility metadata. |
| Affected Paper Sections | Framework and Methodology; Fitting Procedure; Results; Figures; Appendices. |
| Status | FROZEN |
| Date Frozen | 2026-09-23 |

DEC-003 freezes the canonical timestamp reference and cross-band alignment rule only. It does not choose the internal numerical centering constant, observer-frame versus rest-frame fitting, the free/fixed/shared/constrained treatment of t0, the physical interpretation of t0, or the fixed exponential reference time required by DEC-001.
