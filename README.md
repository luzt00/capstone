
# Climate-Aware Real Estate Pricing — Capstone Project

This repository presents an end-to-end solution that combines climate science, machine learning, and real estate market data to compute **risk-adjusted property prices**. Our goal is to help homebuyers, investors, and institutions make more informed decisions by incorporating environmental volatility into asset valuation.

---

## Project Overview

We use high-resolution GridMET weather data and a Transformer-based model to generate a **Climate Risk Score (CRS)** for each location. This score is then fused with live Realtor.com listings to compute a **Climate-Adjusted Price Index (CAPI)**. A Streamlit app provides an interactive front end for exploring how climate risk affects housing prices in Phoenix, AZ.

---

## Components

### `risk_score_models/`
- Transformer model trained on 5 years of GridMET data (Phoenix-only)
- Input: 8-week multivariate weather sequences  
- Output: `std_score` per coordinate = temporal volatility proxy

### `streamlit/`
- Streamlit app to load Realtor listings by ZIP
- Matches each property to the nearest `std_score`
- Computes `capi_price` using a tunable risk penalty
- Includes visualizations, sensitivity sliders, and top-10 insights

### `Dataset/`
- Contains `phoenix_scores.csv`: precomputed risk scores per (lat, lon)
- Optionally includes cached API pulls or exported maps

### `notebooks/`
- EDA, model validation, SHAP explainability
- Visualizations of score distribution and model behavior

---

## Getting Started

1. **Clone the repo**
   ```bash
   git clone https://github.com/luzt00/capstone.git
   cd capstone
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit app**
   ```bash
   streamlit run streamlit/app.py
   ```

4. **(Optional) Retrain the Transformer model**
   See `risk_score_models/Phoenix.ipynb`

---

## Sample Outputs

| Metric                    | Value        |
|---------------------------|--------------|
| Listings processed        | 800+         |
| Avg adjustment (%)        | –13%         |
| Highest penalty           | –60.8%       |
| Highest uplift            | +126.9%      |
| Market value total        | ~$33M        |
| Risk-adjusted value total | ~$29M        |

---

## Folder Structure

```
capstone/
├── Dataset/             # Risk scores, Realtor listings, etc.
├── notebooks/           # EDA, model training, evaluation
├── risk_score_models/   # Transformer model and scripts
├── streamlit/           # Streamlit UI logic
└── README.md            # You're here!
```

---

## Team Structure

Our team was split into two tracks:
- **Business team** — focused on user personas, value prop, GTM, and pricing model
- **Tech team** — built the data pipeline, model architecture, and app interface

---

## Appendix

The full cloud architecture, multi-phase deployment roadmap, and financial model are included in `appendix/Architecture.pdf`.

---

## Contact

Developed by: [Tomas Luz, Tara Teylouni, Luca Adjei, Felix Goossens, Manuel Bonnelly, Joshua Vanderspuy](https://github.com/luzt00)  
For inquiries: `tomasmartinsluz@gmail.com`
