"""
Download KDD Cup 1999 dataset using kagglehub
"""
import kagglehub
import os

def download_kdd_dataset():
    """Download KDD Cup 1999 dataset from Kaggle"""
    
    print("Downloading KDD Cup 1999 dataset from Kaggle...")
    print("Dataset: galaxyh/kdd-cup-1999-data")
    
    # Download dataset using kagglehub
    path = kagglehub.dataset_download("galaxyh/kdd-cup-1999-data")
    
    print(f"\n✓ Dataset downloaded successfully!")
    print(f"  Path to dataset files: {path}")
    
    # List downloaded files
    if os.path.exists(path):
        files = os.listdir(path)
        print(f"\n  Downloaded files ({len(files)}):")
        for file in files:
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path):
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"    - {file} ({size_mb:.2f} MB)")
    
    return path

if __name__ == '__main__':
    download_kdd_dataset()
