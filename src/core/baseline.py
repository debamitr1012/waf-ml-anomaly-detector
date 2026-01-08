"""
Traffic baselining and behavioral learning module.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio

from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaselineManager:
    """
    Manages traffic baselines for behavioral anomaly detection.
    Learns normal patterns per endpoint, user, and time window.
    """
    
    def __init__(self, window_minutes: int = 60, min_samples: int = 100):
        self.window_minutes = window_minutes
        self.min_samples = min_samples
        
        # Baselines per endpoint
        self.endpoint_baselines = {}
        
        # Recent traffic for real-time baseline updates
        self.recent_traffic = deque(maxlen=10000)
        
        # Per-IP statistics
        self.ip_statistics = defaultdict(lambda: {
            'request_count': 0,
            'methods': defaultdict(int),
            'paths': defaultdict(int),
            'anomaly_count': 0,
            'first_seen': None,
            'last_seen': None
        })
        
        # Time-based patterns
        self.time_patterns = {
            'hourly_distribution': np.zeros(24),
            'daily_distribution': np.zeros(7)
        }
        
        logger.info("BaselineManager initialized")
    
    async def load_baselines(self):
        """Load existing baselines from storage."""
        try:
            # In production, load from database or file
            logger.info("Loading baselines...")
            # TODO: Implement persistence
            logger.info("Baselines loaded (or initialized as empty)")
        except Exception as e:
            logger.error(f"Error loading baselines: {e}", exc_info=True)
    
    async def save_baselines(self):
        """Save current baselines to storage."""
        try:
            logger.info("Saving baselines...")
            # TODO: Implement persistence
            logger.info("Baselines saved")
        except Exception as e:
            logger.error(f"Error saving baselines: {e}", exc_info=True)
    
    def update_baseline(self, request_data: Dict[str, Any], is_anomaly: bool = False):
        """
        Update baseline with new traffic data.
        
        Args:
            request_data: Request information
            is_anomaly: Whether the request was detected as anomalous
        """
        try:
            # Add to recent traffic
            traffic_record = {
                **request_data,
                'is_anomaly': is_anomaly,
                'recorded_at': datetime.utcnow().isoformat()
            }
            self.recent_traffic.append(traffic_record)
            
            # Update endpoint baseline
            endpoint = request_data.get('path', '/')
            if endpoint not in self.endpoint_baselines:
                self.endpoint_baselines[endpoint] = {
                    'request_count': 0,
                    'methods': defaultdict(int),
                    'avg_body_length': 0.0,
                    'anomaly_rate': 0.0,
                    'first_seen': datetime.utcnow().isoformat()
                }
            
            baseline = self.endpoint_baselines[endpoint]
            baseline['request_count'] += 1
            baseline['methods'][request_data.get('method', 'GET')] += 1
            baseline['last_seen'] = datetime.utcnow().isoformat()
            
            # Update anomaly rate
            if is_anomaly:
                current_rate = baseline['anomaly_rate']
                baseline['anomaly_rate'] = (
                    current_rate * 0.95 + 0.05  # Exponential moving average
                )
            else:
                baseline['anomaly_rate'] *= 0.95
            
            # Update IP statistics
            source_ip = request_data.get('source_ip', 'unknown')
            ip_stats = self.ip_statistics[source_ip]
            ip_stats['request_count'] += 1
            ip_stats['methods'][request_data.get('method', 'GET')] += 1
            ip_stats['paths'][endpoint] += 1
            
            if is_anomaly:
                ip_stats['anomaly_count'] += 1
            
            if not ip_stats['first_seen']:
                ip_stats['first_seen'] = datetime.utcnow().isoformat()
            ip_stats['last_seen'] = datetime.utcnow().isoformat()
            
            # Update time patterns
            try:
                timestamp = datetime.fromisoformat(
                    request_data.get('timestamp', '').replace('Z', '+00:00')
                )
                self.time_patterns['hourly_distribution'][timestamp.hour] += 1
                self.time_patterns['daily_distribution'][timestamp.weekday()] += 1
            except:
                pass
            
        except Exception as e:
            logger.error(f"Error updating baseline: {e}", exc_info=True)
    
    def get_baseline_score(self, request_data: Dict[str, Any]) -> float:
        """
        Calculate how much a request deviates from baseline.
        
        Args:
            request_data: Request information
        
        Returns:
            Deviation score (0-1, higher = more deviation)
        """
        try:
            scores = []
            
            # Endpoint familiarity score
            endpoint = request_data.get('path', '/')
            if endpoint in self.endpoint_baselines:
                baseline = self.endpoint_baselines[endpoint]
                
                # More requests = more familiar = lower score
                familiarity = min(baseline['request_count'] / 1000.0, 1.0)
                scores.append(1.0 - familiarity)
                
                # Check if method is typical for this endpoint
                method = request_data.get('method', 'GET')
                method_count = baseline['methods'].get(method, 0)
                method_ratio = method_count / max(baseline['request_count'], 1)
                scores.append(1.0 - method_ratio)
                
                # Anomaly history for this endpoint
                scores.append(baseline['anomaly_rate'])
            else:
                # Never seen this endpoint before
                scores.append(0.8)
            
            # IP reputation score
            source_ip = request_data.get('source_ip', 'unknown')
            if source_ip in self.ip_statistics:
                ip_stats = self.ip_statistics[source_ip]
                
                # Anomaly rate for this IP
                if ip_stats['request_count'] > 0:
                    ip_anomaly_rate = ip_stats['anomaly_count'] / ip_stats['request_count']
                    scores.append(ip_anomaly_rate)
            else:
                # New IP
                scores.append(0.3)
            
            # Time-based score
            try:
                timestamp = datetime.fromisoformat(
                    request_data.get('timestamp', '').replace('Z', '+00:00')
                )
                hour = timestamp.hour
                
                # Check if this hour has typical traffic
                hourly_total = sum(self.time_patterns['hourly_distribution'])
                if hourly_total > 0:
                    hour_ratio = self.time_patterns['hourly_distribution'][hour] / hourly_total
                    scores.append(1.0 - hour_ratio * 24)  # Normalize
            except:
                pass
            
            # Average all scores
            if scores:
                return float(np.mean(scores))
            else:
                return 0.5
            
        except Exception as e:
            logger.error(f"Error calculating baseline score: {e}", exc_info=True)
            return 0.5
    
    def get_endpoint_stats(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific endpoint."""
        return self.endpoint_baselines.get(endpoint)
    
    def get_ip_stats(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific IP address."""
        return dict(self.ip_statistics.get(ip_address, {}))
    
    def get_top_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently accessed endpoints."""
        sorted_endpoints = sorted(
            self.endpoint_baselines.items(),
            key=lambda x: x[1]['request_count'],
            reverse=True
        )
        
        return [
            {'endpoint': endpoint, **stats}
            for endpoint, stats in sorted_endpoints[:limit]
        ]
    
    def get_suspicious_ips(self, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Get IPs with high anomaly rates."""
        suspicious = []
        
        for ip, stats in self.ip_statistics.items():
            if stats['request_count'] > self.min_samples:
                anomaly_rate = stats['anomaly_count'] / stats['request_count']
                
                if anomaly_rate >= threshold:
                    suspicious.append({
                        'ip': ip,
                        'anomaly_rate': anomaly_rate,
                        **stats
                    })
        
        return sorted(suspicious, key=lambda x: x['anomaly_rate'], reverse=True)
    
    def get_traffic_patterns(self) -> Dict[str, Any]:
        """Get learned traffic patterns."""
        return {
            'hourly_distribution': self.time_patterns['hourly_distribution'].tolist(),
            'daily_distribution': self.time_patterns['daily_distribution'].tolist(),
            'total_endpoints': len(self.endpoint_baselines),
            'total_ips': len(self.ip_statistics),
            'total_traffic_records': len(self.recent_traffic)
        }
