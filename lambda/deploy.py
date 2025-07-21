#!/usr/bin/env python3
"""
Lambda Deployment Script

This script packages and deploys the PII encryption Lambda function.
"""

import os
import sys
import shutil
import zipfile
import subprocess
import tempfile
from pathlib import Path


def create_deployment_package():
    """
    Create deployment package for Lambda function
    
    Returns:
        str: Path to the deployment zip file
    """
    print("Creating Lambda deployment package...")
    
    # Get project root
    project_root = Path(__file__).parent
    src_dir = project_root / "src" / "pii_encryption_lambda"
    
    # Create temporary directory for packaging
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy source code
        print("Copying source code...")
        shutil.copytree(src_dir, temp_path / "pii_encryption_lambda")
        
        # Install dependencies into temp directory
        print("Installing dependencies...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install",
            "-r", str(project_root / "pyproject.toml"),
            "-t", str(temp_path)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Failed to install dependencies: {result.stderr}")
            # Try with uv instead
            print("Trying with uv...")
            result = subprocess.run([
                "uv", "pip", "install",
                "--python", sys.executable,
                "boto3", "cryptography", "psycopg2-binary",
                "--target", str(temp_path)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Failed to install with uv: {result.stderr}")
                return None
        
        # Create main lambda handler file at root level
        main_handler = temp_path / "lambda_function.py"
        with open(main_handler, "w") as f:
            f.write("""
from pii_encryption_lambda.lambda_function import lambda_handler

# Re-export for Lambda runtime
__all__ = ['lambda_handler']
""")
        
        # Create zip file
        zip_path = project_root / "pii-encryption-lambda.zip"
        print(f"Creating zip file: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_path):
                # Skip __pycache__ directories
                dirs[:] = [d for d in dirs if d != '__pycache__']
                
                for file in files:
                    if file.endswith('.pyc'):
                        continue
                    
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(temp_path)
                    zipf.write(file_path, arc_name)
        
        print(f"Deployment package created: {zip_path}")
        print(f"Package size: {zip_path.stat().st_size / (1024*1024):.2f} MB")
        
        return str(zip_path)


def deploy_to_aws(zip_path: str, function_name: str = "pii-encryption-handler"):
    """
    Deploy Lambda function to AWS
    
    Args:
        zip_path: Path to deployment zip file
        function_name: Name of the Lambda function
    """
    try:
        import boto3
        
        lambda_client = boto3.client('lambda')
        
        print(f"Deploying to Lambda function: {function_name}")
        
        # Update function code
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"Function updated successfully!")
        print(f"Function ARN: {response['FunctionArn']}")
        print(f"Runtime: {response['Runtime']}")
        print(f"Handler: {response['Handler']}")
        
        return True
        
    except Exception as e:
        print(f"Deployment failed: {str(e)}")
        return False


def main():
    """Main deployment script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy PII Encryption Lambda")
    parser.add_argument("--function-name", default="pii-encryption-handler",
                       help="Lambda function name")
    parser.add_argument("--package-only", action="store_true",
                       help="Only create package, don't deploy")
    
    args = parser.parse_args()
    
    # Create deployment package
    zip_path = create_deployment_package()
    if not zip_path:
        print("Failed to create deployment package")
        sys.exit(1)
    
    if not args.package_only:
        # Deploy to AWS
        success = deploy_to_aws(zip_path, args.function_name)
        if not success:
            sys.exit(1)
    
    print("Deployment completed successfully!")


if __name__ == "__main__":
    main()