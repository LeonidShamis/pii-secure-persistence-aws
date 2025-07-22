#!/usr/bin/env python3
"""
Create the final fixed package
"""

import subprocess
import tempfile
import zipfile
import shutil
import os
from pathlib import Path

def create_final_package():
    """Create final fixed package"""
    
    project_root = Path(__file__).parent
    lambda_file = project_root / "lambda_function_generated.py"
    
    print("📦 Creating final fixed package...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Install dependencies
        subprocess.run([
            "pip", "install",
            "--target", str(temp_path),
            "boto3==1.34.144",
            "psycopg2-binary==2.9.7"
        ], check=True)
        
        # Copy fixed Lambda function
        shutil.copy(lambda_file, temp_path / "lambda_function.py")
        
        # Clean up
        for root, dirs, files in os.walk(temp_path):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith(('.pyc', '.pyo')):
                    os.remove(os.path.join(root, file))
        
        # Create zip
        zip_path = project_root / "pii-encryption-lambda-FINAL-FIXED.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_path):
                for file in files:
                    if not file.endswith(('.pyc', '.pyo')):
                        file_path = Path(root) / file
                        arc_name = file_path.relative_to(temp_path)
                        zipf.write(file_path, arc_name)
        
        print(f"✅ Final fixed package: {zip_path}")
        print(f"📦 Size: {zip_path.stat().st_size / (1024*1024):.2f} MB")
        
        return str(zip_path)

if __name__ == "__main__":
    create_final_package()