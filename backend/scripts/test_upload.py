#!/usr/bin/env python3
"""
Simple Upload Test Script

Tests the file upload endpoint with a local document.
Displays file_id and metadata for verification.

Usage:
    python test_upload.py path/to/document.pdf
    python test_upload.py image.jpg --url http://localhost:8000

Requirements:
    - Backend server running on localhost:8000 (or specified URL)
    - requests library: pip install requests
"""

import argparse
import sys
import os
from pathlib import Path
import requests


def test_upload(file_path: str, api_url: str = "http://localhost:8000"):
    """
    Upload a file to the OCR Platform and display results.

    Args:
        file_path: Path to the file to upload (JPG, PNG, PDF)
        api_url: Base URL of the backend API

    Returns:
        dict: Upload response from API
    """
    # Validate file exists
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)

    # Check file size (max 10MB)
    file_size = file_path_obj.stat().st_size
    max_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_size:
        print(f"❌ Error: File too large ({file_size / 1024 / 1024:.2f}MB). Max size: 10MB")
        sys.exit(1)

    # Determine file type
    file_ext = file_path_obj.suffix.lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    if file_ext not in valid_extensions:
        print(f"❌ Error: Invalid file type '{file_ext}'. Valid types: {', '.join(valid_extensions)}")
        sys.exit(1)

    # Prepare upload
    upload_url = f"{api_url.rstrip('/')}/api/upload/"
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.pdf': 'application/pdf'
    }

    print(f"📤 Uploading file...")
    print(f"   File: {file_path_obj.name}")
    print(f"   Size: {file_size / 1024:.2f} KB")
    print(f"   Type: {file_ext}")
    print(f"   URL: {upload_url}")
    print()

    try:
        # Upload file
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path_obj.name, f, mime_types[file_ext])
            }

            response = requests.post(upload_url, files=files, timeout=30)

        # Check response
        if response.status_code == 200:
            data = response.json()

            print("✅ Upload successful!")
            print()
            print("📋 File Metadata:")
            print(f"   File ID:      {data.get('file_id')}")
            print(f"   File Name:    {data.get('file_name')}")
            print(f"   File Type:    {data.get('file_type')}")
            print(f"   File Size:    {data.get('file_size')} bytes")
            print(f"   File Path:    {data.get('file_path')}")
            print()
            print("💡 Use this file_id for processing:")
            print(f"   --file-id {data.get('file_id')}")

            return data
        else:
            print(f"❌ Upload failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            sys.exit(1)

    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Could not connect to backend at {api_url}")
        print("   Make sure the backend server is running:")
        print("   cd backend && uvicorn main:app --reload --port 8000")
        sys.exit(1)

    except requests.exceptions.Timeout:
        print(f"❌ Error: Request timed out after 30 seconds")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test file upload to OCR Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload a PDF document
  python test_upload.py invoice.pdf

  # Upload an image with custom backend URL
  python test_upload.py receipt.jpg --url http://192.168.1.100:8000

  # Upload and display full response
  python test_upload.py document.png --verbose
        """
    )

    parser.add_argument(
        'file',
        help='Path to the file to upload (JPG, PNG, PDF)'
    )

    parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='Backend API URL (default: http://localhost:8000)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Display full API response'
    )

    args = parser.parse_args()

    # Run upload test
    result = test_upload(args.file, args.url)

    # Display full response if verbose
    if args.verbose:
        import json
        print()
        print("📄 Full API Response:")
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
