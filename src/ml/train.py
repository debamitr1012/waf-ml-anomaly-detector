"""
Model training script for initial setup.
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

from ml.models.supervised import SupervisedModel
from ml.models.unsupervised import UnsupervisedModel
from ml.models.semi_supervised import SemiSupervisedModel
from core.preprocessor import TrafficPreprocessor
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def train_models(data_file: str, output_dir: str):
    """
    Train all ML models from a dataset.
    
    Args:
        data_file: Path to training data CSV
        output_dir: Directory to save trained models
    """
    logger.info(f"Loading training data from {data_file}...")
    
    try:
        # Load data
        df = pd.read_csv(data_file)
        logger.info(f"Loaded {len(df)} samples")
        
        # Initialize components
        preprocessor = TrafficPreprocessor()
        
        # Extract features
        logger.info("Extracting features...")
        features_list = []
        labels = []
        
        for idx, row in df.iterrows():
            if idx % 1000 == 0:
                logger.info(f"Processing {idx}/{len(df)}...")
            
            request_data = {
                'source_ip': row.get('source_ip', '0.0.0.0'),
                'method': row.get('method', 'GET'),
                'path': row.get('path', '/'),
                'headers': {},
                'body': row.get('body', ''),
                'timestamp': row.get('timestamp', '')
            }
            
            features = await preprocessor.extract_features(request_data)
            features_list.append(features)
            labels.append(int(row.get('is_anomaly', 0)))
        
        X = np.array(features_list)
        y = np.array(labels)
        feature_names = preprocessor.get_feature_names()
        
        logger.info(f"Features extracted: {X.shape}")
        logger.info(f"Normal samples: {np.sum(y == 0)}")
        logger.info(f"Anomalous samples: {np.sum(y == 1)}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Train supervised model
        logger.info("\n" + "="*50)
        logger.info("Training Supervised Model (XGBoost)")
        logger.info("="*50)
        supervised = SupervisedModel()
        metrics = await supervised.train(
            X_train, y_train,
            feature_names,
            validation_split=0.2,
            tune_hyperparameters=True
        )
        logger.info(f"Supervised model metrics: {metrics}")
        await supervised.save(output_path / "supervised_model.pkl")
        
        # Train unsupervised model (on normal traffic only)
        logger.info("\n" + "="*50)
        logger.info("Training Unsupervised Model (Isolation Forest)")
        logger.info("="*50)
        X_normal = X_train[y_train == 0]
        unsupervised = UnsupervisedModel()
        info = await unsupervised.train(X_normal, feature_names)
        logger.info(f"Unsupervised model info: {info}")
        
        # Evaluate on test set
        eval_metrics = await unsupervised.evaluate(X_test, y_test)
        logger.info(f"Unsupervised evaluation: {eval_metrics}")
        await unsupervised.save(output_path / "unsupervised_model.pkl")
        
        # Train semi-supervised model (AutoEncoder on normal traffic)
        logger.info("\n" + "="*50)
        logger.info("Training Semi-Supervised Model (AutoEncoder)")
        logger.info("="*50)
        X_normal_train, X_normal_val = train_test_split(
            X_normal, test_size=0.2, random_state=42
        )
        semi_supervised = SemiSupervisedModel()
        train_metrics = await semi_supervised.train(
            X_normal_train,
            feature_names,
            X_val=X_normal_val,
            epochs=100,
            batch_size=256
        )
        logger.info(f"Semi-supervised model metrics: {train_metrics}")
        await semi_supervised.save(output_path / "semi_supervised_model.pkl")
        
        logger.info("\n" + "="*50)
        logger.info("Training Complete!")
        logger.info("="*50)
        logger.info(f"Models saved to: {output_path.absolute()}")
        
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise


def main():
    parser = argparse.ArgumentParser(description='Train WAF ML models')
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
    asyncio.run(train_models(args.data, args.output))


if __name__ == '__main__':
    main()
