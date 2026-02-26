#!/usr/bin/env python3
"""
Schema Parsing Test Script

Upload a document and parse it with a specific schema definition.
Tests different schema types (Invoice, Receipt, ID Card, Custom).

Usage:
    python test_schema_parsing.py document.pdf --schema Invoice
    python test_schema_parsing.py receipt.jpg --schema Receipt --provider nebius
    python test_schema_parsing.py id.png --schema "ID Card" --model gemini-2.5-flash

Requirements:
    - Backend server running on localhost:8000
    - At least one VLM provider configured (NEBIUS_API_KEY or GEMINI_API_KEY or OPENROUTER_API_KEY)
"""

import argparse
import sys
import time
import json
from pathlib import Path
import requests


# Built-in schema names
BUILTIN_SCHEMAS = ["Invoice", "Receipt", "ID Card", "Generic Document"]


def get_schema_definition(schema_name: str, api_url: str) -> dict:
    """Get schema definition from API."""
    # List schemas to find the schema ID
    response = requests.get(f"{api_url}/api/schemas?is_template=true")

    if response.status_code != 200:
        print("❌ Error: Could not fetch schemas from API")
        sys.exit(1)

    schemas = response.json()
    target_schema = next((s for s in schemas if s["name"] == schema_name), None)

    if not target_schema:
        print(f"❌ Error: Schema '{schema_name}' not found")
        print(f"   Available schemas: {', '.join([s['name'] for s in schemas])}")
        sys.exit(1)

    return target_schema


def upload_file(file_path: str, api_url: str) -> str:
    """Upload file and return file_id."""
    upload_url = f"{api_url}/api/upload/"

    with open(file_path, "rb") as f:
        files = {"file": (Path(file_path).name, f)}
        response = requests.post(upload_url, files=files)

    if response.status_code != 200:
        print(f"❌ Upload failed: {response.text}")
        sys.exit(1)

    return response.json()["file_id"]


def start_processing(
    file_id: str, provider: str, model: str, schema_name: str, api_url: str
) -> int:
    """Start processing and return job_id."""
    process_url = f"{api_url}/api/process/"

    payload = {
        "file_id": file_id,
        "provider": provider,
        "model": model,
        "schema_name": schema_name,
    }

    response = requests.post(process_url, json=payload)

    if response.status_code != 200:
        print(f"❌ Failed to start processing: {response.text}")
        sys.exit(1)

    return response.json()["job_id"]


def poll_job_status(job_id: int, api_url: str, timeout: int = 120) -> dict:
    """Poll job status until completion."""
    start_time = time.time()
    print()
    print("⏳ Processing document...")
    print("   Status:  ", end="", flush=True)

    while True:
        if time.time() - start_time > timeout:
            print(f"\n❌ Error: Processing timeout after {timeout} seconds")
            sys.exit(1)

        response = requests.get(f"{api_url}/api/process/status/{job_id}")

        if response.status_code != 200:
            print(f"\n❌ Error checking status: {response.text}")
            sys.exit(1)

        job = response.json()
        status = job["status"]

        # Update status display
        print(
            f"\r   Status:  {status.upper()} {'.' * ((int(time.time() - start_time) % 3) + 1)}   ",
            end="",
            flush=True,
        )

        if status in ["success", "error"]:
            print(f"\r   Status:  {status.upper()} ✓")
            print()
            return job

        time.sleep(2)


def display_results(job: dict, schema_name: str, verbose: bool = False):
    """Display processing results."""

    # Processing time
    if job.get("processing_time"):
        print(f"⏱️  Processing Time: {job['processing_time']:.2f} seconds")
    print()

    # Success case
    if job["status"] == "success":
        result = job.get("result")

        if not result:
            print("⚠️  Warning: No result data returned")
            return

        print("✅ Processing successful!")
        print()
        print("📊 Extracted Data:")

        if isinstance(result, dict):
            # Pretty print the extracted data
            print(json.dumps(result, indent=2))
        else:
            print(result)

        print()
        print("💡 Tips:")
        print("   - Review extracted fields for accuracy")
        print("   - Adjust schema if fields are missing")
        print("   - Try different models for better results")

    # Error case
    elif job["status"] == "error":
        error = job.get("error", "Unknown error")
        print("❌ Processing failed")
        print(f"   Error: {error}")
        print()
        print("💡 Common fixes:")
        print("   - Check if API key is valid")
        print("   - Try a different provider/model")
        print("   - Ensure document is clear and readable")
        print("   - Check schema definition is valid")

    # Verbose mode: show full job details
    if verbose:
        print()
        print("📄 Full Job Details:")
        print(json.dumps(job, indent=2))


