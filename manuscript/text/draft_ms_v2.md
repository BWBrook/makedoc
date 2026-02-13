# Title

Biodiversity buffers environmental variability only when species responses diverge

## Abstract

Environmental variability is usually destabilising, yet the insurance hypothesis predicts that biodiversity can buffer ecosystem functioning when species respond asynchronously to fluctuating environments. Despite its influence, we lack simple dynamical demonstrations of when response diversity produces insurance and when it does not, particularly under correlated environmental drivers. Here I use a stochastic multispecies Ricker model to explore how species’ environmental response directions interact with shared environmental variation to shape community-level variability. Species compete symmetrically and differ only in the sign and magnitude of their response slopes to a single environmental axis. Environmental anomalies follow a multivariate autoregressive process with controllable variance, cross-species correlation in drivers, and temporal autocorrelation. I compare communities with mixed positive and negative response slopes to communities where all slopes are positive. For each scenario I quantify the coefficient of variation of total biomass and synchrony metrics based on abundance and per capita growth rates. When response slopes are mixed, realised synchrony in growth rates is much lower than the imposed correlation among environmental drivers and can become negative at low richness. In this regime, community-level variability declines with species richness and can even decrease as environmental correlation increases. When all slopes are positive, imposed environmental correlation yields strong realised synchrony; community-level variability increases with environmental correlation and remains high even at greater richness. These contrasts persist across environmental variances, competition strengths, and slope magnitudes, and mixed-slope insurance remains evident across a wide range of temporal autocorrelation. The results show that biodiversity buffers environmental variability only when it includes diversity in response directions that decouple driver covariance from realised synchrony. Richness alone is not enough: the stabilising effect of biodiversity depends critically on how species’ responses are arranged relative to the structure of environmental variation.

## Keywords

biodiversity; response diversity; ecosystem stability; species synchrony; environmental covariance; stochastic community dynamics; insurance hypothesis.

## Introduction

Environmental variability generally destabilises populations: as climatic and other drivers fluctuate, population abundances tend to vary more through time, increasing the risk of low-biomass episodes and local collapse [@ives2007StabilityDiversityEcosystems]. Against this backdrop, the insurance hypothesis proposes that biodiversity can buffer ecosystem functioning against environmental fluctuations, because different species respond differently in space and time, so that declines in some are offset by increases in others [@yachi1999BiodiversityEcosystemProductivity]. This idea, inspired by portfolio theory in economics, predicts that aggregate ecosystem properties such as total biomass or productivity should fluctuate less in more diverse communities than in species-poor systems subject to the same environmental variance [@loreau2021BiodiversityInsuranceConcept]. Over the last two decades, both experiments and syntheses have produced substantial evidence that biodiversity can stabilise ecosystem functioning [@loreau2013BiodiversityEcosystemStability; @demazancourt2013PredictingEcosystemStability; @wagg2021DiversityAsynchronySoil], but they also reveal that the strength, and even the sign, of diversity–stability relationships depends strongly on the underlying mechanisms [@ives2007StabilityDiversityEcosystems; @loreau2021BiodiversityInsuranceConcept].

A central theme in this work is synchrony among species’ fluctuations. When species respond similarly to environmental variation, community-level variability tends to scale with typical species-level variability; when responses are asynchronous or negatively correlated, aggregate variability can be much lower than the sum of its parts [@doak1998StatisticalInevitabilityStabilitydiversity; @loreau2008SpeciesSynchronyIts; @thibaut2013UnderstandingDiversityStability]. Formal measures such as the variance ratio, Loreau–de Mazancourt’s synchrony index $\phi_{\mathrm{LdM}}$, and related covariance-based metrics provide quantitative links between species-level variances, covariances, and community-level stability [@loreau2008SpeciesSynchronyIts; @loreau2013BiodiversityEcosystemStability; @thibaut2013UnderstandingDiversityStability; @demazancourt2013PredictingEcosystemStability]. At the same time, recent reviews have emphasised that “insurance” is conceptually slippery: it bundles together effects of biodiversity on both the mean and the variability of ecosystem properties, and different studies implicitly use different baselines when they claim that biodiversity “stabilises” functioning [@ives2007StabilityDiversityEcosystems; @loreau2021BiodiversityInsuranceConcept]. In particular, many formulations are vague about whether stabilisation is meant in an absolute sense (reduced community variance as environmental variance increases) or in a relative sense (community variance lower than an appropriate baseline under the same environmental forcing).

