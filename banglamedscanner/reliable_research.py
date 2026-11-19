"""Fail-closed, topic-grounded DeepSeek medical literature workflow.

The 1.5B model proposes queries and extracts passages, but it never decides
which PubMed sources are relevant without an independent lexical topic gate.
This is *not* medical/clinical accuracy verification.
"""
from __future__ import annotations

import os
import re
import time

from . import ai_orchestration as base
from .evidence import extract_abstract_evidence, _verify_quote
from .llm_report import is_configured
from .open_topics import clean_query, plan_public, STOPWORDS

MAX_CANDIDATES = 10
MAX_AUDIT_ITEMS = 10

# Conservative terminology aliases. An unknown Bangla term is *not* silently
# relabeled as another condition; the model query remains explicitly unverified.
TOPICS = (
    ('asthma', ('হাঁপানি', 'অ্যাজমা', 'এজমা', 'asthma', 'asthmatic'), ('asthma', 'asthmatic', 'bronchial asthma')),
    ('diabetes', ('ডায়াবেটিস', 'ডায়াবেটিস', 'ডায়াবেটিক', 'diabetes', 'diabetic'), ('diabetes', 'diabetic', 'hyperglycemia')),
    ('hypertension', ('উচ্চ রক্তচাপ', 'হাইপারটেনশন', 'hypertension'), ('hypertension', 'hypertensive', 'high blood pressure')),
    ('copd', ('সিওপিডি', 'copd', 'ক্রনিক অবস্ট্রাকটিভ'), ('copd', 'chronic obstructive pulmonary disease')),
    ('depression', ('বিষণ্ণতা', 'বিষন্নতা', 'depression', 'depressive disorder'), ('depression', 'depressive', 'major depressive')),
    ('epilepsy', ('মৃগীরোগ', 'এপিলেপসি', 'epilepsy'), ('epilepsy', 'epileptic', 'seizure disorder')),
    ('dengue', ('ডেঙ্গু', 'dengue'), ('dengue', 'dengue fever')),
    ('stroke', ('স্ট্রোক', 'stroke'), ('stroke', 'cerebrovascular accident')),
    ('tuberculosis', ('যক্ষ্মা', 'tuberculosis'), ('tuberculosis', 'tubercular')),
    ('cancer', ('ক্যান্সার', 'cancer'), ('cancer', 'carcinoma', 'malignancy')),
)
THERAPY_QUERY = ('চিকিৎসা', 'থেরাপি', 'ওষুধ', 'treatment', 'therapy', 'therapeutic', 'medication', 'drug', 'management')
THERAPY_SOURCE = ('treat', 'therap', 'intervention', 'clinical trial', 'randomiz', 'medication', 'drug', 'biologic', 'inhaled', 'corticosteroid', 'bronchodilator', 'efficacy', 'management', 'controlled trial', 'pharmacolog', 'immunotherap', 'remission')
QUERY_NOISE = frozenset(STOPWORDS) | frozenset('recent new medical today update findings trials treatments treatment therapy clinical current latest bangladesh'.split())


def _contains(text: str, phrase: str) -> bool:
    """ASCII concepts require word boundaries; Bangla inflections may suffix."""
    src = text.casefold()
    p = phrase.casefold()
    if all(ord(c) < 128 for c in p):
        return re.search(r'(?<![a-z0-9])' + re.escape(p) + r'(?![a-z0-9])', src) is not None
    return p in src


def question_anchors(question: str):
    matches = []
    for topic, user_aliases, source_aliases in TOPICS:
        if any(_contains(question, form) for form in user_aliases):
            matches.append((topic, source_aliases))
    return matches[:3]


def question_needs_treatment(question: str) -> bool:
    return any(_contains(question, x) for x in THERAPY_QUERY)


def protected_query(question: str, proposed: str):
    """Do not allow the tiny LLM to replace a known original disease topic."""
    topic_groups = question_anchors(question)
    proposed = clean_query(proposed)
    if topic_groups:
        anchors = [topic for topic, _ in topic_groups]
        valid = all(_contains(proposed, topic) for topic in anchors)
        if not valid:
            proposed = clean_query(' '.join(anchors + (['treatment'] if question_needs_treatment(question) else [])))
        return proposed, anchors, ('preserved_model_query' if valid else 'replaced_off_topic_model_query'), True
    # For an English original, require its specific subject term to survive.
    terms = [x.lower() for x in re.findall(r'[A-Za-z][A-Za-z0-9-]+', question)
             if len(x) >= 4 and x.lower() not in QUERY_NOISE]
    subjects = list(dict.fromkeys(terms))[:3]
    if subjects and not any(_contains(proposed, s) for s in subjects):
        proposed = clean_query(' '.join(subjects[:2] + (['treatment'] if question_needs_treatment(question) else [])))
        return proposed, subjects, 'replaced_query_missing_original_english_subject', True
    if not proposed:
        raise base.AIWorkflowError('No usable PubMed query could be verified')
    return proposed, subjects, 'model_translation_unverified' if not subjects else 'preserved_model_query', bool(subjects)


