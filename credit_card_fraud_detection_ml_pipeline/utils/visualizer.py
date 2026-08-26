"""
utils/visualizer.py
-------------------
All visualisation functions for:
  - Exploratory Data Analysis (EDA)
  - Model evaluation (confusion matrices, PR curves, ROC curves,
    feature importance, threshold tuning, comparison bar charts)

Each method saves a PNG to outputs/ and optionally displays it.
"""

import logging
import os

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix,
    precision_recall_curve,
    roc_curve,
)

OUTPUT_DIR = "outputs"
LABELS = ["Normal", "Fraud"]
sns.set_theme(style="darkgrid", palette="muted")


class Visualizer:
    """Generate and save all project visualisations."""

    def __init__(
        self,
        data: pd.DataFrame,
        save_plots: bool = True,
        logger: logging.Logger | None = None,
    ):
        self.data       = data
        self.save_plots = save_plots
        self.logger     = logger or logging.getLogger(__name__)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ─────────────────────────────────────────────────────────────────────────
    # EDA
    # ─────────────────────────────────────────────────────────────────────────

    def run_full_eda(self) -> None:
        """Run all EDA plots in sequence."""
        self.logger.info("Generating EDA plots ...")
        self.plot_class_distribution()
        self.plot_amount_analysis()
        self.plot_time_vs_amount()
        self.plot_correlation_heatmap()
        self.logger.info("EDA plots done.")

    def plot_class_distribution(self) -> None:
        counts   = self.data["Class"].value_counts()
        fraud_pct = counts[1] / len(self.data) * 100

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle(
            f"Highly Imbalanced Dataset  —  Fraud = {fraud_pct:.3f}% of transactions",
            fontsize=12, color="crimson"
        )

        # Bar
        axes[0].bar(LABELS, counts.values,
                    color=["steelblue", "crimson"], edgecolor="black")
        axes[0].set_title("Transaction Class Distribution", fontweight="bold")
        axes[0].set_ylabel("Number of Transactions")
        for i, v in enumerate(counts.values):
            axes[0].text(i, v + 50, f"{v:,}", ha="center", fontweight="bold")

        # Pie
        axes[1].pie(
            counts.values, labels=LABELS,
            colors=["steelblue", "crimson"],
            autopct="%1.3f%%", startangle=90,
            explode=(0, 0.1), shadow=True,
        )
        axes[1].set_title("Class Proportion", fontweight="bold")

        plt.tight_layout()
        self._save("plot_class_distribution.png")

    def plot_amount_analysis(self) -> None:
        fraud  = self.data[self.data["Class"] == 1]
        normal = self.data[self.data["Class"] == 0]

        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle("Transaction Amount Analysis by Class", fontsize=14, fontweight="bold")

        # Histograms
        for ax, df, label, color in [
            (axes[0, 0], fraud,  "Fraud",  "crimson"),
            (axes[0, 1], normal, "Normal", "steelblue"),
        ]:
            ax.hist(df["Amount"], bins=50, color=color, alpha=0.8, edgecolor="black")
            ax.set_title(f"{label} — Amount Histogram")
            ax.set_xlabel("Amount ($)")
            ax.set_ylabel("Count")
            ax.set_yscale("log")

        # Box plot
        axes[1, 0].boxplot(
            [normal["Amount"], fraud["Amount"]],
            labels=LABELS, patch_artist=True,
            boxprops=dict(facecolor="lightblue"),
        )
        axes[1, 0].set_title("Amount Box Plot by Class")
        axes[1, 0].set_ylabel("Amount ($)")
        axes[1, 0].set_yscale("log")

        # KDE
        fraud["Amount"].plot.kde(ax=axes[1, 1], color="crimson",
                                  label="Fraud", linewidth=2)
        normal["Amount"].clip(upper=500).plot.kde(
            ax=axes[1, 1], color="steelblue",
            label="Normal (clipped $500)", linewidth=2,
        )
        axes[1, 1].set_title("Amount KDE — Fraud vs Normal")
        axes[1, 1].set_xlabel("Amount ($)")
        axes[1, 1].legend()

        plt.tight_layout()
        self._save("plot_amount_analysis.png")

    def plot_time_vs_amount(self) -> None:
        fraud  = self.data[self.data["Class"] == 1]
        normal = self.data[self.data["Class"] == 0]

        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(14, 8))
        fig.suptitle("Time of Transaction vs Amount by Class",
                     fontsize=14, fontweight="bold")

        ax1.scatter(fraud["Time"],  fraud["Amount"],  alpha=0.5, color="crimson",   s=10)
        ax1.set_title("Fraud Transactions")
        ax1.set_ylabel("Amount ($)")

        ax2.scatter(normal["Time"], normal["Amount"], alpha=0.2, color="steelblue", s=5)
        ax2.set_title("Normal Transactions")
        ax2.set_ylabel("Amount ($)")
        ax2.set_xlabel("Time (seconds from first transaction)")

        plt.tight_layout()
        self._save("plot_time_vs_amount.png")

    def plot_correlation_heatmap(self) -> None:
        sample = self.data.sample(frac=0.1, random_state=42)
        corrmat = sample.corr()
        mask = np.triu(np.ones_like(corrmat, dtype=bool))

        plt.figure(figsize=(22, 18))
        sns.heatmap(
            corrmat, mask=mask, annot=False, cmap="RdYlGn",
            linewidths=0.3, vmin=-1, vmax=1, center=0,
            square=True, cbar_kws={"shrink": 0.8},
        )
        plt.title("Feature Correlation Matrix (10% sample)",
                  fontsize=14, fontweight="bold")
        plt.tight_layout()
        self._save("plot_correlation_heatmap.png")

    # ─────────────────────────────────────────────────────────────────────────
    # Model evaluation
    # ─────────────────────────────────────────────────────────────────────────

    def plot_confusion_matrices(
        self, results: dict, y_true, title_prefix: str, filename: str,
        cmap: str = "Blues"
    ) -> None:
        n = len(results)
        fig, axes = plt.subplots(1, n, figsize=(5 * n, 5))
        if n == 1:
            axes = [axes]
        fig.suptitle(f"Confusion Matrices — {title_prefix}",
                     fontsize=13, fontweight="bold")

        for ax, (name, res) in zip(axes, results.items()):
            cm = confusion_matrix(y_true, res["y_pred"])
            sns.heatmap(
                cm, annot=True, fmt="d", cmap=cmap, ax=ax,
                xticklabels=LABELS, yticklabels=LABELS,
            )
            ax.set_title(name)
            ax.set_xlabel("Predicted")
            ax.set_ylabel("Actual")

        plt.tight_layout()
        self._save(filename)

    def plot_pr_roc_curves(self, results: dict, y_test) -> None:
        palette = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336"]
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle("Supervised Model Performance Curves",
                     fontsize=14, fontweight="bold")

        for (name, res), color in zip(results.items(), palette):
            probs = res["y_prob"]

            prec, rec, _ = precision_recall_curve(y_test, probs)
            ax1.plot(rec, prec, label=f"{name} (AUPRC={res['auprc']:.3f})",
                     color=color, linewidth=2)

            fpr, tpr, _ = roc_curve(y_test, probs)
            ax2.plot(fpr, tpr, label=f"{name} (AUC={res['roc_auc']:.3f})",
                     color=color, linewidth=2)

        ax1.axhline(y=y_test.mean(), linestyle="--", color="gray",
                    label="Random baseline")
        ax2.plot([0, 1], [0, 1], "k--", label="Random baseline")

        ax1.set_xlabel("Recall"); ax1.set_ylabel("Precision")
        ax1.set_title("Precision-Recall Curve\n(AUPRC — best for imbalanced data)")
        ax1.legend(loc="upper right", fontsize=9); ax1.grid(alpha=0.4)

        ax2.set_xlabel("False Positive Rate"); ax2.set_ylabel("True Positive Rate")
        ax2.set_title("ROC Curve")
        ax2.legend(loc="lower right", fontsize=9); ax2.grid(alpha=0.4)

        plt.tight_layout()
        self._save("plot_pr_roc_curves.png")

    def plot_feature_importance(
        self, model, feature_names: list, model_name: str = "Random Forest"
    ) -> None:
        importances = model.feature_importances_
        feat_df = (
            pd.DataFrame({"Feature": feature_names, "Importance": importances})
            .sort_values("Importance", ascending=False)
            .head(20)
        )

        plt.figure(figsize=(12, 7))
        sns.barplot(data=feat_df, x="Importance", y="Feature",
                    palette="viridis", edgecolor="black")
        plt.title(f"Top 20 Feature Importances — {model_name}",
                  fontsize=14, fontweight="bold")
        plt.xlabel("Importance Score")
        plt.tight_layout()
        self._save("plot_feature_importance.png")

    def plot_threshold_tuning(
        self, y_test, y_probs: np.ndarray, model_name: str, best_threshold: float
    ) -> None:
        from sklearn.metrics import f1_score, precision_score, recall_score

        thresholds = np.arange(0.05, 0.95, 0.01)
        precisions, recalls, f1s = [], [], []

        for t in thresholds:
            y_pred_t = (y_probs >= t).astype(int)
            precisions.append(precision_score(y_test, y_pred_t, zero_division=0))
            recalls.append(recall_score(y_test, y_pred_t, zero_division=0))
            f1s.append(f1_score(y_test, y_pred_t, zero_division=0))

        plt.figure(figsize=(13, 6))
        plt.plot(thresholds, precisions, label="Precision", color="blue", linewidth=2)
        plt.plot(thresholds, recalls,    label="Recall",    color="red",  linewidth=2)
        plt.plot(thresholds, f1s,        label="F1-Score",  color="green",linewidth=2)
        plt.axvline(x=best_threshold, linestyle="--", color="orange",
                    label=f"Best F1 threshold = {best_threshold:.2f}")
        plt.axvline(x=0.5, linestyle=":", color="gray",
                    label="Default threshold = 0.50")
        plt.xlabel("Decision Threshold")
        plt.ylabel("Score")
        plt.title(f"Threshold Tuning — {model_name}", fontsize=13, fontweight="bold")
        plt.legend(); plt.grid(alpha=0.4)
        plt.tight_layout()
        self._save("plot_threshold_tuning.png")

    def plot_model_comparison(self, summary_df: pd.DataFrame) -> None:
        metrics = ["F1-Score", "ROC-AUC", "AUPRC"]
        palette = [
            "#FF6B6B" if t == "Unsupervised" else "#4ECDC4"
            for t in summary_df["Type"]
        ]

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle("Model Comparison Across Metrics",
                     fontsize=14, fontweight="bold")

        for ax, metric in zip(axes, metrics):
            vals = summary_df[metric].astype(float)
            bars = ax.bar(summary_df["Model"], vals,
                          color=palette, edgecolor="black", linewidth=0.7)
            ax.set_title(metric, fontweight="bold")
            ax.set_ylabel("Score")
            ax.set_ylim(0, 1.05)
            ax.tick_params(axis="x", rotation=35)
            for bar, val in zip(bars, vals):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.01,
                    f"{val:.3f}", ha="center", fontsize=8,
                )

        legend_elements = [
            mpatches.Patch(facecolor="#FF6B6B", label="Unsupervised"),
            mpatches.Patch(facecolor="#4ECDC4", label="Supervised"),
        ]
        fig.legend(handles=legend_elements, loc="lower center",
                   ncol=2, fontsize=11, bbox_to_anchor=(0.5, -0.04))
        plt.tight_layout()
        self._save("plot_model_comparison.png")

    # ─────────────────────────────────────────────────────────────────────────
    def _save(self, filename: str) -> None:
        if not self.save_plots:
            plt.close()
            return
        path = os.path.join(OUTPUT_DIR, filename)
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        self.logger.info(f"  Saved → {path}")
