"""
Test the API endpoints to verify the system is working.
"""

import requests
import json
import numpy as np
import pandas as pd
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test health endpoint"""
    print("\n[TEST] Health Check")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_single_analysis():
    """Test single traffic analysis"""
    print("\n[TEST] Single Traffic Analysis")
    print("="*60)
    try:
        # Create sample traffic data with 38 features (matching our model)
        sample_data = {
            "source_ip": "192.168.1.100",
            "destination_ip": "10.0.0.1",
            "port": 80,
            "method": "GET",
            "path": "/api/users",
            "headers": {
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*"
            },
            "body": "",
            "timestamp": "2026-01-08T12:00:00Z",
            "packet_size": 256,
            "duration": 0.5,
            "protocol_type": 6,  # TCP
            "service": 0,
            "flag": 0,
            "src_bytes": 512,
            "dst_bytes": 1024,
            "land": 0,
            "wrong_fragment": 0,
            "urgent": 0,
            "hot": 0,
            "num_failed_logins": 0,
            "logged_in": 1,
            "num_compromised": 0,
            "root_shell": 0,
            "su_attempted": 0,
            "num_root": 0,
            "num_file_creations": 0,
            "num_shells": 0,
            "num_access_files": 0,
            "num_outbound_cmds": 0,
            "is_host_login": 0,
            "is_guest_login": 0,
            "count": 10,
            "srv_count": 5,
            "serror_rate": 0.0,
            "srv_serror_rate": 0.0,
            "rerror_rate": 0.0,
            "srv_rerror_rate": 0.0,
            "same_srv_rate": 0.5,
            "diff_srv_rate": 0.2,
            "srv_diff_host_rate": 0.1,
            "dst_host_count": 255,
            "dst_host_srv_count": 50,
            "dst_host_same_srv_rate": 0.3,
            "dst_host_diff_srv_rate": 0.15
        }
        
        response = requests.post(
            f"{BASE_URL}/analyze",
            json=sample_data,
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_batch_analysis():
    """Test batch traffic analysis"""
    print("\n[TEST] Batch Traffic Analysis")
    print("="*60)
    try:
        # Load test data
        df = pd.read_csv('dataset1/Test_data.csv')
        feature_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Take first 5 samples
        X_test = df[feature_cols].head(5).values.tolist()
        
        batch_data = {
            "traffic_samples": X_test
        }
        
        response = requests.post(
            f"{BASE_URL}/analyze/batch",
            json=batch_data,
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Analyzed {len(result.get('predictions', []))} samples")
            print(f"Response: {json.dumps(result, indent=2)[:500]}...")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_statistics():
    """Test statistics endpoint"""
    print("\n[TEST] Statistics")
    print("="*60)
    try:
        response = requests.get(f"{BASE_URL}/statistics", timeout=5)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("WAF ML ANOMALY DETECTOR - API TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test health
    results.append(("Health Check", test_health()))
    
    # Wait a moment
    import time
    time.sleep(1)
    
    # Test statistics
    results.append(("Statistics", test_statistics()))
    
    time.sleep(1)
    
    # Test single analysis
    results.append(("Single Analysis", test_single_analysis()))
    
    time.sleep(1)
    
    # Test batch analysis
    results.append(("Batch Analysis", test_batch_analysis()))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! System is ready for production.")
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Please check the logs.")

if __name__ == '__main__':
    main()
