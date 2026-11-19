"""General medical literature discovery without a five-disease allowlist.

Local 80-paper development subset is unchanged. Other terms use live PubMed.
English terms are unrestricted; common Bangla terminology is mapped without
pretending to provide unlimited offline Bengali-English translation.
"""
from __future__ import annotations

import re
from .pubmed import search_pubmed
from .query import interpret

# Common terms are convenience aliases; the authenticated AI planner handles
# open-ended Bangla and other topics beyond this convenience vocabulary.
ALIASES = {
    'ক্যান্সার': 'cancer', 'স্তন ক্যান্সার': 'breast cancer',
    'ফুসফুসের ক্যান্সার': 'lung cancer', 'লিউকেমিয়া': 'leukemia',
    'লিউকেমিয়া': 'leukemia', 'টিউমার': 'tumor',
    'কিডনি': 'kidney disease', 'বৃক্ক': 'kidney disease',
    'কিডনির': 'kidney disease', 'কিডনি রোগ': 'kidney disease',
    'হৃদরোগ': 'heart disease', 'হার্ট অ্যাটাক': 'myocardial infarction',
    'স্ট্রোক': 'stroke', 'আলঝেইমার': 'Alzheimer disease',
    'পারকিনসন': 'Parkinson disease', 'মাইগ্রেন': 'migraine',
    'মৃগীরোগ': 'epilepsy', 'ডেঙ্গু': 'dengue',
    'ম্যালেরিয়া': 'malaria', 'ম্যালেরিয়া': 'malaria',
    'যক্ষ্মা': 'tuberculosis', 'ক্ষয়রোগ': 'tuberculosis',
    'হেপাটাইটিস': 'hepatitis', 'এইচআইভি': 'HIV',
    'এইডস': 'HIV', 'কোভিড': 'COVID-19',
    'করোনা': 'COVID-19', 'নিউমোনিয়া': 'pneumonia',
    'নিউমোনিয়া': 'pneumonia', 'জ্বর': 'fever',
    'অ্যানিমিয়া': 'anemia', 'রক্তস্বল্পতা': 'anemia',
    'থাইরয়েড': 'thyroid disease', 'থাইরয়েড': 'thyroid disease',
    'গর্ভাবস্থা': 'pregnancy', 'গর্ভধারণ': 'pregnancy',
    'বন্ধ্যাত্ব': 'infertility', 'জন্মগত': 'congenital',
    'অ্যালার্জি': 'allergy', 'অটিজম': 'autism',
    'সোরিয়াসিস': 'psoriasis', 'আর্থ্রাইটিস': 'arthritis',
    'বাত': 'arthritis', 'সিজোফ্রেনিয়া': 'schizophrenia',
    'উদ্বেগ': 'anxiety', 'অনিদ্রা': 'insomnia',
    'স্থূলতা': 'obesity', 'অপুষ্টি': 'malnutrition',
    'হাড়': 'bone disease', 'হাড়': 'bone disease',
    'চোখ': 'eye disease', 'ছানি': 'cataract',
    'গ্লুকোমা': 'glaucoma', 'কোলেস্টেরল': 'cholesterol',
    'লিভার': 'liver disease', 'যকৃত': 'liver disease',
    'আলসার': 'ulcer', 'গ্যাস্ট্রিক': 'gastritis',
    'পেটের': 'gastrointestinal',
    'সেপসিস': 'sepsis', 'মেনিনজাইটিস': 'meningitis',
}
INTENT = {
    'চিকিৎসা': 'treatment', 'ওষুধ': 'medication', 'থেরাপি': 'therapy',
    'প্রতিরোধ': 'prevention', 'ঝুঁকি': 'risk',
    'রোগ নির্ণয়': 'diagnosis', 'রোগ নির্ণয়': 'diagnosis',
    'নতুন': 'recent', 'সাম্প্রতিক': 'recent',
}
STOPWORDS = {
    'what','which','why','how','do','does','did','the','and','about','tell','me',
    'of','for','a','an','on','in','to','can','is','are','be','with','there','any',
    'studies','study','papers','paper','research','latest','evidence','or','not',
}
BANGLA = re.compile(r'[\u0980-\u09ff]')
ASCII_WORDS = re.compile(r'[A-Za-z][A-Za-z0-9-]*')