def _paper_relevance(question: str, query: str, title: str, abstract: str):
    """Transparent topic/intent evidence gate; never a clinical fact judge."""
    text = (title + ' ' + abstract).casefold()
    if len(abstract.split()) < 25:
        return False, 'No usable abstract', 0
    groups = question_anchors(question)
    if groups:
        for name, aliases in groups:
            if not any(_contains(text, alias) for alias in aliases):
                return False, 'Original topic absent from title and abstract: ' + name, 0
        topic_score = len(groups)
    else:
        # Do not accept a paper based solely on generic words such as treatment.
        words = [w.casefold() for w in re.findall(r'[A-Za-z][A-Za-z0-9-]+', query)
                 if len(w) >= 4 and w.casefold() not in QUERY_NOISE]
        terms = list(dict.fromkeys(words))[:5]
        if not terms:
            return False, 'No distinct topic word available for independent relevance check', 0
        hits = sum(_contains(text, w) for w in terms)
        needed = min(2, len(terms))
        if hits < needed:
            return False, 'Insufficient overlap with the PubMed topic query', hits
        topic_score = hits
    if question_needs_treatment(question):
        if not any(term in text for term in THERAPY_SOURCE):
            return False, 'Question asks about treatment but abstract lacks intervention context', topic_score
        if groups:
            clauses = re.split(r'(?<=[.!?])\s+|\n+', abstract.casefold())
            windows = clauses  # One sentence: don't connect unrelated comorbidities to other treatments.
            # Title+abstract query words anywhere is too weak: a dengue trial
            # may mention asthma only as an unrelated background condition.
            if not (any(_contains(title, alias) for _, aliases in groups for alias in aliases)
                    and any(term in text for term in THERAPY_SOURCE)):
                connected = any(
                    any(_contains(chunk, alias) for _, aliases in groups for alias in aliases)
                    and any(term in chunk for term in THERAPY_SOURCE)
                    for chunk in windows)
                if not connected:
                    return False, 'Disease and treatment never discussed in the same passage', topic_score
    title_bonus = 1 if groups and any(_contains(title, alias) for _, aliases in groups for alias in aliases) else 0
    return True, 'Original medical topic and requested intent found', topic_score + title_bonus


def retrieve_grounded(question, query, limit, *, search=None, fetch=None, heldout=None):
    """Fetch first, filter by source text, then rank; never pick the first N blindly."""
    finder = search or base.search_pubmed
    fetcher = fetch or base._fetch_abstracts
    excluded = base._heldout() if heldout is None else set(map(str, heldout))
    # Existing PubMed adapters may cap requests at five even though newer
    # adapters allow a larger preliminary relevance screen.
    try:
        candidates = finder(query, limit=MAX_CANDIDATES)
    except ValueError:
        candidates = finder(query, limit=5)
    if not isinstance(candidates, list):
        raise base.AIWorkflowError('PubMed returned an invalid candidate list')
    indexed = []
    seen = set()
    for raw in candidates[:MAX_CANDIDATES]:
        pmid = str(raw.get('pmid', '')) if isinstance(raw, dict) else ''
        if not re.fullmatch(r'\d{1,10}', pmid) or pmid in seen or pmid in excluded:
            continue
        indexed.append(raw)
        seen.add(pmid)
    abstracts = {}
    for offset in range(0, len(indexed), 5):
        batch = indexed[offset:offset+5]
        abstracts.update(fetcher([str(p['pmid']) for p in batch]))
    accepted, rejected = [], []
    for meta in indexed:
        pmid = str(meta['pmid'])
        title = str(meta.get('title') or '')
        abstract = abstracts.get(pmid, '')
        if not isinstance(abstract, str):
            abstract = ''
        ok, reason, score = _paper_relevance(question, query, title, abstract)
        if not ok:
            rejected.append({'pmid': pmid, 'title': title[:135], 'reason': reason})
            continue
        url = 'https://pubmed.ncbi.nlm.nih.gov/' + pmid + '/'
        excerpts = extract_abstract_evidence(abstract, pmid, url)
        excerpts = [e for e in excerpts if e.get('pmid') == pmid and
                    e.get('source_url') == url and
                    isinstance(e.get('quote_en'), str) and
                    _verify_quote(e['quote_en'], abstract) and
                    len(e['quote_en'].split()) <= 12]
        if not excerpts:
            rejected.append({'pmid': pmid, 'title': title[:135], 'reason': 'No source-verifiable abstract excerpt'})
            continue
        accepted.append((score, {
            'pmid':pmid, 'url':url, 'title_en':title[:300],
            'journal':str(meta.get('journal') or ''),
            'year':str(meta.get('date') or ''),
            'corpus_split':None, 'source':'live_pubmed_abstract',
            'abstract':abstract, 'evidence':excerpts,
            'pico_ai_candidates':{},
            'relevance_check':'original_topic_and_intent_found_in_source',
        }))
    accepted.sort(key=lambda item: -item[0])
    return [p for _, p in accepted[:limit]], {
        'candidates_examined':len(indexed), 'accepted_candidates':len(accepted),
        'rejected_candidates':len(rejected),
        'rejected':rejected[:MAX_AUDIT_ITEMS],
        'accepted':[{'pmid':p['pmid'],'title':p['title_en'][:135]} for _,p in accepted[:limit]],
    }


