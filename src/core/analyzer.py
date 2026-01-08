"""
Core anomaly analyzer that orchestrates multiple ML models for threat detection.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
from pathlib import Path
import joblib

from src.ml.models.supervised import SupervisedModel
from src.ml.models.unsupervised import UnsupervisedModel
from src.ml.models.semi_supervised import SemiSupervisedModel
from src.ml.explainer import ExplainableAI
from src.core.preprocessor import TrafficPreprocessor
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AnomalyAnalyzer:
    """
    Main anomaly detection engine that combines multiple ML approaches.
    """
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        # Initialize models
        self.supervised_model = SupervisedModel()
        self.unsupervised_model = UnsupervisedModel()
        self.semi_supervised_model = SemiSupervisedModel()
        
        # Initialize components
        self.preprocessor = TrafficPreprocessor()
        self.explainer = ExplainableAI()
        
        # Ensemble weights (can be tuned based on validation)
        self.weights = {
            'supervised': 0.4,
            'unsupervised': 0.3,
            'semi_supervised': 0.3
        }
        
        # Performance tracking
        self.stats = {
            'total_analyzed': 0,
            'anomalies_detected': 0,
            'avg_latency_ms': 0
        }
    
    async def load_models(self):
        """Load trained models from disk."""
        try:
            logger.info("Loading ML models...")
            
            # Load each model
            await asyncio.gather(
                self.supervised_model.load(self.model_dir / "supervised_model.pkl"),
                self.unsupervised_model.load(self.model_dir / "unsupervised_model.pkl"),
                self.semi_supervised_model.load(self.model_dir / "semi_supervised_model.pkl")
            )
            
            logger.info("Models loaded successfully!")
            
        except FileNotFoundError:
            logger.warning("No pre-trained models found. Please train models first.")
        except Exception as e:
            logger.error(f"Error loading models: {e}", exc_info=True)
            raise
    
    async def save_models(self):
        """Save current models to disk."""
        try:
            logger.info("Saving ML models...")
            
            await asyncio.gather(
                self.supervised_model.save(self.model_dir / "supervised_model.pkl"),
                self.unsupervised_model.save(self.model_dir / "unsupervised_model.pkl"),
                self.semi_supervised_model.save(self.model_dir / "semi_supervised_model.pkl")
            )
            
            logger.info("Models saved successfully!")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}", exc_info=True)
    
    async def analyze_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single HTTP request for anomalies.
        
        Args:
            request_data: Dictionary containing request details
                {
                    'source_ip': str,
                    'method': str,
                    'path': str,
                    'headers': dict,
                    'body': str,
                    'timestamp': str
                }
        
        Returns:
            Analysis result with anomaly score and explanation
        """
        start_time = time.time()
        
        try:
            # Preprocess request
            features = await self.preprocessor.extract_features(request_data)
            
            # Get predictions from all models
            predictions = await asyncio.gather(
                self.supervised_model.predict(features),
                self.unsupervised_model.predict(features),
                self.semi_supervised_model.predict(features)
            )
            
            # Calculate ensemble score
            anomaly_score = self._calculate_ensemble_score(predictions)
            
            # Determine if anomalous
            is_anomaly = anomaly_score > 0.5
            
            # Get explanation if anomalous
            explanation = None
            if is_anomaly:
                explanation = await self.explainer.explain_prediction(
                    features,
                    predictions,
                    self.supervised_model
                )
            
            # Generate recommended action
            recommended_action = self._get_recommended_action(
                anomaly_score,
                request_data,
                explanation
            )
            
            # Update statistics
            latency_ms = (time.time() - start_time) * 1000
            self._update_stats(latency_ms, is_anomaly)
            
            result = {
                'is_anomaly': is_anomaly,
                'anomaly_score': float(anomaly_score),
                'confidence': self._calculate_confidence(predictions),
                'threat_level': self._get_threat_level(anomaly_score),
                'explanation': explanation,
                'recommended_action': recommended_action,
                'latency_ms': latency_ms,
                'timestamp': datetime.utcnow().isoformat(),
                'model_predictions': {
                    'supervised': float(predictions[0]),
                    'unsupervised': float(predictions[1]),
                    'semi_supervised': float(predictions[2])
                }
            }
            
            logger.debug(f"Request analyzed: anomaly={is_anomaly}, score={anomaly_score:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing request: {e}", exc_info=True)
            raise
    
    async def batch_analyze(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple requests in batch for improved performance.
        
        Args:
            requests: List of request dictionaries
        
        Returns:
            List of analysis results
        """
        tasks = [self.analyze_request(req) for req in requests]
        return await asyncio.gather(*tasks)
    
    def _calculate_ensemble_score(self, predictions: List[float]) -> float:
        """Calculate weighted ensemble anomaly score."""
        return (
            predictions[0] * self.weights['supervised'] +
            predictions[1] * self.weights['unsupervised'] +
            predictions[2] * self.weights['semi_supervised']
        )
    
    def _calculate_confidence(self, predictions: List[float]) -> float:
        """Calculate confidence based on model agreement."""
        variance = np.var(predictions)
        # Low variance = high agreement = high confidence
        confidence = 1.0 / (1.0 + variance)
        return float(confidence)
    
    def _get_threat_level(self, anomaly_score: float) -> str:
        """Convert anomaly score to threat level."""
        if anomaly_score < 0.3:
            return "low"
        elif anomaly_score < 0.6:
            return "medium"
        elif anomaly_score < 0.8:
            return "high"
        else:
            return "critical"
    
    def _get_recommended_action(
        self,
        anomaly_score: float,
        request_data: Dict[str, Any],
        explanation: Optional[Dict[str, Any]]
    ) -> str:
        """Determine recommended action based on analysis."""
        if anomaly_score < 0.3:
            return "allow"
        elif anomaly_score < 0.6:
            return "log"
        elif anomaly_score < 0.8:
            return "challenge"  # CAPTCHA or rate limit
        else:
            return "block"
    
    def _update_stats(self, latency_ms: float, is_anomaly: bool):
        """Update performance statistics."""
        self.stats['total_analyzed'] += 1
        if is_anomaly:
            self.stats['anomalies_detected'] += 1
        
        # Update rolling average latency
        n = self.stats['total_analyzed']
        current_avg = self.stats['avg_latency_ms']
        self.stats['avg_latency_ms'] = (current_avg * (n - 1) + latency_ms) / n
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current analyzer statistics."""
        return {
            **self.stats,
            'detection_rate': (
                self.stats['anomalies_detected'] / max(self.stats['total_analyzed'], 1)
            ) * 100
        }
