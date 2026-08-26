"""
utils/alert_system.py
---------------------
Security Operations Center (SOC) Alert Triage Simulation.

Takes the best supervised model (by AUPRC) and scores transactions,
assigning four severity tiers:

    🔴 CRITICAL  ≥ 85%  → Block immediately + notify cardholder
    🟠 HIGH      ≥ 65%  → Hold for manual analyst review
    🟡 MEDIUM    ≥ thr  → Log and monitor
    🟢 CLEAR     < thr  → Allow; no action required

Outputs:
    outputs/fraud_alert_log.json  — structured log for SIEM ingestion
    Console / log summary table
"""

import json
import logging
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

OUTPUT_DIR = "outputs"

# Severity thresholds (probability of fraud)
CRITICAL_THRESHOLD = 0.85
HIGH_THRESHOLD     = 0.65


class AlertSystem:
    """Score transactions and generate SOC-style alert triage."""

    def __init__(
        self,
        sup_results: dict,
        X_test,
        y_test,
        logger: logging.Logger | None = None,
    ):
        self.sup_results = sup_results
        self.X_test      = X_test
        self.y_test      = y_test
        self.logger      = logger or logging.getLogger(__name__)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Pick the best model by AUPRC
        self.best_name, self.best_result = self._pick_best()
        self.model          = self.best_result["model"]
        self.best_threshold = self.best_result["best_threshold"]

    # ─────────────────────────────────────────────────────────────────────────
    def run(self) -> list[dict]:
        """
        Run the SOC simulation on the test set.
        Returns the list of alert records.
        """
        self.logger.info(
            f"SOC Alert Simulation using '{self.best_name}' "
            f"(threshold={self.best_threshold:.2f})"
        )

        alerts = self._triage(self.X_test, self.y_test)
        self._print_summary(alerts)
        self._save_json(alerts)
        return alerts

    # ─────────────────────────────────────────────────────────────────────────
    def score_new_file(self, csv_path: str, preprocessor) -> None:
        """
        Score new, unseen transactions from a CSV file.

        Parameters
        ----------
        csv_path     : path to a CSV with the same columns as the training data
        preprocessor : fitted Preprocessor instance (for transform_new)
        """
        self.logger.info(f"Scoring new transactions from '{csv_path}' ...")
        try:
            df_raw = pd.read_csv(csv_path)
        except FileNotFoundError:
            self.logger.error(f"File not found: {csv_path}")
            return

        df_proc = preprocessor.transform_new(df_raw)

        # Align columns to what the model was trained on
        try:
            df_proc = df_proc[self.X_test.columns]
        except KeyError as e:
            self.logger.error(f"Column mismatch: {e}")
            return

        y_prob = self.model.predict_proba(df_proc)[:, 1]
        # No ground-truth labels for new data → pass zeros as placeholder
        y_true = pd.Series(np.zeros(len(df_proc), dtype=int))

        alerts = self._triage(df_proc, y_true, y_prob_override=y_prob)
        self._print_summary(alerts)

        out_path = os.path.join(OUTPUT_DIR, "new_transactions_alert_log.json")
        self._save_json(alerts, path=out_path)
        self.logger.info(f"New transaction alerts saved → {out_path}")

    # ─────────────────────────────────────────────────────────────────────────
    def _triage(self, X, y_true, y_prob_override=None) -> list[dict]:
        """Score transactions and assign severity tiers."""
        if y_prob_override is not None:
            y_prob = y_prob_override
        else:
            y_prob = self.model.predict_proba(X)[:, 1]

        true_labels = (
            y_true.values if hasattr(y_true, "values") else np.array(y_true)
        )

        alerts = []
        for i, prob in enumerate(y_prob):
            severity, action = self._assign_severity(prob)
            alerts.append({
                "transaction_id":  int(i),
                "fraud_probability": round(float(prob), 6),
                "severity":         severity,
                "action":           action,
                "true_label":       int(true_labels[i]),
                "correct":          bool(
                    (prob >= self.best_threshold) == bool(true_labels[i])
                ),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model_used": self.best_name,
            })
        return alerts

    # ─────────────────────────────────────────────────────────────────────────
    def _assign_severity(self, prob: float) -> tuple[str, str]:
        if prob >= CRITICAL_THRESHOLD:
            return "CRITICAL", "Block transaction immediately; notify cardholder"
        elif prob >= HIGH_THRESHOLD:
            return "HIGH", "Hold transaction; flag for manual analyst review"
        elif prob >= self.best_threshold:
            return "MEDIUM", "Log and monitor; allow with enhanced tracking"
        else:
            return "CLEAR", "Allow; no action required"

    # ─────────────────────────────────────────────────────────────────────────
    def _print_summary(self, alerts: list[dict]) -> None:
        df = pd.DataFrame(alerts)

        self.logger.info("─" * 60)
        self.logger.info("SOC ALERT TRIAGE SUMMARY")
        self.logger.info("─" * 60)

        counts = df["severity"].value_counts()
        total  = len(df)

        for sev in ("CRITICAL", "HIGH", "MEDIUM", "CLEAR"):
            n   = counts.get(sev, 0)
            pct = n / total * 100
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "CLEAR": "🟢"}[sev]
            self.logger.info(f"  {icon} {sev:<10}: {n:>6,} ({pct:5.2f}%)")

        self.logger.info("─" * 60)

        # Accuracy on flagged vs not-flagged
        flagged = df[df["severity"] != "CLEAR"]
        if len(flagged) > 0:
            correct_flags = flagged["correct"].sum()
            self.logger.info(
                f"  Flagged transactions : {len(flagged):,} "
                f"({len(flagged)/total*100:.2f}%)"
            )
            self.logger.info(
                f"  Correct flags        : {correct_flags:,} "
                f"({correct_flags/len(flagged)*100:.2f}% precision on flagged)"
            )

        # Critical alerts that are actual fraud
        critical = df[df["severity"] == "CRITICAL"]
        if len(critical) > 0:
            true_critical = critical["true_label"].sum()
            self.logger.info(
                f"  CRITICAL true fraud  : {true_critical}/{len(critical)}"
            )
        self.logger.info("─" * 60)

        # Show sample CRITICAL / HIGH alerts
        top_alerts = df[df["severity"].isin(["CRITICAL", "HIGH"])].head(10)
        if len(top_alerts) > 0:
            self.logger.info("  Sample CRITICAL/HIGH Alerts (top 10):")
            self.logger.info(
                f"  {'TxnID':>7} {'P(fraud)':>10} {'Severity':<10} "
                f"{'TrueLabel':>10} {'Correct':>8}"
            )
            for _, row in top_alerts.iterrows():
                self.logger.info(
                    f"  {int(row['transaction_id']):>7} "
                    f"{row['fraud_probability']:>10.4f} "
                    f"{row['severity']:<10} "
                    f"{'Fraud' if row['true_label'] else 'Normal':>10} "
                    f"{'✓' if row['correct'] else '✗':>8}"
                )
        self.logger.info("─" * 60)

    # ─────────────────────────────────────────────────────────────────────────
    def _save_json(
        self, alerts: list[dict], path: str | None = None
    ) -> None:
        if path is None:
            path = os.path.join(OUTPUT_DIR, "fraud_alert_log.json")

        payload = {
            "metadata": {
                "generated_at":    datetime.now(timezone.utc).isoformat(),
                "model":           self.best_name,
                "threshold":       self.best_threshold,
                "total_transactions": len(alerts),
                "severity_counts": {
                    sev: sum(1 for a in alerts if a["severity"] == sev)
                    for sev in ("CRITICAL", "HIGH", "MEDIUM", "CLEAR")
                },
            },
            "alerts": alerts,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

        self.logger.info(f"Alert log saved → {path}  ({len(alerts):,} records)")

    # ─────────────────────────────────────────────────────────────────────────
    def _pick_best(self) -> tuple[str, dict]:
        """Select the supervised model with the highest AUPRC."""
        best_name = max(self.sup_results, key=lambda n: self.sup_results[n]["auprc"])
        self.logger.info(
            f"Best model selected for SOC simulation: '{best_name}' "
            f"(AUPRC={self.sup_results[best_name]['auprc']:.4f})"
        )
        return best_name, self.sup_results[best_name]
