"""
Semi-supervised learning model using sklearn's manifold learning for behavioral analysis.
"""

import numpy as np
from typing import Optional, Dict, Any, Tuple
import joblib
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SemiSupervisedModel:
    """
    Manifold-based semi-supervised model for behavioral anomaly detection.
    Uses dimensionality reduction and reconstruction error for anomaly detection.
    """
    
    def __init__(self, input_dim: Optional[int] = None):
        self.input_dim = input_dim
        self.pca_model: Optional[PCA] = None
        self.scaler: Optional[StandardScaler] = None
        self.threshold = 0.0
        self.feature_names = []
        self.is_trained = False
        
        # Reconstruction error statistics
        self.error_mean = 0.0
        self.error_std = 1.0
        self.n_components = 0
    
    def _build_model(self) -> None:
        """
        Build PCA-based dimensionality reduction model.
        """
        # Initialize scaler and PCA
        self.scaler = StandardScaler()
        # Use reasonable number of components
        self.n_components = min(32, int(0.95 * self.input_dim)) if self.input_dim else 32
        self.pca_model = PCA(n_components=self.n_components, random_state=42)
    
    async def train(
        self,
        X_train: np.ndarray,
        feature_names: list,
        X_val: Optional[np.ndarray] = None,
        epochs: int = 100,
        batch_size: int = 256
    ) -> Dict[str, Any]:
        """
        Train the manifold-based semi-supervised model on normal traffic.
        
        Args:
            X_train: Training features (normal traffic)
            feature_names: Names of features
            X_val: Validation features (optional)
            epochs: Ignored (for API compatibility)
            batch_size: Ignored (for API compatibility)
        
        Returns:
            Training history
        """
        logger.info("Training semi-supervised manifold model...")
        
        # Build model
        self.input_dim = X_train.shape[1]
        self._build_model()
        self.feature_names = feature_names
        
        logger.info(f"Feature dimension: {self.input_dim}")
        logger.info(f"PCA components: {self.n_components}")
        
        # Fit scaler and PCA on training data
        X_scaled = self.scaler.fit_transform(X_train)
        self.pca_model.fit(X_scaled)
        
        # Calculate reconstruction errors on training data (normal traffic)
        X_projected = self.pca_model.transform(X_scaled)
        X_reconstructed = self.pca_model.inverse_transform(X_projected)
        reconstruction_errors = np.mean(np.square(X_scaled - X_reconstructed), axis=1)
        
        # Set threshold (e.g., 95th percentile)
        self.threshold = np.percentile(reconstruction_errors, 95)
        self.error_mean = np.mean(reconstruction_errors)
        self.error_std = np.std(reconstruction_errors)
        
        self.is_trained = True
        
        metrics = {
            'reconstruction_error_mean': float(self.error_mean),
            'reconstruction_error_std': float(self.error_std),
            'threshold': float(self.threshold),
            'n_components': self.n_components,
            'mse': float(np.mean(reconstruction_errors))
        }
        
        logger.info(f"Semi-supervised model training complete. Threshold: {self.threshold:.4f}")
        
        return metrics
    
    async def predict(self, features: np.ndarray) -> float:
        """
        Predict anomaly probability based on reconstruction error.
        
        Args:
            features: Input feature vector
        
        Returns:
            Anomaly probability (0-1)
        """
        if not self.is_trained or self.pca_model is None:
            logger.warning("Model not trained, returning default score")
            return 0.5
        
        try:
            # Ensure 2D array
            if features.ndim == 1:
                features = features.reshape(1, -1)
            
            # Scale and project
            X_scaled = self.scaler.transform(features)
            X_projected = self.pca_model.transform(X_scaled)
            X_reconstructed = self.pca_model.inverse_transform(X_projected)
            
            # Calculate reconstruction error
            error = np.mean(np.square(X_scaled - X_reconstructed))
            
            # Normalize error to probability
            normalized_error = (error - self.error_mean) / (self.error_std + 1e-10)
            
            # Convert to probability using sigmoid
            probability = 1.0 / (1.0 + np.exp(-normalized_error))
            
            return float(probability)
            
        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            return 0.5
    
    async def predict_batch(self, features: np.ndarray) -> np.ndarray:
        """Predict for multiple samples."""
        if not self.is_trained or self.pca_model is None:
            return np.full(len(features), 0.5)
        
        try:
            # Scale and project
            X_scaled = self.scaler.transform(features)
            X_projected = self.pca_model.transform(X_scaled)
            X_reconstructed = self.pca_model.inverse_transform(X_projected)
            
            # Calculate reconstruction errors
            errors = np.mean(np.square(X_scaled - X_reconstructed), axis=1)
            
            # Normalize and convert to probabilities
            normalized_errors = (errors - self.error_mean) / (self.error_std + 1e-10)
            probabilities = 1.0 / (1.0 + np.exp(-normalized_errors))
            
            return probabilities
            
        except Exception as e:
            logger.error(f"Batch prediction error: {e}", exc_info=True)
            return np.full(len(features), 0.5)
    
    def get_reconstruction_error(self, features: np.ndarray) -> float:
        """Get raw reconstruction error for debugging."""
        if not self.is_trained or self.pca_model is None:
            return 0.0
        
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        X_scaled = self.scaler.transform(features)
        X_projected = self.pca_model.transform(X_scaled)
        X_reconstructed = self.pca_model.inverse_transform(X_projected)
        error = np.mean(np.square(X_scaled - X_reconstructed))
        
        return float(error)
    
    async def save(self, path: Path):
        """Save model to disk."""
        if not self.is_trained:
            logger.warning("Cannot save untrained model")
            return
        
        # Save all models together
        models_data = {
            'scaler': self.scaler,
            'pca_model': self.pca_model,
            'input_dim': self.input_dim,
            'n_components': self.n_components,
            'threshold': self.threshold,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained,
            'error_mean': self.error_mean,
            'error_std': self.error_std
        }
        
        joblib.dump(models_data, path)
        logger.info(f"Semi-supervised model saved to {path}")
    
    async def load(self, path: Path):
        """Load model from disk."""
        # Load all models
        models_data = joblib.load(path)
        
        self.scaler = models_data['scaler']
        self.pca_model = models_data['pca_model']
        self.input_dim = models_data['input_dim']
        self.n_components = models_data['n_components']
        self.threshold = models_data['threshold']
        self.feature_names = models_data['feature_names']
        self.is_trained = models_data['is_trained']
        self.error_mean = models_data['error_mean']
        self.error_std = models_data['error_std']
        
        logger.info(f"Semi-supervised model loaded from {path}")
