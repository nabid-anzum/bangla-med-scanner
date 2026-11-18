"""Controlled Bangla/English medical query interpretation.

First-stage deterministic prototype, not a generative AI agent.
"""

import json
import re
import sys
import unicodedata

TOPICS = {
    "diabetes": (
        "type 2 diabetes",
        (
            "ডায়াবেটিস",
            "ডায়াবেটিস",
            "মধুমেহ",
            "diabetes",
        ),
    ),
    "hypertension": (
        "hypertension",
        (
            "উচ্চ রক্তচাপ",
            "হাই ব্লাড প্রেসার",
            "হাই প্রেসার",
            "হাইপারটেনশন",
            "hypertension",
            "high blood pressure",
        ),
    ),
    "asthma": (
        "asthma",
        (
            "হাঁপানি",
            "অ্যাজমা",
            "অ্যাস্থমা",
            "asthma",
        ),
    ),
    "depression": (
        "depression",
        (
            "বিষণ্নতা",
            "বিষণ্ণতা",
            "ডিপ্রেশন",
            "depression",
        ),
    ),
    "copd": (
        "chronic obstructive pulmonary disease",
        (
            "সিওপিডি",
            "ক্রনিক অবস্ট্রাকটিভ পালমোনারি ডিজিজ",
            "copd",
            "chronic obstructive pulmonary disease",
        ),
    ),
}

INTENTS = {
    "treatment": (
        "চিকিৎসা", "ওষুধ", "ঔষধ", "থেরাপি",
        "treatment", "therapy", "medication",
    ),
    "prevention": (
        "প্রতিরোধ", "prevention",
    ),
    "diagnosis": (
        "নির্ণয়", "নির্ণয়", "পরীক্ষা",
        "diagnosis", "diagnostic",
    ),
    "risk": (
        "ঝুঁকি", "risk",
    ),
}

RECENCY = (
    "সাম্প্রতিক", "নতুন", "হালনাগাদ",
    "latest", "recent",
)


def _normalized(value):
    text = unicodedata.normalize("NFKC", value).casefold()
    text = re.sub(
        "[\u200b\u200c\u200d\ufeff]", "", text
    )
    return " ".join(text.split())


def _contains(text, word):
    word = _normalized(word)

    if word.isascii():
        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(word)
            + r"(?![a-z0-9])"
        )
        return re.search(pattern, text) is not None

    return word in text


def interpret(query):
    if (
        not isinstance(query, str)
        or not query.strip()
        or len(query) > 500
    ):
        raise ValueError(
            "Provide a medical question "
            "between 1 and 500 characters."
        )

    normalized = _normalized(query)

    matches = {
        topic: next(
            (
                alias for alias in aliases
                if _contains(normalized, alias)
            ),
            None,
        )
        for topic, (_, aliases) in TOPICS.items()
    }

    matches = {
        topic: alias
        for topic, alias in matches.items()
        if alias is not None
    }

    if not matches:
        raise ValueError(
            "No supported medical topic recognized. "
            "Try diabetes, hypertension, asthma, "
            "depression, or COPD."
        )

    if len(matches) > 1:
        raise ValueError(
            "Multiple medical topics detected. "
            "Ask about one topic per query "
            "in this version."
        )

    topic = next(iter(matches))

    intents = [
        name
        for name, aliases in INTENTS.items()
        if any(
            _contains(normalized, alias)
            for alias in aliases
        )
    ]

    english_query = " ".join(
        (TOPICS[topic][0], *intents)
    )

    return {
        "original_question": query.strip(),
        "detected_language": (
            "bn"
            if re.search(r"[\u0980-\u09ff]", query)
            else "en"
        ),
        "topic": topic,
        "matched_keyword": matches[topic],
        "intents": intents,
        "recent_requested": any(
            _contains(normalized, term)
            for term in RECENCY
        ),
        "english_search_query": english_query,
        "method": "curated_lexicon_v1",
        "limitation": (
            "Terminology-based query mapping only. "
            "It does not yet retrieve papers, "
            "run an LLM, or provide medical advice."
        ),
    }


def main():
    if len(sys.argv) != 2:
        print(
            'Usage: python -m banglamedscanner.query '
            '"Bangla medical question"',
            file=sys.stderr,
        )
        return 2

    try:
        result = interpret(sys.argv[1])
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