## Methods 

### Community dynamics

We model a community of $S$ species using a discrete-time stochastic Ricker model with symmetric competition. Let $N_i(t)$ denote the abundance of species $i$ at time $t$. In the absence of environmental variation, per-capita growth follows
\[
N_i(t+1) = N_i(t)\exp\left[r_0 - \frac{\alpha_{\mathrm{intra}} N_i(t) + \alpha_{\mathrm{inter}}\sum_{j \neq i} N_j(t)}{K_i}\right],
\]
where $r_0$ is a shared intrinsic growth rate, $K_i$ is the carrying capacity of species $i$, $\alpha_{\mathrm{intra}}$ is intraspecific competition, and $\alpha_{\mathrm{inter}}$ is interspecific competition. We set $K_i = 100$ for all species, $\alpha_{\mathrm{intra}} = 1$, and $\alpha_{\mathrm{inter}} = 0.3$ unless otherwise stated. With these choices, the symmetric deterministic equilibrium is
\[
N_i^\ast = \frac{K_i}{\alpha_{\mathrm{intra}} + \alpha_{\mathrm{inter}}(S-1)}.
\]

Environmental variation enters as a linear response term $b_i z_i(t)$ in the per-capita growth rate:
\[
N_i(t+1) = N_i(t)\exp\left[r_0 + b_i z_i(t) - \frac{\alpha_{\mathrm{intra}} N_i(t) + \alpha_{\mathrm{inter}}\sum_{j \neq i} N_j(t)}{K_i}\right].
\]
Species differ only in their response slopes $b_i$, which encode both the direction and magnitude of their response to the environmental anomaly $z_i(t)$. Three slope regimes are considered:

* Mixed slopes: $b_i$ evenly spaced in $[-0.5, 0.5]$, giving both positive and negative responses.
* Positive slopes: $b_i$ evenly spaced in $[0.1, 1.0]$, giving aligned positive responses.
* Mixed–narrow (sensitivity analysis): $b_i$ evenly spaced in $[-0.25, 0.25]$.

Abundances are floored at a small positive constant $N_{\min} = 10^{-9}$ to avoid numerical issues from extinction-driven zeros, and the exponent in the growth term is capped at $\pm 50$ to prevent overflow in $\exp(\cdot)$. Initial abundances are set to $K_i/2$ for all species.

### Monte Carlo uncertainty

Across all scenario grids, Monte Carlo uncertainty in $\mathrm{CV}_{\mathrm{tot}}$ is small relative to the differences highlighted in the Results. In the main mixed-slope grid (150 replicates per scenario), the typical standard error of $\mathrm{CV}_{\mathrm{tot}}$ is $\approx 0.002$ (relative standard error $\approx 1%$). In the positive-slope grid (100 replicates), standard errors are $\approx 0.01$ (relative standard error $\approx 2%$). In the $\phi$-sensitivity and control grids (80 replicates), relative standard errors for $\mathrm{CV}_{\mathrm{tot}}$ are mostly below $5%$. These uncertainties are at least an order of magnitude smaller than the mixed–positive differences reported in the main text (for example, a difference of $\approx 0.18$ in $\mathrm{CV}_{\mathrm{tot}}$ at $\sigma_{\mathrm{env}} = 0.5$, $\rho_{\mathrm{env}} = 0.5$, $S = 4$), so Monte Carlo noise does not affect qualitative conclusions.

## Results

### Insurance patterns under mixed vs aligned responses

