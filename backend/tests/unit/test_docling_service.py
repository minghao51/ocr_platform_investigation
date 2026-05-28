import pytest
from services.docling_service import DoclingService


@pytest.fixture
def docling_service():
    return DoclingService(disable_ocr=True)


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a searchable PDF for testing."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph
    except ImportError:
        pytest.skip("reportlab not installed")

    file_path = tmp_path / "sample.pdf"
    doc = SimpleDocTemplate(str(file_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Test Document", styles["Heading1"]),
        Paragraph("This is test content.", styles["Normal"]),
    ]
    doc.build(story)
    return str(file_path)


def test_parse_searchable_pdf(docling_service, sample_pdf):
    """Test parsing a searchable PDF."""
    result = docling_service.parse_document(sample_pdf)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "#" in result or len(result.strip()) > 0


def test_is_text_searchable(docling_service, sample_pdf):
    """Test the text searchable detection."""
    is_searchable = docling_service._is_text_searchable(sample_pdf)
    assert isinstance(is_searchable, bool)


def test_parse_with_page_range(docling_service, sample_pdf):
    """Test parsing with page range."""
    result = docling_service.parse_document(sample_pdf, page_range=(1, 2))
    assert isinstance(result, str)
    full_result = docling_service.parse_document(sample_pdf)
    assert len(result) <= len(full_result)


def test_force_ocr_flag(docling_service, sample_pdf):
    """Test force_ocr flag."""
    result_normal = docling_service.parse_document(sample_pdf, force_ocr=False)
    assert isinstance(result_normal, str)

    result_forced = docling_service.parse_document(sample_pdf, force_ocr=True)
    assert isinstance(result_forced, str)


def test_parse_non_pdf_file(docling_service, tmp_path):
    """Test handling of non-PDF files."""
    text_file = tmp_path / "test.txt"
    text_file.write_text("This is a text file")

    with pytest.raises(Exception):
        docling_service.parse_document(str(text_file))


def test_batch_processing_helper(docling_service, sample_pdf):
    """Test the batch processing helper method."""
    pdf_paths = [sample_pdf, sample_pdf]

    results = docling_service.parse_documents_batch(pdf_paths)
    assert len(results) == 2
    assert all(isinstance(result, str) for result in results)


def test_batch_processing_with_invalid_file(docling_service, sample_pdf, tmp_path):
    """Test batch processing with mix of valid and invalid files."""
    invalid_file = tmp_path / "invalid.txt"
    invalid_file.write_text("Not a PDF")

    results = docling_service.parse_documents_batch([sample_pdf, str(invalid_file)])
    assert len(results) == 2
    assert isinstance(results[0], str)
    assert results[1] is None
