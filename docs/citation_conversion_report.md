# Citation Conversion Report

Date: 2026-02-13  
Source file: `manuscript/text/draft_ms_v2.md`  
Bibliography source: `references/ih_references.yaml`

## Summary
- Converted manual author-year citations to Pandoc citation tokens in manuscript body text.
- Replaced unresolved placeholder `[REF]` with an inferred citation set based on local paragraph context.
- No unresolved citekeys remain in converted sections.
- `make lint-manuscript` and `make check` both pass after conversion.

## Key Mappings Applied
- `(Ives and Carpenter 2007)` -> `[@ives2007StabilityDiversityEcosystems]`
- `(Yachi and Loreau 1999)` -> `[@yachi1999BiodiversityEcosystemProductivity]`
- `(Loreau 2021)` -> `[@loreau2021BiodiversityInsuranceConcept]`
- `(Loreau and de Mazancourt 2013, de Mazancourt et al. 2013, Wagg et al. 2022)` -> `[@loreau2013BiodiversityEcosystemStability; @demazancourt2013PredictingEcosystemStability; @wagg2021DiversityAsynchronySoil]`
- `(Doak et al. 1998, Loreau and de Mazancourt 2008, Thibaut and Connolly 2013)` -> `[@doak1998StatisticalInevitabilityStabilitydiversity; @loreau2008SpeciesSynchronyIts; @thibaut2013UnderstandingDiversityStability]`
- `(Loreau and de Mazancourt 2008, 2013, Thibaut and Connolly 2013, de Mazancourt et al. 2013)` -> `[@loreau2008SpeciesSynchronyIts; @loreau2013BiodiversityEcosystemStability; @thibaut2013UnderstandingDiversityStability; @demazancourt2013PredictingEcosystemStability]`
- `(Zhao et al. 2022)` -> `[@zhao2022BiodiversityStabilizesPlant]`
- `(Ross and Sasaki 2024, Polazzo et al. 2024)` -> `[@ross2024LimitedTheoreticalEmpirical; @polazzo2024MeasuringResponseDiversity]`

## Ambiguities and Inferences
- Placeholder `[REF]` had no explicit target key in source text.
  - Applied inferred replacement: `[@loreau2008SpeciesSynchronyIts; @loreau2013BiodiversityEcosystemStability]`
  - Rationale: adjacent sentence explicitly references the same synchrony framework.
- Text cited `Wagg et al. 2022`, but bibliography currently contains `@wagg2021DiversityAsynchronySoil` (issued year 2021).
  - Applied available key as best match.
  - Manuscript decision confirmed by user on 2026-02-13; keep this mapping as final.

## Finalized Decisions (User Confirmed)
- 2026-02-13: Keep inferred replacement for former `[REF]` as `[@loreau2008SpeciesSynchronyIts; @loreau2013BiodiversityEcosystemStability]`.
- 2026-02-13: Keep `Wagg et al. 2022` prose mapped to available key `@wagg2021DiversityAsynchronySoil`.

## Remaining Manual Citations
- None detected by current lint pattern (`make lint-manuscript`).
