"""Bank-specific parsers. Register new parsers in REGISTRY below."""

from __future__ import annotations

from .axis import AxisParser
from .base import BankParser, ParsedRate
from .bob import BankOfBarodaParser
from .canara import CanaraParser
from .hdfc import HDFCParser
from .icici import ICICIParser
from .indian_bank import IndianBankParser
from .pnb import PNBParser
from .sbi import SBIParser
from .union import UnionBankParser

REGISTRY: dict[str, type[BankParser]] = {
    AxisParser.BANK_SLUG: AxisParser,
    SBIParser.BANK_SLUG: SBIParser,
    HDFCParser.BANK_SLUG: HDFCParser,
    ICICIParser.BANK_SLUG: ICICIParser,
    BankOfBarodaParser.BANK_SLUG: BankOfBarodaParser,
    CanaraParser.BANK_SLUG: CanaraParser,
    PNBParser.BANK_SLUG: PNBParser,
    UnionBankParser.BANK_SLUG: UnionBankParser,
    IndianBankParser.BANK_SLUG: IndianBankParser,
}

__all__ = [
    "BankParser",
    "ParsedRate",
    "REGISTRY",
    "AxisParser",
    "SBIParser",
    "HDFCParser",
    "ICICIParser",
    "BankOfBarodaParser",
    "CanaraParser",
    "PNBParser",
    "UnionBankParser",
    "IndianBankParser",
]
