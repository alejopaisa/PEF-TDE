# Historical Method Provenance

This document records the provenance level for historical methods, settings, and execution details as they are recovered.

Historical results must never be silently rewritten using reconstructed methodology.

## Evidence Levels

- `A`: Directly supported by surviving artifact.
- `B`: Supported by retained execution/session history.
- `C`: Inference/reconstruction.
- `D`: Historically unrecoverable.

Do not fill this document with guessed historical settings. Entries should be added only when there is explicit provenance or a documented reconstruction decision.

## Temporal Parameter Treatment

### HIST-METHOD-001 — t0 treatment

Historical statement:
The manuscript allows t0 to represent a disruption time, peak time, or fitted temporal offset and states that it may be fixed or constrained depending on the dataset.

Evidence level:
D for the exact numerical implementation.

Provenance conclusion:
The exact historical treatment, bounds, and free/fixed status of t0 cannot be recovered and must not be guessed. Any treatment used in the reconstructed analysis will be explicitly documented as a reconstruction decision.

### HIST-METHOD-002 — tp treatment

Historical statement:
The manuscript introduces tp as the onset/reference time of the exponential component and indicates that it may be fixed or constrained.

Evidence level:
D for the exact numerical implementation.

Provenance conclusion:
The exact historical free/fixed treatment, bounds, and implementation of tp cannot be recovered. The reconstructed model must not claim to reproduce the historical tp implementation.
