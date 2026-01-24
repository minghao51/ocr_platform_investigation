#!/usr/bin/env python3
"""
Document Classifier Test Script

Test the automatic document classification and pipeline routing.
This script analyzes PDFs and recommends the optimal processing pipeline.

Usage:
    python test_document_classifier.py document.pdf
    python test_document_classifier.py ./invoices/ --batch
    python test_document_classifier.py scanned.pdf --verbose

Requirements:
    - PyMuPDF installed (pip install pymupdf)
    - Sample PDF documents for testing
"""

import argparse
import sys
from pathlib import Path
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.document_classifier import DocumentClassifier


def test_single_document(file_path: Path, verbose: bool = False):
    """Test classification of a single document"""

    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}")
        return False

    print(f"🔍 Analyzing: {file_path.name}")
    print("=" * 60)

    try:
        classifier = DocumentClassifier()
        analysis = classifier.analyze_document(str(file_path))

        # Display results
        print(f"\n📊 Classification Results:")
        print(f"   Document Type:     {analysis.type.upper()}")
        print(f"   Has Text Layer:    {analysis.has_text_layer}")
        print(f"   Complexity Score:  {analysis.complexity_score}/100")
        print(f"   Text Density:      {analysis.text_density:.1f} chars/page")
        print(f"   Page Count:        {analysis.page_count}")
        print(f"   Has Tables:        {analysis.has_tables}")
        print(f"   Has Images:        {analysis.has_images}")
        print()

        print(f"🎯 Recommended Pipeline: {analysis.recommended_pipeline.upper()}")
        print(f"   Confidence: {analysis.confidence:.2%}")
        print()

        print(f"💡 Reasoning:")
        print(f"   {analysis.reasoning}")
        print()

        # Verbose mode
        if verbose:
            print("📄 Full Analysis Details:")
            print(json.dumps({
                "type": analysis.type,
                "has_text_layer": analysis.has_text_layer,
                "complexity_score": analysis.complexity_score,
                "recommended_pipeline": analysis.recommended_pipeline,
                "confidence": analysis.confidence,
                "text_density": analysis.text_density,
                "page_count": analysis.page_count,
                "has_tables": analysis.has_tables,
                "has_images": analysis.has_images,
                "reasoning": analysis.reasoning
            }, indent=2))
            print()

        # Performance recommendations
        print("⚡ Expected Performance:")
        if analysis.recommended_pipeline == "text":
            print("   ✅ Speed: <0.5s (87x faster than VLM)")
            print("   ✅ Cost: ~90% cheaper than VLM processing")
            print("   ✅ Accuracy: 95-98% for digital PDFs")
        elif analysis.recommended_pipeline == "vision":
            print("   ⚠️  Speed: 3-10s (VLM processing)")
            print("   ⚠️  Cost: Higher (VLM API calls)")
            print("   ✅ Accuracy: 95%+ for complex/scanned docs")
        elif analysis.recommended_pipeline == "hybrid":
            print("   ⚡ Speed: 1-3s (balanced approach)")
            print("   ⚡ Cost: Moderate (OCR base + VLM refinement)")
            print("   ✅ Accuracy: 96-98% (hybrid approach)")
        print()

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_batch(directory: Path, verbose: bool = False):
    """Test classification of all PDFs in a directory"""

    pdfs = list(directory.rglob("*.pdf"))

    if not pdfs:
        print(f"❌ No PDF files found in {directory}")
        return False

    print(f"📂 Found {len(pdfs)} PDF(s) in {directory}")
    print()

    results = {
        "text": 0,
        "vision": 0,
        "hybrid": 0,
        "total": len(pdfs)
    }

    for i, pdf in enumerate(pdfs, 1):
        print(f"[{i}/{len(pdfs)}] ", end="")

        if test_single_document(pdf, verbose):
            # Get recommendation
            classifier = DocumentClassifier()
            analysis = classifier.analyze_document(str(pdf))
            results[analysis.recommended_pipeline] += 1

        print("-" * 60)
        print()

    # Summary
    print("=" * 60)
    print("📊 BATCH SUMMARY")
    print("=" * 60)
    print(f"Total Documents:     {results['total']}")
    print(f"Text Pipeline:       {results['text']} ({results['text']/results['total']*100:.1f}%)")
    print(f"Vision Pipeline:     {results['vision']} ({results['vision']/results['total']*100:.1f}%)")
    print(f"Hybrid Pipeline:     {results['hybrid']} ({results['hybrid']/results['total']*100:.1f}%)")
    print()

    # Cost/speed analysis
    print("💰 Expected Impact (vs all-VLM approach):")
    if results['text'] > 0:
        print(f"   • Fast text extraction: {results['text']} docs")
        print(f"     → ~87x faster, ~90% cost savings")

    if results['vision'] > 0:
        print(f"   • VLM processing: {results['vision']} docs")
        print(f"     → Highest accuracy for complex/scanned docs")

    if results['hybrid'] > 0:
        print(f"   • Hybrid processing: {results['hybrid']} docs")
        print(f"     → Balanced speed, accuracy, and cost")

    print()

    return True


def test_quick_check(file_path: Path):
    """Test the ultra-fast quick check method"""

    print(f"⚡ Quick Check: {file_path.name}")
    print("-" * 60)

    try:
        classifier = DocumentClassifier()
        result = classifier.quick_check(str(file_path))

        if result == "text":
            print("✅ Result: TEXT pipeline recommended")
            print("   → Document has extractable text layer")
            print("   → Use pdfplumber + LLM for fast, cheap processing")
        elif result == "vision":
            print("✅ Result: VISION pipeline recommended")
            print("   → Document appears to be scanned/image-based")
            print("   → Use VLM for best accuracy")
        else:
            print("⚠️  Result: Unable to determine")

        print()
        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Test document classification and auto-routing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Classify a single PDF
  python test_document_classifier.py invoice.pdf

  # Batch classify all PDFs in a directory
  python test_document_classifier.py ./documents/ --batch

  # Quick check (ultra-fast triage)
  python test_document_classifier.py document.pdf --quick

  # Verbose output with full details
  python test_document_classifier.py complex.pdf --verbose

  # Batch mode with verbose output
  python test_document_classifier.py ./test_pdfs/ --batch --verbose
        """
    )

    parser.add_argument(
        'path',
        help='Path to PDF file or directory'
    )

    parser.add_argument(
        '--batch',
        action='store_true',
        help='Batch mode: process all PDFs in directory'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick check mode (ultra-fast triage)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output with full analysis details'
    )

    args = parser.parse_args()

    path = Path(args.path)

    if not path.exists():
        print(f"❌ Error: Path not found: {path}")
        sys.exit(1)

    print("📋 Document Classifier Test")
    print("=" * 60)
    print()

    # Quick check mode
    if args.quick:
        if not path.is_file():
            print("❌ Error: --quick mode requires a single file")
            sys.exit(1)

        success = test_quick_check(path)
        sys.exit(0 if success else 1)

    # Batch mode
    if args.batch:
        if not path.is_dir():
            print("❌ Error: --batch mode requires a directory")
            sys.exit(1)

        success = test_batch(path, args.verbose)
        sys.exit(0 if success else 1)

    # Single file mode
    if path.is_file():
        if path.suffix.lower() != '.pdf':
            print("❌ Error: Only PDF files are supported")
            sys.exit(1)

        success = test_single_document(path, args.verbose)
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Error: {path} is not a file (use --batch for directories)")
        sys.exit(1)


if __name__ == '__main__':
    main()
