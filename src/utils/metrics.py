"""
Metrics collection and monitoring utilities.
"""

import time
from typing import Dict, Any, List
from collections import deque
from datetime import datetime, timedelta
import threading

from src.utils.logger import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """
    Collects and aggregates metrics for monitoring and analysis.
    """
    
    def __init__(self, max_recent_items: int = 1000):
        self.max_recent_items = max_recent_items
        
        # Thread-safe collections
        self.lock = threading.Lock()
        
        # Recent analyses (for rule generation and monitoring)
        self.recent_analyses = deque(maxlen=max_recent_items)
        
        # Recent anomalies only
        self.recent_anomalies = deque(maxlen=max_recent_items)
        
        # Feedback collection
        self.feedback_data = deque(maxlen=max_recent_items)
        
        # Aggregated statistics
        self.stats = {
            'total_requests': 0,
            'total_anomalies': 0,
            'total_false_positives': 0,
            'avg_latency_ms': 0.0,
            'requests_per_minute': 0.0,
            'start_time': datetime.utcnow().isoformat()
        }
        
        # Time-series data for charts
        self.time_series = {
            'timestamps': deque(maxlen=100),
            'anomaly_scores': deque(maxlen=100),
            'latencies': deque(maxlen=100)
        }
        
        # Attack type counters
        self.attack_types = {}
        
        logger.info("MetricsCollector initialized")
    
    def record_analysis(self, result: Dict[str, Any]):
        """Record an analysis result."""
        with self.lock:
            # Add to recent analyses
            self.recent_analyses.append(result)
            
            # Update stats
            self.stats['total_requests'] += 1
            
            if result['is_anomaly']:
                self.stats['total_anomalies'] += 1
                self.recent_anomalies.append(result)
                
                # Track attack types
                explanation = result.get('explanation', {})
                indicators = explanation.get('attack_indicators', [])
                
                for indicator in indicators:
                    attack_type = self._extract_attack_type(indicator)
                    self.attack_types[attack_type] = self.attack_types.get(attack_type, 0) + 1
            
            # Update average latency
            n = self.stats['total_requests']
            current_avg = self.stats['avg_latency_ms']
            latency = result['latency_ms']
            self.stats['avg_latency_ms'] = (current_avg * (n - 1) + latency) / n
            
            # Update time series
            self.time_series['timestamps'].append(result['timestamp'])
            self.time_series['anomaly_scores'].append(result['anomaly_score'])
            self.time_series['latencies'].append(result['latency_ms'])
    
    def record_feedback(self, feedback: Dict[str, Any]):
        """Record administrator feedback."""
        with self.lock:
            self.feedback_data.append(feedback)
            
            if feedback.get('is_false_positive'):
                self.stats['total_false_positives'] += 1
        
        logger.info(f"Feedback recorded: {feedback}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics."""
        with self.lock:
            # Calculate additional stats
            detection_rate = 0.0
            if self.stats['total_requests'] > 0:
                detection_rate = (
                    self.stats['total_anomalies'] / self.stats['total_requests']
                ) * 100
            
            false_positive_rate = 0.0
            if self.stats['total_anomalies'] > 0:
                false_positive_rate = (
                    self.stats['total_false_positives'] / self.stats['total_anomalies']
                ) * 100
            
            # Calculate uptime
            start_time = datetime.fromisoformat(self.stats['start_time'])
            uptime_seconds = (datetime.utcnow() - start_time).total_seconds()
            
            # Calculate requests per minute
            if uptime_seconds > 0:
                rpm = (self.stats['total_requests'] / uptime_seconds) * 60
            else:
                rpm = 0.0
            
            return {
                **self.stats,
                'detection_rate_percent': round(detection_rate, 2),
                'false_positive_rate_percent': round(false_positive_rate, 2),
                'uptime_seconds': int(uptime_seconds),
                'requests_per_minute': round(rpm, 2),
                'attack_types': dict(self.attack_types),
                'feedback_count': len(self.feedback_data)
            }
    
    def get_recent_anomalies(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent anomaly detections."""
        with self.lock:
            return list(self.recent_anomalies)[-limit:]
    
    def get_time_series_data(self) -> Dict[str, List]:
        """Get time-series data for visualization."""
        with self.lock:
            return {
                'timestamps': list(self.time_series['timestamps']),
                'anomaly_scores': list(self.time_series['anomaly_scores']),
                'latencies': list(self.time_series['latencies'])
            }
    
    def get_attack_distribution(self) -> Dict[str, int]:
        """Get distribution of attack types."""
        with self.lock:
            return dict(self.attack_types)
    
    def _extract_attack_type(self, indicator: str) -> str:
        """Extract attack type from indicator string."""
        indicator_lower = indicator.lower()
        
        if 'sql' in indicator_lower:
            return 'SQL Injection'
        elif 'xss' in indicator_lower or 'script' in indicator_lower:
            return 'XSS'
        elif 'lfi' in indicator_lower or 'file' in indicator_lower:
            return 'LFI'
        elif 'command' in indicator_lower:
            return 'Command Injection'
        elif 'bot' in indicator_lower:
            return 'Bot Traffic'
        elif 'suspicious' in indicator_lower:
            return 'Suspicious Activity'
        else:
            return 'Other'
    
    def reset_statistics(self):
        """Reset all statistics (use with caution)."""
        with self.lock:
            self.recent_analyses.clear()
            self.recent_anomalies.clear()
            self.feedback_data.clear()
            self.attack_types.clear()
            
            for key in self.time_series:
                self.time_series[key].clear()
            
            self.stats = {
                'total_requests': 0,
                'total_anomalies': 0,
                'total_false_positives': 0,
                'avg_latency_ms': 0.0,
                'requests_per_minute': 0.0,
                'start_time': datetime.utcnow().isoformat()
            }
        
        logger.info("Statistics reset")
