# Audited final results

All 132 main paths are present; 0 numerical failures. Uniform budget: 200,000 gradients per path. Primary target: sustained relative gap 1e-6.

Frozen controller parameters: `{"ENDPOINT_RHGD": {"beta": 0}, "FIXED_RHGD": {"period_steps": 512}, "KINETIC_RHGD": {"beta": 0}}`.

Randomized paths use five algorithm seeds on fixed problems. Missing targets remain censored in medians and success denominators. Costs below are observed gradients, never selection penalties.

| Case | Method | Sustained gradients (median) | Hits / paths | Final relative gap (median) |
| --- | --- | ---: | ---: | ---: |
| linear-scaled_common | GD | 229 | 1/1 | 8.52e-10 |
| linear-scaled_common | AGD | 410 | 1/1 | 4.17e-61 |
| linear-scaled_common | Mu-free AGD | 61 | 1/1 | 1.11e-15 |
| linear-scaled_common | Function-restart AGD | 57 | 1/1 | 3.42e-139 |
| linear-scaled_common | Gradient-restart AGD | 55 | 1/1 | 1.58e-156 |
| linear-scaled_common | CAGD | 576 | 5/5 | 7.66e-62 |
| linear-scaled_common | RHGD | 886 | 5/5 | 2.44e-26 |
| linear-scaled_common | Fixed-time RHGD (m=512) | 886 | 1/1 | 5.16e-12 |
| linear-scaled_common | Power-reset RHGD | 82 | 1/1 | 7.53e-156 |
| linear-scaled_common | Endpoint normalized RHGD (β=0) | 82 | 1/1 | 7.53e-156 |
| linear-scaled_common | Kinetic normalized RHGD (β=0) | 76 | 1/1 | 7.53e-156 |
| linear-scaled_common | RCM kin | 200,000 | 1/1 | 8.35e-10 |
| linear-scaled_common | RCM mmd-r | 56 | 1/1 | 2.08e-53 |
| linear-scaled_common | RCM mmd-dr | 64 | 1/1 | 1.32e-154 |
| log-scaled_common | GD | censored | 0/1 | 2.01e-06 |
| log-scaled_common | AGD | 7,005 | 1/1 | 3.14e-60 |
| log-scaled_common | Mu-free AGD | 1,677 | 1/1 | 5.95e-13 |
| log-scaled_common | Function-restart AGD | 1,677 | 1/1 | 5.64e-46 |
| log-scaled_common | Gradient-restart AGD | 1,677 | 1/1 | 5.36e-47 |
| log-scaled_common | CAGD | 7,498 | 5/5 | 1.66e-60 |
| log-scaled_common | RHGD | 27,150 | 5/5 | 4.49e-19 |
| log-scaled_common | Fixed-time RHGD (m=512) | 48,164 | 1/1 | 1.65e-09 |
| log-scaled_common | Power-reset RHGD | 4,104 | 1/1 | 1.5e-30 |
| log-scaled_common | Endpoint normalized RHGD (β=0) | 4,104 | 1/1 | 1.5e-30 |
| log-scaled_common | Kinetic normalized RHGD (β=0) | 4,104 | 1/1 | 4.91e-31 |
| log-scaled_common | RCM kin | censored | 0/1 | 1.3e-06 |
| log-scaled_common | RCM mmd-r | 1,970 | 1/1 | 7.08e-44 |
| log-scaled_common | RCM mmd-dr | 1,769 | 1/1 | 1.55e-55 |
| clustered-scaled_common | GD | 22 | 1/1 | 4.05e-07 |
| clustered-scaled_common | AGD | 41 | 1/1 | 8.34e-61 |
| clustered-scaled_common | Mu-free AGD | 19 | 1/1 | 4.31e-13 |
| clustered-scaled_common | Function-restart AGD | 18 | 1/1 | 7.7e-47 |
| clustered-scaled_common | Gradient-restart AGD | 12 | 1/1 | 6.68e-46 |
| clustered-scaled_common | CAGD | 66 | 5/5 | 2.11e-61 |
| clustered-scaled_common | RHGD | 80 | 5/5 | 4.89e-20 |
| clustered-scaled_common | Fixed-time RHGD (m=512) | 80 | 1/1 | 9.31e-11 |
| clustered-scaled_common | Power-reset RHGD | 22 | 1/1 | 5.29e-35 |
| clustered-scaled_common | Endpoint normalized RHGD (β=0) | 22 | 1/1 | 5.29e-35 |
| clustered-scaled_common | Kinetic normalized RHGD (β=0) | 22 | 1/1 | 8.7e-34 |
| clustered-scaled_common | RCM kin | 200,000 | 1/1 | 3.79e-07 |
| clustered-scaled_common | RCM mmd-r | 15 | 1/1 | 6.75e-42 |
| clustered-scaled_common | RCM mmd-dr | 23 | 1/1 | 1.51e-61 |
| linear-equal | GD | censored | 0/1 | 0.00961 |
| linear-equal | AGD | 20,989 | 1/1 | 4.71e-54 |
| linear-equal | Mu-free AGD | 88,111 | 1/1 | 1.25e-08 |
| linear-equal | Function-restart AGD | 12,005 | 1/1 | 3.74e-132 |
| linear-equal | Gradient-restart AGD | 12,004 | 1/1 | 1.7e-149 |
| linear-equal | CAGD | 20,936 | 5/5 | 8.64e-55 |
| linear-equal | RHGD | 43,702 | 5/5 | 2.75e-19 |
| linear-equal | Fixed-time RHGD (m=512) | censored | 0/1 | 5.82e-05 |
| linear-equal | Power-reset RHGD | 10,020 | 1/1 | 8.44e-149 |
| linear-equal | Endpoint normalized RHGD (β=0) | 10,020 | 1/1 | 8.44e-149 |
| linear-equal | Kinetic normalized RHGD (β=0) | 9,994 | 1/1 | 8.43e-149 |
| linear-equal | RCM kin | censored | 0/1 | 0.00942 |
| linear-equal | RCM mmd-r | 18,507 | 1/1 | 2.47e-46 |
| linear-equal | RCM mmd-dr | 7,670 | 1/1 | 4.93e-148 |
| log-equal | GD | censored | 0/1 | 0.169 |
| log-equal | AGD | 21,593 | 1/1 | 4.73e-54 |
| log-equal | Mu-free AGD | 127,763 | 1/1 | 2.82e-07 |
| log-equal | Function-restart AGD | 27,162 | 1/1 | 8.69e-39 |
| log-equal | Gradient-restart AGD | 27,150 | 1/1 | 2.56e-41 |
| log-equal | CAGD | 21,597 | 5/5 | 8.94e-55 |
| log-equal | RHGD | 112,564 | 5/5 | 1.35e-13 |
| log-equal | Fixed-time RHGD (m=512) | censored | 0/1 | 0.000103 |
| log-equal | Power-reset RHGD | 47,284 | 1/1 | 3.49e-26 |
| log-equal | Endpoint normalized RHGD (β=0) | 47,284 | 1/1 | 3.49e-26 |
| log-equal | Kinetic normalized RHGD (β=0) | 49,856 | 1/1 | 2.08e-25 |
| log-equal | RCM kin | censored | 0/1 | 0.156 |
| log-equal | RCM mmd-r | 28,987 | 1/1 | 2.58e-37 |
| log-equal | RCM mmd-dr | 27,822 | 1/1 | 1.96e-50 |
| clustered-equal | GD | censored | 0/1 | 0.453 |
| clustered-equal | AGD | 22,594 | 1/1 | 4.82e-54 |
| clustered-equal | Mu-free AGD | 196,341 | 1/1 | 8.92e-07 |
| clustered-equal | Function-restart AGD | 28,154 | 1/1 | 1.4e-38 |
| clustered-equal | Gradient-restart AGD | 28,155 | 1/1 | 2.96e-39 |
| clustered-equal | CAGD | 22,543 | 5/5 | 1.01e-54 |
| clustered-equal | RHGD | 93,308 | 5/5 | 2.08e-13 |
| clustered-equal | Fixed-time RHGD (m=512) | censored | 0/1 | 0.000322 |
| clustered-equal | Power-reset RHGD | 57,832 | 1/1 | 1.63e-29 |
| clustered-equal | Endpoint normalized RHGD (β=0) | 57,832 | 1/1 | 1.63e-29 |
| clustered-equal | Kinetic normalized RHGD (β=0) | 57,650 | 1/1 | 4.91e-27 |
| clustered-equal | RCM kin | censored | 0/1 | 0.431 |
| clustered-equal | RCM mmd-r | 26,650 | 1/1 | 2.28e-35 |
| clustered-equal | RCM mmd-dr | 24,054 | 1/1 | 3.01e-58 |

## Geometry

- scaled_common: 64/66 sustained primary-target hits.
- equal: 57/66 sustained primary-target hits.

First primary-target crossing without a sustained crossing: 0/132 paths.

## Robustness

198 paths retained, including 18 numerical failures and 29 censored/failed sustained targets. See robustness.csv for every case, setting and realized fixed-controller physical period. h/h0=1.1 is a stress test.

## Interpretation limits

Training selected beta=0 for both normalization families; positive normalization exponents did not win the predefined training criterion. This is a negative tuning result, not a general impossibility result. Endpoint beta=0 is the existing power controller. Compare discrete kinetic beta=0 separately; discretization can change reset times. Conclusions are conditional on these six geometries, budgets and selected parameters. No general acceleration or novelty claim follows.
