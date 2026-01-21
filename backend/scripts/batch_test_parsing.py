#!/usr/bin/env python3
"""
Batch Testing Script

Test multiple documents at once for regression testing.
Generates summary report with success/fail rates.

Usage:
    python batch_test_parsing.py ./test_documents/
    python batch_test_parsing.py ./docs/ --schema Invoice --output results.json
    python batch_test_parsing.py ./receipts/ --provider nebius --parallel 3

Requirements:
    - Backend server running on localhost:8000
    - Directory with test documents (JPG, PNG, PDF)
    - At least one VLM provider configured
"""

import argparse
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


SUPPORTED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf']
BUILTIN_SCHEMAS = ["Invoice", "Receipt", "ID Card", "Generic Document"]


def find_documents(directory: Path) -> List[Path]:
    """Find all supported documents in directory."""
    documents = []

    for ext in SUPPORTED_EXTENSIONS:
        documents.extend(directory.rglob(f'*{ext}'))

    return sorted(documents)


def upload_file(file_path: Path, api_url: str) -> Dict[str, Any]:
    """Upload file and return result."""
    upload_url = f"{api_url}/api/upload/"

    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f)}
            response = requests.post(upload_url, files=files, timeout=30)

        if response.status_code == 200:
            return {
                'success': True,
                'file_id': response.json()['file_id'],
                'file_name': file_path.name
            }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}: {response.text}",
                'file_name': file_path.name
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'file_name': file_path.name
        }


def process_document(file_id: str, provider: str, model: str, schema_name: str, api_url: str, timeout: int = 120) -> Dict[str, Any]:
    """Process document and return result."""
    process_url = f"{api_url}/api/process/"

    payload = {
        "file_id": file_id,
        "provider": provider,
        "model": model,
        "schema_name": schema_name
    }

    try:
        # Start processing
        response = requests.post(process_url, json=payload, timeout=10)

        if response.status_code != 200:
            return {
                'success': False,
                'error': f"Failed to start processing: {response.text}",
                'status': 'failed'
            }

        job_id = response.json()['job_id']

        # Poll for completion
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                return {
                    'success': False,
                    'error': f'Timeout after {timeout}s',
                    'status': 'timeout'
                }

            response = requests.get(f"{api_url}/api/process/status/{job_id}", timeout=10)

            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"Failed to check status: {response.text}",
                    'status': 'error'
                }

            job = response.json()
            status = job['status']

            if status in ['success', 'error']:
                processing_time = time.time() - start_time

                result = {
                    'status': status,
                    'processing_time': processing_time,
                    'job_id': job_id
                }

                if status == 'success':
                    result['success'] = True
                    result['data'] = job.get('result')
                else:
                    result['success'] = False
                    result['error'] = job.get('error', 'Unknown error')

                return result

            time.sleep(2)

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'status': 'exception'
        }


def test_single_document(file_path: Path, provider: str, model: str, schema_name: str, api_url: str, timeout: int) -> Dict[str, Any]:
    """Test a single document: upload + process."""

    result = {
        'file_path': str(file_path),
        'file_name': file_path.name,
        'file_size': file_path.stat().st_size
    }

    # Upload
    upload_result = upload_file(file_path, api_url)

    if not upload_result['success']:
        result['success'] = False
        result['error'] = upload_result['error']
        result['status'] = 'upload_failed'
        return result

    file_id = upload_result['file_id']

    # Process
    process_result = process_document(file_id, provider, model, schema_name, api_url, timeout)

    result.update(process_result)

    return result


def print_progress(current: int, total: int, file_name: str = ""):
    """Print progress bar."""
    percentage = (current / total) * 100
    bar_length = 40
    filled = int(bar_length * current / total)
    bar = '█' * filled + '░' * (bar_length - filled)

    print(f"\r[{bar}] {percentage:.0f}% ({current}/{total}) {file_name}", end="", flush=True)