In the mixed-slope regime, community variability is strongly buffered relative to aligned responses. Across the ($\sigma_{\mathrm{env}}, \rho_{\mathrm{env}}, S$) grid, $\mathrm{CV}_{\mathrm{tot}}$ increases with $\sigma_{\mathrm{env}}$ but decreases with richness and—counterintuitively for many $\sigma_{\mathrm{env}}$ values—declines as $\rho_{\mathrm{env}}$ increases (Fig. 1A,C). For example, at $\sigma_{\mathrm{env}}=0.5$ and $\rho_{\mathrm{env}}=0.5$, $\mathrm{CV}_{\mathrm{tot}}$ is $\approx 0.15$ for $S=2$, $\approx 0.08$ for $S=4$, and $\approx 0.06$ for $S=8$, illustrating a pronounced richness effect. Averaged over $\rho_{\mathrm{env}}$, mean $\mathrm{CV}_{\mathrm{tot}}$ declines steeply from $S=2$ to $S=4$ and continues to fall towards $S=8$ across all $\sigma_{\mathrm{env}}$ values (Fig. 2).

In the positive-slope regime, community variability behaves very differently. Here $\mathrm{CV}_{\mathrm{tot}}$ increases with $\rho_{\mathrm{env}}$ as well as $\sigma_{\mathrm{env}}$ (Fig. 1B,C), and realised growth synchrony is high and increases with $\rho_{\mathrm{env}}$ (Fig. 1D). Richness still reduces variability through statistical averaging, but does not overturn the positive $\mathrm{CV}_{\mathrm{tot}}$–$\rho_{\mathrm{env}}$ relationship: at $\sigma_{\mathrm{env}}=0.5$ and $\rho_{\mathrm{env}}=0.5$, $\mathrm{CV}_{\mathrm{tot}}$ for $S=4$ is $\approx 0.3$, substantially higher than in the corresponding mixed-slope scenarios. Under high environmental forcing ($\sigma_{\mathrm{env}}\ge 1.0$) and strong driver correlation, positive-slope communities show very large $\mathrm{CV}_{\mathrm{tot}}$ (often approaching or exceeding 1), whereas mixed-slope communities under the same forcing remain far less variable (Fig. 1A,B).

## Discussion

### Response-direction heterogeneity decouples driver correlation from realised synchrony

These simulations isolate a simple mechanism by which response diversity can, but need not, generate insurance: heterogeneity in response direction can decouple imposed correlation among environmental drivers ($\rho_{\mathrm{env}}$) from realised synchrony. With mixed response slopes, a shared environmental anomaly increases growth for some species while decreasing it for others, generating weak or negative covariances in per-capita growth rates. Mean pairwise growth-rate correlations therefore fall well below $\rho_{\mathrm{env}}$, abundance synchrony $\phi_{\mathrm{LdM}}$ remains low, and $\mathrm{CV}_{\mathrm{tot}}$ is reduced relative to aligned-slope baselines under the same $\sigma_{\mathrm{env}}$, $\rho_{\mathrm{env}}$, and $\phi$.

When response slopes are aligned and positive, imposed driver correlation and realised synchrony reinforce each other. Environmental anomalies push all species’ growth rates in the same direction, so increasing $\rho_{\mathrm{env}}$ yields high realised covariances and elevated $\phi_{\mathrm{LdM}}$. Community variability then rises with $\rho_{\mathrm{env}}$ and is only weakly offset by richness, consistent with stabilisation dominated by statistical averaging rather than compensatory dynamics in some empirical systems [@zhao2022BiodiversityStabilizesPlant].

