# PEF–TDE Paper Evidence Register

The historical manuscript is a frozen artifact. The reconstructed manuscript will use only evidence that passes validation through the reconstruction workflow.

This register is the master scientific evidence register for the reconstructed paper. It records where each paper claim, table, figure, and quantitative requirement is supported, how it was generated, and whether it is eligible for use in the reconstructed manuscript.

## Evidence and Result Statuses

- `HISTORICAL`: Preserved from the frozen historical analysis or manuscript.
- `PENDING`: Identified as needed but not yet reconstructed or validated.
- `RECOMPUTE`: Requires regeneration from source data or scripts.
- `UNDER_REVIEW`: Generated evidence exists and is being checked.
- `VALIDATED`: Evidence passed the applicable validation checks.
- `FINAL`: Approved for inclusion in the reconstructed manuscript.
- `SUPERSEDED`: Replaced by a newer validated or final result.
- `REJECTED`: Excluded after review or validation failure.

`VALIDATED` does not automatically mean `FINAL`.

## Master Evidence Table

| ID | Paper Section | Claim / Requirement | Historical Support | Reconstructed Support | Source Data | Generating Script | Result File | Table / Figure | Status | Notes / Discrepancy |
|---|---|---|---|---|---|---|---|---|---|---|
| ABS-001 | Abstract | PEF–TDE compares three minimal observational components: standard fallback, a persistent floor, and a time-dependent exponential-family excess. | Frozen historical manuscript. | — | — | — | — | — | HISTORICAL | Framework definition; not yet approved for reconstructed manuscript. |
| ABS-002 | Abstract | The exponential timescale tau is treated as an effective phenomenological observational descriptor and not as identification of a unique physical mechanism. | Frozen historical manuscript. | — | — | — | — | — | HISTORICAL | Interpretive framework statement; not yet FINAL. |
| ABS-003 | Abstract | The historical analysis uses an exploratory, non-population-complete sample of six TDEs. | Frozen historical manuscript; historical sample metadata exists. | — | — | — | — | — | HISTORICAL | Exact reconstructed sample and selection rationale still require validation before use in the new paper. |
| ABS-004 | Abstract | Each event and photometric band is fitted independently. | Frozen historical manuscript. | — | — | — | — | — | HISTORICAL | Must later agree with the reconstructed pipeline. |
| ABS-005 | Abstract | Historical model comparison reports chi-squared, AIC, BIC, and AICc. | Frozen historical manuscript and surviving historical model-selection evidence. | — | — | — | — | — | HISTORICAL | Do not imply that AICc was the original primary classifier. Historical classification was originally AIC-based; AICc was later used as a finite-sample validation. |
| ABS-006 | Abstract | Residual-distribution, Q-Q, lag-1 autocorrelation, Durbin-Watson, and pathological-fit diagnostics support the analysis. | Historical manuscript contains these claims, but complete reproducible support does not survive. | — | — | — | — | — | RECOMPUTE | Must be regenerated for the reconstructed analysis before use. |
| ABS-007 | Abstract | No single minimal component describes all analyzed events and wavelength bands. | Historical classifications support this as a historical result. | — | — | — | — | — | RECOMPUTE | This conclusion must be determined from reconstructed classifications, not copied from the historical manuscript. |
| ABS-008 | Abstract | PEF–TDE provides a reproducible way to identify event-band combinations requiring additional time-dependent or persistent structure beyond canonical fallback. | Claim made in frozen historical manuscript. | — | — | — | — | — | RECOMPUTE | Reproducibility must be demonstrated by the reconstructed data-to-PDF pipeline before this statement can become FINAL. |
| INT-001 | Introduction | A TDE occurs when a star is disrupted by the tidal field of a supermassive black hole, with bound debris returning toward the black hole. | Historical manuscript cites Rees (1988) and Phinney (1989). | — | — | — | — | — | PENDING | Literature/background claim requiring source verification for the reconstructed manuscript. |
| INT-002 | Introduction | The canonical fallback rate is approximately proportional to t^(-5/3). | Historical manuscript cites Rees (1988) and Phinney (1989). | — | — | — | — | — | PENDING | Verify against appropriate primary/review literature before FINAL. |
| INT-003 | Introduction | Observed TDE light curves can depart from pure fallback through late-time plateaus, excess emission, band-dependent evolution, and structured residual behavior. | Claim present in historical manuscript. | — | — | — | — | — | PENDING | Requires literature support; do not treat the current historical wording as sufficient evidence by itself. |
| INT-004 | Introduction | PEF–TDE is intended as an observational phenomenological taxonomy rather than a first-principles physical accretion model. | Frozen historical manuscript. | — | — | — | — | — | HISTORICAL | Framework scope statement; reconstructed wording will be reviewed later. |
| INT-005 | Introduction | The core framework consists of standard fallback, persistent floor, and time-dependent exponential-family components. | Frozen historical manuscript. | — | — | — | — | — | HISTORICAL | Core framework definition; final parameterization remains subject to reconstruction review. |
| INT-006 | Introduction | Core candidate models are compared independently/parallel for each event and band. | Frozen historical manuscript. | — | — | — | — | — | PENDING | Must be confirmed by the final reconstructed fitting pipeline. |
| INT-007 | Introduction | The phenomenological classifications are intended to guide subsequent physical modeling rather than replace detailed physical models. | Frozen historical manuscript. | — | — | — | — | — | HISTORICAL | Interpretive/scope statement; not a quantitative result. |
| INT-008 | Introduction | The six-event sample is exploratory and not statistically population-complete. | Frozen historical manuscript and historical sample metadata. | — | — | — | — | — | PENDING | Sample composition is known historically, but selection rationale and reconstructed sample definition must be documented before FINAL. |
| INT-009 | Introduction | Population-level frequencies of phenomenological classes are outside the scope of the analysis. | Frozen historical manuscript. | — | — | — | — | — | HISTORICAL | Scope restriction. Do not infer population frequencies from the six-event sample. |
