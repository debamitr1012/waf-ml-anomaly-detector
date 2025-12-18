"""
Security rule generation from ML insights.
"""

from typing import Dict, Any, List
from datetime import datetime
import json

from utils.logger import get_logger

logger = get_logger(__name__)


class RuleGenerator:
    """
    Generates human-readable security rules from ML-detected anomalies.
    Supports multiple WAF formats (ModSecurity, NGINX, etc.)
    """
    
    def __init__(self):
        self.rule_id_counter = 10000
        self.generated_rules = []
    
    async def generate_rules(
        self,
        anomalies: List[Dict[str, Any]],
        confidence_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Generate security rules from detected anomalies.
        
        Args:
            anomalies: List of anomaly detection results
            confidence_threshold: Minimum confidence to generate rule
        
        Returns:
            List of generated rules
        """
        rules = []
        
        # Group similar anomalies
        grouped_anomalies = self._group_similar_anomalies(anomalies)
        
        for group in grouped_anomalies:
            # Only generate rules for high-confidence patterns
            avg_confidence = sum(a['confidence'] for a in group) / len(group)
            
            if avg_confidence >= confidence_threshold:
                rule = await self._create_rule_from_group(group)
                if rule:
                    rules.append(rule)
        
        self.generated_rules.extend(rules)
        logger.info(f"Generated {len(rules)} security rules")
        
        return rules
    
    def _group_similar_anomalies(
        self,
        anomalies: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """Group anomalies with similar characteristics."""
        groups = []
        
        # Simple grouping by attack indicators
        attack_type_groups = {}
        
        for anomaly in anomalies:
            indicators = anomaly.get('explanation', {}).get('attack_indicators', [])
            
            if not indicators:
                continue
            
            # Use first indicator as primary grouping key
            primary_indicator = indicators[0] if indicators else 'unknown'
            
            # Extract attack type
            attack_type = self._extract_attack_type(primary_indicator)
            
            if attack_type not in attack_type_groups:
                attack_type_groups[attack_type] = []
            
            attack_type_groups[attack_type].append(anomaly)
        
        # Convert to list of groups
        for attack_type, group_anomalies in attack_type_groups.items():
            if len(group_anomalies) >= 3:  # Require at least 3 similar anomalies
                groups.append(group_anomalies)
        
        return groups
    
    def _extract_attack_type(self, indicator: str) -> str:
        """Extract attack type from indicator string."""
        indicator_lower = indicator.lower()
        
        if 'sql' in indicator_lower:
            return 'sql_injection'
        elif 'xss' in indicator_lower or 'script' in indicator_lower:
            return 'xss'
        elif 'lfi' in indicator_lower or 'file' in indicator_lower:
            return 'lfi'
        elif 'command' in indicator_lower or 'injection' in indicator_lower:
            return 'command_injection'
        elif 'bot' in indicator_lower:
            return 'bot_traffic'
        else:
            return 'unknown'
    
    async def _create_rule_from_group(
        self,
        group: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a security rule from a group of similar anomalies."""
        # Extract common patterns
        indicators = []
        for anomaly in group:
            explanation = anomaly.get('explanation', {})
            indicators.extend(explanation.get('attack_indicators', []))
        
        # Get most common indicator
        primary_indicator = max(set(indicators), key=indicators.count) if indicators else 'Unknown'
        attack_type = self._extract_attack_type(primary_indicator)
        
        # Generate rule
        rule_id = self._get_next_rule_id()
        
        rule = {
            'id': rule_id,
            'attack_type': attack_type,
            'description': self._generate_rule_description(attack_type, group),
            'severity': self._determine_severity(group),
            'confidence': sum(a['confidence'] for a in group) / len(group),
            'occurrences': len(group),
            'first_seen': min(a.get('timestamp', '') for a in group),
            'last_seen': max(a.get('timestamp', '') for a in group),
            'recommended_action': self._determine_action(attack_type, group),
            'formats': {}
        }
        
        # Generate rule in different formats
        rule['formats']['modsecurity'] = self._generate_modsecurity_rule(rule)
        rule['formats']['nginx'] = self._generate_nginx_rule(rule)
        rule['formats']['generic'] = self._generate_generic_rule(rule)
        
        return rule
    
    def _generate_rule_description(
        self,
        attack_type: str,
        group: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable rule description."""
        descriptions = {
            'sql_injection': f"Block SQL injection attempts detected in {len(group)} requests",
            'xss': f"Block cross-site scripting (XSS) attempts detected in {len(group)} requests",
            'lfi': f"Block local file inclusion (LFI) attempts detected in {len(group)} requests",
            'command_injection': f"Block command injection attempts detected in {len(group)} requests",
            'bot_traffic': f"Block suspicious bot traffic detected in {len(group)} requests",
            'unknown': f"Block anomalous traffic pattern detected in {len(group)} requests"
        }
        
        return descriptions.get(attack_type, descriptions['unknown'])
    
    def _determine_severity(self, group: List[Dict[str, Any]]) -> str:
        """Determine rule severity based on anomalies."""
        avg_score = sum(a['anomaly_score'] for a in group) / len(group)
        
        if avg_score >= 0.9:
            return 'critical'
        elif avg_score >= 0.7:
            return 'high'
        elif avg_score >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _determine_action(self, attack_type: str, group: List[Dict[str, Any]]) -> str:
        """Determine recommended action."""
        severity = self._determine_severity(group)
        
        if severity in ['critical', 'high']:
            return 'block'
        elif severity == 'medium':
            return 'challenge'
        else:
            return 'log'
    
    def _generate_modsecurity_rule(self, rule: Dict[str, Any]) -> str:
        """Generate ModSecurity rule format."""
        attack_type = rule['attack_type']
        rule_id = rule['id']
        description = rule['description']
        action = rule['recommended_action']
        
        # Map attack types to ModSecurity patterns
        patterns = {
            'sql_injection': r"(?i)(union.*select|select.*from|insert.*into|' or '|--)",
            'xss': r"(?i)(<script|javascript:|onerror\s*=|onload\s*=)",
            'lfi': r"(?i)(\.\.\/|\.\.\\|\/etc\/passwd|c:\\windows)",
            'command_injection': r"(?i)(;.*ls|;.*cat|\|.*wget|`.*`)",
            'bot_traffic': r"(?i)(bot|crawler|spider|scraper|curl|wget)"
        }
        
        pattern = patterns.get(attack_type, '.*')
        
        modsec_action = {
            'block': 'deny,status:403',
            'challenge': 'pass,log',
            'log': 'pass,log'
        }.get(action, 'pass,log')
        
        return f'''SecRule REQUEST_URI|ARGS|REQUEST_BODY "@rx {pattern}" \\
    "id:{rule_id},\\
    phase:2,\\
    t:none,t:urlDecodeUni,t:lowercase,\\
    {modsec_action},\\
    msg:'{description}',\\
    logdata:'Matched Data: %{{MATCHED_VAR}}',\\
    severity:'{rule['severity'].upper()}',\\
    tag:'attack-{attack_type}',\\
    tag:'OWASP_CRS',\\
    ver:'ML-WAF/1.0'"'''
    
    def _generate_nginx_rule(self, rule: Dict[str, Any]) -> str:
        """Generate NGINX Lua rule format."""
        attack_type = rule['attack_type']
        description = rule['description']
        action = rule['recommended_action']
        
        nginx_action = {
            'block': 'ngx.exit(403)',
            'challenge': 'ngx.log(ngx.WARN, "Suspicious request")',
            'log': 'ngx.log(ngx.INFO, "Anomaly logged")'
        }.get(action, 'ngx.log(ngx.INFO, "Anomaly logged")')
        
        return f'''-- Rule {rule['id']}: {description}
if ngx.var.request_uri and string.find(ngx.var.request_uri, "pattern") then
    ngx.log(ngx.WARN, "Detected {attack_type} attempt")
    {nginx_action}
end'''
    
    def _generate_generic_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Generate generic rule format."""
        return {
            'condition': {
                'attack_type': rule['attack_type'],
                'min_anomaly_score': 0.5
            },
            'action': rule['recommended_action'],
            'metadata': {
                'rule_id': rule['id'],
                'description': rule['description'],
                'severity': rule['severity'],
                'confidence': rule['confidence']
            }
        }
    
    def _get_next_rule_id(self) -> int:
        """Get next available rule ID."""
        rule_id = self.rule_id_counter
        self.rule_id_counter += 1
        return rule_id
    
    def get_all_rules(self) -> List[Dict[str, Any]]:
        """Get all generated rules."""
        return self.generated_rules
    
    def export_rules(self, format: str = 'json', output_file: str = None) -> str:
        """
        Export rules to file.
        
        Args:
            format: Export format ('json', 'modsecurity', 'nginx')
            output_file: Output file path (optional)
        
        Returns:
            Exported rules as string
        """
        if format == 'json':
            output = json.dumps(self.generated_rules, indent=2)
        elif format == 'modsecurity':
            output = '\n\n'.join(
                rule['formats']['modsecurity']
                for rule in self.generated_rules
            )
        elif format == 'nginx':
            output = '\n\n'.join(
                rule['formats']['nginx']
                for rule in self.generated_rules
            )
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            logger.info(f"Rules exported to {output_file}")
        
        return output
