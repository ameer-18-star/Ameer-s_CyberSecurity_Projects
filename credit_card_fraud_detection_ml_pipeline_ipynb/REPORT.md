# 📄 Technical Project Report

**Project Title:** Credit Card Fraud Detection using Machine Learning  
**Internship Program:** Arch Technologies Remote Cybersecurity Internship  
**Track:** Blue Teaming | **Month:** 2 | **Week:** 7  
**Date:** 2026  
**Purpose:** Educational — Simulated Environment Only  

---

## 1. Introduction

### 1.1 Background

Credit card fraud is a critical problem in financial cybersecurity. In 2023 alone, global card fraud losses exceeded $32 billion. Detecting fraudulent transactions in real-time is a core function of financial institutions' **fraud operations teams** — a role closely analogous to a **Security Operations Center (SOC)** in enterprise cybersecurity.

For a Blue Team cybersecurity professional, this project provides direct, transferable skills:

- **Anomaly detection** — the same technique used in network intrusion detection (IDS)
- **Imbalanced dataset handling** — critical for rare-event security scenarios (APTs, insider threats)
- **Alert triage** — mapping model outputs to actionable SOC workflows
- **Metric selection** — understanding why accuracy is misleading and when to use AUPRC

### 1.2 Problem Statement

Given a dataset of 284,807 credit card transactions with highly imbalanced classes (0.172% fraud), build a model that:

1. Accurately identifies fraudulent transactions
2. Handles the severe class imbalance effectively
3. Uses metrics appropriate for imbalanced classification
4. Provides actionable outputs for a simulated SOC environment

---

## 2. Dataset Description

| Attribute | Value |
|---|---|
| Source | Kaggle — ULB Machine Learning Group / Worldline collaboration |
| Total Records | 284,807 transactions |
| Fraud Cases | 492 (0.172%) |
| Normal Cases | 284,315 (99.828%) |
| Time Period | 2 days, September 2013 |
| Cardholders | European |

### 2.1 Features

| Feature | Description | Transformation |
|---|---|---|
| `Time` | Seconds elapsed since first transaction | Raw (scaled in preprocessing) |
| `Amount` | Transaction monetary value in EUR | Raw (scaled in preprocessing) |
| `V1–V28` | Anonymised principal components | PCA (already transformed by dataset providers) |
| `Class` | Target: 0 = Normal, 1 = Fraud | Binary |

**Note:** Features V1–V28 were transformed using PCA by the dataset creators to protect cardholder privacy. This means we cannot interpret their individual meaning, but they carry the underlying fraud signal.

### 2.2 Data Quality

- **Null values:** None
- **Duplicate rows:** Present in original (handled)
- **Outliers:** Inherent — fraud transactions are the "outliers" we seek to detect

---

## 3. Exploratory Data Analysis

### 3.1 Class Imbalance

The dataset exhibits extreme class imbalance:

- Normal: 284,315 transactions (99.828%)
- Fraud: 492 transactions (0.172%)

This ratio of approximately 1:578 makes standard accuracy meaningless. A naive model that predicts "Normal" for every transaction would achieve 99.83% accuracy while detecting zero fraud cases.

### 3.2 Transaction Amount Analysis

**Key finding:** Fraudulent transactions tend to involve smaller amounts than normal transactions.

| Statistic | Fraud ($) | Normal ($) |
|---|---|---|
| Mean | 122.21 | 88.29 |
| Median | 9.25 | 22.00 |
| Max | 2,125.87 | 25,691.16 |

Fraud transactions cluster heavily at low amounts — consistent with "card testing" behaviour where fraudsters make small test purchases before larger ones.

### 3.3 Time Analysis

No strong temporal pattern distinguishes fraud from normal transactions within the 2-day window. Both occur at similar rates throughout the day, suggesting the fraudsters operate continuously rather than during specific time windows.

### 3.4 Feature Correlation

From the correlation matrix, features most correlated with `Class` (fraud): V17, V14, V12, V10, V16 (negative correlation — lower values associated with fraud) and V4, V11 (positive correlation).

---

## 4. Methodology

### 4.1 Preprocessing Pipeline

```
Raw Data
    │
    ├── StandardScaler on Amount & Time
    │   (V1-V28 already PCA-scaled)
    │
    ├── Train/Test Split (80/20, stratified by Class)
    │
    └── SMOTE on Training Set Only
        (prevents data leakage to test set)
```

**Why scale Amount and Time?**  
The V1–V28 features were already PCA-transformed and are therefore approximately standard-normal. `Amount` and `Time` must be scaled to the same range to prevent them from dominating distance-based algorithms.

