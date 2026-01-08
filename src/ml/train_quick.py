"""
Quick model training script - uses default hyperparameters (no tuning).
"""

import argparse
import asyncio
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ml.models.supervised import SupervisedModel
from src.ml.models.unsupervised import UnsupervisedModel
from src.ml.models.semi_supervised import SemiSupervisedModel
from src.core.preprocessor import TrafficPreprocessor
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


async def train_models_quick(data_file: str, output_dir: str):
    """
    Quick training with default hyperparameters (no tuning).
    
    Args:
        data_file: Path to training data CSV
        output_dir: Directory to save trained models
    """
    logger.info(f"Loading training data from {data_file}...")
    logger.info("="*60)
    
    try:
        # Load data
        df = pd.read_csv(data_file)
        logger.info(f"[OK] Loaded {len(df)} samples")
        
        # Detect dataset format
        if 'class' in df.columns:
            # KDD Cup 1999 format
            logger.info("Detected KDD Cup 1999 format (network intrusion dataset)")
            logger.info(f"Class distribution: {df['class'].value_counts().to_dict()}")
            
            # Convert to binary labels
            df['is_anomaly'] = (df['class'] != 'normal').astype(int)
            
            # Extract numeric features (EXCLUDE the 'is_anomaly' column we just created)
            feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            # Remove 'is_anomaly' from features since it's our target variable
            if 'is_anomaly' in feature_cols:
                feature_cols.remove('is_anomaly')
            
            X = df[feature_cols].values
            y = df['is_anomaly'].values
            feature_names = feature_cols
            
            logger.info(f"[OK] Extracted {len(feature_cols)} numeric features")
        else:
            logger.error("Dataset format not supported (expected KDD format)")
            raise ValueError("Unsupported dataset format")
        
        logger.info(f"[OK] Feature shape: {X.shape}")
        logger.info(f"[OK] Normal samples: {np.sum(y == 0)} ({np.sum(y == 0)/len(y)*100:.1f}%)")
        logger.info(f"[OK] Anomalous samples: {np.sum(y == 1)} ({np.sum(y == 1)/len(y)*100:.1f}%)")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        logger.info(f"[OK] Train/Test split: {len(X_train)}/{len(X_test)}")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"[OK] Output directory: {output_path.absolute()}")
        
        # Train supervised model - WITHOUT hyperparameter tuning
        logger.info("\n" + "="*60)
        logger.info("[TRAIN] Supervised Model (XGBoost) - Quick Mode")
        logger.info("   Purpose: Detect known attack patterns")
        logger.info("="*60)
        supervised = SupervisedModel()
        metrics = await supervised.train(
            X_train, y_train,
            feature_names,
            validation_split=0.2,
            tune_hyperparameters=False  # SKIP tuning for speed
        )
        logger.info(f"[OK] Supervised Model Metrics:")
        for key, value in metrics.items():
            if isinstance(value, (list, tuple)):
                logger.info(f"  - {key}: {value}")
            else:
                try:
                    logger.info(f"  - {key}: {value:.4f}")
                except (TypeError, ValueError):
                    logger.info(f"  - {key}: {value}")
        await supervised.save(output_path / "supervised_model.pkl")
        logger.info(f"[OK] Model saved: {output_path / 'supervised_model.pkl'}")
        
        # Train unsupervised model (on normal traffic only)
        logger.info("\n" + "="*60)
        logger.info("[TRAIN] Unsupervised Model (Isolation Forest)")
        logger.info("   Purpose: Detect unknown anomalies (zero-day attacks)")
        logger.info("="*60)
        X_normal = X_train[y_train == 0]
        logger.info(f"Using {len(X_normal)} normal samples for baseline")
        unsupervised = UnsupervisedModel()
        info = await unsupervised.train(X_normal, feature_names)
        logger.info(f"[OK] Unsupervised Model Info: {info}")
        
        # Evaluate on test set
        eval_metrics = await unsupervised.evaluate(X_test, y_test)
        logger.info(f"[OK] Evaluation Metrics:")
        for key, value in eval_metrics.items():
            if isinstance(value, (list, tuple)):
                logger.info(f"  - {key}: {value}")
            else:
                try:
                    logger.info(f"  - {key}: {value:.4f}")
                except (TypeError, ValueError):
                    logger.info(f"  - {key}: {value}")
        await unsupervised.save(output_path / "unsupervised_model.pkl")
        logger.info(f"[OK] Model saved: {output_path / 'unsupervised_model.pkl'}")
        
        # Train semi-supervised model (PCA-based on normal traffic)
        logger.info("\n" + "="*60)
        logger.info("[TRAIN] Semi-Supervised Model (PCA-based)")
        logger.info("   Purpose: Learn normal behavior patterns")
        logger.info("="*60)
        X_normal_train, X_normal_val = train_test_split(
            X_normal, test_size=0.2, random_state=42
        )
        logger.info(f"Training samples: {len(X_normal_train)}, Validation: {len(X_normal_val)}")
        semi_supervised = SemiSupervisedModel()
        train_metrics = await semi_supervised.train(
            X_normal_train,
            feature_names,
            X_val=X_normal_val,
            epochs=100,
            batch_size=256
        )
        logger.info(f"[OK] Semi-Supervised Model Metrics:")
        for key, value in train_metrics.items():
            if isinstance(value, (list, tuple)):
                logger.info(f"  - {key}: {value}")
            else:
                try:
                    logger.info(f"  - {key}: {value:.4f}")
                except (TypeError, ValueError):
                    logger.info(f"  - {key}: {value}")
        await semi_supervised.save(output_path / "semi_supervised_model.pkl")
        logger.info(f"[OK] Model saved: {output_path / 'semi_supervised_model.pkl'}")
        
        logger.info("\n" + "="*60)
        logger.info("[COMPLETE] Training Complete!")
        logger.info("="*60)
        logger.info(f"[PATH] All models saved to: {output_path.absolute()}")
        logger.info(f"\nNext steps:")
        logger.info(f"  1. Start API: python src/main.py")
        logger.info(f"  2. Access dashboard: http://localhost:3000")
        logger.info(f"  3. Monitor anomalies in real-time")
        
    except Exception as e:
        logger.error(f"[ERROR] Training failed: {e}", exc_info=True)
        raise


def main():
    parser = argparse.ArgumentParser(description='Quick train WAF ML models (no hyperparameter tuning)')
    parser.add_argument(
        '--data',
        required=True,
        help='Path to training data CSV file'
    )
    parser.add_argument(
        '--output',
        default='models',
        help='Output directory for trained models'
    )
    
    args = parser.parse_args()
    
    # Run training
    asyncio.run(train_models_quick(args.data, args.output))


if __name__ == '__main__':
    main()
