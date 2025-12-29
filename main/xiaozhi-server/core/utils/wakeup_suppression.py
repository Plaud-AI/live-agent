from __future__ import annotations

def normalize_for_wakeup(text: str) -> str:
    """Normalize text for wakeup matching / suppression decisions.

    Current behavior aligns with listen/detect's wakeup matching:
    - remove punctuation + spaces (via remove_punctuation_and_length)
    - lower-case ASCII letters for case-insensitive matching
    """
    if not text:
        return ""
    # Keep consistent with core.utils.util.remove_punctuation_and_length(),
    # but avoid importing util.py here (it pulls in heavy/optional deps like opuslib_next).
    full_width_punctuations = (
        "！＂＃＄％＆＇（）＊＋，－。／：；＜＝＞？＠［＼］＾＿｀｛｜｝～"
    )
    half_width_punctuations = r'!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~'
    space = " "
    full_width_space = "　"

    normalized = "".join(
        [
            ch
            for ch in text
            if ch not in full_width_punctuations
            and ch not in half_width_punctuations
            and ch not in space
            and ch not in full_width_space
        ]
    )

    # Preserve the special-case behavior from util.remove_punctuation_and_length
    if normalized == "Yeah":
        return ""

    return (normalized or "").lower()


def should_drop_asr_after_wakeup(
    *,
    asr_text: str,
    wakeup_words: list[str] | None,
    max_norm_len: int = 4,
) -> bool:
    """Decide whether an ASR result should be dropped as "wakeup residue".

    This is used to suppress the common double-trigger pattern:
    - device sends listen/detect wakeup text (fast short reply)
    - the same audio is also transcribed by ASR (often as a short, noisy phrase)
      then TurnDetection triggers a second chat after endpoint delay.

    Strategy (conservative):
    1) If ASR text matches any wakeup word after normalization: drop
    2) Else, if normalized length is very short (<= max_norm_len): drop

    Notes:
    - max_norm_len is intentionally small to avoid dropping real user queries.
    """
    norm = normalize_for_wakeup(asr_text)
    if not norm:
        return True

    wakeup_set = {normalize_for_wakeup(w) for w in (wakeup_words or []) if w}
    if norm in wakeup_set:
        return True

    return len(norm) <= max_norm_len


def is_wakeup_word(text: str, wakeup_words: list[str] | None) -> bool:
    """Return True if `text` should be treated as a wakeup word.

    This is used by listen/detect and wakeup short-reply logic.

    Design goals:
    - Case-insensitive for ASCII (OKayNabu / OKAYNABU / okay nabu)
    - Punctuation/space-insensitive (consistent with normalize_for_wakeup)
    - Add conservative aliases for the common "okaynabu" wake word, to tolerate
      short Chinese ASR variants like "OK那不"/"OK哪不".
    """
    norm = normalize_for_wakeup(text)
    if not norm:
        return False

    wakeup_set = {normalize_for_wakeup(w) for w in (wakeup_words or []) if w}
    if norm in wakeup_set:
        return True

    # Conservative aliases: only enable when okaynabu is configured.
    # (Avoid impacting users who don't use this wake word.)
    if "okaynabu" in wakeup_set:
        if norm in {"ok那不", "ok哪不", "okay那不", "okay哪不"}:
            return True

    return False


