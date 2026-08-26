"""
utils/preprocessor.py
---------------------
Data preprocessing pipeline:
  1. Scale Amount & Time (V1-V28 are already PCA-scaled)
  2. Stratified train/test split
  3. SMOTE oversampling on the training set ONLY
  4. Prepare a smaller sample for slow unsupervised models

Returns a dict with all split arrays and metadata needed
by downstream model modules.
"""

import logging

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

RANDOM_SEED = 42


class Preprocessor:
    """Full preprocessing pipeline for the fraud detection task."""

    def __init__(
        self,
        data: pd.DataFrame,
        sample_fraction: float = 0.1,
        test_size: float = 0.2,
        logger: logging.Logger | None = None,
    ):
        self.data            = data.copy()
        self.sample_fraction = sample_fraction
        self.test_size       = test_size
        self.logger          = logger or logging.getLogger(__name__)
        self.scaler          = StandardScaler()

    # ─────────────────────────────────────────────────────────────────────────
    def run(self) -> dict:
        """
        Execute the full preprocessing pipeline.

        Returns
        -------
        dict with keys:
            X, y               — full processed features / target
            X_train, y_train   — raw training split
            X_test,  y_test    — raw test split
            X_train_sm, y_train_sm  — SMOTE-resampled training set
            X_sample, y_sample — small sample for unsupervised models
            outlier_fraction   — fraud / valid ratio in sample
            feature_names      — list of feature column names
        """
        self.logger.info("Preprocessing — scaling Amount & Time ...")
        self._scale_features()

        self.logger.info("Preprocessing — stratified train/test split ...")
        X_train, X_test, y_train, y_test = self._split()

        self.logger.info("Preprocessing — applying SMOTE to training set ...")
        X_train_sm, y_train_sm = self._smote(X_train, y_train)

        self.logger.info(f"Preprocessing — sampling {self.sample_fraction:.0%} for unsupervised models ...")
        X_sample, y_sample, outlier_fraction = self._sample()

        result = {
            "X":              self.X,
            "y":              self.y,
            "X_train":        X_train,
            "y_train":        y_train,
            "X_test":         X_test,
            "y_test":         y_test,
            "X_train_sm":     X_train_sm,
            "y_train_sm":     y_train_sm,
            "X_sample":       X_sample,
            "y_sample":       y_sample,
            "outlier_fraction": outlier_fraction,
            "feature_names":  list(self.X.columns),
            "scaler":         self.scaler,
        }
        self._log_summary(result)
        return result

    # ─────────────────────────────────────────────────────────────────────────
    def _scale_features(self) -> None:
        """Scale Amount and Time to zero-mean unit-variance."""
        self.data["scaled_Amount"] = self.scaler.fit_transform(
            self.data[["Amount"]]
        )
        self.data["scaled_Time"] = self.scaler.fit_transform(
            self.data[["Time"]]
        )
        self.data.drop(["Amount", "Time"], axis=1, inplace=True)

        self.X = self.data.drop("Class", axis=1)
        self.y = self.data["Class"]

    # ─────────────────────────────────────────────────────────────────────────
    def _split(self):
        return train_test_split(
            self.X,
            self.y,
            test_size=self.test_size,
            random_state=RANDOM_SEED,
            stratify=self.y,
        )

    # ─────────────────────────────────────────────────────────────────────────
    def _smote(self, X_train, y_train):
        """
        Apply SMOTE to the training split only.
        Applying it before splitting would leak synthetic fraud samples
        into the test set, inflating performance metrics.
        """
        smote = SMOTE(random_state=RANDOM_SEED)
        X_sm, y_sm = smote.fit_resample(X_train, y_train)
        return X_sm, y_sm

    # ─────────────────────────────────────────────────────────────────────────
    def _sample(self):
        """
        Create a smaller stratified sample for LOF & One-Class SVM
        which have O(n²) complexity and are too slow on 280k rows.
        """
        sample_df = self.data.sample(
            frac=self.sample_fraction, random_state=RANDOM_SEED
        )
        X_sample = sample_df.drop("Class", axis=1)
        y_sample = sample_df["Class"]

        fraud_in_sample = (y_sample == 1).sum()
        valid_in_sample = (y_sample == 0).sum()
        outlier_fraction = fraud_in_sample / float(valid_in_sample)

        return X_sample, y_sample, outlier_fraction

    # ─────────────────────────────────────────────────────────────────────────
    def _log_summary(self, r: dict) -> None:
        self.logger.info("─" * 50)
        self.logger.info("Preprocessing summary:")
        self.logger.info(f"  Full dataset      : {r['X'].shape[0]:,} rows × {r['X'].shape[1]} features")
        self.logger.info(f"  Train set         : {r['X_train'].shape[0]:,}  |  Fraud: {r['y_train'].sum()}")
        self.logger.info(f"  Test  set         : {r['X_test'].shape[0]:,}   |  Fraud: {r['y_test'].sum()}")
        self.logger.info(f"  After SMOTE train : {r['X_train_sm'].shape[0]:,}  |  Fraud: {r['y_train_sm'].sum()}")
        self.logger.info(f"  Sample (unsup.)   : {r['X_sample'].shape[0]:,}   |  Fraud: {r['y_sample'].sum()}")
        self.logger.info(f"  Outlier fraction  : {r['outlier_fraction']:.5f}")
        self.logger.info("─" * 50)

    # ─────────────────────────────────────────────────────────────────────────
    def transform_new(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply the fitted scaler to new transaction data for inference.
        Expected columns: all original feature columns including Amount & Time.
        """
        df = df.copy()
        if "Amount" in df.columns:
            df["scaled_Amount"] = self.scaler.transform(df[["Amount"]])
            df.drop("Amount", axis=1, inplace=True)
        if "Time" in df.columns:
            df["scaled_Time"] = self.scaler.transform(df[["Time"]])
            df.drop("Time", axis=1, inplace=True)
        if "Class" in df.columns:
            df.drop("Class", axis=1, inplace=True)
        return df
