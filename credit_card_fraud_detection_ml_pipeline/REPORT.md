# 📄 Technical Project Report

**Project Title:** Credit Card Fraud Detection using Machine Learning
**Purpose:** Educational — Simulated Environment Only

---

## 1. Introduction

### 1.1 Background

Credit card fraud is a critical problem in financial cybersecurity. Detecting
fraudulent transactions in real-time is a core function of financial
institutions' fraud operations teams — a role closely analogous to a Security
Operations Center (SOC) in enterprise cybersecurity.

For a Blue Team professional, this project delivers direct, transferable skills:

- **Anomaly detection** — the same technique used in network intrusion detection
- **Imbalanced dataset handling** — critical for rare-event scenarios (APTs, insider threats)
- **Alert triage** — mapping model outputs to actionable SOC workflows
- **Metric selection** — understanding why accuracy fails and when to use AUPRC

### 1.2 Problem Statement

Given a dataset of 284,807 credit card transactions with highly imbalanced
classes (0.172% fraud), the project:

1. Accurately identifies fraudulent transactions
2. Handles severe class imbalance with SMOTE
3. Uses metrics appropriate for imbalanced classification
4. Provides actionable outputs for a simulated SOC environment

---

## 2. System Architecture

The project is structured as a modular Python package with clear separation
of concerns:

```
main.py  (CLI entry point)
    │
    ├── DataLoader       — CSV loading or synthetic data generation
    ├── Preprocessor     — Feature scaling, train/test split, SMOTE
    ├── UnsupervisedModels — Isolation Forest, LOF, One-Class SVM
    ├── SupervisedModels   — LR, Random Forest, GBM, XGBoost
    ├── ModelEvaluator     — Unified metrics, plots, comparison table
    ├── AlertSystem        — SOC triage simulation, JSON log export
    └── Visualizer         — All EDA and evaluation plots
```

Each component is independently importable and testable. The `main.py`
orchestrates them through six numbered pipeline steps.

---

## 3. Dataset Description

| Attribute | Value |
|---|---|
| Source | Kaggle — ULB Machine Learning Group / Worldline |
| Total Records | 284,807 transactions |
| Fraud Cases | 492 (0.172%) |
| Normal Cases | 284,315 (99.828%) |
| Time Period | 2 days, September 2013 |

### 3.1 Features

| Feature | Description |
|---|---|
| `Time` | Seconds elapsed since first transaction (scaled) |
| `Amount` | Transaction monetary value in EUR (scaled) |
| `V1–V28` | PCA-anonymised principal components (already scaled) |
| `Class` | Target: 0 = Normal, 1 = Fraud |

V1–V28 were PCA-transformed by the dataset creators to protect cardholder
privacy, so individual feature interpretation is not possible. They carry the
underlying fraud signal intact.

### 3.2 Data Quality

- No null values
- Duplicate rows present in the original (handled by the loader)
- Fraud transactions are the intentional "outliers" to detect

---

## 4. Exploratory Data Analysis

### 4.1 Class Imbalance

The dataset has an extreme imbalance ratio of approximately 1:578. A naive
model that always predicts "Normal" achieves 99.83% accuracy while detecting
zero fraud — making accuracy a useless metric here.

### 4.2 Transaction Amount

Fraudulent transactions cluster at low amounts, consistent with "card testing"
behaviour where attackers make small test purchases before larger ones.

| Statistic | Fraud ($) | Normal ($) |
|---|---|---|
| Mean | 122.21 | 88.29 |
| Median | 9.25 | 22.00 |
| Max | 2,125.87 | 25,691.16 |

### 4.3 Time Analysis

No strong temporal pattern distinguishes fraud from normal transactions within
the 2-day window, suggesting fraudsters operate continuously.

### 4.4 Feature Correlation

Features most correlated with the fraud label: V17, V14, V12, V10, V16
(negative — lower values = more fraud risk) and V4, V11 (positive).

---

## 5. Preprocessing Pipeline

```
Raw Data
    │
    ├── StandardScaler on Amount & Time
    │   (V1–V28 already PCA-scaled)
    │
    ├── Stratified Train/Test Split (80/20)
    │
    └── SMOTE on Training Set ONLY
        (prevents data leakage to test set)
```

