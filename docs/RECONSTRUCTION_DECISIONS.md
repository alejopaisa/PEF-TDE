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
| Date Frozen | 2026-09-22 |

DEC-003 freezes the canonical timestamp reference and cross-band alignment rule only. It does not choose the internal numerical centering constant, observer-frame versus rest-frame fitting, the free/fixed/shared/constrained treatment of t0, the physical interpretation of t0, or the fixed exponential reference time required by DEC-001.

## DEC-004

| Field | Entry |
|---|---|
| Decision ID | DEC-004 |
| Title / Topic | Adopted reconstruction redshifts |
| Scientific Question | Which redshift value should the reconstructed PEF-TDE analysis use for each event when repository metadata and published literature differ slightly? |
| Historical Method | Recovered raw JSON files contain redshift metadata for all six events. A dedicated reconstruction provenance audit subsequently compared those values against literature-supported redshifts. |
| Historical Evidence Level | A for the repository redshift values as preserved metadata. Published-source provenance is documented in `data/metadata/RECONSTRUCTION_REDSHIFT_PROVENANCE.csv`. |
| Reconstruction Decision | Adopt the literature-supported redshift values recorded in the reconstruction provenance table: AT2018hyz = 0.04573; AT2019qiz = 0.01513; AT2020wey = 0.02738; AT2020ysg = 0.277; AT2020yue = 0.204; AT2020zso = 0.0563. These values are adopted reconstruction metadata and are not presented as new redshift measurements by this work. |
| Scientific Justification | Where repository metadata and published values agree, the common value is retained. Where small differences exist, the documented literature value is preferred so that cosmological time transformations and other redshift-dependent quantities are tied to an explicit published provenance rather than inherited metadata of uncertain precision. For AT2020yue, the adopted value is the currently verified published value 0.204; the additional fourth decimal place in the repository value 0.2042 has not been independently verified from the cited publication. The numerical differences involved are small, but explicit provenance is required for reproducibility. |
| Affected Data | No raw data are modified. |
| Affected Results | Future redshift-dependent temporal transformations and any quantities explicitly derived using event redshift. |
| Affected Paper Sections | Data; Fitting Procedure; Results where rest-frame quantities may later be reported; Appendices. |
| Status | FROZEN |
| Date Frozen | 2026-09-22 |

DEC-004 freezes only the adopted event redshifts. It does not decide whether reconstructed fitting or reported timescales use observer-frame or rest-frame time. That remains a separate reconstruction decision.

## DEC-005

| Field | Entry |
|---|---|
| Decision ID | DEC-005 |
| Title / Topic | Rest-frame temporal scaling for reconstructed fitting |
| Scientific Question | Should the elapsed times entering reconstructed PEF-TDE model fitting and the resulting fitted temporal parameters be expressed in the observer frame or in the source rest frame? |
| Historical Method | The recovered historical processed light curves store `time_days` from observer-frame MJD differences, with no redshift correction in the stored coordinate. The exact internal treatment of cosmological time dilation in the historical fitting implementation is not independently recoverable and must not be guessed. |
| Historical Evidence Level | A for the recovered stored time coordinate and its observer-frame MJD basis. D for any unrecovered additional transformation that may or may not have occurred inside the historical fitting implementation. |
| Reconstruction Decision | Source MJD remains the canonical timestamp reference established by DEC-003. Elapsed times entering reconstructed model equations will be expressed in source rest-frame days using the event redshift frozen by DEC-004. For an event-level numerical centering constant `C_event`: `t_model = (MJD - C_event) / (1 + z_adopted)`. All reconstructed fitted temporal parameters and model-facing temporal intervals will therefore use rest-frame days. This includes, where applicable: tau; fitted temporal offsets such as t0; the fixed exponential reference-time coordinate once later defined; future model-facing temporal bounds or constraints; and temporal residual/diagnostic quantities when they depend on elapsed time. Raw timestamps and literature epochs expressed as MJD remain stored and reported as observer-frame calendar timestamps unless explicitly converted as elapsed intervals. |
| Scientific Justification | Cosmological time dilation scales observed temporal intervals by `(1 + z)`. Therefore: `delta_t_rest = delta_t_observer / (1 + z)` and, for an exponential timescale: `tau_rest = tau_observer / (1 + z)`. The adopted event redshifts span a range for which this correction is not uniform across the sample. Using rest-frame elapsed times provides a common intrinsic temporal scale for comparisons among events while preserving source MJD as the canonical observational timestamp. A consistent linear time rescaling does not change the underlying functional model family. Any future model bounds, reference epochs, or other time-dependent numerical settings must therefore be defined consistently in the same rest-frame coordinate. The numerical normalization A of the fallback power-law term is coordinate-dependent under time rescaling and must not be compared between frame conventions without the appropriate transformation. |
| Affected Data | No raw timestamps or flux measurements are modified. |
| Affected Results | Future reconstructed fits, tau values, fitted temporal offsets, cross-event timescale comparisons, temporal diagnostics, tables, and figures. |
| Affected Paper Sections | Framework and Methodology; Fitting Procedure; Results; Discussion; Tables; Figures; Appendices. |
| Status | FROZEN |
| Date Frozen | 2026-09-22 |