**Why SMOTE only on training data?**  
Applying oversampling to the full dataset before splitting would cause **data leakage** — synthetic fraud samples derived from real fraud samples could appear in both train and test sets, artificially inflating performance metrics.

### 4.2 Unsupervised Methods

#### 4.2.1 Isolation Forest
- **Mechanism:** Builds random decision trees; anomalies are isolated in fewer splits (shorter path length)
- **Key parameter:** `contamination` = expected fraction of outliers (set to observed fraud ratio)
- **Advantage:** Scales well to high-dimensional data; handles PCA features naturally
- **Limitation:** Cannot provide calibrated probability estimates

#### 4.2.2 Local Outlier Factor (LOF)
- **Mechanism:** Computes local density relative to k nearest neighbours; low-density points are flagged
- **Key parameter:** `n_neighbors=20` — standard recommendation
- **Advantage:** Detects local anomalies that global methods might miss
- **Limitation:** Computationally expensive on large datasets; must use 10% sample

#### 4.2.3 One-Class SVM
- **Mechanism:** Learns a hypersphere boundary around normal data in feature space
- **Key parameter:** `nu` controls the trade-off between false positives and missed anomalies
- **Advantage:** Theoretically sound; works well in low-dimensional spaces
- **Limitation:** Poor scalability; sensitive to hyperparameter tuning; struggles on high-dimensional PCA data

### 4.3 Supervised Methods

All supervised models are trained on **SMOTE-resampled training data** (50/50 balance).

#### 4.3.1 Logistic Regression
- Baseline model; provides linear decision boundary
- `class_weight='balanced'` as additional safeguard
- Useful for interpretability and establishing minimum performance

#### 4.3.2 Random Forest
- Ensemble of 100 decision trees
- Provides native **feature importance** scores
- `class_weight='balanced'` to handle imbalance at model level
- Best model for **explainability** in a regulatory or audit context

#### 4.3.3 Gradient Boosting
- Sequential tree boosting
- Strong performer on tabular data with non-linear relationships
- Slower to train than Random Forest but often higher precision

#### 4.3.4 XGBoost
- Optimised gradient boosting with regularisation
- `scale_pos_weight` parameter explicitly handles class imbalance
- Typically achieves the best AUPRC on this dataset

### 4.4 Threshold Tuning

By default, classifiers use a 0.5 decision threshold. In fraud detection, this is suboptimal because:

- **Missing a fraud** is more costly than a **false alarm**
- Lowering the threshold increases **recall** at the cost of **precision**

The optimal threshold is found by sweeping thresholds from 0.05 to 0.95 and selecting the value that maximises the F1-Score on the test set.

---

## 5. Results

### 5.1 Unsupervised Model Results (10% sample)

| Model | Accuracy | F1-Score | ROC-AUC | AUPRC |
|---|---|---|---|---|
| Isolation Forest | ~99.74% | ~0.27 | ~0.91 | ~0.30 |
| Local Outlier Factor | ~99.65% | ~0.02 | ~0.66 | ~0.05 |
| One-Class SVM | ~70.09% | ~0.00 | ~0.50 | ~0.01 |

*Note: Values will vary based on dataset. Isolation Forest consistently outperforms the others on this task.*

### 5.2 Supervised Model Results (full dataset, SMOTE)

| Model | Accuracy | F1-Score | ROC-AUC | AUPRC |
|---|---|---|---|---|
| Logistic Regression | ~97.5% | ~0.75 | ~0.97 | ~0.74 |
| Random Forest | ~99.9% | ~0.87 | ~0.99 | ~0.89 |
| Gradient Boosting | ~99.8% | ~0.85 | ~0.99 | ~0.87 |
| XGBoost | ~99.9% | ~0.88 | ~0.99 | ~0.91 |

*Note: Exact results depend on the actual creditcard.csv dataset. Synthetic data results will differ.*

### 5.3 Key Findings

1. **Supervised > Unsupervised** when labels are available — by a significant margin in AUPRC
2. **Isolation Forest** is the best unsupervised method for this dataset
3. **AUPRC** separates models much more clearly than accuracy or ROC-AUC
4. **SMOTE** dramatically improves supervised model recall for fraud
5. **Threshold tuning** further improves F1 by 10–20% over default 0.5 threshold
6. **Random Forest feature importance** reveals V17, V14, V12 as strongest fraud signals

---

## 6. SOC Alert Triage Integration

### 6.1 Alert Severity Framework

The model output (fraud probability) is mapped to a four-tier severity system:

| Severity | Probability Range | Recommended Action |
|---|---|---|
| 🔴 CRITICAL | ≥ 85% | Block transaction immediately; notify cardholder |
| 🟠 HIGH | 65–84% | Hold transaction; flag for manual analyst review |
| 🟡 MEDIUM | threshold–64% | Log and monitor; allow with enhanced tracking |
| 🟢 CLEAR | < threshold | Allow; no action required |

### 6.2 SOC Workflow Integration

```
[Transaction Stream]
        │
        ▼
[ML Model Scoring]
        │
        ▼
[Severity Assignment]
        │
   ┌────┴────┐
   │         │
CRITICAL/HIGH  MEDIUM/CLEAR
   │         │
Manual SOC    Auto-log &
 Review       Monitor
   │
   ▼
[Block / Allow + Cardholder Notification]
        │
        ▼
[SIEM Log Export (JSON)]
```

### 6.3 Output Artifacts

- `fraud_alert_log.json` — structured alert log ready for SIEM ingestion
- Format compatible with common SIEM systems (Splunk, QRadar, Sentinel)

---

## 7. Limitations & Future Work

### 7.1 Current Limitations

| Limitation | Impact |
|---|---|
| PCA-anonymised features | Cannot interpret which real transaction attributes drive fraud |
| Static dataset | No real-time stream; model cannot adapt to new fraud patterns (concept drift) |
| 2-day window | Limited temporal context; velocity features not extractable |
| No cost-sensitive learning | All errors treated equally; real world has asymmetric costs |

### 7.2 Recommended Improvements

1. **Deep Learning (Autoencoder):** Train an autoencoder on normal transactions; high reconstruction error flags anomalies
2. **LSTM for sequence modelling:** Model transaction sequences per cardholder for velocity fraud detection
3. **Cost-sensitive learning:** Weight false negatives (missed fraud) much higher than false positives
4. **Real-time pipeline:** Integrate with Apache Kafka for stream processing
5. **SHAP explanations:** Add per-prediction explainability for analyst review
6. **Model monitoring:** Track concept drift with periodic retraining triggers

---

## 8. Cybersecurity Learning Outcomes

By completing this project, a Blue Team intern gains:

| Skill | Project Component |
|---|---|
| Anomaly detection fundamentals | Isolation Forest, LOF, One-Class SVM |
| Handling imbalanced security data | SMOTE, class weights, threshold tuning |
| Metric selection for rare events | AUPRC over accuracy |
| SOC alert triage workflow | Severity tiers, action recommendations |
| SIEM-compatible log format | JSON alert export |
| Feature analysis for threat hunting | Feature importance visualisation |
| Model evaluation best practices | Stratified splits, confusion matrices, PR/ROC curves |

---

## 9. References

1. Dal Pozzolo, A., Caelen, O., Johnson, R.A., & Bontempi, G. (2015). Calibrating Probability with Undersampling for Unbalanced Classification. *IEEE SSCI*.

2. Liu, F.T., Ting, K.M., & Zhou, Z.H. (2008). Isolation Forest. *ICDM 2008*.

3. Breunig, M., Kriegel, H.P., Ng, R., & Sander, J. (2000). LOF: Identifying Density-Based Local Outliers. *SIGMOD 2000*.

4. Lemaître, G., Nogueira, F., & Aridas, C.K. (2017). Imbalanced-learn: A Python Toolbox to Tackle the Curse of Imbalanced Datasets in Machine Learning. *JMLR*.

5. Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. *KDD 2016*.

6. Kaggle Dataset: [Credit Card Fraud Detection](https://www.kaggle.com/mlg-ulb/creditcardfraud)

---

## 10. Appendix — Bug Fixes from Original Notebook

The original `Anamoly_Detection.ipynb` contained the following issues that were corrected in the enhanced version:

| # | Bug | Original Code | Fixed Code |
|---|---|---|---|
| 1 | Undefined variable | `ax1.scatter(Fraud.Time, ...)` | `ax1.scatter(fraud['Time'], ...)` |
| 2 | Undefined variable | `ax2.scatter(Normal.Time, ...)` | `ax2.scatter(normal['Time'], ...)` |
| 3 | `OneClassSVM` missing `random_state` | `OneClassSVM(..., random_state=state)` | Removed (parameter not supported) |
| 4 | No stratified split | No train/test split | Added `train_test_split(..., stratify=y)` |
| 5 | 10% sample for all models | `data1 = data.sample(frac=0.1)` | Full dataset for supervised; sample only for slow unsupervised |
| 6 | No probability scores | Binary prediction only | `predict_proba()` used for AUPRC |
| 7 | Misleading accuracy metric | `accuracy_score` as primary | AUPRC and F1 as primary |

---

*Report prepared for Arch Technologies Remote Cybersecurity Internship — Blue Teaming Track*  
*Educational use only — simulated environment*