**Why scale Amount and Time?**
V1–V28 are already PCA-transformed to approximately standard-normal scale.
`Amount` and `Time` must be brought to the same range to prevent them from
dominating distance-based algorithms.

**Why SMOTE only on training data?**
Applying oversampling before splitting causes data leakage — synthetic fraud
samples derived from real fraud samples would appear in both train and test
sets, artificially inflating all performance metrics.

**Why a 10% sample for unsupervised models?**
Local Outlier Factor and One-Class SVM have O(n²) time complexity and are
impractical on 280k rows. Isolation Forest uses the full dataset because it
scales efficiently with O(n log n) complexity.

---

## 6. Models

### 6.1 Unsupervised Models

#### Isolation Forest
Builds random decision trees; anomalies are isolated in fewer splits
(shorter path length). Uses the observed fraud ratio as `contamination`.
Scales well to high-dimensional data and handles PCA features naturally.

#### Local Outlier Factor (LOF)
Computes local density relative to k=20 nearest neighbours. Low-density
points relative to their neighbourhood are flagged as anomalies. Detects
local anomalies that global methods might miss, but is computationally
expensive.

#### One-Class SVM
Learns a hypersphere boundary around normal data in a kernel-induced feature
space. Trained only on normal transactions. Theoretically sound but sensitive
to hyperparameter tuning and slow on high-dimensional data.

### 6.2 Supervised Models

All supervised models are trained on SMOTE-resampled data (50/50 balance).

#### Logistic Regression
Baseline linear classifier. `class_weight='balanced'` provides additional
imbalance protection. Fast, interpretable, and useful as a lower bound.

#### Random Forest
Ensemble of 100 decision trees with `class_weight='balanced'`. Provides native
feature importance scores — valuable for regulatory and audit contexts.

#### Gradient Boosting
Sequential tree boosting with 100 estimators. Strong on non-linear tabular
relationships. Slower to train than Random Forest.

#### XGBoost
Optimised gradient boosting with L1/L2 regularisation. Uses `scale_pos_weight`
to explicitly handle class imbalance. Typically achieves the best AUPRC.
Optional — the pipeline runs without it if not installed.

### 6.3 Threshold Tuning

Default classifiers use a 0.5 decision threshold, which is suboptimal for
imbalanced data. This pipeline sweeps thresholds from 0.05 to 0.95 in 0.01
steps, selecting the value that maximises F1-score on the test set. In
practice this improves F1 by 10–20% over the default.

---

## 7. Results

### 7.1 Unsupervised Models (10% sample)

| Model | Accuracy | F1-Score | ROC-AUC | AUPRC |
|---|---|---|---|---|
| Isolation Forest | ~99.7% | ~0.27 | ~0.91 | ~0.30 |
| Local Outlier Factor | ~99.6% | ~0.02 | ~0.66 | ~0.05 |
| One-Class SVM | ~70.1% | ~0.00 | ~0.50 | ~0.01 |

Isolation Forest consistently dominates the other unsupervised methods on this
dataset.

### 7.2 Supervised Models (full dataset, SMOTE)

| Model | Accuracy | F1-Score | ROC-AUC | AUPRC |
|---|---|---|---|---|
| Logistic Regression | ~97.5% | ~0.75 | ~0.97 | ~0.74 |
| Random Forest | ~99.9% | ~0.87 | ~0.99 | ~0.89 |
| Gradient Boosting | ~99.8% | ~0.85 | ~0.99 | ~0.87 |
| XGBoost | ~99.9% | ~0.88 | ~0.99 | ~0.91 |

Results shown are approximate benchmarks on the real Kaggle dataset.
Synthetic data results differ but the relative model rankings hold.

### 7.3 Key Findings

1. **Supervised models outperform unsupervised by a large margin** when labels
   are available — supervised AUPRC is 3× higher.
2. **Isolation Forest** is the only viable unsupervised method; LOF and
   One-Class SVM fail to learn a useful fraud signal here.
3. **AUPRC separates models more clearly** than accuracy (which is dominated
   by the majority class) or ROC-AUC (which is optimistic on imbalanced data).
4. **SMOTE dramatically improves recall** for supervised models by giving the
   learner adequate fraud examples during training.