def clean_query(text):
    """Allow short English PubMed keyword searches; no raw fielded syntax."""
    if not isinstance(text, str):
        raise ValueError('Search terms must be text')
    safe = re.sub(r'\[[^]\n]{0,40}\]', '', text[:400])
    words = ASCII_WORDS.findall(safe)
    terms = [w for w in words if w.casefold() not in STOPWORDS and len(w) > 1]
    terms = terms[:14]
    return ' '.join(terms)[:180]


def plan_public(question):
    if not isinstance(question, str) or not 2 <= len(question.strip()) <= 500:
        raise ValueError('Question must be 2 to 500 characters')
    question = question.strip()
    try:
        classified = interpret(question)
    except ValueError:
        classified = None
    if classified is not None:
        return {
            'topic': classified['topic'],
            'english_search_query': classified['english_search_query'],
            'translation_method': 'fixed_five_topic_lexicon',
            'needs_ai_translation': False,
            'local_corpus_supported': True,
        }
    text = ' '.join(question.split()).casefold()
    found = []
    # Prefer longest aliases so "breast cancer" is not replaced by "cancer".
    for phrase in sorted(ALIASES, key=len, reverse=True):
        if phrase.casefold() in text and not any(phrase in other for other in found):
            found.append(phrase)
    mapped = []
    for phrase in found:
        term = ALIASES[phrase]
        if term not in mapped:
            mapped.append(term)
    english = clean_query(question)
    if mapped:
        extra = [term for phrase, term in INTENT.items() if phrase in text]
        terms = ' '.join(mapped[:3] + extra[:2])
        return {
            'topic': ', '.join(mapped[:3]),
            'english_search_query': clean_query(terms),
            'translation_method': 'extended_bangla_vocabulary',
            'needs_ai_translation': False,
            'local_corpus_supported': False,
        }
    # English PubMed terms work for any medical area, not only five conditions.
    if english:
        return {
            'topic': english,
            'english_search_query': english,
            'translation_method': 'english_keyword_cleanup',
            'needs_ai_translation': False,
            'local_corpus_supported': False,
        }
    return {
        'topic': 'Open medical topic',
        'english_search_query': '',
        'translation_method': 'not_translated',
        'needs_ai_translation': True,
        'local_corpus_supported': False,
    }


def public_live_search(question, limit=5, pubmed_search=None):
    """Retrieve actual PubMed metadata; never fabricate abstracts or findings."""
    if type(limit) is not int or not 1 <= limit <= 5:
        raise ValueError('Limit must be between 1 and 5')
    parsed = plan_public(question)
    if parsed['needs_ai_translation']:
        found = []
    else:
        search = pubmed_search or search_pubmed
        found = search(parsed['english_search_query'], limit=limit)
    papers = []
    for raw in found[:limit]:
        pmid = str(raw.get('pmid', ''))
        if not re.fullmatch(r'\d{1,10}', pmid):
            continue
        papers.append({
            'pmid': pmid,
            'title_en': str(raw.get('title') or ''),
            'journal': str(raw.get('journal') or ''),
            'year': str(raw.get('date') or ''),
            'url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/',
            'topic': parsed['topic'],
            'abstract_excerpt_en': None,
            'study_type': None,
            'corpus_split': None,
        })
    return {
        'question_bn': question.strip(), 'source': 'live',
        'interpretation': parsed,
        'method': 'PubMed ESearch/ESummary; metadata only, no AI used',
        'count': len(papers), 'papers': papers,
        'heading_bn': (
            'অপরিচিত বাংলা পরিভাষা। প্রশাসকের DeepSeek গবেষণা মোড ব্যবহার করুন অথবা ইংরেজি রোগের নাম লিখুন।'
            if parsed['needs_ai_translation'] else
            f'লাইভ PubMed থেকে {len(papers)}টি গবেষণাপত্রের তথ্য পাওয়া গেছে।'
        ),
        'limitations_bn': (
            'PubMed-এ ইংরেজি শব্দে অনুসন্ধান করা হয়। এই সাধারণ অনুসন্ধানে AI, '
            'গবেষণার সারাংশ বা যাচাইকৃত PICO বিশ্লেষণ নেই। চিকিৎসা পরামর্শ নয়।'
        ),
        'needs_ai_translation': parsed['needs_ai_translation'],
    }
