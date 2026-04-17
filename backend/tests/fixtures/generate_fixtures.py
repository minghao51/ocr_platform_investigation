#!/usr/bin/env python3
"""
Generate test fixtures for Phase 1 E2E tests.

This script creates sample documents for testing:
- sample.docx
- sample.pptx
- large_pdf.pdf (50+ pages)
- searchable.pdf
- image_only.pdf
"""

import importlib.util
import sys
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []

    if importlib.util.find_spec("docx") is None:
        missing.append("python-docx")

    if importlib.util.find_spec("pptx") is None:
        missing.append("python-pptx")

    if importlib.util.find_spec("reportlab") is None:
        missing.append("reportlab")

    if missing:
        print("Missing required dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstall them with:")
        print(f"  pip install {' '.join(missing)}")
        return False

    return True


def create_sample_docx(output_path):
    """Create a sample DOCX file."""
    from docx import Document

    doc = Document()
    doc.add_heading("Test Document", level=1)
    doc.add_paragraph("This is a test paragraph for DOCX parsing.")
    doc.add_paragraph("Another paragraph with some content.")

    doc.add_heading("Section 1", level=2)
    doc.add_paragraph("Content for section 1 with some details.")

    doc.add_heading("Section 2", level=2)
    doc.add_paragraph("Content for section 2 with more information.")

    doc.save(output_path)
    print(f"Created: {output_path}")


def create_sample_pptx(output_path):
    """Create a sample PPTX file."""
    from pptx import Presentation

    prs = Presentation()

    # Add title slide
    title_slide = prs.slides.add_slide(prs.slide_layouts[0])
    title = title_slide.shapes.title
    subtitle = title_slide.placeholders[1]
    title.text = "Test Presentation"
    subtitle.text = "E2E Testing for Phase 1"

    # Add content slide
    content_slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = content_slide.shapes.title
    title.text = "Content Slide"
    body = content_slide.placeholders[1]
    text_frame = body.text_frame
    text_frame.text = "This is test content for PPTX parsing."

    # Add another content slide
    content_slide2 = prs.slides.add_slide(prs.slide_layouts[1])
    title = content_slide2.shapes.title
    title.text = "Another Slide"
    body = content_slide2.placeholders[1]
    text_frame = body.text_frame
    text_frame.text = "Additional content for testing purposes."

    prs.save(output_path)
    print(f"Created: {output_path}")


def create_searchable_pdf(output_path):
    """Create a searchable PDF file."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph

    doc = SimpleDocTemplate(str(output_path), pagesize=letter)

    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("Searchable PDF Document", styles["Heading1"]))
    story.append(
        Paragraph(
            "This is a test paragraph for searchable PDF parsing.", styles["Normal"]
        )
    )
    story.append(
        Paragraph("Another paragraph with searchable text content.", styles["Normal"])
    )
    story.append(Paragraph("This PDF should be parsed without OCR.", styles["Normal"]))

    doc.build(story)
    print(f"Created: {output_path}")


def create_image_only_pdf(output_path):
    """Create an image-only PDF for testing OCR."""
    from PIL import Image, ImageDraw, ImageFont

    # Create image with text
    img = Image.new("RGB", (800, 600), color="white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    except Exception:
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except Exception:
            font = ImageFont.load_default()

    draw.text((50, 50), "Image-Only PDF", fill="black", font=font)
    draw.text((50, 100), "This text is embedded in an image", fill="black", font=font)
    draw.text(
        (50, 150), "OCR is required to extract this text", fill="black", font=font
    )

    # Save as PDF
    img.save(output_path, "PDF")
    print(f"Created: {output_path}")


def create_large_pdf(output_path, num_pages=50):
    """Create a large PDF (50+ pages) for testing chunking."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak

    doc = SimpleDocTemplate(str(output_path), pagesize=letter)

    styles = getSampleStyleSheet()
    story = []

    # Create pages with substantial content
    for i in range(num_pages):
        story.append(Paragraph(f"Chapter {i + 1}", styles["Heading1"]))
        story.append(
            Paragraph(
                f"This is the content for chapter {i + 1}. " * 20, styles["Normal"]
            )
        )
        story.append(
            Paragraph(
                f"Additional details for section {i + 1}. " * 10, styles["Normal"]
            )
        )
        if i < num_pages - 1:
            story.append(PageBreak())

    doc.build(story)
    print(f"Created: {output_path} ({num_pages} pages)")


def main():
    """Main function to generate all fixtures."""
    print("Generating Phase 1 E2E test fixtures...")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Get output directory
    script_dir = Path(__file__).parent
    fixtures_dir = script_dir

    # Ensure fixtures directory exists
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    # Generate fixtures
    try:
        create_sample_docx(fixtures_dir / "sample.docx")
        create_sample_pptx(fixtures_dir / "sample.pptx")
        create_searchable_pdf(fixtures_dir / "searchable.pdf")
        create_image_only_pdf(fixtures_dir / "image_only.pdf")
        create_large_pdf(fixtures_dir / "large_pdf.pdf", num_pages=50)

        print("\n✓ All fixtures generated successfully!")
        print(f"Fixture directory: {fixtures_dir}")

        # List generated files
        print("\nGenerated files:")
        for file_path in fixtures_dir.glob("*.*"):
            if file_path.is_file() and file_path.name != "generate_fixtures.py":
                size = file_path.stat().st_size
                print(f"  - {file_path.name} ({size:,} bytes)")

    except Exception as e:
        print(f"\n✗ Error generating fixtures: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
