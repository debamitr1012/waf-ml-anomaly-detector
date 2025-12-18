"""
Download and process KDD Cup 1999 dataset for WAF ML training.
This dataset contains network intrusion data that we'll adapt for WAF anomaly detection.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path

try:
    import kagglehub
except ImportError:
    print("Installing kagglehub...")
    import subprocess
    subprocess.check_call(["pip", "install", "kagglehub"])
    import kagglehub


def download_kdd_dataset():
    """Download KDD Cup 1999 dataset from Kaggle."""
    print("Downloading KDD Cup 1999 dataset from Kaggle...")
    try:
        path = kagglehub.dataset_download("galaxyh/kdd-cup-1999-data")
        print(f"Dataset downloaded to: {path}")
        return path
    except Exception as e:
        print(f"Error downloading: {e}")
        # Fallback to local data directory
        local_path = Path("data/training")
        if (local_path / "kddcup.data").exists():
            print(f"Using local dataset at: {local_path}")
            return str(local_path)
        raise


def load_kdd_data(dataset_path):
    """Load KDD Cup 1999 data with column names."""
    # KDD Cup 1999 column names
    columns = [
        'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
        'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in',
        'num_compromised', 'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
        'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login',
        'is_guest_login', 'count', 'srv_count', 'serror_rate', 'srv_serror_rate',
        'rerror_rate', 'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate',
        'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
        'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
        'dst_host_srv_diff_host_rate', 'dst_host_serror_rate', 'dst_host_srv_serror_rate',
        'dst_host_rerror_rate', 'dst_host_srv_rerror_rate', 'attack_type', 'difficulty_level'
    ]
    
    # Find data files in the dataset (KDD uses .data extension)
    dataset_dir = Path(dataset_path)
    data_files = list(dataset_dir.glob("*.data")) + list(dataset_dir.glob("*.csv"))
    
    if not data_files:
        raise FileNotFoundError(f"No data files found in {dataset_path}")
    
    print(f"Found {len(data_files)} data file(s)")
    
    # Load the first/main data file with explicit read mode
    try:
        with open(data_files[0], 'r', encoding='utf-8', errors='ignore') as f:
            df = pd.read_csv(f, names=columns, header=None)
        print(f"Loaded {len(df)} records from {data_files[0].name}")
    except PermissionError:
        # Try copying to temp location
        import shutil
        import tempfile
        temp_file = Path(tempfile.gettempdir()) / "kddcup_temp.data"
        shutil.copy2(data_files[0], temp_file)
        df = pd.read_csv(temp_file, names=columns, header=None)
        temp_file.unlink()
        print(f"Loaded {len(df)} records from {data_files[0].name} (via temp copy)")
    
    return df


def map_kdd_to_waf_features(df, sample_size=None):
    """
    Transform KDD Cup features to WAF-relevant features.
    Maps network intrusion patterns to HTTP/WAF attack patterns.
    """
    print("\nTransforming KDD data to WAF format...")
    
    if sample_size:
        df = df.sample(n=min(sample_size, len(df)), random_state=42)
        print(f"Sampled {len(df)} records")
    
    # Classify attacks
    attack_mapping = {
        'normal': 0,
        'back': 1, 'buffer_overflow': 1, 'ftp_write': 1, 'guess_passwd': 1,
        'imap': 1, 'ipsweep': 1, 'land': 1, 'loadmodule': 1, 'multihop': 1,
        'neptune': 1, 'nmap': 1, 'perl': 1, 'phf': 1, 'pod': 1, 'portsweep': 1,
        'rootkit': 1, 'satan': 1, 'smurf': 1, 'spy': 1, 'teardrop': 1,
        'warezclient': 1, 'warezmaster': 1
    }
    
    # Map attack types to categories relevant to WAF
    attack_category_mapping = {
        'normal': 'normal',
        'back': 'dos', 'land': 'dos', 'neptune': 'dos', 'pod': 'dos',
        'smurf': 'dos', 'teardrop': 'dos',
        'buffer_overflow': 'u2r', 'loadmodule': 'u2r', 'perl': 'u2r',
        'rootkit': 'u2r',
        'ftp_write': 'r2l', 'guess_passwd': 'r2l', 'imap': 'r2l',
        'multihop': 'r2l', 'phf': 'r2l', 'spy': 'r2l', 'warezclient': 'r2l',
        'warezmaster': 'r2l',
        'ipsweep': 'probe', 'nmap': 'probe', 'portsweep': 'probe', 'satan': 'probe'
    }
    
    # Create WAF-style dataset
    waf_data = []
    
    for idx, row in df.iterrows():
        attack_type = row['attack_type'].strip('.')
        is_anomaly = attack_mapping.get(attack_type, 1)
        attack_category = attack_category_mapping.get(attack_type, 'unknown')
        
        # Generate synthetic HTTP-like features based on network patterns
        waf_sample = {
            # Network features mapped to WAF context
            'source_ip': f"10.{np.random.randint(0, 255)}.{np.random.randint(0, 255)}.{np.random.randint(1, 255)}",
            'method': np.random.choice(['GET', 'POST', 'PUT', 'DELETE'], p=[0.6, 0.3, 0.05, 0.05]),
            'path': generate_path_from_attack(attack_category),
            'body': '',
            
            # Use KDD features as additional context
            'protocol': row['protocol_type'],
            'src_bytes': row['src_bytes'],
            'dst_bytes': row['dst_bytes'],
            'duration': row['duration'],
            'service': row['service'],
            'flag': row['flag'],
            
            # Connection patterns
            'count': row['count'],
            'srv_count': row['srv_count'],
            'error_rate': row['serror_rate'],
            'same_srv_rate': row['same_srv_rate'],
            
            # Security indicators
            'num_failed_logins': row['num_failed_logins'],
            'logged_in': row['logged_in'],
            'num_compromised': row['num_compromised'],
            'root_shell': row['root_shell'],
            'num_file_creations': row['num_file_creations'],
            
            # Labels
            'is_anomaly': is_anomaly,
            'attack_category': attack_category,
            'original_attack_type': attack_type
        }
        
        waf_data.append(waf_sample)
    
    return pd.DataFrame(waf_data)


def generate_path_from_attack(attack_category):
    """Generate realistic HTTP paths based on attack category."""
    normal_paths = [
        '/home', '/about', '/api/users', '/api/products', '/dashboard',
        '/login', '/profile', '/settings', '/api/data', '/search'
    ]
    
    dos_paths = [
        '/api/large-data', '/heavy-computation', '/api/report',
        '/download?file=large.zip', '/api/bulk-export'
    ]
    
    probe_paths = [
        '/admin', '/.git/config', '/phpinfo.php', '/server-status',
        '/.env', '/config.php', '/wp-admin'
    ]
    
    u2r_paths = [  # User to Root (privilege escalation)
        "/api/users?id=1' OR '1'='1",
        "/admin?cmd=cat /etc/passwd",
        "/api/exec?command=whoami",
        "/upload?file=../../etc/shadow"
    ]
    
    r2l_paths = [  # Remote to Local (unauthorized access)
        "/login?user=admin&pass=' OR '1'='1",
        "/api/auth?token=<script>alert(1)</script>",
        "/ftp/upload?path=../../../root",
        "/api/download?file=../../../../etc/passwd"
    ]
    
    if attack_category == 'normal':
        return np.random.choice(normal_paths)
    elif attack_category == 'dos':
        return np.random.choice(dos_paths)
    elif attack_category == 'probe':
        return np.random.choice(probe_paths)
    elif attack_category == 'u2r':
        return np.random.choice(u2r_paths)
    elif attack_category == 'r2l':
        return np.random.choice(r2l_paths)
    else:
        return np.random.choice(normal_paths)


def save_processed_data(df, output_path):
    """Save processed dataset to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\nProcessed dataset saved to: {output_path}")
    print(f"Total records: {len(df)}")
    print(f"Normal: {len(df[df['is_anomaly'] == 0])} ({len(df[df['is_anomaly'] == 0])/len(df)*100:.1f}%)")
    print(f"Anomalous: {len(df[df['is_anomaly'] == 1])} ({len(df[df['is_anomaly'] == 1])/len(df)*100:.1f}%)")
    
    print("\nAttack category distribution:")
    print(df['attack_category'].value_counts())


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Process KDD Cup 1999 dataset for WAF training')
    parser.add_argument(
        '--sample-size',
        type=int,
        default=10000,
        help='Number of samples to use (default: 10000, use -1 for all data)'
    )
    parser.add_argument(
        '--output',
        default='data/training/kdd_waf_dataset.csv',
        help='Output CSV file path'
    )
    
    args = parser.parse_args()
    
    try:
        # Download dataset
        dataset_path = download_kdd_dataset()
        
        # Load KDD data
        df = load_kdd_data(dataset_path)
        
        # Transform to WAF features
        sample_size = None if args.sample_size == -1 else args.sample_size
        waf_df = map_kdd_to_waf_features(df, sample_size=sample_size)
        
        # Save processed data
        save_processed_data(waf_df, args.output)
        
        print("\n✅ Dataset processing complete!")
        print(f"\nNext steps:")
        print(f"1. Train models: python src/ml/train.py --data {args.output}")
        print(f"2. Start API: python src/main.py")
        print(f"3. Start dashboard: cd dashboard && npm run dev")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
