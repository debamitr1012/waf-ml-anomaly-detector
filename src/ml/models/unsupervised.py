"""
Unsupervised learning model using Isolation Forest for anomaly detection.
"""

import numpy as np
from typing import Optional, Dict, Any
import joblib
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, roc_auc_score

from utils.logger import get_logger

logger = get_logger(__name__)


class UnsupervisedModel:
    """
    Isolation Forest model for detecting anomalies without labeled data.
    Ideal for discovering novel attack patterns.
    """
    
    def __init__(self):
        self.model = IsolationForest(
            n_estimators=200,
            max_samples='auto',
            contamination=0.1,  # Expected proportion of anomalies
            max_features=1.0,
            bootstrap=False,
            n_jobs=-1,
            random_state=42,
            verbose=0
        )
        
        self.feature_names = []
        self.is_trained = False
        
        # Statistics for score normalization
        self.score_mean = 0.0
        self.score_std = 1.0
    
    async def train(
        self,
        X_train: np.ndarray,
        feature_names: list,
        contamination: float = 0.1
    ) -> Dict[str, Any]:
        """
        Train the unsupervised model on normal traffic.
        
        Args:
            X_train: Training features (mostly normal traffic)
            feature_names: Names of features
            contamination: Expected proportion of anomalies
        
        Returns:
            Training information
        """
        logger.info("Training unsupervised Isolation Forest model...")
        
        # Update contamination parameter
        self.model.contamination = contamination
        
        # Fit model
        self.model.fit(X_train)
        
        # Store feature names
        self.feature_names = feature_names
        self.is_trained = True
        
        # Calculate score statistics for normalization
        scores = self.model.score_samples(X_train)
        self.score_mean = np.mean(scores)
        self.score_std = np.std(scores)
        
        # Get training info
        info = {
            'n_samples': len(X_train),
            'n_features': X_train.shape[1],
            'contamination': contamination,
            'score_mean': float(self.score_mean),
            'score_std': float(self.score_std)
        }
        
        logger.info(f"Unsupervised model training complete. Trained on {len(X_train)} samples.")
        
        return info
    
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
            
            # Get anomaly score (more negative = more anomalous)
            score = self.model.score_samples(features)[0]
            
            # Normalize score to probability [0, 1]
            # Lower scores indicate anomalies
            normalized_score = (score - self.score_mean) / (self.score_std + 1e-10)
            
            # Convert to probability (invert so higher = more anomalous)
            probability = 1.0 / (1.0 + np.exp(normalized_score))
            
            return float(probability)
            
        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            return 0.5
    
    async def predict_batch(self, features: np.ndarray) -> np.ndarray:
        """Predict for multiple samples."""
        if not self.is_trained:
            return np.full(len(features), 0.5)
        
        try:
            scores = self.model.score_samples(features)
            
            # Normalize and convert to probabilities
            normalized_scores = (scores - self.score_mean) / (self.score_std + 1e-10)
            probabilities = 1.0 / (1.0 + np.exp(normalized_scores))
            
            return probabilities
            
        except Exception as e:
            logger.error(f"Batch prediction error: {e}", exc_info=True)
            return np.full(len(features), 0.5)
    
    def get_anomaly_threshold(self, percentile: float = 95) -> float:
        """
        Get the anomaly score threshold at given percentile.
        
        Args:
            percentile: Percentile for threshold (e.g., 95 means top 5% are anomalies)
        
        Returns:
            Score threshold
        """
        if not self.is_trained:
            return 0.0
        
        # This would require storing training scores
        # For now, use a heuristic based on contamination
        return float(self.model.contamination)
    
    async def evaluate(
        self,
        X_test: np.ndarray,
        y_test: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Evaluate model performance if labels are available.
        
        Args:
            X_test: Test features
            y_test: Test labels (optional)
        
        Returns:
            Evaluation metrics
        """
        if not self.is_trained:
            return {}
        
        # Get predictions
        predictions = self.model.predict(X_test)  # -1 for anomaly, 1 for normal
        scores = self.model.score_samples(X_test)
        
        metrics = {
            'n_samples': len(X_test),
            'n_anomalies_detected': int(np.sum(predictions == -1)),
            'anomaly_rate': float(np.mean(predictions == -1)),
            'score_mean': float(np.mean(scores)),
            'score_std': float(np.std(scores))
        }
        
        # If labels provided, calculate additional metrics
        if y_test is not None:
            # Convert predictions: -1 -> 1 (anomaly), 1 -> 0 (normal)
            y_pred = (predictions == -1).astype(int)
            
            # Convert scores to probabilities for AUC
            probabilities = await self.predict_batch(X_test)
            
            try:
                auc = roc_auc_score(y_test, probabilities)
                report = classification_report(y_test, y_pred, output_dict=True)
                
                metrics.update({
                    'auc': float(auc),
                    'accuracy': float(report['accuracy']),
                    'precision': float(report['1']['precision']),
                    'recall': float(report['1']['recall']),
                    'f1_score': float(report['1']['f1-score'])
                })
            except Exception as e:
                logger.warning(f"Could not calculate supervised metrics: {e}")
        
        return metrics
    
    async def save(self, path: Path):
        """Save model to disk."""
        if not self.is_trained:
            logger.warning("Cannot save untrained model")
            return
        
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained,
            'score_mean': self.score_mean,
            'score_std': self.score_std
        }
        
        joblib.dump(model_data, path)
        logger.info(f"Unsupervised model saved to {path}")
    
    async def load(self, path: Path):
        """Load model from disk."""
        model_data = joblib.load(path)
        
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.is_trained = model_data['is_trained']
        self.score_mean = model_data['score_mean']
        self.score_std = model_data['score_std']
        
        logger.info(f"Unsupervised model loaded from {path}")
