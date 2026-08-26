"""
utils/data_loader.py
--------------------
Handles loading of the credit card fraud dataset.

If the real CSV is unavailable (simulated / offline environment),
automatically generates synthetic data so every part of the
pipeline still runs without errors.
"""

import logging
import os

import numpy as np
import pandas as pd

RANDOM_SEED = 42


class DataLoader:
    """Load creditcard.csv or generate synthetic demo data."""

    def __init__(
        self,
        csv_path: str = "creditcard.csv",
        force_synthetic: bool = False,
        logger: logging.Logger | None = None,
    ):
        self.csv_path = csv_path
        self.force_synthetic = force_synthetic
        self.logger = logger or logging.getLogger(__name__)

    # ─────────────────────────────────────────────────────────────────────────
    def load(self) -> pd.DataFrame:
        """Return a DataFrame with the credit card transaction data."""
        if not self.force_synthetic and os.path.exists(self.csv_path):
            return self._load_csv()
        else:
            if not self.force_synthetic:
                self.logger.warning(
                    f"'{self.csv_path}' not found. "
                    "Generating synthetic demo data instead."
                )
                self.logger.warning(
                    "Download the real dataset from: "
                    "https://www.kaggle.com/mlg-ulb/creditcardfraud"
                )
            return self._generate_synthetic()

    # ─────────────────────────────────────────────────────────────────────────
    def _load_csv(self) -> pd.DataFrame:
        self.logger.info(f"Loading dataset from '{self.csv_path}' ...")
        data = pd.read_csv(self.csv_path, sep=",")

        self.logger.info(
            f"Dataset loaded: {data.shape[0]:,} rows × {data.shape[1]} columns"
        )
        self._validate(data)
        return data

    # ─────────────────────────────────────────────────────────────────────────
    def _generate_synthetic(self) -> pd.DataFrame:
        """
        Generate a synthetic dataset that mirrors the statistical
        properties of the Kaggle credit card fraud dataset.

        - V1–V28  : PCA-like features (normal fraud cluster shifted)
        - Time    : seconds elapsed since first transaction
        - Amount  : transaction amount (exponential distribution)
        - Class   : 0 = normal, 1 = fraud (0.5 % fraud rate)
        """
        self.logger.info("Generating synthetic demo dataset ...")
        rng = np.random.default_rng(RANDOM_SEED)

        n_normal = 9_950
        n_fraud  = 50
        v_cols   = [f"V{i}" for i in range(1, 29)]

        # Normal transactions — tight cluster near origin
        normal_v = rng.normal(loc=0.0, scale=0.8, size=(n_normal, 28))
        # Fraud transactions — shifted cluster with higher variance
        fraud_v  = rng.normal(loc=3.5, scale=2.0, size=(n_fraud, 28))

        df_normal = pd.DataFrame(normal_v, columns=v_cols)
        df_fraud  = pd.DataFrame(fraud_v,  columns=v_cols)

        df_normal["Time"]   = np.sort(rng.uniform(0, 172_792, n_normal))
        df_fraud ["Time"]   = rng.uniform(0, 172_792, n_fraud)
        df_normal["Amount"] = np.abs(rng.exponential(scale=80, size=n_normal))
        df_fraud ["Amount"] = np.abs(rng.exponential(scale=15, size=n_fraud))
        df_normal["Class"]  = 0
        df_fraud ["Class"]  = 1

        data = (
            pd.concat([df_normal, df_fraud], ignore_index=True)
            .sample(frac=1, random_state=RANDOM_SEED)
            .reset_index(drop=True)
        )

        fraud_pct = data["Class"].mean() * 100
        self.logger.info(
            f"Synthetic dataset ready: {data.shape[0]:,} rows  |  "
            f"Fraud: {data['Class'].sum()} ({fraud_pct:.2f}%)"
        )
        return data

    # ─────────────────────────────────────────────────────────────────────────
    def _validate(self, data: pd.DataFrame) -> None:
        """Basic sanity checks on the loaded dataset."""
        required = {"Time", "Amount", "Class"}
        missing = required - set(data.columns)
        if missing:
            raise ValueError(f"Dataset missing required columns: {missing}")

        null_count = data.isnull().values.sum()
        dup_count  = data.duplicated().sum()

        self.logger.info(f"  Null values  : {null_count}")
        self.logger.info(f"  Duplicates   : {dup_count}")

        fraud_count  = (data["Class"] == 1).sum()
        normal_count = (data["Class"] == 0).sum()
        fraud_pct    = fraud_count / len(data) * 100

        self.logger.info(f"  Normal       : {normal_count:,}")
        self.logger.info(f"  Fraud        : {fraud_count:,} ({fraud_pct:.3f}%)")