def generate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics from results."""

    total = len(results)
    success = sum(1 for r in results if r['success'])
    failed = total - success

    # Processing times
    times = [r.get('processing_time', 0) for r in results if r.get('processing_time')]
    avg_time = sum(times) / len(times) if times else 0
    max_time = max(times) if times else 0
    min_time = min(times) if times else 0

    # Errors
    errors = {}
    for r in results:
        if not r['success'] and 'error' in r:
            error_type = r['error'].split(':')[0] if ':' in r['error'] else r['error']
            errors[error_type] = errors.get(error_type, 0) + 1

    return {
        'total': total,
        'success': success,
        'failed': failed,
        'success_rate': (success / total * 100) if total > 0 else 0,
        'avg_processing_time': avg_time,
        'max_processing_time': max_time,
        'min_processing_time': min_time,
        'errors': errors
    }


def print_summary(summary: Dict[str, Any]):
    """Print summary report."""

    print("\n\n")
    print("=" * 60)
    print("📊 BATCH TEST SUMMARY")
    print("=" * 60)
    print()

    print(f"Total Documents:     {summary['total']}")
    print(f"✅ Successful:       {summary['success']}")
    print(f"❌ Failed:           {summary['failed']}")
    print(f"📈 Success Rate:     {summary['success_rate']:.1f}%")
    print()

    if summary['avg_processing_time'] > 0:
        print(f"⏱️  Processing Times:")
        print(f"   Average: {summary['avg_processing_time']:.2f}s")
        print(f"   Min:     {summary['min_processing_time']:.2f}s")
        print(f"   Max:     {summary['max_processing_time']:.2f}s")
        print()

    if summary['errors']:
        print("❌ Error Breakdown:")
        for error, count in sorted(summary['errors'].items(), key=lambda x: x[1], reverse=True):
            print(f"   • {error}: {count}")
        print()


def save_results(results: List[Dict[str, Any]], summary: Dict[str, Any], output_path: str):
    """Save results to JSON file."""

    output = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'summary': summary,
        'results': results
    }

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"💾 Results saved to: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch test multiple documents for regression testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all documents in a directory with Invoice schema
  python batch_test_parsing.py ./test_invoices/ --schema Invoice

  # Test with specific provider and save results
  python batch_test_parsing.py ./receipts/ --schema Receipt --provider nebius --output results.json

  # Test with parallel processing (faster for multiple documents)
  python batch_test_parsing.py ./docs/ --schema "Generic Document" --parallel 3

  # Test with custom timeout
  python batch_test_parsing.py ./large_pdfs/ --schema Invoice --timeout 180
        """
    )

    parser.add_argument(
        'directory',
        help='Directory containing test documents'
    )

    parser.add_argument(
        '--schema',
        required=True,
        choices=BUILTIN_SCHEMAS,
        help='Schema to use for parsing'
    )

    parser.add_argument(
        '--provider',
        help='VLM provider (default: first available)'
    )

    parser.add_argument(
        '--model',
        help='Specific model (default: first available)'
    )

    parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='Backend API URL (default: http://localhost:8000)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=120,
        help='Processing timeout per document in seconds (default: 120)'
    )

    parser.add_argument(
        '--parallel',
        type=int,
        default=1,
        help='Number of parallel tests (default: 1, sequential)'
    )

    parser.add_argument(
        '--output',
        help='Save results to JSON file'
    )

    parser.add_argument(
        '--fail-fast',
        action='store_true',
        help='Stop on first failure'
    )

    args = parser.parse_args()

    # Validate directory
    directory = Path(args.directory)
    if not directory.exists():
        print(f"❌ Error: Directory not found: {directory}")
        sys.exit(1)

    # Find documents
    documents = find_documents(directory)

    if not documents:
        print(f"❌ Error: No documents found in {directory}")
        print(f"   Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}")
        sys.exit(1)

    print(f"📂 Found {len(documents)} document(s)")
    print()

    # Configure provider/model
    api_url = args.url.rstrip('/')

    if not args.provider or not args.model:
        response = requests.get(f"{api_url}/api/providers")
        if response.status_code != 200:
            print("❌ Error: Could not fetch providers")
            sys.exit(1)

        providers = response.json()
        if not providers:
            print("❌ Error: No providers configured")
            sys.exit(1)

        provider = args.provider or providers[0]['name']
        model = args.model or providers[0]['models'][0]['id']

        print(f"✅ Using provider: {provider}")
        print(f"✅ Using model: {model}")
        print()
    else:
        provider = args.provider
        model = args.model

    # Run tests
    print("🚀 Starting batch test...")
    print("=" * 60)
    print()

    results = []
    start_time = time.time()

    if args.parallel > 1:
        # Parallel processing
        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            futures = {
                executor.submit(
                    test_single_document,
                    doc, provider, model, args.schema, api_url, args.timeout
                ): doc for doc in documents
            }

            for i, future in enumerate(as_completed(futures), 1):
                doc = futures[future]
                result = future.result()
                results.append(result)

                print_progress(i, len(documents), doc.name)

                if args.fail_fast and not result['success']:
                    print(f"\n❌ Stopping due to failure: {doc.name}")
                    break
    else:
        # Sequential processing
        for i, doc in enumerate(documents, 1):
            print_progress(i, len(documents), doc.name)

            result = test_single_document(doc, provider, model, args.schema, api_url, args.timeout)
            results.append(result)

            if args.fail_fast and not result['success']:
                print(f"\n❌ Stopping due to failure: {doc.name}")
                break

    total_time = time.time() - start_time

    # Generate and print summary
    summary = generate_summary(results)
    summary['total_time'] = total_time
    summary['schema'] = args.schema
    summary['provider'] = provider
    summary['model'] = model

    print_summary(summary)

    print(f"⏱️  Total Time: {total_time:.2f}s")
    print()

    # Save results if requested
    if args.output:
        save_results(results, summary, args.output)

    # Exit with error code if any failed
    if summary['failed'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
