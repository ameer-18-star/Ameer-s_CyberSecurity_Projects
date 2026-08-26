"""
============================================================
 Credit Card Fraud Detection — Main Entry Point
 Purpose: Educational — Simulated Environment Only
============================================================

Usage:
    python main.py                    # Full pipeline (all steps)
    python main.py --mode eda         # Exploratory data analysis only
    python main.py --mode train       # Train models only
    python main.py --mode evaluate    # Evaluate models only
    python main.py --mode alert       # Run SOC alert simulator only
    python main.py --mode predict --input transaction.csv   # Score new transactions
    python main.py --synthetic        # Force synthetic demo data
"""

import argparse
import sys
import time
from datetime import datetime

from utils.data_loader import DataLoader
from utils.preprocessor import Preprocessor
from utils.visualizer import Visualizer
from utils.alert_system import AlertSystem
from utils.logger import setup_logger
from models.unsupervised import UnsupervisedModels
from models.supervised import SupervisedModels
from models.evaluator import ModelEvaluator

# ─────────────────────────────────────────────────────────────────────────────
BANNER = r"""
  ╔══════════════════════════════════════════════════════════════╗
  ║   🛡️  CREDIT CARD FRAUD DETECTION SYSTEM  🛡️                ║
  ╚══════════════════════════════════════════════════════════════╝
"""
# ─────────────────────────────────────────────────────────────────────────────


def parse_args():
    parser = argparse.ArgumentParser(
        description="Credit Card Fraud Detection — ML Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--mode",
        choices=["full", "eda", "train", "evaluate", "alert", "predict"],
        default="full",
        help="Pipeline mode to run (default: full)"
    )
    parser.add_argument(
        "--data",
        type=str,
        default="creditcard.csv",
        help="Path to the creditcard.csv dataset (default: creditcard.csv)"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="CSV of new transactions to score (used with --mode predict)"
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Force generation of synthetic demo data (ignores --data)"
    )
    parser.add_argument(
        "--sample",
        type=float,
        default=0.1,
        help="Fraction of data for unsupervised models (default: 0.1)"
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip saving plots (faster; useful for CI/headless environments)"
    )
    return parser.parse_args()


def run_pipeline(args, logger):
    """Execute the full fraud detection pipeline based on selected mode."""

    start_total = time.time()
    logger.info(f"Pipeline started  | mode={args.mode} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ── 1. Load Data ──────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STEP 1: DATA LOADING")
    loader = DataLoader(
        csv_path=args.data,
        force_synthetic=args.synthetic,
        logger=logger
    )
    data = loader.load()

    if args.mode == "eda":
        logger.info("=" * 60)
        logger.info("STEP 2: EXPLORATORY DATA ANALYSIS")
        viz = Visualizer(data, save_plots=not args.no_plots, logger=logger)
        viz.run_full_eda()
        logger.info("EDA complete. Plots saved to outputs/")
        return

    # ── 2. Preprocess ─────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STEP 2: PREPROCESSING")
    preprocessor = Preprocessor(data, sample_fraction=args.sample, logger=logger)
    prep_result = preprocessor.run()

    if not args.no_plots:
        viz = Visualizer(data, save_plots=True, logger=logger)
        viz.run_full_eda()

    if args.mode in ("full", "train", "evaluate", "alert"):

        # ── 3. Unsupervised Models ─────────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 3: UNSUPERVISED ANOMALY DETECTION")
        unsup = UnsupervisedModels(prep_result, logger=logger)
        unsup_results = unsup.run()

        # ── 4. Supervised Models ───────────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 4: SUPERVISED CLASSIFICATION (with SMOTE)")
        sup = SupervisedModels(prep_result, logger=logger)
        sup_results = sup.run()

        if args.mode == "train":
            logger.info("Training complete. Exiting (--mode train).")
            return

        # ── 5. Evaluation ──────────────────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 5: MODEL EVALUATION & COMPARISON")
        evaluator = ModelEvaluator(
            unsup_results=unsup_results,
            sup_results=sup_results,
            y_test=prep_result["y_test"],
            y_sample=prep_result["y_sample"],
            save_plots=not args.no_plots,
            logger=logger
        )
        evaluator.run()

        if args.mode == "evaluate":
            return

        # ── 6. SOC Alert Simulation ────────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 6: SOC ALERT TRIAGE SIMULATION")
        alert = AlertSystem(
            sup_results=sup_results,
            X_test=prep_result["X_test"],
            y_test=prep_result["y_test"],
            logger=logger
        )
        alert.run()

    elif args.mode == "predict":
        if args.input is None:
            logger.error("--mode predict requires --input <path_to_csv>")
            sys.exit(1)
        logger.info("=" * 60)
        logger.info(f"PREDICT MODE: scoring {args.input}")

        # Train a quick model then predict
        sup = SupervisedModels(prep_result, logger=logger)
        sup_results = sup.run()

        alert = AlertSystem(
            sup_results=sup_results,
            X_test=prep_result["X_test"],
            y_test=prep_result["y_test"],
            logger=logger
        )
        alert.score_new_file(args.input, preprocessor)

    elapsed = time.time() - start_total
    logger.info("=" * 60)
    logger.info(f"✅ Pipeline finished in {elapsed:.1f}s")
    logger.info(f"   Output files saved to: outputs/")


def main():
    print(BANNER)
    args = parse_args()
    logger = setup_logger()
    try:
        run_pipeline(args, logger)
    except KeyboardInterrupt:
        print("\n[Interrupted by user]")
        sys.exit(0)
    except Exception as exc:
        import traceback
        print(f"\n[ERROR] {exc}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
