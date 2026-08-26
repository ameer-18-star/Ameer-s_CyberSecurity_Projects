# 🛡️ Credit Card Fraud Detection — Anomaly Detection with ML

> **Arch Technologies Remote Cybersecurity Internship**  
> **Track:** Blue Teaming | **Month:** 2 | **Week:** 7  
> **Purpose:** Educational — Simulated Environment Only

---

## 📌 Project Overview

Credit card fraud is one of the most prevalent financial crimes, causing billions in losses annually. For **Blue Team security professionals**, fraud detection is a foundational skill — it directly maps to **anomaly-based intrusion detection**, **user behaviour analytics (UBA)**, and **SIEM alert triage** workflows.

This project builds a complete fraud detection pipeline using the [Kaggle Credit Card Fraud Dataset](https://www.kaggle.com/mlg-ulb/creditcardfraud), combining both **unsupervised anomaly detection** and **supervised classification** methods, with a simulated **SOC alert triage system**.

---

## 📁 Project Structure

```
credit_card_fraud_detection/
│
├── Credit_Card_Fraud_Detection_Enhanced.ipynb  ← Main notebook (enhanced)
├── requirements.txt                            ← Python dependencies
├── README.md                                   ← This file
├── REPORT.md                                   ← Technical project report
│
├── creditcard.csv                              ← Dataset (download separately)
│
└── outputs/                                    ← Generated after running notebook
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
    └── fraud_alert_log.json
```

---

## 📊 Dataset

| Property | Value |
|---|---|
| Source | Kaggle — ULB Machine Learning Group |
| Total Transactions | 284,807 |
| Fraud Cases | 492 (0.172%) |
| Time Period | 2 days (September 2013, European cardholders) |
| Features | V1–V28 (PCA-anonymised), Time, Amount, Class |

**⚠️ Download required:** The dataset is not included due to size. Download `creditcard.csv` from [Kaggle](https://www.kaggle.com/mlg-ulb/creditcardfraud) and place it in the project root.

> **Note for simulated environments:** If `creditcard.csv` is not found, the notebook automatically generates synthetic data for demonstration.

---

## 🧠 Models Implemented

### Unsupervised (No Labels Required)
| Model | Description |
|---|---|
| **Isolation Forest** | Isolates anomalies using random feature splits; fewer splits = more anomalous |
| **Local Outlier Factor (LOF)** | Compares local density to neighbourhood; low density = outlier |
| **One-Class SVM** | Learns a decision boundary around normal data; deviations flagged |

### Supervised (Labels Required + SMOTE Balancing)
| Model | Description |
|---|---|
| **Logistic Regression** | Baseline linear classifier; fast and interpretable |
| **Random Forest** | Ensemble of decision trees; robust and provides feature importance |
| **Gradient Boosting** | Sequential boosting; strong on tabular data |
| **XGBoost** | Optimised gradient boosting; often best performance |

---

## ⚙️ Key Features & Improvements Over Original

| Feature | Original | Enhanced Version |
|---|---|---|
| Variable naming consistency | ❌ Mixed (`Fraud` / `fraud`) | ✅ Fixed |
| Dataset used | 10% sample only | ✅ Full dataset + sample where needed |
| Class imbalance handling | ❌ None | ✅ SMOTE oversampling |
| Supervised models | ❌ None | ✅ 4 models added |
| Metrics | Accuracy only | ✅ F1, AUPRC, ROC-AUC (correct for imbalance) |
| Curves | ❌ None | ✅ PR Curve + ROC Curve |
| Confusion matrices | ❌ None | ✅ Heatmaps for all models |
| Feature importance | ❌ None | ✅ Random Forest importances |
| Threshold tuning | ❌ None | ✅ F1-optimal threshold search |
| Model comparison | Text only | ✅ Summary table + bar chart |
| SOC simulation | ❌ None | ✅ Alert triage with severity levels |
| Alert logging | ❌ None | ✅ JSON alert log export |
| Synthetic data fallback | ❌ None | ✅ For simulated environments |

---

## 🚀 Setup & Usage

### 1. Clone / Download the Project

```bash
git clone https://github.com/your-username/credit-card-fraud-detection
cd credit-card-fraud-detection
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the Dataset

Download `creditcard.csv` from [Kaggle](https://www.kaggle.com/mlg-ulb/creditcardfraud) and place it in the project root directory.

### 5. Launch the Notebook

```bash
jupyter notebook Credit_Card_Fraud_Detection_Enhanced.ipynb
```

Run all cells top to bottom (`Kernel → Restart & Run All`).

---

## 📈 Evaluation Metrics Explained

Because the dataset is highly imbalanced (0.172% fraud), standard **accuracy** is misleading.

| Metric | Why It Matters for Fraud Detection |
|---|---|
| **AUPRC** (Primary) | Measures precision-recall trade-off; most reliable for imbalanced data |
| **ROC-AUC** | Measures discrimination ability across all thresholds |
| **F1-Score** | Harmonic mean of precision & recall; balanced metric |
| **Recall (Sensitivity)** | How many actual frauds were caught (missing fraud = costly) |
| **Precision** | Of flagged transactions, how many were actually fraud |

> 📌 **Rule of thumb for fraud detection:** High recall is usually preferred over high precision. It is better to flag a legitimate transaction for review than to miss a real fraud.

---

## 🚨 SOC Alert Triage Simulation

The notebook includes a **Security Operations Center (SOC)** simulation that:

1. Takes incoming transactions
2. Scores them with the best trained model
3. Assigns severity levels:
   - 🔴 **CRITICAL** (≥85% fraud probability) → Block immediately
   - 🟠 **HIGH** (≥65%) → Hold for manual review
   - 🟡 **MEDIUM** (≥threshold) → Monitor and log
   - 🟢 **CLEAR** (<threshold) → Allow
4. Exports a structured **JSON alert log** (`fraud_alert_log.json`)

This simulates real-world tools like **Splunk**, **IBM QRadar**, or **Microsoft Sentinel** alert workflows.

---

## 🔗 Blue Team Cybersecurity Relevance

| This Project | Real-World Blue Team Skill |
|---|---|
| Fraud anomaly detection | Network intrusion detection (IDS/IPS) |
| Class imbalance handling | Rare event detection (APTs, insider threats) |
| Threshold tuning | Alert fatigue reduction in SIEM |
| Feature importance | Log source prioritisation |
| Alert severity triage | SOC L1 analyst workflow |
| JSON alert log | SIEM ingestion format (CEF/JSON) |

---

## 📚 References

- [Kaggle Dataset — Credit Card Fraud Detection](https://www.kaggle.com/mlg-ulb/creditcardfraud)
- Dal Pozzolo et al. (2015) — *Calibrating Probability with Undersampling for Unbalanced Classification* — IEEE SSCI
- [scikit-learn Documentation](https://scikit-learn.org/)
- [imbalanced-learn Documentation](https://imbalanced-learn.org/)
- [Isolation Forest — Liu et al. (2008)](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf)

---

## ⚠️ Disclaimer

This project is created **strictly for educational purposes** as part of the Arch Technologies Remote Cybersecurity Internship program. All analysis is performed in a **simulated, offline environment**. No real financial data or personal information is used.

---

*Made with 🛡️ for learning Blue Team cybersecurity skills*
