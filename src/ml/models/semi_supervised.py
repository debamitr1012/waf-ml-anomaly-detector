"""
Semi-supervised learning model using AutoEncoder for behavioral analysis.
"""

import numpy as np
from typing import Optional, Dict, Any, Tuple
import joblib
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

from utils.logger import get_logger

logger = get_logger(__name__)


class SemiSupervisedModel:
    """
    AutoEncoder-based semi-supervised model for behavioral anomaly detection.
    Learns normal traffic patterns and detects deviations.
    """
    
    def __init__(self, input_dim: Optional[int] = None):
        self.input_dim = input_dim
        self.model: Optional[Model] = None
        self.threshold = 0.0
        self.feature_names = []
        self.is_trained = False
        
        # Reconstruction error statistics
        self.error_mean = 0.0
        self.error_std = 1.0
    
    def _build_model(self, input_dim: int) -> Model:
        """
        Build AutoEncoder architecture.
        
        Args:
            input_dim: Number of input features
        
        Returns:
            Compiled Keras model
        """
        # Encoder
        encoder_input = layers.Input(shape=(input_dim,), name='encoder_input')
        
        # Encoding layers with dropout for regularization
        x = layers.Dense(128, activation='relu', name='encoder_layer1')(encoder_input)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        x = layers.Dense(64, activation='relu', name='encoder_layer2')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        # Bottleneck (latent space)
        encoded = layers.Dense(32, activation='relu', name='bottleneck')(x)
        
        # Decoder
        x = layers.Dense(64, activation='relu', name='decoder_layer1')(encoded)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        x = layers.Dense(128, activation='relu', name='decoder_layer2')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.2)(x)
        
        # Output layer
        decoded = layers.Dense(input_dim, activation='sigmoid', name='decoder_output')(x)
        
        # Create model
        autoencoder = Model(encoder_input, decoded, name='autoencoder')
        
        # Compile with appropriate loss and optimizer
        autoencoder.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return autoencoder
    
    async def train(
        self,
        X_train: np.ndarray,
        feature_names: list,
        X_val: Optional[np.ndarray] = None,
        epochs: int = 100,
        batch_size: int = 256
    ) -> Dict[str, Any]:
        """
        Train the AutoEncoder on normal traffic.
        
        Args:
            X_train: Training features (normal traffic)
            feature_names: Names of features
            X_val: Validation features (optional)
            epochs: Number of training epochs
            batch_size: Batch size for training
        
        Returns:
            Training history
        """
        logger.info("Training semi-supervised AutoEncoder model...")
        
        # Build model
        self.input_dim = X_train.shape[1]
        self.model = self._build_model(self.input_dim)
        self.feature_names = feature_names
        
        # Log model architecture
        logger.info(f"Model architecture: {self.model.summary()}")
        
        # Callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_loss' if X_val is not None else 'loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_loss' if X_val is not None else 'loss',
                factor=0.5,
                patience=5,
                verbose=1
            )
        ]
        
        # Train (AutoEncoder tries to reconstruct input)
        validation_data = (X_val, X_val) if X_val is not None else None
        
        history = self.model.fit(
            X_train, X_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=validation_data,
            callbacks=callbacks,
            verbose=1
        )
        
        # Calculate reconstruction errors on training data
        reconstructions = self.model.predict(X_train)
        reconstruction_errors = np.mean(np.square(X_train - reconstructions), axis=1)
        
        # Set threshold (e.g., 95th percentile)
        self.threshold = np.percentile(reconstruction_errors, 95)
        self.error_mean = np.mean(reconstruction_errors)
        self.error_std = np.std(reconstruction_errors)
        
        self.is_trained = True
        
        metrics = {
            'final_loss': float(history.history['loss'][-1]),
            'final_mae': float(history.history['mae'][-1]),
            'threshold': float(self.threshold),
            'error_mean': float(self.error_mean),
            'error_std': float(self.error_std),
            'epochs_trained': len(history.history['loss'])
        }
        
        if X_val is not None:
            metrics['final_val_loss'] = float(history.history['val_loss'][-1])
            metrics['final_val_mae'] = float(history.history['val_mae'][-1])
        
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
        if not self.is_trained:
            logger.warning("Model not trained, returning default score")
            return 0.5
        
        try:
            # Ensure 2D array
            if features.ndim == 1:
                features = features.reshape(1, -1)
            
            # Reconstruct input
            reconstruction = self.model.predict(features, verbose=0)
            
            # Calculate reconstruction error
            error = np.mean(np.square(features - reconstruction))
            
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
        if not self.is_trained:
            return np.full(len(features), 0.5)
        
        try:
            # Reconstruct inputs
            reconstructions = self.model.predict(features, verbose=0)
            
            # Calculate reconstruction errors
            errors = np.mean(np.square(features - reconstructions), axis=1)
            
            # Normalize and convert to probabilities
            normalized_errors = (errors - self.error_mean) / (self.error_std + 1e-10)
            probabilities = 1.0 / (1.0 + np.exp(-normalized_errors))
            
            return probabilities
            
        except Exception as e:
            logger.error(f"Batch prediction error: {e}", exc_info=True)
            return np.full(len(features), 0.5)
    
    def get_reconstruction_error(self, features: np.ndarray) -> float:
        """Get raw reconstruction error for debugging."""
        if not self.is_trained:
            return 0.0
        
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        reconstruction = self.model.predict(features, verbose=0)
        error = np.mean(np.square(features - reconstruction))
        
        return float(error)
    
    async def save(self, path: Path):
        """Save model to disk."""
        if not self.is_trained:
            logger.warning("Cannot save untrained model")
            return
        
        # Save Keras model
        model_path = path.parent / f"{path.stem}_keras.h5"
        self.model.save(model_path)
        
        # Save metadata
        metadata = {
            'input_dim': self.input_dim,
            'threshold': self.threshold,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained,
            'error_mean': self.error_mean,
            'error_std': self.error_std,
            'model_path': str(model_path)
        }
        
        joblib.dump(metadata, path)
        logger.info(f"Semi-supervised model saved to {path}")
    
    async def load(self, path: Path):
        """Load model from disk."""
        # Load metadata
        metadata = joblib.load(path)
        
        self.input_dim = metadata['input_dim']
        self.threshold = metadata['threshold']
        self.feature_names = metadata['feature_names']
        self.is_trained = metadata['is_trained']
        self.error_mean = metadata['error_mean']
        self.error_std = metadata['error_std']
        
        # Load Keras model
        model_path = Path(metadata['model_path'])
        self.model = keras.models.load_model(
            model_path,
            custom_objects={'mse': keras.losses.MeanSquaredError()}
        )
        
        logger.info(f"Semi-supervised model loaded from {path}")
