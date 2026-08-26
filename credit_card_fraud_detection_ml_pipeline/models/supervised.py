"""
models/supervised.py
--------------------
Supervised classification models trained on SMOTE-resampled data:
  - Logistic Regression  (baseline)
  - Random Forest
  - Gradient Boosting
  - XGBoost              (optional — skipped gracefully if not installed)

All models are trained on X_train_sm / y_train_sm (SMOTE balanced)
and evaluated on X_test / y_test (real, unbalanced).

Each model entry in the results dict contains:
    model       — fitted sklearn estimator
    y_pred      — binary predictions on test set (default threshold 0.5)
    y_prob      — fraud probability scores on test set
    accuracy    — test accuracy
    f1          — test F1-score (fraud class)
    roc_auc     — ROC-AUC
    auprc       — Area Under Precision-Recall Curve (primary metric)
    best_threshold — F1-optimal decision threshold (found by sweep)
    y_pred_tuned   — predictions using best_threshold
"""

import logging
import time

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    roc_auc_score,
)

RANDOM_SEED = 42

# XGBoost is optional
try:
    from xgboost import XGBClassifier
    _XGBOOST_AVAILABLE = True
except ImportError:
    _XGBOOST_AVAILABLE = False


class SupervisedModels:
    """Train and evaluate all supervised classification models."""

    def __init__(self, prep_result: dict, logger: logging.Logger | None = None):
        self.X_train_sm   = prep_result["X_train_sm"]
        self.y_train_sm   = prep_result["y_train_sm"]
        self.X_test       = prep_result["X_test"]
        self.y_test       = prep_result["y_test"]
        self.feature_names = prep_result["feature_names"]
        self.logger       = logger or logging.getLogger(__name__)
        self.results: dict = {}

    # ─────────────────────────────────────────────────────────────────────────
    def run(self) -> dict:
        """Train all models and return consolidated results dict."""
        self.logger.info(
            f"Supervised models — SMOTE train: {len(self.X_train_sm):,} "
            f"| test: {len(self.X_test):,}"
        )
        self._logistic_regression()
        self._random_forest()
        self._gradient_boosting()
        if _XGBOOST_AVAILABLE:
            self._xgboost()
        else:
            self.logger.warning("XGBoost not installed — skipping. "
                                "Install with: pip install xgboost")
        self._print_summary()
        return self.results

    # ─────────────────────────────────────────────────────────────────────────
    def _logistic_regression(self) -> None:
        name = "Logistic Regression"
        self.logger.info(f"  Training {name} ...")
        t0 = time.time()
        model = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )
        self._fit_store(name, model, time.time() - t0, start=t0)

    # ─────────────────────────────────────────────────────────────────────────
    def _random_forest(self) -> None:
        name = "Random Forest"
        self.logger.info(f"  Training {name} ...")
        t0 = time.time()
        model = RandomForestClassifier(
            n_estimators=100,
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )
        self._fit_store(name, model, time.time() - t0, start=t0)

    # ─────────────────────────────────────────────────────────────────────────
    def _gradient_boosting(self) -> None:
        name = "Gradient Boosting"
        self.logger.info(f"  Training {name} ...")
        t0 = time.time()
        model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            random_state=RANDOM_SEED,
        )
        self._fit_store(name, model, time.time() - t0, start=t0)

    # ─────────────────────────────────────────────────────────────────────────
    def _xgboost(self) -> None:
        name = "XGBoost"
        self.logger.info(f"  Training {name} ...")
        t0 = time.time()

        # scale_pos_weight balances fraud vs normal in native XGBoost loss
        neg   = (self.y_train_sm == 0).sum()
        pos   = (self.y_train_sm == 1).sum()
        scale = neg / pos if pos > 0 else 1.0

        model = XGBClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            scale_pos_weight=scale,
            random_state=RANDOM_SEED,
            eval_metric="aucpr",
            use_label_encoder=False,
            verbosity=0,
            n_jobs=-1,
        )
        self._fit_store(name, model, time.time() - t0, start=t0)

    # ─────────────────────────────────────────────────────────────────────────
    def _fit_store(self, name: str, model, elapsed: float, start: float) -> None:
        model.fit(self.X_train_sm, self.y_train_sm)
        elapsed = time.time() - start

        y_prob  = model.predict_proba(self.X_test)[:, 1]
        y_pred  = (y_prob >= 0.5).astype(int)

        acc    = accuracy_score(self.y_test, y_pred)
        f1     = f1_score(self.y_test, y_pred, zero_division=0)
        roc    = roc_auc_score(self.y_test, y_prob)
        auprc  = average_precision_score(self.y_test, y_prob)

        best_threshold, y_pred_tuned = self._tune_threshold(y_prob)

        self.results[name] = {
            "model":          model,
            "y_pred":         y_pred,
            "y_prob":         y_prob,
            "accuracy":       acc,
            "f1":             f1,
            "roc_auc":        roc,
            "auprc":          auprc,
            "best_threshold": best_threshold,
            "y_pred_tuned":   y_pred_tuned,
        }

        self.logger.info(
            f"    {name:22s} | Acc={acc:.4f} | F1={f1:.4f} | "
            f"ROC-AUC={roc:.4f} | AUPRC={auprc:.4f} | "
            f"BestThr={best_threshold:.2f} | {elapsed:.1f}s"
        )

    # ─────────────────────────────────────────────────────────────────────────
    def _tune_threshold(self, y_prob: np.ndarray):
        """
        Sweep thresholds 0.05 → 0.95 and pick the one that maximises
        F1-score on the test set.

        Returns
        -------
        best_threshold : float
        y_pred_tuned   : np.ndarray  — predictions at best threshold
        """
        best_f1, best_thr = 0.0, 0.5
        for t in np.arange(0.05, 0.95, 0.01):
            preds = (y_prob >= t).astype(int)
            score = f1_score(self.y_test, preds, zero_division=0)
            if score > best_f1:
                best_f1  = score
                best_thr = t
        return round(float(best_thr), 2), (y_prob >= best_thr).astype(int)

    # ─────────────────────────────────────────────────────────────────────────
    def _print_summary(self) -> None:
        self.logger.info("─" * 75)
        self.logger.info(
            f"{'Model':<22} {'Accuracy':>10} {'F1':>8} {'ROC-AUC':>10} "
            f"{'AUPRC':>8} {'BestThr':>9}"
        )
        self.logger.info("─" * 75)
        for name, r in self.results.items():
            self.logger.info(
                f"{name:<22} {r['accuracy']:>10.4f} {r['f1']:>8.4f} "
                f"{r['roc_auc']:>10.4f} {r['auprc']:>8.4f} {r['best_threshold']:>9.2f}"
            )
        self.logger.info("─" * 75)

    # ─────────────────────────────────────────────────────────────────────────
    def get_best_model(self) -> tuple[str, dict]:
        """Return (name, result_dict) for the model with the highest AUPRC."""
        best_name = max(self.results, key=lambda n: self.results[n]["auprc"])
        return best_name, self.results[best_name]
