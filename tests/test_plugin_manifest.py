import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ALLOWED_LOGO_SUFFIXES = {".png", ".svg", ".jpg", ".jpeg", ".webp"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _read_logo_dimensions(logo_file: Path) -> tuple[int, int]:
    suffix = logo_file.suffix.lower()
    if suffix == ".png":
        header = logo_file.read_bytes()[:24]
        assert len(header) >= 24, f"PNG file too small: {logo_file}"
        assert header[:8] == PNG_SIGNATURE, f"Invalid PNG signature in {logo_file}"
        assert header[12:16] == b"IHDR", f"Missing IHDR chunk in {logo_file}"
        return struct.unpack(">II", header[16:24])
    if suffix == ".svg":
        tree = ET.parse(logo_file)
        root = tree.getroot()
        assert root.tag.endswith("svg"), "Logo must be a valid SVG root"
        return int(root.attrib.get("width", 0)), int(root.attrib.get("height", 0))
    raise AssertionError(f"Unsupported logo dimension check for suffix: {suffix}")


def test_plugin_manifest_structure():
    manifest_path = REPO_ROOT / "plugin.json"
    assert manifest_path.exists(), "plugin.json does not exist"

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data.get("name") == "agystack"
    assert data.get("displayName") == "agystack"
    assert "version" in data
    assert "description" in data
    assert len(data["description"]) > 10

    prompts = data.get("suggestedPrompts", [])
    assert 1 <= len(prompts) <= 3, f"Expected 1 to 3 suggestedPrompts, found {len(prompts)}"

    author = data.get("author")
    assert isinstance(author, dict), "author should be an object"
    assert "name" in author
    assert "url" in author

    logo_rel = data.get("logo")
    assert isinstance(logo_rel, str) and logo_rel, "logo path missing"
    assert "://" not in logo_rel, f"logo must be a relative path, not a URL: {logo_rel}"
    logo_path = Path(logo_rel)
    assert not logo_path.is_absolute() and ".." not in logo_path.parts, (
        f"logo must be a relative path inside plugin root: {logo_rel}"
    )
    assert logo_path.suffix.lower() in ALLOWED_LOGO_SUFFIXES, (
        f"Unsupported logo extension: {logo_path.suffix}"
    )
    logo_file = REPO_ROOT / logo_path
    assert logo_file.exists(), f"Logo file does not exist at {logo_file}"

    width, height = _read_logo_dimensions(logo_file)
    assert width >= 128 and height >= 128, "Logo dimensions should be at least 128x128"
