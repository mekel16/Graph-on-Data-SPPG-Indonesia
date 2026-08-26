import re
import unicodedata
from typing import Optional


def clean_text(value: Optional[str]) -> str:
    """
    Membersihkan whitespace, newline, dan karakter aneh.
    """
    if value is None:
        return ""

    value = str(value)

    # Normalisasi unicode
    value = unicodedata.normalize("NFKC", value)

    # Ganti newline, tab, dan whitespace berulang
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize_text(value: Optional[str]) -> str:
    """
    Bentuk standar untuk pencarian.
    Contoh:
    ' Kec. Buayan ' -> 'buayan'
    """
    value = clean_text(value).lower()

    # Hilangkan tanda baca tertentu
    value = value.replace(".", "")
    value = value.replace(",", "")
    value = value.replace("-", " ")

    # Hilangkan prefix umum wilayah
    prefixes = [
        "kecamatan ",
        "kec ",
        "kabupaten ",
        "kab ",
        "kota ",
        "provinsi ",
        "prov ",
    ]

    for prefix in prefixes:
        if value.startswith(prefix):
            value = value[len(prefix):]

    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize_province(value: Optional[str]) -> str:
    return normalize_text(value)


def normalize_city(value: Optional[str]) -> str:
    return normalize_text(value)


def normalize_district(value: Optional[str]) -> str:
    return normalize_text(value)


def normalize_village(value: Optional[str]) -> str:
    return normalize_text(value)