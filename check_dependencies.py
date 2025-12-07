#!/usr/bin/env python
"""
Quick script to check if all required dependencies are installed
Run this in your deployment environment to diagnose issues
"""

import sys

required_packages = [
    'django',
    'allauth',
    'guardian',
    'gunicorn',
    'whitenoise',
    'psycopg2',
    'decouple',
    'boto3',
    'storages',
]

print("Python version:", sys.version)
print("\nChecking required packages...\n")

missing = []
for package in required_packages:
    try:
        __import__(package)
        print(f"✓ {package}")
    except ImportError:
        print(f"✗ {package} - MISSING")
        missing.append(package)

if missing:
    print(f"\n❌ Missing packages: {', '.join(missing)}")
    print("\nRun: pip install -r requirements.txt")
    sys.exit(1)
else:
    print("\n✅ All required packages are installed!")
    sys.exit(0)
