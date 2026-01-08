"""
Test script to evaluate trained models on test data.
"""

import argparse
import asyncio
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ml.models.supervised import SupervisedModel
from src.ml.models.unsupervised import UnsupervisedModel
from src.ml.models.semi_supervised import SemiSupervisedModel
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


async def test_models(test_file: str, models_dir: str):
    """
    Test all trained models on test data.
    
    Args:
        test_file: Path to test data CSV
        models_dir: Directory containing trained models
    """
    logger.info(f"Loading test data from {test_file}...")
    logger.info("="*60)
    
    try:
        # Load test data
        df = pd.read_csv(test_file)
        logger.info(f"[OK] Loaded {len(df)} test samples")
        
        # Detect dataset format and extract features
        if 'class' in df.columns:
            # KDD Cup 1999 format with labels
            logger.info("Detected KDD Cup 1999 format with labels")
            
            # Convert to binary labels
            df['is_anomaly'] = (df['class'] != 'normal').astype(int)
            y_test = df['is_anomaly'].values
            has_labels = True
            
            # Extract numeric features (EXCLUDE the 'is_anomaly' column we just created)
            feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if 'is_anomaly' in feature_cols:
                feature_cols.remove('is_anomaly')
        else:
            # KDD Cup 1999 format WITHOUT labels (raw test data)
            logger.info("Detected KDD Cup 1999 format WITHOUT labels (unlabeled test data)")
            y_test = None
            has_labels = False
            
            # Extract numeric features
            feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        X_test = df[feature_cols].values
        
        logger.info(f"[OK] Extracted {len(feature_cols)} numeric features")
        logger.info(f"[OK] Feature shape: {X_test.shape}")
        
        if has_labels:
            logger.info(f"[OK] Normal samples: {np.sum(y_test == 0)} ({np.sum(y_test == 0)/len(y_test)*100:.1f}%)")
            logger.info(f"[OK] Anomalous samples: {np.sum(y_test == 1)} ({np.sum(y_test == 1)/len(y_test)*100:.1f}%)")
        
        models_path = Path(models_dir)
        
        # ============================================================
        # TEST SUPERVISED MODEL (XGBoost)
        # ============================================================
        logger.info("\n" + "="*60)
        logger.info("[TEST] Supervised Model (XGBoost)")
        logger.info("="*60)
        
        supervised = SupervisedModel()
        await supervised.load(models_path / "supervised_model.pkl")
        
        y_pred_supervised = await supervised.predict_batch(X_test)
        y_pred_supervised_binary = (y_pred_supervised >= 0.5).astype(int)
        
        logger.info(f"[RESULTS] Supervised Model Predictions:")
        logger.info(f"  - Anomalies detected: {np.sum(y_pred_supervised_binary)}/{len(X_test)} ({np.sum(y_pred_supervised_binary)/len(X_test)*100:.2f}%)")
        logger.info(f"  - Mean anomaly score: {np.mean(y_pred_supervised):.4f}")
        logger.info(f"  - Min/Max scores: {np.min(y_pred_supervised):.4f} / {np.max(y_pred_supervised):.4f}")
        
        if has_labels:
            acc_sup = accuracy_score(y_test, y_pred_supervised_binary)
            prec_sup = precision_score(y_test, y_pred_supervised_binary, zero_division=0)
            rec_sup = recall_score(y_test, y_pred_supervised_binary, zero_division=0)
            f1_sup = f1_score(y_test, y_pred_supervised_binary, zero_division=0)
            auc_sup = roc_auc_score(y_test, y_pred_supervised)
            
            logger.info(f"  - Accuracy:  {acc_sup:.4f}")
            logger.info(f"  - Precision: {prec_sup:.4f}")
            logger.info(f"  - Recall:    {rec_sup:.4f}")
            logger.info(f"  - F1 Score:  {f1_sup:.4f}")
            logger.info(f"  - AUC:       {auc_sup:.4f}")
            
            cm_sup = confusion_matrix(y_test, y_pred_supervised_binary)
            logger.info(f"  - Confusion Matrix:")
            logger.info(f"      Normal:     {cm_sup[0]}")
            logger.info(f"      Anomalous:  {cm_sup[1]}")
        
        # ============================================================
        # TEST UNSUPERVISED MODEL (Isolation Forest)
        # ============================================================
        logger.info("\n" + "="*60)
        logger.info("[TEST] Unsupervised Model (Isolation Forest)")
        logger.info("="*60)
        
        unsupervised = UnsupervisedModel()
        await unsupervised.load(models_path / "unsupervised_model.pkl")
        
        y_pred_unsupervised = await unsupervised.predict_batch(X_test)
        y_pred_unsupervised_binary = (y_pred_unsupervised >= 0.5).astype(int)
        
        logger.info(f"[RESULTS] Unsupervised Model Predictions:")
        logger.info(f"  - Anomalies detected: {np.sum(y_pred_unsupervised_binary)}/{len(X_test)} ({np.sum(y_pred_unsupervised_binary)/len(X_test)*100:.2f}%)")
        logger.info(f"  - Mean anomaly score: {np.mean(y_pred_unsupervised):.4f}")
        logger.info(f"  - Min/Max scores: {np.min(y_pred_unsupervised):.4f} / {np.max(y_pred_unsupervised):.4f}")
        
        if has_labels:
            acc_unsp = accuracy_score(y_test, y_pred_unsupervised_binary)
            prec_unsp = precision_score(y_test, y_pred_unsupervised_binary, zero_division=0)
            rec_unsp = recall_score(y_test, y_pred_unsupervised_binary, zero_division=0)
            f1_unsp = f1_score(y_test, y_pred_unsupervised_binary, zero_division=0)
            auc_unsp = roc_auc_score(y_test, y_pred_unsupervised)
            
            logger.info(f"  - Accuracy:  {acc_unsp:.4f}")
            logger.info(f"  - Precision: {prec_unsp:.4f}")
            logger.info(f"  - Recall:    {rec_unsp:.4f}")
            logger.info(f"  - F1 Score:  {f1_unsp:.4f}")
            logger.info(f"  - AUC:       {auc_unsp:.4f}")
            
            cm_unsp = confusion_matrix(y_test, y_pred_unsupervised_binary)
            logger.info(f"  - Confusion Matrix:")
            logger.info(f"      Normal:     {cm_unsp[0]}")
            logger.info(f"      Anomalous:  {cm_unsp[1]}")
        
        # ============================================================
        # TEST SEMI-SUPERVISED MODEL (PCA-based)
        # ============================================================
        logger.info("\n" + "="*60)
        logger.info("[TEST] Semi-Supervised Model (PCA-based)")
        logger.info("="*60)
        
        semi_supervised = SemiSupervisedModel()
        await semi_supervised.load(models_path / "semi_supervised_model.pkl")
        
        y_pred_semi = await semi_supervised.predict_batch(X_test)
        y_pred_semi_binary = (y_pred_semi >= 0.5).astype(int)
        
        logger.info(f"[RESULTS] Semi-Supervised Model Predictions:")
        logger.info(f"  - Anomalies detected: {np.sum(y_pred_semi_binary)}/{len(X_test)} ({np.sum(y_pred_semi_binary)/len(X_test)*100:.2f}%)")
        logger.info(f"  - Mean anomaly score: {np.mean(y_pred_semi):.4f}")
        logger.info(f"  - Min/Max scores: {np.min(y_pred_semi):.4f} / {np.max(y_pred_semi):.4f}")
        
        if has_labels:
            acc_semi = accuracy_score(y_test, y_pred_semi_binary)
            prec_semi = precision_score(y_test, y_pred_semi_binary, zero_division=0)
            rec_semi = recall_score(y_test, y_pred_semi_binary, zero_division=0)
            f1_semi = f1_score(y_test, y_pred_semi_binary, zero_division=0)
            auc_semi = roc_auc_score(y_test, y_pred_semi)
            
            logger.info(f"  - Accuracy:  {acc_semi:.4f}")
            logger.info(f"  - Precision: {prec_semi:.4f}")
            logger.info(f"  - Recall:    {rec_semi:.4f}")
            logger.info(f"  - F1 Score:  {f1_semi:.4f}")
            logger.info(f"  - AUC:       {auc_semi:.4f}")
            
            cm_semi = confusion_matrix(y_test, y_pred_semi_binary)
            logger.info(f"  - Confusion Matrix:")
            logger.info(f"      Normal:     {cm_semi[0]}")
            logger.info(f"      Anomalous:  {cm_semi[1]}")
        
        # ============================================================
        # ENSEMBLE PREDICTIONS (majority voting)
        # ============================================================
        logger.info("\n" + "="*60)
        logger.info("[TEST] Ensemble Model (Majority Voting)")
        logger.info("="*60)
        
        # Ensemble: majority vote from all three models
        ensemble_votes = y_pred_supervised_binary + y_pred_unsupervised_binary + y_pred_semi_binary
        y_pred_ensemble = (ensemble_votes >= 2).astype(int)
        ensemble_score = ensemble_votes / 3.0
        
        logger.info(f"[RESULTS] Ensemble Model Predictions:")
        logger.info(f"  - Anomalies detected: {np.sum(y_pred_ensemble)}/{len(X_test)} ({np.sum(y_pred_ensemble)/len(X_test)*100:.2f}%)")
        logger.info(f"  - Mean anomaly score: {np.mean(ensemble_score):.4f}")
        logger.info(f"  - Min/Max scores: {np.min(ensemble_score):.4f} / {np.max(ensemble_score):.4f}")
        
        if has_labels:
            acc_ens = accuracy_score(y_test, y_pred_ensemble)
            prec_ens = precision_score(y_test, y_pred_ensemble, zero_division=0)
            rec_ens = recall_score(y_test, y_pred_ensemble, zero_division=0)
            f1_ens = f1_score(y_test, y_pred_ensemble, zero_division=0)
            auc_ens = roc_auc_score(y_test, ensemble_score)
            
            logger.info(f"  - Accuracy:  {acc_ens:.4f}")
            logger.info(f"  - Precision: {prec_ens:.4f}")
            logger.info(f"  - Recall:    {rec_ens:.4f}")
            logger.info(f"  - F1 Score:  {f1_ens:.4f}")
            logger.info(f"  - AUC:       {auc_ens:.4f}")
            
            cm_ens = confusion_matrix(y_test, y_pred_ensemble)
            logger.info(f"  - Confusion Matrix:")
            logger.info(f"      Normal:     {cm_ens[0]}")
            logger.info(f"      Anomalous:  {cm_ens[1]}")
            
            # ============================================================
            # SUMMARY COMPARISON
            # ============================================================
            logger.info("\n" + "="*60)
            logger.info("[SUMMARY] Model Comparison")
            logger.info("="*60)
            
            results = {
                'Supervised (XGBoost)': {'Accuracy': acc_sup, 'AUC': auc_sup, 'F1': f1_sup},
                'Unsupervised (IsoForest)': {'Accuracy': acc_unsp, 'AUC': auc_unsp, 'F1': f1_unsp},
                'Semi-Supervised (PCA)': {'Accuracy': acc_semi, 'AUC': auc_semi, 'F1': f1_semi},
                'Ensemble (Voting)': {'Accuracy': acc_ens, 'AUC': auc_ens, 'F1': f1_ens}
            }
            
            logger.info("\nModel Performance Comparison:")
            logger.info(f"{'Model':<30} {'Accuracy':<12} {'AUC':<12} {'F1 Score':<12}")
            logger.info("-" * 66)
            for model_name, metrics in results.items():
                logger.info(f"{model_name:<30} {metrics['Accuracy']:<12.4f} {metrics['AUC']:<12.4f} {metrics['F1']:<12.4f}")
            
            # Find best model
            best_model = max(results.items(), key=lambda x: x[1]['F1'])
            logger.info(f"\n[BEST] Model: {best_model[0]} with F1 Score: {best_model[1]['F1']:.4f}")
        
        logger.info("\n" + "="*60)
        logger.info("[COMPLETE] Testing Complete!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"[ERROR] Testing failed: {e}", exc_info=True)
        raise


def main():
    parser = argparse.ArgumentParser(description='Test trained WAF ML models')
    parser.add_argument(
        '--data',
        required=True,
        help='Path to test data CSV file'
    )
    parser.add_argument(
        '--models',
        default='models',
        help='Directory containing trained models'
    )
    
    args = parser.parse_args()
    
    # Run testing
    asyncio.run(test_models(args.data, args.models))


if __name__ == '__main__':
    main()
