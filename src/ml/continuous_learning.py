"""
Continuous learning engine for model retraining and improvement.
"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)


class ContinuousLearningEngine:
    """
    Manages continuous learning and model retraining based on feedback.
    """
    
    def __init__(
        self,
        analyzer,
        retrain_interval_hours: int = 24,
        min_samples_for_retrain: int = 1000
    ):
        self.analyzer = analyzer
        self.retrain_interval_hours = retrain_interval_hours
        self.min_samples_for_retrain = min_samples_for_retrain
        
        self.is_running = False
        self.retrain_task = None
        
        # Collect training data from feedback
        self.training_buffer = []
        self.last_retrain = datetime.utcnow()
        
        logger.info("ContinuousLearningEngine initialized")
    
    async def start(self):
        """Start the continuous learning loop."""
        if self.is_running:
            logger.warning("Continuous learning already running")
            return
        
        self.is_running = True
        self.retrain_task = asyncio.create_task(self._retrain_loop())
        logger.info("Continuous learning started")
    
    async def stop(self):
        """Stop the continuous learning loop."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.retrain_task:
            self.retrain_task.cancel()
            try:
                await self.retrain_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Continuous learning stopped")
    
    async def _retrain_loop(self):
        """Main retraining loop."""
        while self.is_running:
            try:
                # Wait for retrain interval
                await asyncio.sleep(self.retrain_interval_hours * 3600)
                
                # Check if we have enough samples
                if len(self.training_buffer) >= self.min_samples_for_retrain:
                    await self._perform_retrain()
                else:
                    logger.info(
                        f"Not enough samples for retraining "
                        f"({len(self.training_buffer)}/{self.min_samples_for_retrain})"
                    )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in retrain loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait before retrying
    
    async def add_training_sample(
        self,
        features: np.ndarray,
        label: int,
        feedback: Dict[str, Any]
    ):
        """
        Add a training sample based on administrator feedback.
        
        Args:
            features: Feature vector
            label: True label (0=normal, 1=anomaly)
            feedback: Feedback metadata
        """
        self.training_buffer.append({
            'features': features,
            'label': label,
            'feedback': feedback,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logger.debug(f"Training sample added. Buffer size: {len(self.training_buffer)}")
    
    async def _perform_retrain(self):
        """Perform model retraining."""
        logger.info("Starting model retraining...")
        
        try:
            # Prepare training data
            X_new = np.array([sample['features'] for sample in self.training_buffer])
            y_new = np.array([sample['label'] for sample in self.training_buffer])
            
            # Save current model as backup
            backup_dir = Path("models/backups")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            await self.analyzer.supervised_model.save(
                backup_dir / f"supervised_backup_{timestamp}.pkl"
            )
            
            # Retrain supervised model (incremental if possible)
            # In practice, you might want to combine with existing training data
            await self.analyzer.supervised_model.train(
                X_new,
                y_new,
                self.analyzer.preprocessor.get_feature_names(),
                validation_split=0.2,
                tune_hyperparameters=False  # Skip for incremental training
            )
            
            # Update unsupervised model with normal traffic only
            X_normal = X_new[y_new == 0]
            if len(X_normal) > 100:
                await self.analyzer.unsupervised_model.train(
                    X_normal,
                    self.analyzer.preprocessor.get_feature_names()
                )
            
            # Update semi-supervised model
            if len(X_normal) > 100:
                await self.analyzer.semi_supervised_model.train(
                    X_normal,
                    self.analyzer.preprocessor.get_feature_names(),
                    epochs=50
                )
            
            # Save updated models
            await self.analyzer.save_models()
            
            # Clear training buffer
            self.training_buffer.clear()
            self.last_retrain = datetime.utcnow()
            
            logger.info("Model retraining completed successfully")
            
        except Exception as e:
            logger.error(f"Model retraining failed: {e}", exc_info=True)
            # Restore from backup if needed
    
    def get_status(self) -> Dict[str, Any]:
        """Get continuous learning status."""
        time_since_retrain = datetime.utcnow() - self.last_retrain
        
        return {
            'is_running': self.is_running,
            'training_buffer_size': len(self.training_buffer),
            'min_samples_required': self.min_samples_for_retrain,
            'last_retrain': self.last_retrain.isoformat(),
            'hours_since_retrain': time_since_retrain.total_seconds() / 3600,
            'next_retrain_in_hours': max(
                0,
                self.retrain_interval_hours - (time_since_retrain.total_seconds() / 3600)
            )
        }
