"""
Extended dataset adapters for benchmarking.
Adds support for FUNSD and other document types.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import importlib
import sys

# Import HuggingFace datasets FIRST, before local path manipulation
try:
    _hf_datasets = importlib.import_module("datasets")
    hf_load_dataset_fn = _hf_datasets.load_dataset
except (ImportError, AttributeError):
    hf_load_dataset_fn = None

# Now add local benchmarks dir to import local datasets.py
_local_benchmarks_dir = str(Path(__file__).parent)
if _local_benchmarks_dir not in sys.path:
    sys.path.insert(0, _local_benchmarks_dir)

_local_datasets = importlib.import_module("benchmarks.datasets")
BenchmarkSample = _local_datasets.BenchmarkSample
BENCHMARKS_DIR = _local_datasets.BENCHMARKS_DIR
load_cord_samples = _local_datasets.load_cord_samples


# ============================================================================
# FUNSD Dataset (Form Understanding in Noisy Scanned Documents)
# ============================================================================

FUNSD_CACHE_DIR = BENCHMARKS_DIR / "funds"

FUNSD_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "form_type": {
            "type": "string",
            "description": "Type of form (invoice, receipt, etc.)",
        },
        "items": {
            "type": "array",
            "description": "Key-value pairs extracted from the form",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Field name"},
                    "value": {"type": "string", "description": "Field value"},
                },
            },
        },
    },
}


def _load_funds_json_file(json_path: str) -> tuple[str, Dict[str, Any]]:
    """Load a single FUNSD JSON annotation file."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Image path is derived from json filename
    json_name = Path(json_path).stem
    img_rel = f"{json_name}.png"

    # Extract form data
    form_data: Dict[str, Any] = {"items": []}

    form_type = data.get("form_type", "unknown")
    if form_type:
        form_data["form_type"] = form_type

    # Extract key-value pairs from the 'entity' annotations
    for item in data.get("form", []):
        key = item.get("words", [])
        value = item.get("words", [])

        if key:
            key_text = " ".join(w.get("text", "") for w in key)
            value_text = " ".join(w.get("text", "") for w in value)

            if key_text:
                form_data["items"].append(
                    {
                        "key": key_text,
                        "value": value_text,
                    }
                )

    return img_rel, form_data


def load_funds_samples(
    limit: Optional[int] = None,
    data_dir: Optional[str] = None,
    split: str = "train",
) -> List[BenchmarkSample]:
    """
    Load FUNSD dataset samples.

    Args:
        limit: Max samples to return (None = all)
        data_dir: Path to FUNSD data directory
        split: Which split to use — "train" or "test"

    Returns:
        List of BenchmarkSample
    """
    if data_dir is None:
        data_dir = str(FUNSD_CACHE_DIR)

    base = Path(data_dir) / split
    if not base.exists():
        raise FileNotFoundError(f"FUNSD data directory not found: {data_dir}")

    json_dir = base
    img_dir = base

    json_files = sorted(json_dir.glob("*.json"))

    if limit:
        json_files = json_files[:limit]

    samples: List[BenchmarkSample] = []
    for idx, json_file in enumerate(json_files):
        try:
            img_rel, expected = _load_funds_json_file(str(json_file))

            if not expected.get("items"):
                continue

            # Find image
            img_path = str(img_dir / img_rel)
            if not os.path.exists(img_path):
                # Try same directory as json
                img_path = str(json_file.parent / img_rel)
            if not os.path.exists(img_path):
                continue

            samples.append(
                BenchmarkSample(
                    image_path=img_path,
                    expected=expected,
                    schema=FUNSD_SCHEMA,
                    source="funds",
                    sample_index=idx,
                )
            )
        except Exception as e:
            print(f"Warning: Failed to load FUNSD sample {json_file}: {e}")
            continue

    return samples


# ============================================================================
# HuggingFace Invoice Dataset (mychen76/invoices-and-receipts_ocr_v1)
# ============================================================================