def list_available_providers(api_url: str):
    """List available VLM providers."""
    response = requests.get(f"{api_url}/api/providers")

    if response.status_code != 200:
        print("❌ Error: Could not fetch providers")
        sys.exit(1)

    providers = response.json()

    print("📋 Available Providers:")
    print()

    for provider in providers:
        print(f"🏢 {provider['display_name']} ({provider['name']})")
        print("   Models:")
        for model in provider.get("models", []):
            print(f"      • {model.get('id')} - {model.get('name', 'N/A')}")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test schema parsing with uploaded document",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse an invoice with default provider
  python test_schema_parsing.py invoice.pdf --schema Invoice

  # Parse a receipt with specific provider and model
  python test_schema_parsing.py receipt.jpg --schema Receipt --provider nebius

  # Parse ID card with Gemini 2.5 Flash
  python test_schema_parsing.py id.png --schema "ID Card" --provider gemini --model gemini-2.5-flash

  # List available providers and models
  python test_schema_parsing.py --list-providers
        """,
    )

    parser.add_argument("file", nargs="?", help="Path to document file (JPG, PNG, PDF)")

    parser.add_argument(
        "--schema", choices=BUILTIN_SCHEMAS, help="Schema name to use for parsing"
    )

    parser.add_argument("--provider", help="VLM provider (nebius, gemini, openrouter)")

    parser.add_argument(
        "--model", help="Specific model to use (e.g., gemini-2.5-flash)"
    )

    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Backend API URL (default: http://localhost:8000)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Processing timeout in seconds (default: 120)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Display full job details"
    )

    parser.add_argument(
        "--list-providers",
        action="store_true",
        help="List available providers and models",
    )

    args = parser.parse_args()

    # List providers mode
    if args.list_providers:
        list_available_providers(args.url)
        return

    # Validate required arguments
    if not args.file or not args.schema:
        parser.print_help()
        print(
            "\n❌ Error: Both FILE and --schema are required (unless using --list-providers)"
        )
        sys.exit(1)

    # Validate file exists
    if not Path(args.file).exists():
        print(f"❌ Error: File not found: {args.file}")
        sys.exit(1)

    api_url = args.url.rstrip("/")

    print("🔍 Schema Parsing Test")
    print("=" * 50)
    print(f"   File:     {Path(args.file).name}")
    print(f"   Schema:   {args.schema}")
    print(f"   API URL:  {api_url}")
    print()

    # Get schema definition
    schema = get_schema_definition(args.schema, api_url)
    print(f"✅ Schema found: {schema['name']}")

    # Determine provider and model
    provider = args.provider
    model = args.model

    if not provider or not model:
        # Fetch providers and use first available
        response = requests.get(f"{api_url}/api/providers")
        providers = response.json()

        if not providers:
            print("❌ Error: No providers configured. Please set API keys in .env file")
            sys.exit(1)

        # Use first provider if not specified
        if not provider:
            provider = providers[0]["name"]
            print(f"✅ Using provider: {providers[0]['display_name']}")

        # Use first model if not specified
        if not model:
            model = providers[0]["models"][0]["id"]
            print(f"✅ Using model: {model}")

    print(f"   Provider: {provider}")
    print(f"   Model:    {model}")
    print()

    # Upload file
    print("📤 Step 1: Uploading file...")
    file_id = upload_file(args.file, api_url)
    print(f"✅ File uploaded: {file_id}")
    print()

    # Start processing
    print("⚙️  Step 2: Starting processing...")
    job_id = start_processing(file_id, provider, model, args.schema, api_url)
    print(f"✅ Job started: {job_id}")
    print()

    # Poll for results
    print("⏳ Step 3: Waiting for results...")
    job = poll_job_status(job_id, api_url, args.timeout)

    # Display results
    print("📊 Step 4: Results")
    print("=" * 50)
    display_results(job, args.schema, args.verbose)


if __name__ == "__main__":
    main()
