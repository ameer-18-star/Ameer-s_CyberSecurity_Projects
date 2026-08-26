"""
models/unsupervised.py
----------------------
Unsupervised anomaly detection models:
  - Isolation Forest
  - Local Outlier Factor (LOF)
  - One-Class SVM

All three are trained on the 10% sample (X_sample) because LOF and
One-Class SVM have O(n²) complexity — too slow on 280k rows.

Each model returns a results dict with:
    y_pred      — binary predictions (0=normal, 1=fraud)
    y_score     — raw anomaly scores (higher = more anomalous)
    accuracy    — overall accuracy
    f1          — F1-score (fraud class)
    roc_auc     — ROC-AUC
    auprc       — Area Under Precision-Recall Curve (primary metric)
"""

import logging
import time

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    roc_auc_score,
)
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM

RANDOM_SEED = 42


class UnsupervisedModels:
    """Train and evaluate all unsupervised anomaly detection models."""

    def __init__(self, prep_result: dict, logger: logging.Logger | None = None):
        self.X_sample        = prep_result["X_sample"]
        self.y_sample        = prep_result["y_sample"]
        self.outlier_fraction = prep_result["outlier_fraction"]
        self.logger          = logger or logging.getLogger(__name__)
        self.results: dict   = {}

    # ─────────────────────────────────────────────────────────────────────────
    def run(self) -> dict:
        """Train all models and return consolidated results dict."""
        self.logger.info(
            f"Unsupervised models — sample size: {len(self.X_sample):,} "
            f"| outlier fraction: {self.outlier_fraction:.5f}"
        )
        self._isolation_forest()
        self._local_outlier_factor()
        self._one_class_svm()
        self._print_summary()
        return self.results

    # ─────────────────────────────────────────────────────────────────────────
    def _isolation_forest(self) -> None:
        name = "Isolation Forest"
        self.logger.info(f"  Training {name} ...")
        t0 = time.time()

        model = IsolationForest(
            n_estimators=100,
            contamination=self.outlier_fraction,
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )
        model.fit(self.X_sample)

        # IsolationForest.predict returns  1 (normal) / -1 (anomaly)
        raw_pred  = model.predict(self.X_sample)
        y_pred    = np.where(raw_pred == -1, 1, 0)          # → 1=fraud, 0=normal

        # decision_function: lower score = more anomalous; negate for "fraud score"
        y_score   = -model.decision_function(self.X_sample)

        self._store(name, y_pred, y_score, model, time.time() - t0)

    # ─────────────────────────────────────────────────────────────────────────
    def _local_outlier_factor(self) -> None:
        name = "Local Outlier Factor"
        self.logger.info(f"  Training {name} (this may take a moment) ...")
        t0 = time.time()

        model = LocalOutlierFactor(
            n_neighbors=20,
            contamination=self.outlier_fraction,
            n_jobs=-1,
        )
        raw_pred = model.fit_predict(self.X_sample)
        y_pred   = np.where(raw_pred == -1, 1, 0)

        # negative_outlier_factor_: more negative = more anomalous; negate to get "fraud score"
        y_score  = -model.negative_outlier_factor_

        self._store(name, y_pred, y_score, model=None, elapsed=time.time() - t0)

    # ─────────────────────────────────────────────────────────────────────────
    def _one_class_svm(self) -> None:
        name = "One-Class SVM"
        self.logger.info(f"  Training {name} (slow — using small sample) ...")
        t0 = time.time()

        model = OneClassSVM(
            kernel="rbf",
            nu=min(self.outlier_fraction * 2, 0.5),   # upper bound on outlier fraction
            gamma="scale",
        )
        model.fit(self.X_sample[self.y_sample == 0])   # train on normal only

        raw_pred = model.predict(self.X_sample)
        y_pred   = np.where(raw_pred == -1, 1, 0)

        # decision_function: negative = anomaly; negate for "fraud score"
        y_score  = -model.decision_function(self.X_sample)

        self._store(name, y_pred, y_score, model, time.time() - t0)

    # ─────────────────────────────────────────────────────────────────────────
    def _store(
        self,
        name: str,
        y_pred: np.ndarray,
        y_score: np.ndarray,
        model,
        elapsed: float,
    ) -> None:
        y_true = self.y_sample.values

        acc    = accuracy_score(y_true, y_pred)
        f1     = f1_score(y_true, y_pred, zero_division=0)
        try:
            roc    = roc_auc_score(y_true, y_score)
            auprc  = average_precision_score(y_true, y_score)
        except ValueError:
            roc   = 0.5
            auprc = y_true.mean()

        self.results[name] = {
            "y_pred":   y_pred,
            "y_score":  y_score,
            "accuracy": acc,
            "f1":       f1,
            "roc_auc":  roc,
            "auprc":    auprc,
            "model":    model,
        }

        self.logger.info(
            f"    {name:25s} | Acc={acc:.4f} | F1={f1:.4f} | "
            f"ROC-AUC={roc:.4f} | AUPRC={auprc:.4f} | {elapsed:.1f}s"
        )

    # ─────────────────────────────────────────────────────────────────────────
    def _print_summary(self) -> None:
        self.logger.info("─" * 65)
        self.logger.info(f"{'Model':<25} {'Accuracy':>10} {'F1':>8} {'ROC-AUC':>10} {'AUPRC':>8}")
        self.logger.info("─" * 65)
        for name, r in self.results.items():
            self.logger.info(
                f"{name:<25} {r['accuracy']:>10.4f} {r['f1']:>8.4f} "
                f"{r['roc_auc']:>10.4f} {r['auprc']:>8.4f}"
            )
        self.logger.info("─" * 65)
