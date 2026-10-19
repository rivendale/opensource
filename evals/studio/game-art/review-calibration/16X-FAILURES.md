# T38 failure list, before implementation

- Register the third batch before implementation. Preserve all 58 pairs, their ordering, model, sampling, parser, caching OFF, 116-request/$1 stops and every scoring floor.
- Only calibration uses the new 16x enlargement policy. Ordinary runner/supervisor reviews remain at 8x; no caller-controlled scale number or CLI option is added.
- A 16x16 image becomes 256x256 on each original neutral background, with nearest-neighbor pixels. Every image remains within the existing 512-pixel bound.
- The driver pins the 16x run-list hash and scale 16. A changed list or wrong settings refuses before provider access.
- Recorded request scale/dimensions and receipt settings must agree with the fixed run list. A hash-consistent artifact with scale 8 must still refuse.
- Existing driver tests and all existing component mutants still pass. Add a denying-direction test and mutation for recorded-scale disagreement.
- No model, key, provider or container run. Historical first-batch fixtures and scoring floors stay unchanged; paid execution and independent review remain with the operator.
