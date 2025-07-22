#!/usr/bin/env python3
"""
Lambda Folder Cleanup Script
Removes obsolete files and keeps only essential ones
"""

import os
import shutil
from pathlib import Path

def cleanup_lambda_folder():
    """Clean up obsolete files in lambda folder"""
    
    project_root = Path(__file__).parent
    
    print("🧹 LAMBDA FOLDER CLEANUP")
    print("=" * 50)
    
    # Files to DELETE - Obsolete build scripts
    obsolete_build_scripts = [
        "build_amazon_linux.py",
        "build_lambda_compatible.py", 
        "build_no_cryptography.py",
        "build_schema_compatible.py",
        "build_with_prebuilt_libs.py",
        "deploy.py",
        "deploy_lambda_compatible.py",
        "fix_create_user_bug.py",
        "fix_cryptography.py",
        "build_lambda_package.sh",
        "main.py",
        "test_lambda.py"
    ]
    
    # Files to DELETE - Debug scripts
    obsolete_debug_scripts = [
        "check_secrets.py",
        "debug_lambda.py", 
        "simple_health_lambda.py",
        "create_database_schema.sql"
    ]
    
    # ZIP files to DELETE - Keep only the final working one
    obsolete_zip_files = [
        "check-secrets-lambda.zip",
        "debug-lambda.zip",
        "pii-encryption-lambda-EXACT-SCHEMA.zip",
        "pii-encryption-lambda-amazon-linux.zip",
        "pii-encryption-lambda-compatible.zip",
        "pii-encryption-lambda-full.zip",
        "pii-encryption-lambda-level12-only.zip",
        "pii-encryption-lambda-minimal.zip",
        "pii-encryption-lambda-prebuilt.zip",
        "pii-encryption-lambda-schema-compatible.zip",
        "pii-encryption-lambda.zip",
        "simple-health-lambda.zip"
    ]
    
    all_obsolete_files = obsolete_build_scripts + obsolete_debug_scripts + obsolete_zip_files
    
    # Count files before cleanup
    total_files_before = len(list(project_root.glob("*")))
    
    print(f"📊 Found {total_files_before} files total")
    print(f"🗑️  Will delete {len(all_obsolete_files)} obsolete files")
    
    # Delete obsolete files
    deleted_count = 0
    not_found_count = 0
    
    for file_name in all_obsolete_files:
        file_path = project_root / file_name
        
        if file_path.exists():
            if file_path.is_file():
                os.remove(file_path)
                print(f"  ❌ Deleted: {file_name}")
                deleted_count += 1
            else:
                print(f"  ⚠️  Skipped (not a file): {file_name}")
        else:
            not_found_count += 1
    
    # Show what's kept
    print(f"\n✅ CLEANUP COMPLETE")
    print(f"   Deleted: {deleted_count} files")
    print(f"   Not found: {not_found_count} files")
    
    # List remaining files
    remaining_files = sorted([f.name for f in project_root.iterdir() if f.is_file()])
    print(f"\n📋 REMAINING FILES ({len(remaining_files)}):")
    
    essential_files = [
        "lambda_function_generated.py",
        "pii-encryption-lambda-FINAL-FIXED.zip", 
        "introspect_schema.py",
        "database_schema.json",
        "pyproject.toml",
        "uv.lock",
        "README.md"
    ]
    
    useful_files = [
        "debug_user_data.py",
        "create_final_package.py"
    ]
    
    for file_name in remaining_files:
        if file_name in essential_files:
            print(f"  ✅ {file_name} (essential)")
        elif file_name in useful_files:
            print(f"  🔧 {file_name} (useful)")
        else:
            print(f"  📄 {file_name}")
    
    # Show remaining directories
    remaining_dirs = [d.name for d in project_root.iterdir() if d.is_dir()]
    if remaining_dirs:
        print(f"\n📁 DIRECTORIES ({len(remaining_dirs)}):")
        for dir_name in remaining_dirs:
            print(f"  📁 {dir_name}/")
    
    print(f"\n🎯 RESULT:")
    print(f"   Before: {total_files_before} files")
    print(f"   After:  {len(remaining_files)} files")
    print(f"   Cleaned: {deleted_count} obsolete files")
    
    print(f"\n💡 KEY FILES TO USE:")
    print(f"   📦 Lambda Package: pii-encryption-lambda-FINAL-FIXED.zip")
    print(f"   🐍 Source Code: lambda_function_generated.py")
    print(f"   📋 Schema Info: database_schema.json")

def main():
    """Main function - auto cleanup"""
    
    print("⚠️  Cleaning up obsolete files:")
    print("   - Old build scripts")
    print("   - Debug scripts") 
    print("   - Failed ZIP packages")
    print("   - Temporary files")
    
    cleanup_lambda_folder()

if __name__ == "__main__":
    main()