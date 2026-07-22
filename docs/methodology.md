# Methodology

This document explains the statistics behind each module and the design
decisions. Every claim here is exercised by the test-suite in `tests/`.

## 1. Simulation

Experiments are simulated with a **known ground truth** so the rest of the
platform can be validated end-to-end.

- **Binary metric** — each user is a Bernoulli draw: control `~ Bernoulli(p_c)`,
  treatment `~ Bernoulli(p_t)`.
- **Continuous metric** — each user is a Normal draw with a shared standard
  deviation: control `~ N(μ_c, σ²)`, treatment `~ N(μ_t, σ²)`.
- **Stream form** — for sequential methods we also emit an *interleaved* stream:
  users are randomised 50/50 into arms and arrive one at a time, exactly as an
  online experiment accumulates data.

## 2. Fixed-horizon tests

These are run **once**, at the pre-planned sample size.

### Welch's t-test (continuous)
Unequal-variance two-sample test. Statistic and p-value delegate to SciPy;
the confidence interval on the mean difference uses the Welch–Satterthwaite
degrees of freedom:

```
diff = mean_t − mean_c
SE   = sqrt(s_t²/n_t + s_c²/n_c)
CI   = diff ± t_{1−α/2, df} · SE
```

### Two-proportion z-test (binary)
The **test statistic** uses the pooled variance; the **confidence interval**
uses the unpooled (Wald) variance — the interval you actually report:

```
z  = (p_t − p_c) / sqrt( p_pool·(1−p_pool)·(1/n_c + 1/n_t) )
CI = (p_t − p_c) ± z_{1−α/2} · sqrt( p_c(1−p_c)/n_c + p_t(1−p_t)/n_t )
```

### Chi-square test (binary)
Pearson's test of independence on the 2×2 table. Without the continuity
correction it is algebraically identical to the two-sided z-test
(`χ² = z²`). The test-suite asserts this identity — a strong correctness check.

### Effect sizes
Absolute difference, relative lift, **Cohen's d** (means) and **Cohen's h**
(proportions).

## 3. Power, sample size, MDE

Built on `statsmodels` power solvers (`NormalIndPower` via Cohen's h for
proportions, `TTestIndPower` via Cohen's d for means).

- **Power** — probability of rejecting H0 when a given true effect exists.
- **Sample size** — invert power for `n` given α, power, baseline and MDE.
- **MDE** — invert for the effect given `n`, α and power. For proportions the
  required Cohen's h is mapped back to an absolute rate difference via
  `p₂ = sin(arcsin(√p₁) + h/2)²`.

The suite checks these numerically (round-trips are exact) **and** empirically:
simulate at the sample size computed for 80% power and the observed rejection
rate lands near 80%.

## 4. Sequential testing — the headline

**The peeking problem.** If you run a fixed-horizon test but look at the
p-value repeatedly and stop the first time `p < 0.05`, the real false-positive
rate is far above 5%. With five equally-spaced looks it is ≈ **14%**
(`sequential_alpha([1.96]*5) ≈ 0.142`), and it keeps rising with more looks.

Three principled fixes are implemented.

### 4a. Wald SPRT
Tests a simple H0 effect against a simple H1 effect by accumulating the
log-likelihood ratio and stopping when it crosses the Wald boundaries:

```
upper = log((1−β)/α)   → reject H0
lower = log(β/(1−α))   → accept H0
```

### 4b. Always-valid inference (mixture SPRT)
A confidence sequence that is valid at **every** sample size simultaneously, so
you may stop whenever you like. Using a `N(0, τ²)` mixture over the effect and
the Gaussian estimate `θ̂_n ~ N(θ, V_n)`:

```
Λ_n = sqrt( V_n /(V_n+τ²) ) · exp( θ̂_n²·τ² / (2·V_n·(V_n+τ²)) )
p_n = min(1, 1/Λ_n)        (running minimum → always-valid p-value)
```

The confidence sequence `{θ₀ : Λ_n(θ₀) < 1/α}` has the closed-form half-width

```
radius = sqrt( (2·V_n·(V_n+τ²)/τ²) · ( ½·ln((V_n+τ²)/V_n) + ln(1/α) ) )
```

Practical guards: a short **warm-up** (`min_samples`) before the first look and
a **Laplace-smoothed** proportion variance, so the plug-in variance never
collapses to zero on the first few identical observations. The log-likelihood
ratio is computed in log-space to avoid overflow.

### 4c. Group-sequential boundaries (Pocock / O'Brien-Fleming)
Pre-plan `K` interim looks and reject at look `k` if `|Z_k| ≥ b_k`.

- **Pocock** — constant boundary `b_k = c`. Easy early stopping, stringent final
  look.
- **O'Brien-Fleming** — `b_k = c·√(K/k)`: very stringent early, relaxing to
  ≈ the fixed-sample value at the end (the popular default).

The single constant `c` is solved so the **family-wise** error equals α, using
the **Armitage–McPherson–Rowe recursion**: the score `S_k = Z_k·√k` is a random
walk of iid `N(0,1)` increments; the continuation density is propagated on a
grid and convolved with a unit-normal step at each look, and the total exit
probability is the achieved α. `sequential_alpha()` runs this recursion for any
boundary set — the suite checks the computed boundaries reproduce published
Pocock (≈ 2.41 for K=5) and O'Brien-Fleming (final ≈ 2.04 for K=5) values and
that the achieved α matches the target to within 0.002.

## References

- Wald (1945), *Sequential Tests of Statistical Hypotheses*.
- Armitage, McPherson & Rowe (1969), *Repeated significance tests on
  accumulating data*.
- Pocock (1977); O'Brien & Fleming (1979) — group-sequential designs.
- Robbins (1970); Johari, Koomen, Pekelis & Walsh (2017/2022), *Always Valid
  Inference* — the mixture-SPRT confidence sequences used by modern
  experimentation platforms.
