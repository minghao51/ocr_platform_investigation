from unittest.mock import patch

from services.processors.factory import ProcessorFactory


def test_hybrid_pdf_uses_hybrid_processor():
    factory = ProcessorFactory()

    with patch(
        "services.processors.hybrid.HybridProcessor", autospec=True
    ) as hybrid_cls:
        hybrid_instance = object()
        hybrid_cls.return_value = hybrid_instance

        result = factory.get_processor("hybrid", "pdf")

    assert result is hybrid_instance
    hybrid_cls.assert_called_once()


def test_hybrid_non_pdf_falls_back_to_vision():
    factory = ProcessorFactory()

    with patch(
        "services.processors.factory.VisionProcessor", autospec=True
    ) as vision_cls:
        vision_instance = object()
        vision_cls.return_value = vision_instance

        result = factory.get_processor("hybrid", "docx")

    assert result is vision_instance
    vision_cls.assert_called_once()


def test_docling_parse_uses_dedicated_processor():
    factory = ProcessorFactory()

    with patch(
        "services.processors.factory.DoclingParseProcessor", autospec=True
    ) as parse_cls:
        parse_instance = object()
        parse_cls.return_value = parse_instance

        result = factory.get_processor("docling-parse", "pdf")

    assert result is parse_instance
    parse_cls.assert_called_once()


def test_transcription_uses_dedicated_processor():
    factory = ProcessorFactory()

    with patch(
        "services.processors.factory.TranscriptionProcessor", autospec=True
    ) as transcription_cls:
        transcription_instance = object()
        transcription_cls.return_value = transcription_instance

        result = factory.get_processor("transcription", "document")

    assert result is transcription_instance
    transcription_cls.assert_called_once()
