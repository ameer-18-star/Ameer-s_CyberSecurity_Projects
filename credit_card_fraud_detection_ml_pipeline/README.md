# 🛡️ Credit Card Fraud Detection — ML Pipeline

---

## 📌 Overview

Credit card fraud detection is a foundational Blue Team skill that maps
directly to anomaly-based intrusion detection, user behaviour analytics (UBA),
and SIEM alert triage workflows.

This project implements a **modular, end-to-end Python pipeline** combining:

- Unsupervised anomaly detection (no labels needed)
- Supervised classification with class-imbalance handling (SMOTE)
- Threshold tuning for optimal recall
- A simulated SOC alert triage system with JSON log export

The pipeline runs cleanly with the real [Kaggle Credit Card Fraud dataset](https://www.kaggle.com/mlg-ulb/creditcardfraud)
or falls back to auto-generated synthetic data in offline environments.

---

## 📁 Project Structure

```
fraud_detection/
│
├── main.py                          ← Entry point (CLI)
├── requirements.txt                 ← Python dependencies
├── README.md                        ← This file
├── REPORT.md                        ← Technical project report
│
├── creditcard.csv                   ← Dataset (download separately)
│
├── models/
│   ├── __init__.py
│   ├── unsupervised.py              ← Isolation Forest, LOF, One-Class SVM
│   ├── supervised.py                ← LR, Random Forest, GBM, XGBoost
│   └── evaluator.py                 ← Unified metrics, plots, comparison table
│
├── utils/
│   ├── __init__.py
│   ├── data_loader.py               ← CSV loader + synthetic data generator
│   ├── preprocessor.py              ← Scaling, train/test split, SMOTE
│   ├── visualizer.py                ← All EDA and evaluation plots
│   ├── alert_system.py              ← SOC triage simulation + JSON export
│   └── logger.py                    ← Console + file logging setup
│
└── outputs/                         ← Generated after running the pipeline
    ├── plot_class_distribution.png
    ├── plot_amount_analysis.png
    ├── plot_time_vs_amount.png
    ├── plot_correlation_heatmap.png
    ├── plot_confusion_unsupervised.png
    ├── plot_confusion_supervised.png
    ├── plot_pr_roc_curves.png
    ├── plot_feature_importance.png
    ├── plot_threshold_tuning.png
    ├── plot_model_comparison.png
    ├── model_summary.csv
    ├── fraud_alert_log.json
    └── run_<timestamp>.log
```

---

## 📊 Dataset

| Property | Value |
|---|---|
| Source | Kaggle — ULB Machine Learning Group |
| Total Transactions | 284,807 |
| Fraud Cases | 492 (0.172%) |
| Features | V1–V28 (PCA-anonymised), Time, Amount, Class |

**Download required:** Get `creditcard.csv` from [Kaggle](https://www.kaggle.com/mlg-ulb/creditcardfraud)
and place it in the project root. If the file is absent, the pipeline
automatically generates synthetic demo data.

---

## 🧠 Models

### Unsupervised (no labels required — trained on 10% sample)

| Model | Key Idea |
|---|---|
| **Isolation Forest** | Anomalies are isolated in fewer random splits |
| **Local Outlier Factor** | Low local density relative to neighbours = outlier |
| **One-Class SVM** | Learns a boundary around normal data; deviations flagged |

### Supervised (labels + SMOTE balancing — trained on full dataset)

| Model | Key Idea |
|---|---|
| **Logistic Regression** | Baseline linear classifier |
| **Random Forest** | Ensemble of trees; provides feature importances |
| **Gradient Boosting** | Sequential boosting; strong on tabular data |
| **XGBoost** | Optimised gradient boosting (optional) |

---

## 🚀 Quick Start

### 1. Clone / download the project

```bash
git clone https://github.com/your-username/credit-card-fraud-detection
cd credit-card-fraud-detection
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. (Optional) Download the real dataset

Place `creditcard.csv` in the project root. If omitted, synthetic data is used.

### 5. Run the full pipeline

```bash
python main.py
```

---

## 🔧 CLI Reference

```
python main.py [--mode MODE] [--data PATH] [--synthetic] [--sample FRAC] [--no-plots]
```

| Flag | Default | Description |
|---|---|---|
| `--mode` | `full` | `full` / `eda` / `train` / `evaluate` / `alert` / `predict` |
| `--data` | `creditcard.csv` | Path to the dataset CSV |
| `--input` | — | CSV of new transactions (required for `--mode predict`) |
| `--synthetic` | off | Force synthetic demo data |
| `--sample` | `0.1` | Sample fraction for slow unsupervised models |
| `--no-plots` | off | Skip saving PNG plots (headless/CI environments) |

### Mode examples

```bash
# EDA only
python main.py --mode eda

# Train models only (no evaluation plots)
python main.py --mode train

# Full pipeline on synthetic data (no CSV needed)
python main.py --synthetic

# Score new transactions from a CSV file
python main.py --mode predict --input new_transactions.csv

# Headless (no plots saved)
python main.py --no-plots
```

---

## 📈 Evaluation Metrics

Standard **accuracy** is misleading on imbalanced data (0.172% fraud).
This pipeline prioritises:

| Metric | Why It Matters |
|---|---|
| **AUPRC** (primary) | Precision-recall trade-off; most reliable for imbalanced data |
| **ROC-AUC** | Discrimination ability across all thresholds |
| **F1-Score** | Harmonic mean of precision and recall |
| **Recall** | How many real frauds were caught |
| **Precision** | Of flagged transactions, how many were actually fraud |

> High recall is preferred in fraud detection — missing real fraud is more
> costly than a false alarm.

---

## 🚨 SOC Alert Triage

The `AlertSystem` scores every transaction and assigns a severity tier:

| Severity | Probability | Action |
|---|---|---|
| 🔴 CRITICAL | ≥ 85% | Block immediately; notify cardholder |
| 🟠 HIGH | ≥ 65% | Hold; flag for manual analyst review |
| 🟡 MEDIUM | ≥ best threshold | Log and monitor |
| 🟢 CLEAR | < best threshold | Allow; no action required |

Alert records are exported to `outputs/fraud_alert_log.json` in a format
compatible with Splunk, IBM QRadar, and Microsoft Sentinel.

---

## 🔗 Blue Team Cybersecurity Relevance

| This Project | Real-World Blue Team Skill |
|---|---|
| Fraud anomaly detection | Network intrusion detection (IDS/IPS) |
| Class imbalance handling | Rare event detection (APTs, insider threats) |
| Threshold tuning | Alert fatigue reduction in SIEM |
| Feature importance | Log source prioritisation |
| Severity triage | SOC L1 analyst workflow |
| JSON alert log | SIEM ingestion format (CEF/JSON) |

---

## ⚠️ Disclaimer

This project is created strictly for educational purposes. All analysis runs in a
simulated, offline environment. No real financial data or personal
information is used.

---

*Made with 🛡️ for learning Blue Team cybersecurity skills*
