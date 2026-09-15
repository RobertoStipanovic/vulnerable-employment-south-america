# Predicting Vulnerable Employment in South America

Can a high-dimensional panel of World Bank development indicators predict the share of
**vulnerable employment** in South American economies? This project builds an end-to-end
pipeline — from the raw World Development Indicators release to a neural network with
country fixed effects — and finds that *how* you normalise the panel matters far more
than which model you fit.

> Final project for **Data Science for Economics**, Tilburg University, Joint work with Tim Jetten.

---

## The question

Vulnerable employment (own-account workers plus contributing family workers, as a share of
total employment) is one of the ILO's headline measures of labour-market precariousness.
It is expensive to measure and reported with a lag. If it can be predicted from indicators
that are cheaper and timelier to collect, that is useful.

**Target variable:** `Vulnerable employment, total (% of total employment) (modeled ILO estimate)`

## Data

| | |
|---|---|
| Source | [World Bank – World Development Indicators](https://datatopics.worldbank.org/world-development-indicators/) |
| Countries | Argentina, Bolivia, Brazil, Chile, Colombia, Ecuador, Paraguay, Peru, Uruguay |
| Period | 1991–2022 (annual) |
| Raw size | ~1,500 indicators × 217 economies × 66 years (~190 MB) |

Venezuela was excluded for lack of reliable reporting; Guyana and Suriname were dropped
after the missing-value audit showed they were too sparse to carry.

**Indicator funnel:** ~1,500 raw indicators → kept those with ≥15 country-years of data →
restricted to 1991–2022 → kept those ≥70% complete → linear interpolation *within* country
(`limit_area='inside'`) → **429 complete series**.

All employment-composition indicators were removed before modelling (self-employed, wage
and salaried workers, contributing family workers, and their male/female splits), since
they are definitionally close to the target and would leak.

## Method

1. **Chronological split** — train ≤ 2014, validation 2015–2018, test 2019–2022. Standard
   random splits would leak future information into a panel forecast.
2. **Standardisation fit on train only**, then applied to validation and test.
3. **Lasso, written from scratch** — the objective
   `MSE + λ·Σ|w|` minimised with `scipy.optimize.minimize` over a log-spaced λ grid.
   Best λ = 0.01 (validation MSE 0.0395). Coefficients are thresholded at |β| > 0.01,
   leaving **34 indicators**.
4. **Stability selection** — Lasso refit on random 50% subsamples; indicators selected in
   ≥80% of runs are kept, leaving **32 indicators**. This guards against Lasso's known
   instability when predictors are many and highly correlated.
5. **Neural network** — Keras feed-forward net (32 → 16 units, ReLU, dropout 0.2, Adam
   1e-3, 100 epochs, batch size 16) on each feature set.
6. **Country fixed effects** — the whole thing re-estimated with variables standardised
   *within* country, which absorbs persistent level differences between economies.

## Results

Mean absolute error, in percentage points of vulnerable employment:

| Model | Train MAE | Validation MAE | Test MAE |
|---|---:|---:|---:|
| Global – Lasso features | 12.80 | 20.04 | 17.65 |
| Global – Stable features | 12.69 | 21.20 | 17.64 |
| **Fixed effects – Lasso features** | **2.45** | **2.81** | 3.48 |
| **Fixed effects – Stable features** | 2.64 | 2.84 | **3.15** |

**The finding is the gap between those two blocks.** Pooled across countries, the models
are close to useless — an MAE of ~18 pp on a variable that ranges from roughly 20% to 50%.
Once variables are standardised within country, error drops by a factor of five. Almost
all of the apparent signal in the pooled model was between-country level variation, not
within-country dynamics; the pooled network learned an average level and applied it to
economies that sit nowhere near it.

Secondary observations:

- Stability selection barely changes accuracy (3.48 → 3.15 pp on test) but the surviving
  set is much more defensible: it drops indicators that Lasso picked up by chance from
  correlated clusters.
- The indicators that survive both filters are mostly **structural**, not cyclical —
  maternal mortality, female labour-force participation ratios, employment in agriculture,
  energy use per capita, GDP per capita, manufacturing value added. That fits the
  interpretation of vulnerable employment as a slow-moving development outcome.
- Test error exceeds validation error for the fixed-effects models, which is expected:
  the test window (2019–2022) contains the COVID-19 shock.

## Repository layout

```
.
├── notebooks/
│   └── vulnerable_employment_south_america.ipynb   # the full analysis
├── data/
│   ├── raw/                                        # git-ignored (see data/raw/README.md)
│   └── processed/
│       └── WDI_SouthAmerica_Filtered.csv           # South-America subset, ~9 MB
├── scripts/
│   └── download_wdi.py                             # fetches the full WDI release
├── requirements.txt
└── README.md
```

## Reproducing

```bash
git clone https://github.com/RobertoStipanovic/vulnerable-employment-south-america.git
cd vulnerable-employment-south-america
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab notebooks/vulnerable_employment_south_america.ipynb
```

The notebook runs out of the box on the committed subset — no download needed. To start
from the full World Bank release instead:

```bash
python scripts/download_wdi.py
```

then point `csv_path` at `../data/raw/WDICSV.csv`.

Seeds are fixed (`RANDOM_SEED = 42`), but exact neural-network figures can still shift
slightly across TensorFlow versions and hardware. Stability selection runs 5 subsamples by
default; the reported run used 100, which takes hours.

## Limitations and next steps

- **Small N.** 9 countries × 32 years = 288 observations against 429 candidate predictors.
  This is the binding constraint on everything below.
- **No lags.** A dense network treats each country-year independently, so it cannot see
  that vulnerable employment is highly persistent. Adding lagged predictors — and a lag of
  the target — is the single most promising improvement.
- **Interpolated values are treated as observed.** The models cannot distinguish an
  imputed point from a measured one. Bayesian imputation with propagated uncertainty
  would be the honest fix.
- **Lasso λ grid is coarse** (5 points) and the stability-selection λ is inherited rather
  than re-tuned, both for compute reasons.
- **Tree ensembles** (XGBoost, random forests) often do better than neural networks on
  wide, short tabular panels like this one and are an obvious benchmark to add.

## License

[MIT](LICENSE) for the code. The underlying data is published by the World Bank under
[CC BY 4.0](https://datacatalog.worldbank.org/public-licenses#cc-by).
