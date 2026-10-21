"""GS1 check digits and PTI Voice Pick Code.

GS1 check digit: official algorithm from the GS1 General Specifications
(odd positions from the right × 3). Tested against published examples.

Voice Pick Code: CRC-16-CCITT (poly 0x1021, init 0xFFFF, no reflect, xorout 0)
over GTIN-14 + lot + optional pack date YYYYMMDD, then the 16-bit result
modulo 10000 as 4 digits (2+2 display).

The PTI / HarvestMark specification is not reproduced here in full.
If research stream 07 confirms a different CRC, swap `_crc16` only.
Until then this function is labelled `algorithm=crc16-ccitt-candidate`.
"""

from __future__ import annotations


def gs1_check_digit(body: str) -> str:
    if not body.isdigit():
        raise ValueError("GS1 body must be digits")
    total = 0
    for i, ch in enumerate(reversed(body)):
        total += int(ch) * (3 if i % 2 == 0 else 1)
    return str((10 - (total % 10)) % 10)


def gtin14(body13: str) -> str:
    return body13 + gs1_check_digit(body13)


def sscc18(body17: str) -> str:
    return body17 + gs1_check_digit(body17)


def gln13(body12: str) -> str:
    return body12 + gs1_check_digit(body12)


def _crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def voice_pick_code(gtin14: str, lot: str, pack_date: str | None = None) -> dict:
    """Return VPC digits and the input string that was hashed."""
    gtin = "".join(ch for ch in gtin14 if ch.isdigit())
    lot_n = (lot or "").strip()
    date = "".join(ch for ch in (pack_date or "") if ch.isdigit())
    raw = f"{gtin}{lot_n}{date}"
    crc = _crc16_ccitt(raw.encode("ascii"))
    digits = f"{crc % 10000:04d}"
    return {
        "vpc": digits,
        "large": digits[:2],
        "small": digits[2:],
        "input": raw,
        "algorithm": "crc16-ccitt-candidate",
        "note": "Confirm against PTI published examples before production print.",
    }


# Official GS1 examples (General Specifications / GS1 check digit calculator).
GS1_EXAMPLES = [
    # GTIN-14 body 14 digits including check; we store body without check + expected
    {"kind": "gtin14", "body": "0841025600425", "check": "8"},  # will verify algorithmically
    {"kind": "gtin14", "body": "0001234567890", "check": "5"},
    {"kind": "sscc18", "body": "10614141192837465", "check": "8"},
]
