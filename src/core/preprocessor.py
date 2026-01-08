"""
Traffic preprocessing and feature extraction module.
"""

import re
import hashlib
from typing import Dict, Any, List
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import numpy as np
import pandas as pd
from collections import Counter

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TrafficPreprocessor:
    """
    Extracts and preprocesses features from HTTP/HTTPS traffic for ML models.
    """
    
    def __init__(self):
        # Common attack patterns
        self.sql_patterns = [
            r"(\bunion\b.*\bselect\b)", r"(\bselect\b.*\bfrom\b)",
            r"(\binsert\b.*\binto\b)", r"(\bupdate\b.*\bset\b)",
            r"(\bdelete\b.*\bfrom\b)", r"(\bdrop\b.*\btable\b)",
            r"'.*or.*'.*=.*'", r"--", r"/\*.*\*/"
        ]
        
        self.xss_patterns = [
            r"<script.*?>", r"javascript:", r"onerror\s*=",
            r"onload\s*=", r"<iframe", r"alert\(", r"document\.cookie"
        ]
        
        self.lfi_patterns = [
            r"\.\./", r"\.\.\\", r"/etc/passwd", r"c:\\windows",
            r"file://", r"php://", r"data://"
        ]
        
        self.command_injection_patterns = [
            r";.*\s*(ls|cat|wget|curl|bash|sh)", r"\|.*\s*(ls|cat|wget)",
            r"`.*`", r"\$\(.*\)"
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = {
            'sql': [re.compile(p, re.IGNORECASE) for p in self.sql_patterns],
            'xss': [re.compile(p, re.IGNORECASE) for p in self.xss_patterns],
            'lfi': [re.compile(p, re.IGNORECASE) for p in self.lfi_patterns],
            'cmd': [re.compile(p, re.IGNORECASE) for p in self.command_injection_patterns]
        }
    
    async def extract_features(self, request_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract comprehensive feature vector from HTTP request.
        
        Args:
            request_data: Dictionary with request details
        
        Returns:
            Feature vector as numpy array
        """
        features = {}
        
        # Basic request features
        features.update(self._extract_basic_features(request_data))
        
        # URL features
        features.update(self._extract_url_features(request_data.get('path', '')))
        
        # Header features
        features.update(self._extract_header_features(request_data.get('headers', {})))
        
        # Body features
        features.update(self._extract_body_features(request_data.get('body', '')))
        
        # Pattern matching features
        features.update(self._extract_pattern_features(request_data))
        
        # Temporal features
        features.update(self._extract_temporal_features(request_data.get('timestamp', '')))
        
        # Convert to numpy array
        feature_vector = np.array(list(features.values()), dtype=np.float32)
        
        return feature_vector
    
    def _extract_basic_features(self, request_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract basic request features."""
        method = request_data.get('method', 'GET')
        
        return {
            'method_get': 1.0 if method == 'GET' else 0.0,
            'method_post': 1.0 if method == 'POST' else 0.0,
            'method_put': 1.0 if method == 'PUT' else 0.0,
            'method_delete': 1.0 if method == 'DELETE' else 0.0,
            'method_other': 1.0 if method not in ['GET', 'POST', 'PUT', 'DELETE'] else 0.0,
        }
    
    def _extract_url_features(self, url: str) -> Dict[str, float]:
        """Extract URL-based features."""
        parsed = urlparse(url)
        path = parsed.path
        query = parsed.query
        
        # Query parameters
        params = parse_qs(query)
        
        return {
            'url_length': float(len(url)),
            'path_length': float(len(path)),
            'query_length': float(len(query)),
            'num_query_params': float(len(params)),
            'num_path_segments': float(len(path.split('/'))),
            'has_query': 1.0 if query else 0.0,
            'num_dots_in_path': float(path.count('.')),
            'num_slashes_in_path': float(path.count('/')),
            'num_special_chars': float(sum(c in url for c in ['<', '>', '"', "'", '&', '|', ';'])),
            'entropy': self._calculate_entropy(url),
        }
    
    def _extract_header_features(self, headers: Dict[str, str]) -> Dict[str, float]:
        """Extract header-based features."""
        user_agent = headers.get('User-Agent', headers.get('user-agent', ''))
        content_type = headers.get('Content-Type', headers.get('content-type', ''))
        
        return {
            'num_headers': float(len(headers)),
            'has_user_agent': 1.0 if user_agent else 0.0,
            'user_agent_length': float(len(user_agent)),
            'is_bot_user_agent': 1.0 if self._is_bot_user_agent(user_agent) else 0.0,
            'has_content_type': 1.0 if content_type else 0.0,
            'content_type_json': 1.0 if 'json' in content_type.lower() else 0.0,
            'content_type_xml': 1.0 if 'xml' in content_type.lower() else 0.0,
            'has_referer': 1.0 if 'Referer' in headers or 'referer' in headers else 0.0,
            'has_cookie': 1.0 if 'Cookie' in headers or 'cookie' in headers else 0.0,
        }
    
    def _extract_body_features(self, body: str) -> Dict[str, float]:
        """Extract request body features."""
        return {
            'body_length': float(len(body)),
            'has_body': 1.0 if body else 0.0,
            'body_entropy': self._calculate_entropy(body) if body else 0.0,
            'body_printable_ratio': self._calculate_printable_ratio(body) if body else 1.0,
        }
    
    def _extract_pattern_features(self, request_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract attack pattern features."""
        # Combine all request data into searchable text
        search_text = ' '.join([
            request_data.get('path', ''),
            str(request_data.get('headers', {})),
            request_data.get('body', '')
        ]).lower()
        
        features = {}
        
        # Check each pattern type
        for pattern_type, patterns in self.compiled_patterns.items():
            matches = sum(1 for pattern in patterns if pattern.search(search_text))
            features[f'pattern_{pattern_type}_count'] = float(matches)
            features[f'has_pattern_{pattern_type}'] = 1.0 if matches > 0 else 0.0
        
        return features
    
    def _extract_temporal_features(self, timestamp: str) -> Dict[str, float]:
        """Extract time-based features."""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except:
            dt = datetime.utcnow()
        
        return {
            'hour_of_day': float(dt.hour),
            'day_of_week': float(dt.weekday()),
            'is_weekend': 1.0 if dt.weekday() >= 5 else 0.0,
            'is_business_hours': 1.0 if 9 <= dt.hour <= 17 else 0.0,
        }
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text."""
        if not text:
            return 0.0
        
        # Count character frequencies
        counter = Counter(text)
        length = len(text)
        
        # Calculate entropy
        entropy = 0.0
        for count in counter.values():
            probability = count / length
            entropy -= probability * np.log2(probability)
        
        return float(entropy)
    
    def _calculate_printable_ratio(self, text: str) -> float:
        """Calculate ratio of printable characters."""
        if not text:
            return 1.0
        
        printable_count = sum(1 for c in text if c.isprintable())
        return printable_count / len(text)
    
    def _is_bot_user_agent(self, user_agent: str) -> bool:
        """Check if user agent indicates a bot."""
        bot_indicators = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
            'python', 'java', 'perl', 'ruby', 'php'
        ]
        
        user_agent_lower = user_agent.lower()
        return any(indicator in user_agent_lower for indicator in bot_indicators)
    
    def get_feature_names(self) -> List[str]:
        """Get names of all extracted features."""
        # This should match the order in extract_features
        return [
            # Basic
            'method_get', 'method_post', 'method_put', 'method_delete', 'method_other',
            # URL
            'url_length', 'path_length', 'query_length', 'num_query_params',
            'num_path_segments', 'has_query', 'num_dots_in_path', 'num_slashes_in_path',
            'num_special_chars', 'entropy',
            # Headers
            'num_headers', 'has_user_agent', 'user_agent_length', 'is_bot_user_agent',
            'has_content_type', 'content_type_json', 'content_type_xml',
            'has_referer', 'has_cookie',
            # Body
            'body_length', 'has_body', 'body_entropy', 'body_printable_ratio',
            # Patterns
            'pattern_sql_count', 'has_pattern_sql',
            'pattern_xss_count', 'has_pattern_xss',
            'pattern_lfi_count', 'has_pattern_lfi',
            'pattern_cmd_count', 'has_pattern_cmd',
            # Temporal
            'hour_of_day', 'day_of_week', 'is_weekend', 'is_business_hours',
        ]
