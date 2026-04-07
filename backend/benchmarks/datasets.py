"""
Dataset adapters for benchmarking.
Downloads and converts public datasets into our benchmark format.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from paths import BENCHMARKS_DIR


@dataclass
class BenchmarkSample:
    """A single benchmark sample with image and ground truth."""
    image_path: str
    expected: Dict[str, Any]
    schema: Dict[str, Any]
    source: str = ""
    sample_index: int = 0


CORD_CACHE_DIR = BENCHMARKS_DIR / "cord"
CORD_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "total": {"type": "number", "description": "Total amount on receipt"},
        "subtotal": {"type": "number", "description": "Subtotal before tax"},
        "tax": {"type": "number", "description": "Tax amount"},
        "discount": {"type": "number", "description": "Discount amount"},
        "date": {"type": "string", "description": "Date of purchase"},
        "time": {"type": "string", "description": "Time of purchase"},
        "store_name": {"type": "string", "description": "Name of the store"},
        "items": {
            "type": "array",
            "description": "Line items on the receipt",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Item name"},
                    "price": {"type": "number", "description": "Item price"},
                    "quantity": {"type": "number", "description": "Item quantity"},
                },
                "required": ["name", "price"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["total", "items"],
}


def _parse_cord_lines(valid_lines: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert CORD valid_line annotations to flat expected output."""
    result: Dict[str, Any] = {}

    # Group words by category
    category_texts: Dict[str, List[str]] = {}
    for line in valid_lines:
        cat = line.get("category", "")
        words = line.get("words", [])
        texts = [w.get("text", "") for w in words if w.get("text", "").strip()]
        if texts:
            category_texts.setdefault(cat, []).extend(texts)

    # Extract totals
    if "total.total_price" in category_texts:
        total_str = "".join(category_texts["total.total_price"]).replace(",", "")
        try:
            result["total"] = float(total_str)
        except ValueError:
            pass

    if "sub_total.subtotal_price" in category_texts:
        sub_str = "".join(category_texts["sub_total.subtotal_price"]).replace(",", "")
        try:
            result["subtotal"] = float(sub_str)
        except ValueError:
            pass

    if "sub_total.tax_price" in category_texts:
        tax_str = "".join(category_texts["sub_total.tax_price"]).replace(",", "")
        try:
            result["tax"] = float(tax_str)
        except ValueError:
            pass

    if "sub_total.discount_price" in category_texts:
        disc_str = "".join(category_texts["sub_total.discount_price"]).replace(",", "")
        try:
            result["discount"] = float(disc_str)
        except ValueError:
            pass

    # Extract menu items — group by group_id
    items_by_group: Dict[int, Dict[str, str]] = {}
    for line in valid_lines:
        cat = line.get("category", "")
        group_id = line.get("group_id", 0)
        words = line.get("words", [])
        text = "".join(w.get("text", "") for w in words if w.get("text", ""))
        if not text:
            continue

        if group_id not in items_by_group:
            items_by_group[group_id] = {}

        if cat == "menu.nm":
            items_by_group[group_id]["name"] = text
        elif cat == "menu.price":
            clean = text.replace(",", "")
            try:
                items_by_group[group_id]["price"] = float(clean)
            except ValueError:
                pass
        elif cat == "menu.cnt":
            try:
                items_by_group[group_id]["quantity"] = float(text)
            except ValueError:
                pass
        elif cat == "menu.sub_nm":
            # Sub-item name, append to existing item or create new
            if "name" in items_by_group[group_id]:
                items_by_group[group_id]["name"] += f" + {text}"
            else:
                items_by_group[group_id]["name"] = text

    items = []
    for gid in sorted(items_by_group.keys()):
        item = items_by_group[gid]
        if "name" in item or "price" in item:
            items.append(item)

    if items:
        result["items"] = items

    return result


def _load_cord_json_file(json_path: str) -> tuple[str, List[Dict[str, Any]]]:
    """Load a single CORD JSON annotation file, return (image_rel_path, valid_lines)."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Image path is derived from json filename
    json_name = Path(json_path).stem  # e.g. "receipt_00000"
    img_rel = f"{json_name}.png"

    valid_lines = data.get("valid_line", [])
    return img_rel, valid_lines


def load_cord_samples(
    limit: Optional[int] = None,
    data_dir: Optional[str] = None,
    split: str = "train",
) -> List[BenchmarkSample]:
    """
    Load CORD dataset samples.

    Args:
        limit: Max samples to return (None = all)
        data_dir: Path to CORD data directory (should contain CORD/ subfolder)
        split: Which split to use — "train", "dev", or "test"

    Returns:
        List of BenchmarkSample
    """
    if data_dir is None:
        data_dir = str(CORD_CACHE_DIR)

    base = Path(data_dir) / "CORD" / split
    if not base.exists():
        # Try without the CORD subfolder
        base = Path(data_dir) / split
    if not base.exists():
        # Try data_dir directly
        base = Path(data_dir)
    if not base.exists():
        raise FileNotFoundError(f"CORD data directory not found: {data_dir}")

    json_dir = base / "json"
    img_dir = base / "image"

    if not json_dir.exists():
        raise FileNotFoundError(f"No json directory found in {base}")

    json_files = sorted(json_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {json_dir}")

    if limit:
        json_files = json_files[:limit]

    samples: List[BenchmarkSample] = []
    for idx, json_file in enumerate(json_files):
        try:
            img_rel, valid_lines = _load_cord_json_file(str(json_file))
            expected = _parse_cord_lines(valid_lines)
            if not expected:
                continue

            # Find image
            img_path = str(img_dir / img_rel)
            if not os.path.exists(img_path):
                # Try same directory as json
                img_path = str(json_file.parent.parent / "image" / img_rel)
            if not os.path.exists(img_path):
                img_path = str(json_file.with_suffix(".png"))
            if not os.path.exists(img_path):
                candidates = list(json_file.parent.parent.glob(f"image/{img_rel}"))
                if candidates:
                    img_path = str(candidates[0])
                else:
                    continue

            samples.append(BenchmarkSample(
                image_path=img_path,
                expected=expected,
                schema=CORD_SCHEMA,
                source="cord",
                sample_index=idx,
            ))
        except Exception as e:
            print(f"Warning: Failed to load CORD sample {json_file}: {e}")
            continue

    return samples