DEC-005 freezes the temporal scaling convention only. It does not choose C_event, the physical interpretation or free/fixed/shared/constrained treatment of t0, the fixed exponential reference time, parameter bounds, optimizer settings, or model-selection criteria.

Historical tau values must not be silently relabeled as rest-frame values unless their historical frame treatment is independently verified or an explicit post-hoc conversion is documented.

## DEC-006

| Field | Entry |
|---|---|
| Decision ID | DEC-006 |
| Title / Topic | Reconstructed measurement preprocessing and sign-neutral flux inclusion |
| Scientific Question | Which individual photometric measurements should be retained as valid candidates for reconstructed PEF-TDE fitting before any temporal fitting window is applied? |
| Historical Method | The reproducible historical preprocessing audit establishes that all 23 historical 2020 flux-based event-band samples were generated using: finite(flux) AND finite(flux_err) AND flux > 0 AND flux_err > 0. The same audit verifies the four historical magnitude-based analyzed datasets using finite magnitude measurements, non-upper-limit selection where applicable, and finite positive magnitude uncertainties. |
| Historical Evidence Level | A for the recovered historical preprocessing rules, supported by raw data, processed data, deterministic audit script, and machine-readable audit results. |
| Reconstruction Decision | For flux-based reconstructed datasets, a measurement is eligible for later fitting when: 1. flux is finite, 2. flux uncertainty is finite, and 3. flux uncertainty is strictly positive. No requirement is imposed on the sign of the measured flux. Therefore finite positive, zero, and negative flux measurements with valid positive uncertainties remain eligible reconstructed measurements. The historical flux > 0 truncation will NOT be applied to reconstructed flux-based datasets. For magnitude-based datasets, eligible detection measurements require: 1. finite magnitude, 2. finite strictly positive magnitude uncertainty, and 3. non-upper-limit status where that information is available. Upper limits will not be treated as ordinary detections in the core least-squares fitting dataset. If magnitude measurements are converted to a flux-like representation for model fitting, that transformation and uncertainty propagation must be explicit and reproducible. |
| Scientific Justification | For difference-photometry, host-subtracted, baseline-subtracted, or otherwise background-referenced flux measurements, negative and zero measured flux values can be statistically valid realizations. Conditioning the retained sample on measured flux being positive truncates the measurement distribution and can shift its mean and median upward. The reproducible historical preprocessing audit demonstrates that this effect is relevant to many of the historical 2020 datasets, while not establishing that any historical model classification was caused by that preprocessing. A sign-neutral measurement eligibility rule preserves the measured noise distribution more faithfully and avoids conditioning the fitting sample directly on the observed flux sign. Upper limits require a censored-data likelihood or another explicit statistical treatment and therefore are not treated as ordinary detections in the core reconstructed fitting sample. |
| Affected Data | Future reconstructed/cleaned light-curve datasets generated from the recovered raw measurements. No recovered raw files are modified. |
| Affected Results | Future fitting samples, flux distributions, model fits, floor estimates, residual diagnostics, information criteria, classifications, and robustness tests. |
| Affected Paper Sections | Data; Fitting Procedure; Results; Robustness; Discussion; Appendices. |
| Status | FROZEN |
| Date Frozen | 2026-09-23 |

DEC-006 defines measurement-level eligibility only. It does not define the temporal fitting window. A measurement may be valid under DEC-006 and still be excluded later by an independently frozen temporal-window rule.

DEC-006 does not conclude that historical Floor classifications were caused by positive-flux truncation and does not invalidate any historical classification. Those questions require reconstructed model fits.

DEC-006 does not define a censored-likelihood treatment for upper limits. Upper limits remain available in the raw source data for possible future robustness analysis.
