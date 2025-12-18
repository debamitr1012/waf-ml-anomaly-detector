"""
Traffic generation script for testing and demonstration.
"""

import argparse
import random
import requests
import time
from datetime import datetime
from typing import List, Dict, Any


class TrafficGenerator:
    """Generate synthetic traffic for testing."""
    
    def __init__(self, api_url: str = "http://localhost:8000/api/v1"):
        self.api_url = api_url
        
        # Normal traffic patterns
        self.normal_paths = [
            "/",
            "/api/users",
            "/api/products",
            "/api/orders",
            "/dashboard",
            "/login",
            "/about",
            "/contact"
        ]
        
        self.normal_methods = ["GET", "POST", "PUT", "DELETE"]
        
        # Anomalous traffic patterns
        self.attack_patterns = {
            'sql_injection': [
                "/api/users?id=1' OR '1'='1",
                "/search?q=admin'--",
                "/api/products?id=1 UNION SELECT * FROM users--",
                "/login?user=admin' OR 1=1#"
            ],
            'xss': [
                "/search?q=<script>alert('XSS')</script>",
                "/comment?text=<img src=x onerror=alert(1)>",
                "/profile?name=<script>document.location='evil.com'</script>"
            ],
            'lfi': [
                "/download?file=../../etc/passwd",
                "/view?page=../../../windows/system32/config/sam",
                "/api/file?path=..\\..\\..\\etc\\shadow"
            ],
            'command_injection': [
                "/ping?host=127.0.0.1;ls -la",
                "/api/exec?cmd=cat /etc/passwd",
                "/run?script=`whoami`"
            ]
        }
    
    def generate_normal_request(self) -> Dict[str, Any]:
        """Generate a normal request."""
        return {
            'source_ip': f"192.168.1.{random.randint(1, 255)}",
            'method': random.choice(self.normal_methods),
            'path': random.choice(self.normal_paths),
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/json'
            },
            'body': '',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def generate_anomalous_request(self, attack_type: str = None) -> Dict[str, Any]:
        """Generate an anomalous request."""
        if attack_type is None:
            attack_type = random.choice(list(self.attack_patterns.keys()))
        
        path = random.choice(self.attack_patterns[attack_type])
        
        return {
            'source_ip': f"10.0.0.{random.randint(1, 50)}",
            'method': random.choice(['GET', 'POST']),
            'path': path,
            'headers': {
                'User-Agent': 'curl/7.68.0',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            'body': '',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def send_request(self, request_data: Dict[str, Any]):
        """Send request to API for analysis."""
        try:
            response = requests.post(
                f"{self.api_url}/analyze",
                json=request_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                status = "🚨 ANOMALY" if result['is_anomaly'] else "✅ NORMAL"
                print(f"{status} - {request_data['method']} {request_data['path'][:50]}")
                if result['is_anomaly']:
                    print(f"  Score: {result['anomaly_score']:.3f}, Action: {result['recommended_action']}")
                return result
            else:
                print(f"❌ Error: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return None
    
    def generate_traffic(
        self,
        num_normal: int = 100,
        num_anomalous: int = 10,
        delay_ms: int = 100
    ):
        """Generate mixed traffic."""
        print(f"\n{'='*60}")
        print(f"Generating Traffic:")
        print(f"  Normal requests: {num_normal}")
        print(f"  Anomalous requests: {num_anomalous}")
        print(f"  API endpoint: {self.api_url}")
        print(f"{'='*60}\n")
        
        total = num_normal + num_anomalous
        requests_sent = 0
        
        # Generate all requests
        requests_list = []
        for _ in range(num_normal):
            requests_list.append(('normal', self.generate_normal_request()))
        
        for _ in range(num_anomalous):
            requests_list.append(('anomalous', self.generate_anomalous_request()))
        
        # Shuffle to mix normal and anomalous
        random.shuffle(requests_list)
        
        # Send requests
        anomalies_detected = 0
        for request_type, request_data in requests_list:
            result = self.send_request(request_data)
            
            if result and result['is_anomaly']:
                anomalies_detected += 1
            
            requests_sent += 1
            
            # Progress
            if requests_sent % 10 == 0:
                print(f"\nProgress: {requests_sent}/{total}")
            
            time.sleep(delay_ms / 1000.0)
        
        print(f"\n{'='*60}")
        print(f"Traffic Generation Complete!")
        print(f"  Total requests sent: {requests_sent}")
        print(f"  Anomalies detected: {anomalies_detected}")
        print(f"  Detection rate: {anomalies_detected/num_anomalous*100:.1f}%")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description='Generate traffic for WAF ML testing')
    parser.add_argument(
        '--api-url',
        default='http://localhost:8000/api/v1',
        help='API base URL'
    )
    parser.add_argument(
        '--normal',
        type=int,
        default=100,
        help='Number of normal requests'
    )
    parser.add_argument(
        '--anomalous',
        type=int,
        default=10,
        help='Number of anomalous requests'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=100,
        help='Delay between requests (ms)'
    )
    
    args = parser.parse_args()
    
    generator = TrafficGenerator(api_url=args.api_url)
    generator.generate_traffic(
        num_normal=args.normal,
        num_anomalous=args.anomalous,
        delay_ms=args.delay
    )


if __name__ == '__main__':
    main()