def run_reliable_ai_research(question, limit=2, ai_summary=True, *, model_call=None, search=None, fetch=None, heldout=None):
    """Drop-in for /api/ai/research/jobs with auditable, fail-closed selection."""
    if not isinstance(question, str) or not 2 <= len(question.strip()) <= 500:
        raise ValueError('Question must be 2 to 500 characters')
    if type(limit) is not int or not 1 <= limit <= 2:
        raise ValueError('AI research paper limit must be 1 or 2')
    if not is_configured():
        raise base.AIWorkflowError('Local DeepSeek unavailable')
    question = question.strip()
    model = model_call or base._chat
    base._MODEL_ATTEMPTS.set(0)
    trace = []

    def phase(agent, method, fn, *, model_invoked=False, job_builder=None):
        before = base._MODEL_ATTEMPTS.get()
        started = time.monotonic()
        value = fn()
        jobs = job_builder(value) if job_builder is not None else []
        attempts = base._MODEL_ATTEMPTS.get() - before
        trace.append({
            'agent':agent, 'method':method, 'status':'completed',
            'model_invoked':model_invoked,
            'model_name':os.environ.get('BMS_LLM_MODEL','') if model_invoked else None,
            'model_attempts':max(1,attempts) if model_invoked else 0,
            'elapsed_ms':round((time.monotonic()-started)*1000,1),
            'jobs':jobs[:MAX_AUDIT_ITEMS],
        })
        return value

    plan = phase('AI Query Planning Agent','DeepSeek proposes search terms; independent topic lock',
        lambda: base._plan(question, model), model_invoked=True,
        job_builder=lambda p:[{'action':'Translate original question','outcome':'Proposed: '+p['english_search_query'][:130]}])
    proposed = plan['english_search_query']
    query, anchors, decision, objectively_checkable = protected_query(question, proposed)
    if len(query) < 3:
        raise base.AIWorkflowError('No source-verifiable medical query')
    trace[0]['jobs'].append({'action':'Protect original topic', 'outcome':decision + ' | query: ' + query})
    if anchors:
        trace[0]['jobs'].append({'action':'Identify topic from the original question','outcome':', '.join(anchors)})

    papers, audit = phase('PubMed Retrieval and Relevance Agent',
        'ESearch/ESummary/EFetch + independent title and abstract relevance screening',
        lambda:retrieve_grounded(question,query,limit,search=search,fetch=fetch,heldout=heldout),
        job_builder=lambda value: ([{'action':'Search PubMed','outcome':query+' | inspected '+str(value[1]['candidates_examined'])+' source records'}] +
            [{'pmid':p['pmid'],'title':p['title'],'action':'Accept paper','outcome':'Original topic and intent verified'} for p in value[1]['accepted']] +
            [{'pmid':p['pmid'],'title':p['title'],'action':'Reject paper','outcome':p['reason']} for p in value[1]['rejected']]))
    # Explicitly label that a previously unfamiliar Bengali term could not be
    # independently validated against the original question.
    trace[1]['topic_guard_level'] = ('original_question_topic_checked' if objectively_checkable else 'model_translation_not_independently_verified')
    trace[1]['papers_examined'] = audit['candidates_examined']
    trace[1]['papers_rejected'] = audit['rejected_candidates']
    trace[1]['papers_accepted'] = audit['accepted_candidates']

    if not papers:
        report = {'summary_bn':'প্রশ্নটির মূল বিষয় ও চিকিৎসা-প্রসঙ্গের সঙ্গে মেলে এমন যাচাইযোগ্য গবেষণার সারাংশ পাওয়া যায়নি। ভুল বা অপ্রাসঙ্গিক পত্র দেখানোর পরিবর্তে ফলাফল খালি রাখা হয়েছে।',
                  'paper_explanations':[]}
        phase('Evidence Agent','No off-topic source evidence admitted',lambda:0,
              job_builder=lambda n:[{'action':'Protect medical relevance','outcome':'No admissible paper; AI synthesis skipped'}])
        phase('AI PICO Extraction Agent','Skipped: no relevant source evidence',lambda:0,
              job_builder=lambda n:[{'action':'PICO extraction','outcome':'Skipped to prevent fabrication'}])
        phase('AI Bangla Synthesis Agent','Skipped: no relevant source evidence',lambda:0,
              job_builder=lambda n:[{'action':'Synthesis','outcome':'Skipped; no AI claims generated'}])
        phase('Verification Agent','No unsupported source passed into the report',lambda:0,
              job_builder=lambda n:[{'action':'Final check','outcome':'Zero off-topic papers returned'}])
        return {'report_mode':'research','question_bn':question,'topic':', '.join(anchors) or plan['topic'],
                'english_search_query':query,'paper_count':0,'papers':[], 'ai_report':report,
                'agent_trace':trace,'model_used':True,'model_invocations':base._MODEL_ATTEMPTS.get() if model_call is None else 1,
                'status':'no_relevant_evidence', 'relevance_audit':audit,
                'topic_guard_level':trace[1]['topic_guard_level'],
                'clinical_validation':False,'disclaimer':'Unrelated results rejected. This is a lexical topic screen, NOT scientific or clinical validation.'}

    phase('Evidence Agent','Extract short source-verifiable quotes from accepted abstracts',
          lambda:sum(len(p['evidence']) for p in papers),
          job_builder=lambda count:[{'pmid':p['pmid'],'title':p['title_en'][:135],
             'action':'Extract abstract excerpts','outcome':str(len(p['evidence']))+' exact source-linked quote(s)'} for p in papers])
    count = phase('AI PICO Extraction Agent','DeepSeek chooses PICO candidates, verified against abstracts',
          lambda:base._model_pico(question,papers,model_call=model), model_invoked=True,
          job_builder=lambda c:[{'pmid':p['pmid'],'title':p['title_en'][:135],
              'action':'Extract PICO','outcome':', '.join(p['pico_ai_candidates'].keys()) or 'No verified PICO quote'} for p in papers])
    report = phase('AI Bangla Synthesis Agent','DeepSeek writes constrained Bangla summary from accepted evidence',
          lambda:base._model_synthesis(question,papers,model_call=model), model_invoked=True,
          job_builder=lambda r:[{'action':'Write source-constrained Bengali summary',
              'outcome':str(len(r['summary_bn']))+' characters; '+str(r.get('synthesis_model_attempts',1))+' synthesis attempt(s)'}])
    if model_call is not None:
        trace[-1]['model_attempts'] = report.get('synthesis_model_attempts',1)

    def verify_all():
        for p in papers:
            valid, _, _ = _paper_relevance(question, query, p['title_en'], p['abstract'])
            if not valid:
                raise base.AIWorkflowError('Relevance check failed after model synthesis')
            if p['url'] != 'https://pubmed.ncbi.nlm.nih.gov/'+p['pmid']+'/':
                raise base.AIWorkflowError('PMID URL mismatch')
            if any(not _verify_quote(e['quote_en'],p['abstract']) for e in p['evidence']):
                raise base.AIWorkflowError('A selected quote is not in its source')
            if any(not _verify_quote(v['quote_en'],p['abstract']) for v in p['pico_ai_candidates'].values()):
                raise base.AIWorkflowError('A PICO candidate is not in its source')
        return len(papers)
    phase('Verification Agent','Recheck original topic, PMID URL and literal evidence quotations',verify_all,
          job_builder=lambda _: [{'pmid':p['pmid'],'title':p['title_en'][:135],
               'action':'Check citations and relevance','outcome':'Source PMID, topic and quotes verified'} for p in papers])
    safe_papers = [{k:v for k,v in p.items() if k != 'abstract'} for p in papers]
    invocations = base._MODEL_ATTEMPTS.get() if model_call is None else sum(s.get('model_attempts',0) for s in trace)
    return {'report_mode':'research','question_bn':question,'topic':', '.join(anchors) or plan['topic'],
            'english_search_query':query,'paper_count':len(safe_papers),'papers':safe_papers,
            'ai_report':report,'pico_verified_quote_candidates':count,
            'model_used':True,'model_invocations':invocations,
            'agent_trace':trace,'status':'ai_generated_requires_human_review',
            'relevance_audit':audit,'topic_guard_level':trace[1]['topic_guard_level'],
            'clinical_validation':False,
            'disclaimer':'Independent disease/intent screen and literal quotation checks passed. DeepSeek medical conclusions and translations are NOT clinically validated.'}
