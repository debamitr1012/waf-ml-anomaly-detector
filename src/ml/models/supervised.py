"""
Supervised learning model using XGBoost for known attack pattern detection.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any
import joblib
from pathlib import Path
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

from utils.logger import get_logger

logger = get_logger(__name__)


class SupervisedModel:
    """
    Supervised XGBoost classifier for detecting known attack patterns.
    Trained on labeled data with known attack types.
    """
    
    def __init__(self):
        self.model = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            objective='binary:logistic',
            eval_metric='auc',
            random_state=42,
            n_jobs=-1,
            tree_method='hist'
        )
        
        self.feature_names = []
        self.is_trained = False
    
    async def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        feature_names: list,
        validation_split: float = 0.2,
        tune_hyperparameters: bool = True
    ) -> Dict[str, Any]:
        """
        Train the supervised model.
        
        Args:
            X_train: Training features
            y_train: Training labels (0=normal, 1=anomaly)
            feature_names: Names of features
            validation_split: Fraction of data for validation
            tune_hyperparameters: Whether to perform hyperparameter tuning
        
        Returns:
            Training metrics
        """
        logger.info("Training supervised XGBoost model...")
        
        # Split data
        X_tr, X_val, y_tr, y_val = train_test_split(
            X_train, y_train,
            test_size=validation_split,
            random_state=42,
            stratify=y_train
        )
        
        # Hyperparameter tuning
        if tune_hyperparameters:
            logger.info("Performing hyperparameter tuning...")
            param_grid = {
                'max_depth': [4, 6, 8],
                'learning_rate': [0.01, 0.1, 0.2],
                'n_estimators': [100, 200, 300],
                'min_child_weight': [1, 3, 5]
            }
            
            grid_search = GridSearchCV(
                self.model,
                param_grid,
                cv=3,
                scoring='roc_auc',
                n_jobs=-1,
                verbose=1
            )
            
            grid_search.fit(X_tr, y_tr)
            self.model = grid_search.best_estimator_
            logger.info(f"Best parameters: {grid_search.best_params_}")
        else:
            # Standard training
            self.model.fit(
                X_tr, y_tr,
                eval_set=[(X_val, y_val)],
                early_stopping_rounds=10,
                verbose=False
            )
        
        # Store feature names
        self.feature_names = feature_names
        self.is_trained = True
        
        # Evaluate
        metrics = self._evaluate(X_val, y_val)
        
        logger.info(f"Supervised model training complete. AUC: {metrics['auc']:.4f}")
        
        return metrics
    
    async def predict(self, features: np.ndarray) -> float:
        """
        Predict anomaly probability for given features.
        
        Args:
            features: Input feature vector
        
        Returns:
            Anomaly probability (0-1)
        """
        if not self.is_trained:
            logger.warning("Model not trained, returning default score")
            return 0.5
        
        try:
            # Ensure 2D array
            if features.ndim == 1:
                features = features.reshape(1, -1)
            
            # Get probability of anomaly class
            proba = self.model.predict_proba(features)[0, 1]
            
            return float(proba)
            
        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            return 0.5
    
    async def predict_batch(self, features: np.ndarray) -> np.ndarray:
        """Predict for multiple samples."""
        if not self.is_trained:
            return np.full(len(features), 0.5)
        
        try:
            probas = self.model.predict_proba(features)[:, 1]
            return probas
        except Exception as e:
            logger.error(f"Batch prediction error: {e}", exc_info=True)
            return np.full(len(features), 0.5)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if not self.is_trained:
            return {}
        
        importance = self.model.feature_importances_
        return dict(zip(self.feature_names, importance))
    
    def _evaluate(self, X_val: np.ndarray, y_val: np.ndarray) -> Dict[str, Any]:
        """Evaluate model performance."""
        y_pred = self.model.predict(X_val)
        y_proba = self.model.predict_proba(X_val)[:, 1]
        
        # Calculate metrics
        auc = roc_auc_score(y_val, y_proba)
        cm = confusion_matrix(y_val, y_pred)
        report = classification_report(y_val, y_pred, output_dict=True)
        
        metrics = {
            'auc': float(auc),
            'accuracy': float(report['accuracy']),
            'precision': float(report['1']['precision']),
            'recall': float(report['1']['recall']),
            'f1_score': float(report['1']['f1-score']),
            'confusion_matrix': cm.tolist()
        }
        
        return metrics
    
    async def save(self, path: Path):
        """Save model to disk."""
        if not self.is_trained:
            logger.warning("Cannot save untrained model")
            return
        
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }
        
        joblib.dump(model_data, path)
        logger.info(f"Supervised model saved to {path}")
    
    async def load(self, path: Path):
        """Load model from disk."""
        model_data = joblib.load(path)
        
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.is_trained = model_data['is_trained']
        
        logger.info(f"Supervised model loaded from {path}")
