# ⚡ Quick Setup Guide

This guide gets you from zero to running the notebook in under 5 minutes.

---

## Step 1 — Python Version

Ensure you have **Python 3.8 or higher**:

```bash
python --version
```

---

## Step 2 — Create a Virtual Environment

```bash
# Create
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — Linux / macOS
source venv/bin/activate
```

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

Expected output: All packages install without errors. If `xgboost` fails, you can skip it — the notebook handles its absence gracefully.

---

## Step 4 — Get the Dataset

1. Go to: https://www.kaggle.com/mlg-ulb/creditcardfraud
2. Click **Download**
3. Extract `creditcard.csv`
4. Place `creditcard.csv` in the **same folder** as the notebook

> **No Kaggle account?** The notebook will automatically generate **synthetic demo data** so you can still run all cells.

---

## Step 5 — Launch Jupyter

```bash
jupyter notebook
```

Open `Credit_Card_Fraud_Detection_Enhanced.ipynb` in your browser.

---

## Step 6 — Run All Cells

In Jupyter: **Kernel → Restart & Run All**

The notebook will:
1. Load the dataset (or generate synthetic data)
2. Perform EDA with visualisations
3. Train 6–7 models
4. Show all evaluation metrics
5. Run the SOC alert triage simulation
6. Save output plots and `fraud_alert_log.json`

---

## Troubleshooting

| Error | Fix |
|---|---|
| `ModuleNotFoundError: imblearn` | `pip install imbalanced-learn` |
| `ModuleNotFoundError: xgboost` | `pip install xgboost` (optional) |
| `FileNotFoundError: creditcard.csv` | Normal — synthetic data will be used automatically |
| Kernel crashes on LOF | Memory issue — reduce `sample_fraction` in Section 5 |
| Slow execution | LOF and OCSVM are slow. Run Isolation Forest section first for quick results |

---

*Arch Technologies Remote Cybersecurity Internship — Blue Teaming Track*