HF_INVOICE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "invoice_no": {"type": "string", "description": "Invoice number"},
        "invoice_date": {"type": "string", "description": "Date of issue"},
        "seller": {"type": "string", "description": "Seller name"},
        "client": {"type": "string", "description": "Client name"},
        "seller_tax_id": {"type": "string", "description": "Seller tax ID"},
        "client_tax_id": {"type": "string", "description": "Client tax ID"},
        "iban": {"type": "string", "description": "IBAN"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_desc": {"type": "string", "description": "Item description"},
                    "item_qty": {"type": "number", "description": "Quantity"},
                    "item_net_price": {"type": "number", "description": "Unit price"},
                    "item_net_worth": {"type": "number", "description": "Net worth"},
                    "item_vat": {"type": "number", "description": "VAT amount"},
                    "item_gross_worth": {"type": "number", "description": "Gross worth"},
                },
                "required": ["item_desc", "item_gross_worth"],
            },
        },
        "total_net_worth": {"type": "number", "description": "Total net"},
        "total_vat": {"type": "number", "description": "Total VAT"},
        "total_gross_worth": {"type": "number", "description": "Total gross"},
    },
    "required": ["invoice_no", "total_gross_worth"],
}


def _flatten_invoice_ground_truth(gt_parse: Dict[str, Any]) -> Dict[str, Any]:
    header = gt_parse.get("header", {})
    result: Dict[str, Any] = {}

    for key in ("invoice_no", "invoice_date", "seller", "client", "seller_tax_id", "client_tax_id", "iban"):
        val = header.get(key)
        if val is not None:
            result[key] = val

    items = gt_parse.get("items")
    if items is not None:
        result["items"] = items

    total = gt_parse.get("total", gt_parse.get("summary", {}))
    for key in ("total_net_worth", "total_vat", "total_gross_worth"):
        val = total.get(key)
        if val is not None:
            result[key] = val

    return result


def _parse_python_dict_literal(s: str) -> Dict[str, Any]:
    """Parse a Python dict literal string (single quotes) into a dict."""
    import ast
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return json.loads(s.replace("'", '"'))


def load_invoice_samples(
    limit: Optional[int] = None,
    split: str = "test",
) -> List[BenchmarkSample]:
    if hf_load_dataset_fn is None:
        raise ImportError(
            "The 'datasets' library is required to load the invoice dataset. "
            "Install it with: uv add datasets"
        )

    cache_dir = BENCHMARKS_DIR / "invoices" / "images"
    cache_dir.mkdir(parents=True, exist_ok=True)

    dataset = hf_load_dataset_fn("mychen76/invoices-and-receipts_ocr_v1", split=split)

    samples: List[BenchmarkSample] = []
    max_count = limit if limit else len(dataset)

    for idx, row in enumerate(dataset):
        if len(samples) >= max_count:
            break

        try:
            parsed_data = row.get("parsed_data")
            if not parsed_data:
                continue

            if isinstance(parsed_data, str):
                parsed = _parse_python_dict_literal(parsed_data)
            else:
                parsed = parsed_data

            json_str = parsed.get("json", "")
            if not json_str:
                continue

            if isinstance(json_str, str):
                gt_parse = _parse_python_dict_literal(json_str)
            else:
                gt_parse = json_str

            expected = _flatten_invoice_ground_truth(gt_parse)

            image = row.get("image")
            if image is None:
                continue

            img_path = str(cache_dir / f"invoice_{split}_{idx:05d}.png")
            if not Path(img_path).exists():
                image.save(img_path)

            samples.append(
                BenchmarkSample(
                    image_path=img_path,
                    expected=expected,
                    schema=HF_INVOICE_SCHEMA,
                    source="invoice",
                    sample_index=idx,
                )
            )
        except Exception as e:
            print(f"Warning: Failed to load invoice sample {idx}: {e}")
            continue

    return samples


# ============================================================================
# Invoice Dataset (Simple synthetic invoice data)
# ============================================================================

INVOICE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "invoice_number": {"type": "string"},
        "vendor_name": {"type": "string"},
        "invoice_date": {"type": "string"},
        "due_date": {"type": "string"},
        "total_amount": {"type": "number"},
        "subtotal": {"type": "number"},
        "tax_amount": {"type": "number"},
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit_price": {"type": "number"},
                    "total": {"type": "number"},
                },
            },
        },
    },
}


