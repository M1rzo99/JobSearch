"""Bir xil e'lon turli saytlarda chiqsa, uni bitta deb aniqlash."""
import hashlib
import re
from difflib import SequenceMatcher

_COMPANY_NOISE = re.compile(
    r"\(주\)|㈜|주식회사|\(유\)|유한회사|\(재\)|재단법인|\(사\)|사단법인|co\.?,?\s*ltd\.?|inc\.?|corp\.?|corporation|company",
    re.IGNORECASE,
)
_TITLE_NOISE = re.compile(
    r"\[[^\]]*\]|\([^)]*\)|【[^】]*】|<[^>]*>|채용|모집|구인|급구|신입|경력|정규직|계약직|담당자|및|/|\||-|·",
    re.IGNORECASE,
)
_NON_WORD = re.compile(r"[^\w가-힣]+")


def norm_company(name: str) -> str:
    s = _COMPANY_NOISE.sub("", name or "")
    return _NON_WORD.sub("", s).lower()


def norm_title(title: str) -> str:
    s = _TITLE_NOISE.sub(" ", title or "")
    return _NON_WORD.sub("", s).lower()


def dedup_key(company: str, title: str) -> str:
    raw = f"{norm_company(company)}|{norm_title(title)}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def is_similar(title_a: str, title_b: str, threshold: float = 0.8) -> bool:
    a, b = norm_title(title_a), norm_title(title_b)
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    return SequenceMatcher(None, a, b).ratio() >= threshold