Imposed driver correlation and realised synchrony are therefore not interchangeable. Treating $\rho_{\mathrm{env}}$ as a proxy for synchrony—an assumption that is often implicit in models and in interpretations of correlated environmental forcing—can misattribute mechanism [@loreau2008SpeciesSynchronyIts; @loreau2013BiodiversityEcosystemStability]. Under heterogeneous response directions, even strong driver correlation can yield near-zero or negative realised growth correlations; under aligned responses the same forcing produces tight positive synchrony. This emphasis on response-direction heterogeneity complements the synchrony framework [@loreau2008SpeciesSynchronyIts; @loreau2013BiodiversityEcosystemStability] by identifying a concrete lever that controls how environmental covariance is translated into dynamical synchrony.

### Conclusion

Biodiversity insurance theory has matured to the point where the broad claim—that diversity can buffer ecosystem functioning against environmental variability—is no longer contentious [@loreau2013BiodiversityEcosystemStability; @loreau2021BiodiversityInsuranceConcept]. The sharper questions are mechanistic: when does biodiversity provide insurance, through which pathways, and how do those pathways depend on environmental covariance and response diversity [@ross2024LimitedTheoreticalEmpirical; @polazzo2024MeasuringResponseDiversity]? The simulations here provide a clear answer within a simple dynamical model. When species share environmental drivers but differ in response direction, biodiversity can decouple imposed driver correlation $\rho_{\mathrm{env}}$ from realised synchrony, generating compensatory dynamics and stabilising aggregate biomass relative to aligned-response baselines. When responses are aligned, the same environmental covariance acts as a common shock that elevates synchrony and increases community variability, with richness providing only modest buffering through statistical averaging.

The implication is straightforward: richness alone is insufficient. Stabilisation depends on how species’ response directions are arranged relative to the structure of environmental variation. Making that relationship explicit offers a route to reconciling divergent empirical results on richness, synchrony, and response diversity, and it suggests that future work should quantify not only species counts but also the alignment of response slopes with the covariance structure of the dominant environmental drivers.

## References

[To do in Zotero later]

---

### Table 1
Model parameters and baseline values (or ranges) used in the stochastic multispecies Ricker simulations. Unless otherwise stated, parameters are held fixed across all scenarios.

| Parameter                                 | Value(s) / description                                                                                                                    |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| $r_0$                                     | $1.0$                                                                                                                                     |
| $K_i$                                     | $100$ for all species                                                                                                                     |
| $\alpha_{\mathrm{intra}}$                 | $1.0$                                                                                                                                     |
| $\alpha_{\mathrm{inter}}$                 | $0.3$ (set to $0$ in no-competition controls)                                                                                             |
| $b_i$ (mixed)                             | evenly spaced in $[-0.5, 0.5]$                                                                                                            |
| $b_i$ (positive)                          | evenly spaced in $[0.1, 1.0]$                                                                                                             |
| $b_i$ (positive-matched control)          | $\lvert b_i^{\mathrm{mixed}} \rvert$ (all slopes non-negative; evaluated for $S \in \{4, 8\}$)                                          |
| $b_i$ (mixed–narrow)                      | evenly spaced in $[-0.25, 0.25]$                                                                                                          |
| $\sigma_{\mathrm{env}}$                   | $0$–$1.5$ (specific values given in the scenario grids)                                                                                   |
| $\rho_{\mathrm{env}}$ (requested)         | $-0.5$ to $1.0$                                                                                                                           |
| $\rho_{\mathrm{eff}}$ (used in simulator) | $\rho_{\mathrm{eff}}=\mathrm{clip}\!\left(\rho_{\mathrm{env}},-1/(S-1)+10^{-6},\,1-10^{-6}\right)$ to ensure positive-definite covariance |
| $\phi$                                    | $0$–$0.95$                                                                                                                                |
| $N_{\min}$                                | $10^{-9}$ (abundance floor)                                                                                                               |
| Ricker exponent clipping                  | $x \in [-50, 50]$ before $\exp(x)$                                                                                                        |
| Steps / burn-in                           | $600 / 300$ (main and control grids); $400 / 200$ ($\phi$-sensitivity grids)                                                              |
| Replicates per scenario                   | 150 (mixed main and richness sweep), 100 (positive and positive-matched), 80 (reduced grids and control runs)                             |