def load_synthetic_invoice_samples(
    limit: Optional[int] = None,
) -> List[BenchmarkSample]:
    """
    Load synthetic invoice samples for testing.

    This creates mock invoice data for testing when actual invoice
    datasets are not available.

    Args:
        limit: Max samples to return (None = default 10)

    Returns:
        List of BenchmarkSample with synthetic data
    """
    samples: List[BenchmarkSample] = []

    # Sample invoice data
    sample_invoices = [
        {
            "invoice_number": "INV-001",
            "vendor_name": "Acme Corp",
            "invoice_date": "2024-01-15",
            "due_date": "2024-02-15",
            "total_amount": 1500.00,
            "subtotal": 1250.00,
            "tax_amount": 250.00,
            "line_items": [
                {
                    "description": "Widget A",
                    "quantity": 10,
                    "unit_price": 100.00,
                    "total": 1000.00,
                },
                {
                    "description": "Widget B",
                    "quantity": 5,
                    "unit_price": 50.00,
                    "total": 250.00,
                },
            ],
        },
        {
            "invoice_number": "INV-002",
            "vendor_name": "Tech Solutions Inc",
            "invoice_date": "2024-01-20",
            "due_date": "2024-02-20",
            "total_amount": 3500.00,
            "subtotal": 3000.00,
            "tax_amount": 500.00,
            "line_items": [
                {
                    "description": "Server License",
                    "quantity": 1,
                    "unit_price": 2000.00,
                    "total": 2000.00,
                },
                {
                    "description": "Support Contract",
                    "quantity": 1,
                    "unit_price": 1000.00,
                    "total": 1000.00,
                },
            ],
        },
        {
            "invoice_number": "INV-003",
            "vendor_name": "Office Supplies Co",
            "invoice_date": "2024-01-25",
            "due_date": "2024-02-25",
            "total_amount": 450.00,
            "subtotal": 400.00,
            "tax_amount": 50.00,
            "line_items": [
                {
                    "description": "Paper (reams)",
                    "quantity": 10,
                    "unit_price": 15.00,
                    "total": 150.00,
                },
                {
                    "description": "Ink Cartridges",
                    "quantity": 2,
                    "unit_price": 50.00,
                    "total": 100.00,
                },
                {
                    "description": "Desk Organizer",
                    "quantity": 5,
                    "unit_price": 40.00,
                    "total": 200.00,
                },
            ],
        },
    ]

    # Create placeholder image paths (in real use, these would be actual images)
    for idx, invoice_data in enumerate(
        sample_invoices[: limit or len(sample_invoices)]
    ):
        samples.append(
            BenchmarkSample(
                image_path=f"/fake/path/invoice_{idx:03d}.png",
                expected=invoice_data,
                schema=INVOICE_SCHEMA,
                source="synthetic_invoice",
                sample_index=idx,
            )
        )

    return samples


# ============================================================================
# Dataset Registry
# ============================================================================

DATASET_LOADERS: Dict[str, callable] = {
    "cord": load_cord_samples,
    "funds": load_funds_samples,
    "invoice": load_invoice_samples,
    "synthetic_invoice": load_synthetic_invoice_samples,
}


def load_dataset(
    dataset_name: str,
    limit: Optional[int] = None,
    data_dir: Optional[str] = None,
    split: str = "train",
) -> List[BenchmarkSample]:
    """
    Load samples from a registered dataset.

    Args:
        dataset_name: Name of the dataset ("cord", "funds", "synthetic_invoice")
        limit: Max samples to return
        data_dir: Path to dataset directory (if applicable)
        split: Dataset split to use ("train", "test")

    Returns:
        List of BenchmarkSample

    Raises:
        ValueError: If dataset name is unknown
    """
    if dataset_name not in DATASET_LOADERS:
        raise ValueError(
            f"Unknown dataset: {dataset_name}. "
            f"Available datasets: {list(DATASET_LOADERS.keys())}"
        )

    loader = DATASET_LOADERS[dataset_name]

    # Build kwargs based on what the loader accepts
    kwargs = {"limit": limit}
    if data_dir and dataset_name in ["cord", "funds"]:
        kwargs["data_dir"] = data_dir
    if dataset_name in ["cord", "funds"]:
        kwargs["split"] = split
    if dataset_name == "invoice":
        kwargs["split"] = split

    return loader(**kwargs)


def list_available_datasets() -> List[str]:
    """Return list of available dataset names."""
    return list(DATASET_LOADERS.keys())
