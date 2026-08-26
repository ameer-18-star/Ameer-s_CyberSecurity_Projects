"""
models/evaluator.py
-------------------
Unified model evaluator.  Takes unsupervised + supervised results
and produces:
  - Classification reports (printed to log)
  - Confusion matrix plots (unsupervised & supervised)
  - PR / ROC curves (supervised only)
  - Feature importance plot (Random Forest if present)
  - Threshold tuning plot (best supervised model)
  - Summary comparison bar chart (all models)
  - Pandas summary table (saved to outputs/model_summary.csv)
"""

import logging
import os

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report

from utils.visualizer import Visualizer

OUTPUT_DIR = "outputs"


class ModelEvaluator:
    """Evaluate and compare all trained models."""

    def __init__(
        self,
        unsup_results: dict,
        sup_results: dict,
        y_test,
        y_sample,
        save_plots: bool = True,
        logger: logging.Logger | None = None,
    ):
        self.unsup   = unsup_results
        self.sup     = sup_results
        self.y_test  = y_test
        self.y_sample = y_sample
        self.save    = save_plots
        self.logger  = logger or logging.getLogger(__name__)

        # Visualizer needs a DataFrame — pass empty; it's only used for EDA
        self.viz = Visualizer(
            data=pd.DataFrame(),
            save_plots=save_plots,
            logger=logger,
        )
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ─────────────────────────────────────────────────────────────────────────
    def run(self) -> pd.DataFrame:
        """Run all evaluation steps; return summary DataFrame."""
        self._print_classification_reports()
        self._plot_confusion_matrices()
        self._plot_curves()
        self._plot_feature_importance()
        self._plot_threshold_tuning()
        summary_df = self._build_summary()
        self._plot_comparison(summary_df)
        self._save_summary(summary_df)
        return summary_df

    # ─────────────────────────────────────────────────────────────────────────
    def _print_classification_reports(self) -> None:
        self.logger.info("─" * 60)
        self.logger.info("CLASSIFICATION REPORTS — Unsupervised (sample)")
        for name, res in self.unsup.items():
            self.logger.info(f"\n  ── {name} ──")
            report = classification_report(
                self.y_sample, res["y_pred"],
                target_names=["Normal", "Fraud"],
                zero_division=0,
            )
            for line in report.splitlines():
                self.logger.info(f"    {line}")

        self.logger.info("─" * 60)
        self.logger.info("CLASSIFICATION REPORTS — Supervised (full test set)")
        for name, res in self.sup.items():
            self.logger.info(f"\n  ── {name} ──")
            report = classification_report(
                self.y_test, res["y_pred"],
                target_names=["Normal", "Fraud"],
                zero_division=0,
            )
            for line in report.splitlines():
                self.logger.info(f"    {line}")
            self.logger.info(
                f"    Tuned threshold ({res['best_threshold']:.2f}) F1 = "
                f"{self._f1(self.y_test, res['y_pred_tuned']):.4f}"
            )
        self.logger.info("─" * 60)

    # ─────────────────────────────────────────────────────────────────────────
    def _plot_confusion_matrices(self) -> None:
        if not self.unsup:
            return
        self.viz.plot_confusion_matrices(
            results=self.unsup,
            y_true=self.y_sample,
            title_prefix="Unsupervised Models",
            filename="plot_confusion_unsupervised.png",
            cmap="Oranges",
        )
        self.viz.plot_confusion_matrices(
            results=self.sup,
            y_true=self.y_test,
            title_prefix="Supervised Models",
            filename="plot_confusion_supervised.png",
            cmap="Blues",
        )

    # ─────────────────────────────────────────────────────────────────────────
    def _plot_curves(self) -> None:
        if not self.sup:
            return
        self.viz.plot_pr_roc_curves(self.sup, self.y_test)

    # ─────────────────────────────────────────────────────────────────────────
    def _plot_feature_importance(self) -> None:
        """Plot feature importances from Random Forest (if trained)."""
        for name in ("Random Forest", "XGBoost", "Gradient Boosting"):
            if name not in self.sup:
                continue
            model = self.sup[name]["model"]
            if not hasattr(model, "feature_importances_"):
                continue
            # Infer feature names from the training data shape
            # (stored in model if sklearn >= 1.0, otherwise use generic names)
            try:
                feat_names = list(model.feature_names_in_)
            except AttributeError:
                n = len(model.feature_importances_)
                feat_names = [f"V{i}" for i in range(1, n - 1)] + [
                    "scaled_Amount", "scaled_Time"
                ]
            self.viz.plot_feature_importance(model, feat_names, model_name=name)
            break   # only plot for the first model that has importances

    # ─────────────────────────────────────────────────────────────────────────
    def _plot_threshold_tuning(self) -> None:
        """Plot threshold tuning for the best supervised model by AUPRC."""
        if not self.sup:
            return
        best_name = max(self.sup, key=lambda n: self.sup[n]["auprc"])
        res = self.sup[best_name]
        self.viz.plot_threshold_tuning(
            y_test=self.y_test,
            y_probs=res["y_prob"],
            model_name=best_name,
            best_threshold=res["best_threshold"],
        )

    # ─────────────────────────────────────────────────────────────────────────
    def _build_summary(self) -> pd.DataFrame:
        rows = []
        for name, res in self.unsup.items():
            rows.append({
                "Model":    name,
                "Type":     "Unsupervised",
                "Accuracy": round(res["accuracy"], 4),
                "F1-Score": round(res["f1"], 4),
                "ROC-AUC":  round(res["roc_auc"], 4),
                "AUPRC":    round(res["auprc"], 4),
            })
        for name, res in self.sup.items():
            rows.append({
                "Model":    name,
                "Type":     "Supervised",
                "Accuracy": round(res["accuracy"], 4),
                "F1-Score": round(res["f1"], 4),
                "ROC-AUC":  round(res["roc_auc"], 4),
                "AUPRC":    round(res["auprc"], 4),
            })
        df = pd.DataFrame(rows)

        self.logger.info("\n" + df.to_string(index=False))
        return df

    # ─────────────────────────────────────────────────────────────────────────
    def _plot_comparison(self, summary_df: pd.DataFrame) -> None:
        self.viz.plot_model_comparison(summary_df)

    # ─────────────────────────────────────────────────────────────────────────
    def _save_summary(self, df: pd.DataFrame) -> None:
        path = os.path.join(OUTPUT_DIR, "model_summary.csv")
        df.to_csv(path, index=False)
        self.logger.info(f"Model summary saved → {path}")

    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _f1(y_true, y_pred) -> float:
        from sklearn.metrics import f1_score
        return f1_score(y_true, y_pred, zero_division=0)
