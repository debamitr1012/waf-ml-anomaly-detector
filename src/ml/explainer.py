"""
Explainable AI module using SHAP and LIME for model interpretation.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
import shap

from utils.logger import get_logger

logger = get_logger(__name__)


class ExplainableAI:
    """
    Provides explanations for ML model predictions using SHAP and LIME.
    """
    
    def __init__(self):
        self.shap_explainer = None
        self.background_data = None
    
    def initialize_explainer(self, model, background_data: np.ndarray):
        """
        Initialize SHAP explainer with background data.
        
        Args:
            model: Trained ML model
            background_data: Sample of normal traffic for baseline
        """
        try:
            # Use TreeExplainer for tree-based models (XGBoost)
            self.shap_explainer = shap.TreeExplainer(model.model)
            self.background_data = background_data
            logger.info("SHAP explainer initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize SHAP explainer: {e}")
    
    async def explain_prediction(
        self,
        features: np.ndarray,
        model_predictions: List[float],
        model: Any,
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate explanation for a prediction.
        
        Args:
            features: Input feature vector
            model_predictions: Predictions from all models
            model: Primary model for explanation
            feature_names: Names of features
        
        Returns:
            Explanation dictionary
        """
        try:
            explanation = {
                'method': 'shap',
                'feature_importance': {},
                'top_contributing_features': [],
                'attack_indicators': [],
                'confidence': 0.0
            }
            
            # Ensure 2D array
            if features.ndim == 1:
                features = features.reshape(1, -1)
            
            # Get SHAP values if explainer is available
            if self.shap_explainer:
                shap_values = self.shap_explainer.shap_values(features)
                
                # Handle different output formats
                if isinstance(shap_values, list):
                    shap_values = shap_values[1]  # Get positive class for binary classification
                
                # Get feature importance
                if feature_names:
                    importance = dict(zip(feature_names, shap_values[0]))
                    # Sort by absolute importance
                    sorted_importance = sorted(
                        importance.items(),
                        key=lambda x: abs(x[1]),
                        reverse=True
                    )
                    
                    explanation['feature_importance'] = {
                        k: float(v) for k, v in sorted_importance[:10]
                    }
                    
                    # Get top contributing features
                    explanation['top_contributing_features'] = [
                        {
                            'feature': k,
                            'impact': float(v),
                            'direction': 'increases' if v > 0 else 'decreases'
                        }
                        for k, v in sorted_importance[:5]
                    ]
            
            # Generate human-readable attack indicators
            explanation['attack_indicators'] = self._generate_attack_indicators(
                features[0],
                feature_names
            )
            
            # Calculate confidence based on model agreement
            explanation['confidence'] = self._calculate_explanation_confidence(
                model_predictions
            )
            
            # Add summary
            explanation['summary'] = self._generate_summary(explanation)
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}", exc_info=True)
            return {
                'method': 'fallback',
                'summary': 'Anomaly detected based on statistical deviation from normal traffic patterns.',
                'confidence': 0.5
            }
    
    def _generate_attack_indicators(
        self,
        features: np.ndarray,
        feature_names: Optional[List[str]]
    ) -> List[str]:
        """Generate human-readable attack indicators."""
        indicators = []
        
        if not feature_names:
            return indicators
        
        # Create feature dict
        feature_dict = dict(zip(feature_names, features))
        
        # Check for specific attack patterns
        if feature_dict.get('has_pattern_sql', 0) > 0.5:
            count = int(feature_dict.get('pattern_sql_count', 0))
            indicators.append(f"SQL injection patterns detected ({count} instances)")
        
        if feature_dict.get('has_pattern_xss', 0) > 0.5:
            count = int(feature_dict.get('pattern_xss_count', 0))
            indicators.append(f"Cross-site scripting (XSS) patterns detected ({count} instances)")
        
        if feature_dict.get('has_pattern_lfi', 0) > 0.5:
            count = int(feature_dict.get('pattern_lfi_count', 0))
            indicators.append(f"Local file inclusion (LFI) patterns detected ({count} instances)")
        
        if feature_dict.get('has_pattern_cmd', 0) > 0.5:
            count = int(feature_dict.get('pattern_cmd_count', 0))
            indicators.append(f"Command injection patterns detected ({count} instances)")
        
        # Check for suspicious characteristics
        url_length = feature_dict.get('url_length', 0)
        if url_length > 500:
            indicators.append(f"Unusually long URL ({int(url_length)} characters)")
        
        entropy = feature_dict.get('entropy', 0)
        if entropy > 4.5:
            indicators.append(f"High entropy in URL (possible obfuscation: {entropy:.2f})")
        
        if feature_dict.get('is_bot_user_agent', 0) > 0.5:
            indicators.append("Suspicious user agent (possible bot)")
        
        num_special_chars = feature_dict.get('num_special_chars', 0)
        if num_special_chars > 10:
            indicators.append(f"Excessive special characters ({int(num_special_chars)})")
        
        # Temporal anomalies
        hour = feature_dict.get('hour_of_day', 12)
        if hour < 2 or hour > 22:
            indicators.append(f"Unusual access time ({int(hour):02d}:00)")
        
        return indicators
    
    def _calculate_explanation_confidence(self, model_predictions: List[float]) -> float:
        """Calculate confidence in the explanation."""
        # High agreement between models = high confidence
        variance = np.var(model_predictions)
        confidence = 1.0 / (1.0 + variance * 10)
        return float(confidence)
    
    def _generate_summary(self, explanation: Dict[str, Any]) -> str:
        """Generate human-readable summary."""
        indicators = explanation.get('attack_indicators', [])
        confidence = explanation.get('confidence', 0.5)
        
        if not indicators:
            return (
                "Anomalous traffic detected. The request deviates from normal patterns "
                "but does not match known attack signatures. Manual review recommended."
            )
        
        summary_parts = [
            f"This request exhibits characteristics of a potential attack with "
            f"{confidence*100:.0f}% confidence."
        ]
        
        if indicators:
            summary_parts.append("Key findings:")
            for indicator in indicators[:3]:  # Top 3
                summary_parts.append(f"  • {indicator}")
        
        return "\n".join(summary_parts)
    
    def explain_batch(
        self,
        features: np.ndarray,
        model: Any,
        feature_names: List[str]
    ) -> np.ndarray:
        """
        Get SHAP values for a batch of predictions.
        
        Args:
            features: Batch of feature vectors
            model: Trained model
            feature_names: Feature names
        
        Returns:
            SHAP values array
        """
        if not self.shap_explainer:
            self.initialize_explainer(model, features[:100])
        
        try:
            shap_values = self.shap_explainer.shap_values(features)
            
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
            
            return shap_values
            
        except Exception as e:
            logger.error(f"Error in batch explanation: {e}", exc_info=True)
            return np.zeros_like(features)
    
    def get_feature_impact_summary(
        self,
        shap_values: np.ndarray,
        feature_names: List[str],
        top_n: int = 10
    ) -> pd.DataFrame:
        """
        Get summary of feature impacts across multiple predictions.
        
        Args:
            shap_values: SHAP values array
            feature_names: Feature names
            top_n: Number of top features to return
        
        Returns:
            DataFrame with feature impact statistics
        """
        # Calculate mean absolute SHAP values
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        
        # Create summary DataFrame
        summary = pd.DataFrame({
            'feature': feature_names,
            'mean_impact': mean_abs_shap
        })
        
        summary = summary.sort_values('mean_impact', ascending=False).head(top_n)
        
        return summary
