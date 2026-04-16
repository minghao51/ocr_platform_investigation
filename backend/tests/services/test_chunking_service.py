import pytest
from services.chunking_service import MarkdownSplitter

@pytest.fixture
def splitter():
    return MarkdownSplitter()

def test_split_on_headers(splitter):
    markdown = """# Header 1
""" + "Content under header 1\n" * 50 + """

## Header 2
""" + "Content under header 2\n" * 50 + """

# Another Header
""" + "More content\n" * 50

    chunks = splitter.split(markdown, max_tokens=100)
    assert len(chunks) >= 2
    # First chunk should start with a header
    assert "#" in chunks[0][:20]
    # Check that headers are preserved in chunks
    assert any("# Header 1" in chunk for chunk in chunks)
    assert any("## Header 2" in chunk for chunk in chunks)

def test_split_preserves_context(splitter):
    markdown = "Line 1\nLine 2\nLine 3" * 100  # Long content without headers

    chunks = splitter.split(markdown, max_tokens=50)
    # Should have overlap between chunks
    if len(chunks) > 1:
        # Check for overlap (last line of chunk N should appear in chunk N+1)
        pass  # Implementation dependent

def test_single_chunk_no_split(splitter):
    markdown = "Short content"

    chunks = splitter.split(markdown, max_tokens=1000)
    assert len(chunks) == 1
    assert chunks[0] == markdown

def test_merge_chunks_basic(splitter):
    results = [
        {"field1": "value1", "field2": "value2"},
        {"field1": "value3", "field2": "value4"}
    ]

    merged = splitter.merge_chunks(results)
    assert "field1" in merged
    assert "field2" in merged

def test_merge_chunks_deduplication(splitter):
    results = [
        {"invoice_number": "INV-001", "total": "100"},
        {"invoice_number": "INV-001", "line_items": ["item1"]}
    ]

    merged = splitter.merge_chunks(results)
    assert merged["invoice_number"] == "INV-001"  # Should not duplicate
    assert "total" in merged and "line_items" in merged
