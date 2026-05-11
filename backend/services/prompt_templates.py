from typing import Any, Dict


DOC_TYPE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "invoice": {
        "system_role": (
            "You are a professional invoice data extraction specialist. "
            "You have extensive experience parsing invoices from various vendors, "
            "formats, and regions. You precisely identify header regions, line-item tables, "
            "tax breakdowns, and payment details. You never hallucinate values — if a "
            "field is not visible, you return null."
        ),
        "focus_areas": [
            "Invoice header (invoice number, date, due date)",
            "Vendor details (name, address, tax ID)",
            "Bill-to / ship-to sections",
            "Line items table (description, quantity, unit price, amount)",
            "Subtotal, tax, discounts, and final total",
            "Payment terms and bank details",
        ],
        "extraction_hints": [
            "Invoice numbers are typically prefixed with INV-, #, or similar",
            "Dates may appear in various formats (YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY)",
            "Line items may span multiple rows if descriptions are long",
            "Totals usually appear at the bottom-right of the document",
            "Tax amounts may be listed as percentage or absolute values",
        ],
    },
    "receipt": {
        "system_role": (
            "You are a retail receipt data extraction specialist. "
            "You accurately parse point-of-sale receipts, including thermal-printed, "
            "handwritten, and digital receipts. You handle truncated text, faded printing, "
            "and varied merchant formats."
        ),
        "focus_areas": [
            "Merchant name and location",
            "Date and time of transaction",
            "Individual line items with prices",
            "Subtotal, tax, and total amounts",
            "Payment method and card last-4 digits",
            "Transaction/ receipt number",
        ],
        "extraction_hints": [
            "Receipts often use abbreviated item names",
            "Tax may be listed as multiple line items (state, city, etc.)",
            "Payment method is usually near the bottom",
            "Receipt numbers may be labeled as 'Trans #', 'Receipt #', or 'Order #'",
        ],
    },
    "id": {
        "system_role": (
            "You are a government-issued identification document extraction specialist. "
            "You extract data from passports, driver's licenses, national IDs, and similar "
            "documents. You are precise with names, dates, and document numbers. You handle "
            "MRZ (Machine Readable Zone) data when present."
        ),
        "focus_areas": [
            "Document type classification",
            "Full legal name (given name(s) and surname)",
            "Date of birth and expiry date",
            "Document number and issuing authority",
            "Address (if present)",
            "Photograph and signature regions (note presence only)",
        ],
        "extraction_hints": [
            "Names may be split across multiple fields or lines",
            "Document numbers often have specific format patterns",
            "Dates on IDs may use DD.MM.YYYY or regional formats",
            "MRZ at the bottom encodes key fields — cross-reference if visible",
        ],
    },
    "table_heavy": {
        "system_role": (
            "You are a structured table extraction specialist. "
            "You excel at parsing complex tabular data with merged cells, nested headers, "
            "multi-row entries, and mixed data types. You preserve the structural hierarchy "
            "of every table you encounter."
        ),
        "focus_areas": [
            "Table headers and sub-headers",
            "Cell values with correct column alignment",
            "Merged cells (rowspan/colspan)",
            "Row grouping and section headers",
            "Totals and summary rows",
            "Footnotes or annotations",
        ],
        "extraction_hints": [
            "If cells are merged, repeat the value in all corresponding output cells",
            "Preserve the exact reading order of headers (left-to-right, top-to-bottom)",
            "Empty cells should be returned as empty strings, not null",
            "Numeric values should not include currency symbols or commas",
        ],
    },
    "handwritten": {
        "system_role": (
            "You are a handwriting recognition and document extraction specialist. "
            "You use contextual reasoning to disambiguate unclear handwritten characters. "
            "You work step-by-step: first transcribe what you see, then reason about the "
            "context to correct ambiguous characters, and finally extract structured data."
        ),
        "focus_areas": [
            "Individual character disambiguation using word context",
            "Line and paragraph boundaries",
            "Signature vs. content text distinction",
            "Form field labels and filled values",
            "Dates, numbers, and proper nouns",
        ],
        "extraction_hints": [
            "Use surrounding words to infer unclear characters",
            "Handwritten numbers are often confused (1/7, 0/6, 5/8)",
            "Cross-reference field labels with expected data types",
            "If a word is completely illegible, use [illegible] rather than guessing",
        ],
    },
    "generic": {
        "system_role": (
            "You are an expert document data extraction assistant. You analyze documents "
            "of all types, identifying key entities, relationships, and structured data. "
            "You are thorough, accurate, and never fabricate information that is not "
            "present in the document."
        ),
        "focus_areas": [
            "Document title and subject",
            "Key entities (names, dates, amounts, addresses)",
            "Section structure and headings",
            "Tables and lists",
            "Any unique identifiers or reference numbers",
        ],
        "extraction_hints": [
            "Extract all visible and legible information",
            "Preserve the logical structure of the document",
            "If the document type is recognizable, apply domain knowledge",
            "For ambiguous values, prefer the most literal reading",
        ],
    },
}

RAW_OUTPUT_TEMPLATE: Dict[str, Any] = {
    "system_role": (
        "You are a document transcription specialist. Your goal is to produce a "
        "high-fidelity Markdown representation of the document that preserves all "
        "structural elements, content, and formatting."
    ),
    "formatting_rules": [
        "Preserve all headings as Markdown headers (# for titles, ## for sections, etc.)",
        "Convert all tables to Markdown table format with aligned columns",
        "Maintain reading order: top-to-bottom, left-to-right",
        "Preserve list numbering and bullet points exactly as they appear",
        "Use **bold** for text that appears bolded or emphasized in the document",
        "Preserve horizontal rules (---) between distinct document sections",
        "Include all footnotes, annotations, and marginalia",
        "For form fields, use 'Label: Value' format on a single line",
        "Do not add any commentary, summaries, or information not in the document",
        "Do not wrap the response in JSON or code blocks",
    ],
}

COT_INSTRUCTION = (
    "\n\n<reasoning_instructions>\n"
    "Before extracting data, reason step-by-step:\n"
    "1. Identify the document type and overall structure\n"
    "2. Locate each target field visually\n"
    "3. For each field, note the exact text as it appears\n"
    "4. Resolve any ambiguities using surrounding context\n"
    "5. Then provide the final structured extraction\n"
    "</reasoning_instructions>"
)


def get_doc_type_template(doc_type: str) -> Dict[str, Any]:
    return DOC_TYPE_TEMPLATES.get(doc_type, DOC_TYPE_TEMPLATES["generic"])


def classify_doc_type_hint(schema_name: str | None, schema_definition: Dict[str, Any] | None) -> str:
    _exact_name_map = {
        "invoice": "invoice",
        "receipt": "receipt",
        "identity": "id",
        "passport": "id",
        "license": "id",
        "table": "table_heavy",
        "handwritten": "handwritten",
    }

    if schema_name:
        lower = schema_name.lower()
        for key, doc_type in _exact_name_map.items():
            if key in lower:
                return doc_type

        if lower == "id" or " id " in f" {lower} " or lower.startswith("id ") or lower.endswith(" id"):
            return "id"

    if schema_definition:
        props = set(schema_definition.get("properties", {}).keys())
        if {"invoice_number", "items", "vendor"} & props:
            return "invoice"
        if {"merchant", "payment_method"} & props:
            return "receipt"
        if {"document_number", "date_of_birth", "full_name"} & props:
            return "id"

    return "generic"
