import pytest

from app.ingestion.validate_upload import UploadValidationError, validate_docx_bytes
from tests.fixtures.gen import minimal_docx_bytes, zip_bytes

MAX = 25 * 1024 * 1024


def test_valid_docx_passes():
    validate_docx_bytes(minimal_docx_bytes(), MAX)


def test_non_zip_rejected():
    with pytest.raises(UploadValidationError) as exc:
        validate_docx_bytes(b"MZ\x90\x00\x03\x00\x00\x00", MAX)
    assert exc.value.code == "not_docx"


def test_truncated_zip_is_corrupt():
    with pytest.raises(UploadValidationError) as exc:
        validate_docx_bytes(minimal_docx_bytes()[:180], MAX)
    assert exc.value.code == "corrupt"


def test_zip_missing_document_xml_is_corrupt():
    data = zip_bytes({"[Content_Types].xml": b"<Types/>"}, include_required=False)
    with pytest.raises(UploadValidationError) as exc:
        validate_docx_bytes(data, MAX)
    assert exc.value.code == "corrupt"


def test_oversize_rejected():
    with pytest.raises(UploadValidationError) as exc:
        validate_docx_bytes(minimal_docx_bytes(), max_bytes=100)
    assert exc.value.code == "too_large"


def test_path_traversal_entry_rejected():
    data = zip_bytes({"../evil.txt": b"x"})
    with pytest.raises(UploadValidationError) as exc:
        validate_docx_bytes(data, MAX)
    assert exc.value.code == "unsafe_zip"


def test_entry_count_cap():
    data = zip_bytes({f"media/{i}.bin": b"0" for i in range(50)})
    with pytest.raises(UploadValidationError) as exc:
        validate_docx_bytes(data, MAX, max_entries=10)
    assert exc.value.code == "unsafe_zip"


def test_uncompressed_size_cap():
    data = zip_bytes({"big.bin": b"A" * 5000})
    with pytest.raises(UploadValidationError) as exc:
        validate_docx_bytes(data, MAX, max_uncompressed=1000)
    assert exc.value.code == "unsafe_zip"
