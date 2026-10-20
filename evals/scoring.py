"""Scoring helpers for the audit eval: find numbers, dates and refusals in an answer.

Same rules as the CDC dashboard eval (https://github.com/NeelVadlamudi/cdc-outbreak-dashboard),
copied so this eval runs on its own. Changing them changes the scores.
"""

import json
import re
from datetime import datetime
from pathlib import Path

REFUSAL_PATTERNS = [
    r"\bnot (?:available|covered|in (?:the|my) data)\b",
    r"\bdoes(?:n't| not) (?:cover|include|contain|have)\b",
    r"\bdo(?:n't| not) have\b",
    r"\bno data\b",
    r"\bcan(?:not|'t)\b",
    r"\bunable to\b",
    r"\bcould not (?:verify|find)\b",
    r"\bisn't (?:available|tracked)\b",
    r"\boutside (?:the|my) data\b",
]
_REFUSAL = re.compile("|".join(REFUSAL_PATTERNS), re.IGNORECASE)

_MONTHS = ("january february march april may june july august september "
           "october november december").split()
_DATE_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b"
    r"|\b(?:" + "|".join(m[:3] for m in _MONTHS) + r")[a-z]*\.? \d{1,2}(?:st|nd|rd|th)?,? \d{4}\b"
    r"|\b\d{1,2}/\d{1,2}/\d{2,4}\b",
    re.IGNORECASE,
)
_NUM_RE = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?")
# Names that contain digits but are not figures: pathogens, subtypes, model ids.
_NAME_RE = re.compile(
    r"\b(?:COVID-19|SARS-CoV-2|H\dN\d+|H\d+|N\d+|RSV-NET|COVID-NET|FluSurv-NET|"
    r"gemini-[\w.-]+|qwen[\w.:-]*|llama[\w.:-]*)\b",
    re.IGNORECASE,
)


def strip_dates(text: str) -> str:
    return _DATE_RE.sub(" ", text)


def strip_names(text: str) -> str:
    return _NAME_RE.sub(" ", text)


def numbers_in(text: str) -> list[float]:
    """Numbers in free text, ignoring dates and names such as COVID-19.
    '1,162' -> 1162, '3.6%' -> 3.6."""
    out = []
    for m in _NUM_RE.findall(strip_dates(strip_names(text))):
        try:
            out.append(float(m.replace(",", "")))
        except ValueError:
            pass
    return out


def dates_in(text: str) -> set[str]:
    """Dates in free text as ISO strings."""
    found = set()
    for m in _DATE_RE.findall(text):
        s = m.replace(".", "").replace(",", "")
        s = re.sub(r"(\d)(st|nd|rd|th)", r"\1", s)
        for fmt in ("%Y-%m-%d", "%B %d %Y", "%b %d %Y", "%m/%d/%Y", "%m/%d/%y"):
            try:
                found.add(datetime.strptime(s, fmt).date().isoformat())
                break
            except ValueError:
                continue
    return found


def is_refusal(answer: str) -> bool:
    return bool(_REFUSAL.search(answer or ""))


def tool_output_numbers(tool_calls: list) -> list[float]:
    nums = []
    for call in tool_calls or []:
        for key in ("output", "result", "outputs"):
            if key in call:
                nums.extend(numbers_in(json.dumps(call[key], default=str)))
    return nums


def matches(value, candidates: list[float], tol: float) -> bool:
    return any(abs(c - value) <= tol + 1e-9 for c in candidates)


def _sum_or_difference(n: float, values: list[float], tol: float) -> bool:
    """n (or -n) equals a + b or a - b for two different tool values."""
    for v in (n, -n):
        for k in values:
            for a in (v + k, v - k):
                if abs(a - k) > tol and matches(a, values, tol):
                    return True
    return False


def grounded(answer: str, question: str, tool_calls: list) -> bool:
    """Every number in the answer appears in a tool result after rounding, or is
    the sum or difference of two tool values. Numbers already in the question are allowed."""
    tool_values = tool_output_numbers(tool_calls)
    source = tool_values + numbers_in(question)
    for n in numbers_in(answer):
        decimals = 0 if n == int(n) else len(repr(n).split(".")[1])
        tol = 0.5 * 10 ** -decimals
        if matches(n, source, tol) or matches(-n, source, tol):
            continue
        if not _sum_or_difference(n, tool_values, tol):
            return False
    return True


# ---------- scoring ----------


def value_found(expected, answer: str, tol: float) -> bool:
    if isinstance(expected, str):
        return expected in dates_in(answer) or expected in answer
    nums = numbers_in(answer)
    exp = float(expected)
    return matches(exp, nums, tol) or (exp < 0 and matches(-exp, nums, tol))



def pct(n: int, d: int):
    return round(100.0 * n / d, 1) if d else None




def result_base(out_dir: Path, model: str, day: str) -> Path:
    """<model>_<date>, then <model>_<date>_2, _3 ... so an earlier run is never overwritten."""
    stem = f"{re.sub(r'[^A-Za-z0-9_.-]', '-', model)}_{day}"
    base, n = out_dir / stem, 1
    while base.with_name(base.name + ".json").exists():
        n += 1
        base = out_dir / f"{stem}_{n}"
    return base