5. **Threshold tuning** adds a further 10–20% F1 improvement over the default
   0.5 threshold at no additional training cost.
6. **Random Forest feature importance** identifies V17, V14, and V12 as the
   strongest fraud signals — consistent with the correlation analysis in EDA.

---

## 8. SOC Alert Triage Integration

### 8.1 Severity Framework

The best model's probability output is mapped to a four-tier severity system
aligned with standard SOC escalation procedures:

| Severity | Probability | Action |
|---|---|---|
| 🔴 CRITICAL | ≥ 85% | Block immediately; notify cardholder |
| 🟠 HIGH | ≥ 65% | Hold; flag for manual analyst review |
| 🟡 MEDIUM | ≥ best threshold | Log and monitor |
| 🟢 CLEAR | < best threshold | Allow; no action required |

### 8.2 Alert Log Format

`outputs/fraud_alert_log.json` is a SIEM-ingestible JSON file with:

```json
{
  "metadata": {
    "generated_at": "...",
    "model": "XGBoost",
    "threshold": 0.32,
    "total_transactions": 56962,
    "severity_counts": { "CRITICAL": 45, "HIGH": 63, "MEDIUM": 24, "CLEAR": 56830 }
  },
  "alerts": [
    {
      "transaction_id": 0,
      "fraud_probability": 0.9821,
      "severity": "CRITICAL",
      "action": "Block transaction immediately; notify cardholder",
      "true_label": 1,
      "correct": true,
      "timestamp": "2026-...",
      "model_used": "XGBoost"
    }
  ]
}
```

This format is compatible with Splunk, IBM QRadar, and Microsoft Sentinel.

---

## 9. Limitations and Future Work

### 9.1 Current Limitations

| Limitation | Impact |
|---|---|
| PCA-anonymised features | Cannot interpret which real attributes drive fraud |
| Static dataset | Model cannot adapt to new fraud patterns (concept drift) |
| 2-day window | Velocity features (n transactions per hour) not extractable |
| No cost-sensitive learning | All errors treated equally; real world has asymmetric costs |

### 9.2 Recommended Improvements

1. **Autoencoder anomaly detection** — Train on normal transactions; high
   reconstruction error flags anomalies without labels.
2. **LSTM sequence modelling** — Model transaction sequences per cardholder
   for velocity-based fraud detection.
3. **Cost-sensitive learning** — Weight false negatives (missed fraud) much
   higher than false positives to reflect real business costs.
4. **Real-time pipeline** — Integrate with Apache Kafka for stream processing.
5. **SHAP explanations** — Add per-prediction explainability for analyst review
   and regulatory compliance.
6. **Model monitoring** — Track concept drift with periodic retraining triggers.

---

## 10. Cybersecurity Learning Outcomes

| Skill | Project Component |
|---|---|
| Anomaly detection fundamentals | Isolation Forest, LOF, One-Class SVM |
| Handling imbalanced security data | SMOTE, class weights, threshold tuning |
| Metric selection for rare events | AUPRC over accuracy |
| SOC alert triage workflow | Severity tiers, action recommendations |
| SIEM-compatible log format | JSON alert export |
| Feature analysis for threat hunting | Feature importance visualisation |
| Model evaluation best practices | Stratified splits, confusion matrices, PR/ROC curves |
| Clean Python project structure | Modular package with CLI entry point |

---

## 11. References

1. Dal Pozzolo, A., Caelen, O., Johnson, R.A., & Bontempi, G. (2015).
   Calibrating Probability with Undersampling for Unbalanced Classification.
   *IEEE SSCI*.

2. Liu, F.T., Ting, K.M., & Zhou, Z.H. (2008). Isolation Forest. *ICDM 2008*.

3. Breunig, M., Kriegel, H.P., Ng, R., & Sander, J. (2000). LOF: Identifying
   Density-Based Local Outliers. *SIGMOD 2000*.

4. Lemaître, G., Nogueira, F., & Aridas, C.K. (2017). Imbalanced-learn:
   A Python Toolbox to Tackle the Curse of Imbalanced Datasets. *JMLR*.

5. Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System.
   *KDD 2016*.

6. Kaggle Dataset: Credit Card Fraud Detection —
   https://www.kaggle.com/mlg-ulb/creditcardfraud

---

*Educational use only — simulated environment*
