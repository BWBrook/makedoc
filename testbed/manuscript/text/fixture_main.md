# Fixture Manuscript Title

## Abstract

Lorem ipsum dolor sit amet, consectetur adipiscing elit. This synthetic fixture manuscript exists to stress the manuscript build pipeline rather than evaluate scientific claims. We include citations, equations, a table, and cross-referenced figures [@alpha2020SyntheticWorkflow].

## Introduction

This is a deterministic test document for CI. A single citation appears here [@alpha2020SyntheticWorkflow]. A grouped citation appears here [@beta2021DummyFigures; @gamma2022DummyTables]. A narrative citation appears here: @delta2023LayoutRegression demonstrated why stable build fixtures reduce false alarms in publication pipelines.

## Methods

Inline math appears as $E = mc^2$. Display math appears below.

\[
S = \sum_{i=1}^{n} x_i
\]

The principal result references Fig. [1](#fig-fixture-main) and Fig. [2](#fig-fixture-richness), while supplementary context appears in Fig. [S1](#fig-fixture-s1).

### Fixture Table

| Component       | Presence | Notes                                                       |
| --------------- | -------- | ----------------------------------------------------------- |
| Citation group  | yes      | Includes multiple keys in one bracketed citation            |
| Equation block  | yes      | Uses display math via `\\[ ... \\]`                         |
| Table math      | yes      | Includes $\sigma^2$ in a table cell                         |
| Figure refs     | yes      | Anchor links target figure IDs                              |
| Variance marker | yes      | $\sigma^2$ is represented as a non-content regression probe |

## Results

Citations continue to resolve in results text [@alpha2020SyntheticWorkflow; @delta2023LayoutRegression]. Figure references remain clickable and deterministic in generated output.

## Discussion

This fixture prioritizes predictable structure over domain realism, enabling regression detection for layout and tooling changes.

## References
