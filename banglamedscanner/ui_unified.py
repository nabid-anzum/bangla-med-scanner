"""Unified, lightweight BanglaMedScanner interface.

One research question powers a single result workspace. Existing API endpoints and
all AI authorization remain untouched. No third-party assets or trackers.
"""

PAGE = r'''<!doctype html>
<html lang="bn">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#f7f9f7">
<meta name="description" content="Bangla-language, source-linked PubMed literature research prototype.">
<title>BanglaMedScanner — Evidence, made accessible</title>
<style>
:root{
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI","Noto Sans Bengali",sans-serif;
  color:#1b2927;background:#f7f9f7;font-synthesis:none;
  --ink:#1b2927;--muted:#687872;--brand:#126a5b;--brand-dark:#0f574b;
  --line:#e1e8e3;--soft:#f1f6f2;--paper:#fff;--focus:#49a898;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;min-width:320px}
button,input,select,textarea{font:inherit}
button,a{ -webkit-tap-highlight-color:transparent }
a{color:var(--brand);text-decoration:none}
a:hover{text-decoration:underline}
button{cursor:pointer}
button:disabled{cursor:wait;opacity:.65}
:focus-visible{outline:3px solid var(--focus);outline-offset:3px}
[hidden]{display:none!important}
.wrap{width:min(1100px,calc(100% - 42px));margin-inline:auto}
.site-header{height:76px;display:flex;align-items:center;border-bottom:1px solid var(--line);background:#fff}
.nav{display:flex;align-items:center;justify-content:space-between;gap:18px}
.identity{display:flex;align-items:center;gap:11px;font-weight:750;color:var(--ink);font-size:17px;letter-spacing:-.45px}
.brand-mark{width:37px;height:37px;display:grid;place-items:center;background:var(--brand);color:#fff;
  border-radius:11px;font-size:21px;font-weight:500;line-height:1}
.identity:hover{text-decoration:none}
.nav-actions{display:flex;align-items:center;gap:22px;font-size:13px;font-weight:570}
.nav-actions a{color:#4d6059}
.nav-actions .source-link{display:flex;align-items:center;gap:7px}
.nav-actions svg{width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:1.8}
.nav-pill{padding:6px 10px;border:1px solid #d2e5dc;border-radius:50px;background:#f4faf6;
  color:#2c6b58;font-weight:670;font-size:11px;white-space:nowrap}
.hero{display:grid;grid-template-columns:1.4fr .85fr;gap:32px;padding-top:65px;padding-bottom:38px;align-items:end}
.eyebrow{text-transform:uppercase;letter-spacing:1.7px;font-weight:770;font-size:11px;color:var(--brand);margin:0 0 16px}
h1{font-size:clamp(35px,5vw,58px);line-height:1.1;letter-spacing:-2.1px;margin:0;color:var(--ink);font-weight:750}
h1 span{color:var(--brand)}
.hero-desc{max-width:650px;margin:22px 0 0;color:#5e7069;font-size:15px;line-height:1.85}
.hero-aside{border-left:1px solid var(--line);padding:0 0 3px 25px}
.hero-aside strong{font-size:13px;font-weight:720;display:block;margin-bottom:10px}
.hero-aside p{font-size:13px;line-height:1.75;color:var(--muted);margin:0}
.hero-chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:14px}
.hero-chip{font-size:11px;border:1px solid #d9e4db;color:#557066;border-radius:999px;padding:5px 9px;background:white}
.card{background:var(--paper);border:1px solid var(--line);border-radius:18px;box-shadow:0 8px 34px rgba(18,42,30,.035)}
.search-card{padding:26px 28px 23px}
.search-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:17px}
h2{font-size:20px;letter-spacing:-.45px;margin:0;font-weight:735}
.subtle{color:var(--muted);font-size:13px}
.section-tag{font-size:11px;letter-spacing:.7px;text-transform:uppercase;color:#6a8378;font-weight:750}
.prompt-label{font-weight:680;font-size:13px;display:block;margin-bottom:9px}
textarea{width:100%;min-height:106px;padding:17px 18px;resize:vertical;line-height:1.8;
  background:#fcfdfc;color:var(--ink);border:1px solid #d5e0d8;border-radius:11px;outline-offset:2px;font-size:15px}
textarea::placeholder{color:#9aa9a1}
.examples{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:13px}
.examples span{color:#8a9b91;font-size:12px;margin-right:2px}
.example{border:1px solid #e1e9e3;background:#f8faf8;color:#4a6459;padding:7px 11px;
  border-radius:999px;font-size:12px;text-align:left;transition:background .12s,border-color .12s}
.example:hover{background:#eef6f1;border-color:#bfd6c9}
.search-bottom{display:flex;align-items:end;justify-content:space-between;gap:18px;flex-wrap:wrap;
  margin-top:25px;padding-top:18px;border-top:1px solid #edf1ed}
.source-control{display:grid;gap:7px;min-width:240px}
.source-control label{font-weight:680;font-size:12px;color:#566c61}
select{background:#fff;border:1px solid #d8e4da;color:#29433a;border-radius:9px;
  min-height:44px;padding:0 13px;font-size:13px;max-width:340px;width:100%}
.primary{display:inline-flex;justify-content:center;align-items:center;gap:11px;background:var(--brand);
  border:1px solid var(--brand);color:#fff;font-weight:680;border-radius:10px;min-height:46px;
  padding:0 23px;font-size:13px;box-shadow:0 3px 8px #136c591e;white-space:nowrap}
.primary:hover{background:var(--brand-dark)}
.primary .arrow{font-size:17px}
.status{font-size:12px;color:#57786b;min-height:20px;margin:15px 0 0}
.status.error{color:#a44337}
.micro-note{display:flex;align-items:center;gap:7px;margin-top:11px;color:#899a90;font-size:11px}
.micro-note:before{content:"";width:6px;height:6px;border-radius:50%;background:#65a68a}
#results{margin-top:29px;scroll-margin-top:24px}
.results-top{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin-bottom:13px}
.results-top p{color:var(--muted);margin:6px 0 0;font-size:13px}
.result-chip{padding:7px 11px;border-radius:999px;color:var(--brand);background:#e7f4ed;font-size:12px;font-weight:730}
.result-card{overflow:hidden}
.metrics{padding:19px 24px;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;background:#fafcf9}
.metric{border-right:1px solid #e6eee7;min-width:0}
.metric:last-child{border-right:0}
.metric-label{color:#718277;font-size:11px;text-transform:uppercase;font-weight:710;letter-spacing:.5px}
.metric-value{font-size:17px;color:#263e32;font-weight:730;display:block;margin-top:4px;overflow-wrap:anywhere}
.tabs{display:flex;gap:7px;padding:13px 23px 0;border-top:1px solid var(--line);
  border-bottom:1px solid var(--line);overflow-x:auto;scrollbar-width:thin}
.tab{background:none;border:0;border-bottom:2px solid transparent;color:#6a7b71;font-weight:650;
  padding:12px 13px 14px;white-space:nowrap;font-size:13px;min-height:43px}
.tab:hover{color:var(--brand)}
.tab[aria-selected="true"]{color:var(--brand);border-bottom-color:var(--brand)}
.result-pane{padding:28px 25px 30px;min-height:240px}
.pane-title{font-size:17px;font-weight:740;letter-spacing:-.35px;margin:0 0 9px}
.note{font-size:12px;line-height:1.7;color:#7d8e83}
.report{font-size:15px;line-height:2.0;color:#324a3e;max-width:820px;margin:12px 0}
.notice{padding:12px 15px;border-radius:10px;font-size:12px;line-height:1.7;color:#87622f;
  background:#fff9ef;border:1px solid #f2e5c9;margin-top:19px}
.sources-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:13px;margin-top:19px}
.source-note{padding:16px;border-radius:11px;border:1px solid var(--line);background:#fafcf9}
.source-note strong{display:block;font-size:13px;color:#2b4438;margin-bottom:6px}
.source-note p{margin:0;font-size:12px;color:var(--muted);line-height:1.7}
.paper{border:1px solid var(--line);border-radius:12px;padding:19px;margin:14px 0;background:#fff}
.paper-top{display:flex;align-items:start;justify-content:space-between;gap:12px}
.paper-index{display:grid;place-items:center;min-width:32px;height:32px;border-radius:9px;
  color:#417568;background:#e9f5ee;font-size:12px;font-weight:800}
.paper-title{font-size:14px;line-height:1.65;font-weight:720;margin:0 0 6px}
.paper-title a{color:#233c31}
.paper-title a:hover{color:var(--brand)}
.paper-meta{font-size:11px;color:#839188;line-height:1.65}
.excerpts{margin:14px 0 0;display:grid;gap:8px}
.excerpt{margin:0;padding:12px 13px;background:#f6f9f6;border-left:3px solid #80b6a2;
  border-radius:0 9px 9px 0;color:#41574a;font-size:12px;line-height:1.8}
.excerpt .eyeline{display:block;text-transform:uppercase;font-size:10px;letter-spacing:.7px;
  font-weight:740;color:#568572;margin-bottom:4px}
.pico-grid{display:grid;gap:0;margin-top:13px}
.pico-row{display:grid;grid-template-columns:135px 1fr;gap:16px;padding:11px 0;border-top:1px solid #edf1ed}
.pico-key{color:#6a8072;font-size:12px;font-weight:700}
.pico-text{font-size:12px;color:#334b3e;line-height:1.75;overflow-wrap:anywhere}
.pico-text.empty{color:#9ba9a0;font-style:italic}
.pico-section{color:#91a098;font-size:11px;display:block;margin-top:3px}
.trace-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px;margin-top:23px}
.agent{border:1px solid var(--line);border-radius:13px;padding:19px;background:#fbfcfb}
.agent-number{width:31px;height:31px;display:grid;place-items:center;border-radius:9px;
  background:#e4f3eb;color:var(--brand);font-size:12px;font-weight:790;margin-bottom:14px}
.agent strong{font-size:13px;display:block;margin-bottom:6px}
.agent p{font-size:11px;line-height:1.65;color:var(--muted);margin:0}
.agent-foot{display:flex;justify-content:space-between;gap:5px;margin-top:16px;padding-top:11px;
  border-top:1px solid var(--line);font-size:11px;color:#467762}
.admin-card{margin-top:26px;border:1px solid var(--line);border-radius:12px;background:#fcfdfc;padding:17px}
.admin-card summary{cursor:pointer;font-size:13px;font-weight:750;color:#334d3f}
.admin-desc{color:var(--muted);font-size:12px;line-height:1.7;margin:13px 0}
.admin-controls{display:flex;gap:10px;flex-wrap:wrap}
.admin-controls input{flex:1;min-width:190px;height:43px;padding:0 12px;border:1px solid #d3ded6;
  background:white;border-radius:9px;font-size:12px}
.admin-controls .primary{min-height:43px;padding-inline:15px}
.ai-result{padding:13px;margin-top:13px;background:#f2f8f4;border-radius:10px;
  font-size:13px;line-height:1.9;white-space:pre-wrap;color:#2c4b3b}
footer{border-top:1px solid var(--line);margin-top:55px;padding:22px 0 34px;display:flex;
  justify-content:space-between;gap:18px;align-items:start;flex-wrap:wrap;color:#8a9a90;font-size:11px;line-height:1.7}
footer a{color:#5a7a68}
@media(max-width:820px){.hero{grid-template-columns:1fr;gap:22px;padding-top:49px}
  .hero-aside{border-left:0;border-top:1px solid var(--line);padding:17px 0 0}
  .trace-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:540px){.wrap{width:min(100% - 28px,1100px)}
  .site-header{height:67px}.nav-actions{gap:12px}.nav-pill,.nav-actions .source-link{display:none}
  .hero{padding-top:42px;padding-bottom:25px}h1{letter-spacing:-1.3px;font-size:37px}
  .hero-desc{font-size:14px}.search-card{padding:19px 16px}
  .search-head{display:block}.search-head .section-tag{display:block;margin-top:6px}
  .search-bottom{align-items:stretch;gap:13px}.source-control{min-width:0;width:100%}
  .search-bottom .primary{width:100%}.metrics{grid-template-columns:repeat(2,minmax(0,1fr));padding:15px 16px}
  .metric:nth-child(2){border-right:0}.metric:last-child{grid-column:1/-1;border-top:1px solid #e6eee7;padding-top:12px}
  .tabs{padding-left:9px}.result-pane{padding:20px 15px}.trace-grid{grid-template-columns:1fr}
  .pico-row{grid-template-columns:1fr;gap:4px}.paper{padding:15px}.results-top{align-items:start}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
</style>
</head>
<body data-bms-unified="v1">
<header class="site-header">
  <div class="wrap nav">
    <a class="identity" href="/" aria-label="BanglaMedScanner home">
      <span class="brand-mark" aria-hidden="true">✳</span><span>BanglaMedScanner</span>
    </a>
    <nav class="nav-actions" aria-label="Resources">
      <span class="nav-pill">RESEARCH PREVIEW</span>
      <a href="#how-it-works">How it works</a>
      <a class="source-link" href="https://github.com/nabid-anzum/bangla-med-scanner" target="_blank" rel="noopener noreferrer">
        GitHub <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7M8 7h9v9"/></svg>
      </a>
    </nav>
  </div>
</header>
<main class="wrap">
  <section class="hero" aria-labelledby="hero-title">
    <div>
      <p class="eyebrow">Bangla-first medical literature research</p>
      <h1 id="hero-title">Research in Bangla.<br><span>Evidence you can trace.</span></h1>
      <p class="hero-desc">বাংলায় প্রশ্ন করুন, ইংরেজি PubMed গবেষণা খুঁজুন এবং যাচাইযোগ্য উদ্ধৃতি,
      PICO তথ্য ও ছয়টি সফটওয়্যার এজেন্টের কাজ এক জায়গায় দেখুন।</p>
    </div>
    <aside class="hero-aside" id="how-it-works">
      <strong>From question to source</strong>
      <p>One search connects query interpretation, literature retrieval, evidence extraction,
      PICO screening, citation verification and reporting.</p>
      <div class="hero-chips"><span class="hero-chip">6 software agents</span>
        <span class="hero-chip">PubMed sources</span><span class="hero-chip">Local DeepSeek</span></div>
    </aside>
  </section>
  <section class="card search-card" aria-label="Research question">
    <div class="search-head"><h2>Explore the literature</h2>
      <span class="section-tag">Single search workspace</span></div>
    <form id="research-form">
      <label class="prompt-label" for="question">Your question / আপনার প্রশ্ন</label>
      <textarea id="question" name="question" minlength="2" maxlength="500" required
       placeholder="উদাহরণ: ডায়াবেটিসের চিকিৎসায় নতুন গবেষণা কী বলছে?">ডায়াবেটিসের চিকিৎসায় নতুন গবেষণা কী বলছে?</textarea>
      <div class="examples" aria-label="Example questions">
        <span>Try:</span>
        <button class="example" type="button" data-example="ডায়াবেটিসের চিকিৎসা">ডায়াবেটিস</button>
        <button class="example" type="button" data-example="উচ্চ রক্তচাপের ঝুঁকি">উচ্চ রক্তচাপ</button>
        <button class="example" type="button" data-example="হাঁপানি প্রতিরোধ">হাঁপানি</button>
        <button class="example" type="button" data-example="বিষণ্নতার চিকিৎসা">বিষণ্নতা</button>
        <button class="example" type="button" data-example="সিওপিডি গবেষণা">COPD</button>
      </div>
      <div class="search-bottom">
        <div class="source-control">
          <label for="source">Research source</label>
          <select id="source" name="source">
            <option value="auto" selected>Automatic · any medical topic</option>
            <option value="corpus">Local 5-topic development corpus</option>
            <option value="live">Live PubMed · any English topic / common Bangla terms</option>
          </select>
        </div>
        <button id="search-submit" class="primary" type="submit">
          <span>Search research papers</span><span class="arrow" aria-hidden="true">↗</span>
        </button>
      </div>
      <p id="search-status" class="status" role="status" aria-live="polite"></p>
    </form>
    <p class="micro-note">No patient records. No third-party trackers. Research assistance, not medical advice.</p>
  </section>
  <section id="results" hidden aria-label="Research results">
    <div class="results-top"><div><h2>Research workspace</h2>
      <p>One question, four connected views. No need to search again.</p></div>
      <span class="result-chip" id="result-state">Source verified</span></div>
    <div class="card result-card">
      <div class="metrics" id="metrics" aria-live="polite"></div>
      <div class="tabs" role="tablist" aria-label="Research report sections" id="result-tabs">
        <button type="button" class="tab" role="tab" data-tab="overview" aria-selected="true" aria-controls="tab-panel" id="tab-overview">Overview</button>
        <button type="button" class="tab" role="tab" data-tab="papers" aria-selected="false" aria-controls="tab-panel" id="tab-papers">Research papers</button>
        <button type="button" class="tab" role="tab" data-tab="pico" aria-selected="false" aria-controls="tab-panel" id="tab-pico">PICO evidence</button>
        <button type="button" class="tab" role="tab" data-tab="trace" aria-selected="false" aria-controls="tab-panel" id="tab-trace">Agent workflow</button>
      </div>
      <section class="result-pane" id="tab-panel" role="tabpanel" aria-labelledby="tab-overview" tabindex="0" aria-live="polite"></section>
    </div>
  </section>
</main>
<footer class="wrap"><span>BanglaMedScanner · MSc research prototype · Not a clinical decision tool.</span>
  <span><a href="https://github.com/nabid-anzum/bangla-med-scanner" target="_blank" rel="noopener noreferrer">Source code</a> ·
    <a href="https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B" target="_blank" rel="noopener noreferrer">Open-weight model</a></span>
</footer>
<script>
(()=>{'use strict';
  const $=id=>document.getElementById(id);
  const state={data:null,kind:'corpus',tab:'overview',busy:false,aiReport:null,aiAgentReport:null};
  const labels={population:'Population',intervention:'Intervention',comparator:'Comparator',outcome:'Outcome',result:'Reported result'};
  const viewParam=new URLSearchParams(location.search).get('view');
  const requestedTab=location.pathname==='/structured'?'pico':location.pathname==='/workflow'?'trace':viewParam;
  if(['overview','papers','pico','trace'].includes(requestedTab))state.tab=requestedTab;

  function element(tag,text,klass){const el=document.createElement(tag);if(text!==undefined&&text!==null)el.textContent=String(text);if(klass)el.className=klass;return el;}
  function append(parent,tag,text,klass){const el=element(tag,text,klass);parent.append(el);return el;}
  function status(text,isError=false){$('search-status').textContent=text;$('search-status').classList.toggle('error',isError);}
  function clear(node){node.replaceChildren();}
  function field(parent,key,value){const wrap=element('div',undefined,'metric');append(wrap,'span',key,'metric-label');append(wrap,'strong',value,'metric-value');parent.append(wrap);}
  function citation(parent,paper,title){
    const pmid=String(paper.pmid||'');
    if(!/^\d{1,10}$/.test(pmid)){append(parent,'span',title,'paper-title');return;}
    const a=element('a',title);a.href='https://pubmed.ncbi.nlm.nih.gov/'+pmid+'/';
    a.target='_blank';a.rel='noopener noreferrer';parent.append(a);
  }
  function paperHeader(parent,paper,index){
    const top=append(parent,'div',undefined,'paper-top'),info=append(top,'div');
    const h=append(info,'h3',undefined,'paper-title');citation(h,paper,paper.title_en||'Untitled paper');
    append(info,'p','PMID '+String(paper.pmid||'—')+'  ·  '+String(paper.year||'Year unknown')+'  ·  '+String(paper.journal||'Journal unknown'),'paper-meta');
    append(top,'div',String(index+1).padStart(2,'0'),'paper-index');
  }
  function setTabs(){
    for(const b of document.querySelectorAll('[data-tab]')){
      const active=b.dataset.tab===state.tab;
      b.setAttribute('aria-selected',active?'true':'false');b.tabIndex=active?0:-1;
    }
    $('tab-panel').setAttribute('aria-labelledby','tab-'+state.tab);
  }
  function selectTab(tab){
    if(!['overview','papers','pico','trace'].includes(tab))return;
    state.tab=tab;setTabs();renderTab();
  }
  function warning(parent,text){append(parent,'div',text,'notice');}
  function addPapers(container,papers,withEvidence){
    if(!papers.length){append(container,'p','No matching papers were found. Try a different topic.','subtle');return;}
    papers.forEach((p,index)=>{
      const card=append(container,'article',undefined,'paper');paperHeader(card,p,index);
      const evidence=Array.isArray(p.evidence)?p.evidence:[];
      if(withEvidence&&evidence.length){
        const ex=append(card,'div',undefined,'excerpts');
        for(const ev of evidence){const q=append(ex,'blockquote',undefined,'excerpt');
          append(q,'span',String(ev.section||'Abstract')+' · source excerpt','eyeline');
          append(q,'span',ev.quote_en||'');}
      }else if(p.abstract_excerpt_en){append(card,'blockquote',p.abstract_excerpt_en,'excerpt');}
      if(state.kind==='live')append(card,'p','Live PubMed: bibliographic metadata only; PICO evidence is unavailable.','note');
    });
  }
  function renderOverview(root,data){
    append(root,'h3','Research overview','pane-title');
    append(root,'p',state.kind==='corpus'?data.bangla_report:data.heading_bn,'report');
    append(root,'p','English search: '+String(state.kind==='corpus'?data.english_search_query:(data.interpretation?.english_search_query||'—')),'subtle');
    const grid=append(root,'div',undefined,'sources-grid');
    const notes=state.kind==='corpus'?[
      ['Relevant papers',String(data.paper_count)+' development-set studies, with original PubMed links'],
      ['Verified excerpts','Short verbatim passages checked against stored abstracts'],
      ['Study data','PICO mentions are extracted candidates requiring human review']
    ]:[
      ['Live literature',String(data.count||0)+' PubMed metadata records'],
      ['Abstracts','Not retrieved in live mode; no PICO claims are generated'],
      ['Full pipeline','Switch to the local corpus to view six-agent orchestration']
    ];
    for(const [key,val] of notes){const box=append(grid,'div',undefined,'source-note');append(box,'strong',key);append(box,'p',val);}
    if(state.kind==='corpus'){
      const details=append(root,'details',undefined,'admin-card');
      append(details,'summary','DeepSeek synthesis · Administrator only');
      append(details,'p','Runs a separate, private, single-job local AI pipeline. It is not part of the six deterministic public agents. Generated text is not medically validated.','admin-desc');
      const controls=append(details,'div',undefined,'admin-controls');
      const input=append(controls,'input');input.type='password';input.id='ai-token';input.placeholder='Administrator token';
      input.maxLength=256;input.autocomplete='off';input.spellcheck=false;
      const go=append(controls,'button','Generate Bangla AI summary','primary');go.type='button';go.id='ai-generate';
      const progress=append(details,'p','','status');progress.id='ai-progress';progress.setAttribute('role','status');progress.setAttribute('aria-live','polite');
      const result=append(details,'div',undefined,'ai-result');result.id='ai-result';result.hidden=true;
      if(state.aiReport){result.textContent=state.aiReport;result.hidden=false;}
      go.addEventListener('click',()=>runAI(data.question_bn,input,go,progress,result));
    }
    const box=append(root,'details',undefined,'admin-card');
    box.open=true;
    append(box,'summary','AI multi-agent research · DeepSeek (administrator only)');
    append(box,'p','Unlike the public six-stage rule-based search, this flow really invokes DeepSeek for query planning, PICO candidate interpretation and Bangla synthesis (3 sequential calls). One active AI job; unlimited medical topics with English PubMed sources, subject to model translation quality and availability.','admin-desc');
    const row=append(box,'div',undefined,'admin-controls');
    const key=append(row,'input');key.type='password';key.placeholder='Private administrator token';
    key.maxLength=256;key.autocomplete='off';key.spellcheck=false;
    const go=append(row,'button','Run DeepSeek research agents','primary');go.type='button';
    const progress=append(box,'p','','status');progress.setAttribute('role','status');
    progress.setAttribute('aria-live','polite');
    const result=append(box,'div',undefined,'ai-result');result.hidden=true;
    if(state.aiAgentReport)paintAIResearch(result,state.aiAgentReport);
    go.addEventListener('click',()=>runAgentAI(data.question_bn,key,go,progress,result));
    warning(root,'Research prototype · Source linkage and excerpts are mechanically checked; medical accuracy and clinical significance are not independently verified.');
  }
  function renderPico(root,data){
    append(root,'h3','Structured PICO evidence','pane-title');
    if(state.kind==='live'){
      append(root,'p','This source returns PubMed metadata only. Select “Verified local research corpus” and search again to inspect source-anchored PICO candidates.','subtle');return;
    }
    append(root,'p','Candidate Population, Intervention, Comparator, Outcome, and reported-result information from development abstracts. Not clinical conclusions.','subtle');
    if(!data.papers.length){append(root,'p','No candidate studies found.','subtle');return;}
    data.papers.forEach((p,index)=>{
      const card=append(root,'article',undefined,'paper');paperHeader(card,p,index);
      const grid=append(card,'div',undefined,'pico-grid');
      for(const [key,label] of Object.entries(labels)){
        const line=append(grid,'div',undefined,'pico-row');append(line,'span',label,'pico-key');
        const field=p.pico?.[key];
        const text=append(line,'div',field?.quote_en||'Not identified with sufficient evidence','pico-text'+(!field?' empty':''));
        if(field)append(text,'span','Abstract: '+String(field.section||'unspecified')+' · unverified candidate','pico-section');
      }
    });
    warning(root,'PICO values are lexical candidates. A source-linked quotation is not proof that the field was correctly interpreted.');
  }
  function renderTrace(root,data){
    append(root,'h3','Six-agent execution trace','pane-title');
    if(state.kind==='live'){
      append(root,'p','Live PubMed search uses a separate metadata-only retrieval path. The six-stage source-verification trace is available in local corpus mode.','subtle');return;
    }
    append(root,'p','Each stage runs as a specialized software component; these are not six independent large-language models.','subtle');
    const grid=append(root,'div',undefined,'trace-grid');
    (data.agent_trace||[]).forEach((agent,index)=>{
      const box=append(grid,'article',undefined,'agent');append(box,'div',String(index+1).padStart(2,'0'),'agent-number');
      append(box,'strong',agent.agent);append(box,'p',agent.method);
      const foot=append(box,'div',undefined,'agent-foot');append(foot,'span',agent.status);append(foot,'span',String(agent.elapsed_ms||0)+' ms');
    });
    append(root,'p','Run ID: '+String(data.request_id||'—')+' · Held-out exposure: '+String(data.heldout_exposure||0),'note');
  }
  function renderTab(){
    if(!state.data)return;
    const root=$('tab-panel');clear(root);
    switch(state.tab){
      case 'papers':append(root,'h3','Research papers & citations','pane-title');
        append(root,'p','Original PubMed references open in a new tab. Excerpts, when available, are short source quotations.','subtle');
        addPapers(root,state.data.papers||[],state.kind==='corpus');break;
      case 'pico':renderPico(root,state.data);break;
      case 'trace':renderTrace(root,state.data);break;
      default:renderOverview(root,state.data);
    }
  }
  function renderResults(){
    const d=state.data,kind=state.kind;
    clear($('metrics'));
    field($('metrics'),'Topic',kind==='corpus'?d.topic:d.interpretation?.topic||'—');
    field($('metrics'),'Papers',kind==='corpus'?d.paper_count:d.count);
    field($('metrics'),'Source',kind==='corpus'?'Local corpus · 80 dev':'Live PubMed');
    $('result-state').textContent=kind==='corpus'?'Source-linked evidence':'Metadata search';
    $('results').hidden=false;setTabs();renderTab();
    $('results').scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
  }
  async function readJSON(response){
    const body=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(typeof body.detail==='string'?body.detail:'The research service is unavailable.');
    return body;
  }
  // Legacy '/api/research' with {source:'live'} is still available.
  async function submit(){
    if(state.busy)return;
    const question=$('question').value.trim(),kind=$('source').value;
    if(question.length<2||question.length>500){status('Enter a question between 2 and 500 characters.',true);return;}
    state.busy=true;state.aiReport=null;state.aiAgentReport=null;state.data=null;state.kind=kind==='corpus'?'corpus':'live';
    $('search-submit').disabled=true;$('results').hidden=true;
    status(kind==='corpus'?'Six research agents are retrieving and verifying evidence…':'Searching live PubMed metadata…');
    try{
      const path=kind==='corpus'?'/api/orchestrate':kind==='auto'?'/api/smart-search':'/api/open-search';
      const payload=kind==='corpus'?{question,limit:3}:{question,limit:5};
      const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),28000);
      let response;
      try{response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify(payload),signal:controller.signal,cache:'no-store'});}
      finally{clearTimeout(timeout);}
      const data=await readJSON(response);
      if((kind==='corpus'||(kind==='auto'&&data.source==='corpus'))&&
          (!Array.isArray(data.agent_trace)||data.agent_trace.length!==6||!Array.isArray(data.papers)))
        throw new Error('The research workflow returned incomplete evidence.');
      if((kind==='live'||(kind==='auto'&&data.source!=='corpus'))&&
          !Array.isArray(data.papers))throw new Error('PubMed returned an unexpected response.');
      state.kind=kind==='auto'?(data.source==='corpus'?'corpus':'live'):(kind==='corpus'?'corpus':'live');
      state.data=data;renderResults();
      status(data.needs_ai_translation?'For less common Bangla medical terms, use the administrator DeepSeek research mode or enter English terms.':
        state.kind==='corpus'?'Six software-agent stages completed; DeepSeek was not used.':'Live PubMed discovery completed; DeepSeek was not used.');
    }catch(err){status(err.name==='AbortError'?'The request timed out. Try again.':String(err.message||err),true);}
    finally{state.busy=false;$('search-submit').disabled=false;}
  }
  function paintAIResearch(root,data){
    root.replaceChildren();root.hidden=false;
    if(data.status==='no_abstract_evidence'){
      append(root,'strong','No usable PubMed abstracts were retrieved. No AI medical conclusion was generated.');return;
    }
    append(root,'strong','DeepSeek actually ran '+String(data.model_invocations||0)+' times');
    append(root,'p',String(data.ai_report?.summary_bn||'No validated Bangla summary.'),'report');
    append(root,'p','Generated text is not clinically verified. Source quotations are checked mechanically.','note');
    for(const p of (data.papers||[])){
      const article=append(root,'article',undefined,'paper');paperHeader(article,p,0);
      for(const ev of (p.evidence||[]))append(article,'blockquote',ev.quote_en,'excerpt');
      const c=Object.entries(p.pico_ai_candidates||{});
      for(const [key,value] of c)append(article,'p',key.toUpperCase()+': '+String(value.quote_en||'')+' (exact-quote candidate, unreviewed)','note');
    }
    append(root,'h4','Actual execution trace');
    for(const stage of (data.agent_trace||[])){
      append(root,'p',String(stage.agent)+': '+(stage.model_invoked?'DeepSeek model called':'Software step')+
        ' · '+String(stage.elapsed_ms||0)+' ms','note');
    }
  }
  async function runAgentAI(question,input,button,progress,result){
    const token=input.value.trim();
    if(!token){progress.textContent='Enter the private administrator token.';return;}
    button.disabled=true;result.hidden=true;progress.textContent='Starting private DeepSeek multi-agent research…';
    const headers={'Content-Type':'application/json','X-BMS-AI-Token':token};
    try{
      const start=await readJSON(await fetch('/api/ai/research/jobs',{
        method:'POST',headers,body:JSON.stringify({question,limit:2}),cache:'no-store'}));
      if(!/^[a-zA-Z0-9_-]{1,64}$/.test(String(start.job_id||'')))throw Error('Invalid job ID');
      for(let attempt=0;attempt<195;attempt++){
        await new Promise(resolve=>setTimeout(resolve,3000));
        const job=await readJSON(await fetch('/api/ai/research/jobs/'+encodeURIComponent(start.job_id),{
          headers:{'X-BMS-AI-Token':token},cache:'no-store'}));
        if(job.status==='completed'){
          state.aiAgentReport=job.result;
          paintAIResearch(result,job.result);
          progress.textContent='Model-based research finished. Independently review every finding.';return;
        }
        if(job.status==='failed')throw Error(job.detail||'Local AI job failed');
        progress.textContent='Running DeepSeek sequentially on the CPU-limited model. This may take several minutes…';
      }
      throw Error('Timed out waiting for the local model. Research search remains available.');
    }catch(err){progress.textContent=String(err.message||err);}
    finally{button.disabled=false;input.value='';}
  }
  async function runAI(question,input,button,progress,result){
    const token=input.value.trim();
    if(!token){progress.textContent='Enter your private administrator token.';return;}
    if(state.busy){progress.textContent='Finish the current search first.';return;}
    button.disabled=true;progress.textContent='Submitting private DeepSeek job…';result.hidden=true;
    const headers={'Content-Type':'application/json','X-BMS-AI-Token':token};
    try{
      const start=await readJSON(await fetch('/api/ai/jobs',{method:'POST',headers,
        body:JSON.stringify({question,limit:2,ai_summary:true}),cache:'no-store'}));
      if(!/^[a-zA-Z0-9_-]{1,64}$/.test(String(start.job_id||'')))throw new Error('Invalid AI job identifier');
      for(let n=0;n<110;n++){
        await new Promise(resolve=>setTimeout(resolve,2000));
        const r=await readJSON(await fetch('/api/ai/jobs/'+encodeURIComponent(start.job_id),
          {headers:{'X-BMS-AI-Token':token},cache:'no-store'}));
        if(r.status==='completed'){
          const summary=r.result?.ai_report?.summary_bn;
          if(typeof summary!=='string'||!summary.trim())throw new Error('AI returned no usable explanation');
          state.aiReport=summary;result.textContent=summary;result.hidden=false;
          progress.textContent='Local DeepSeek synthesis completed. Review against cited sources.';return;
        }
        if(r.status==='failed')throw new Error(r.detail||'AI generation was unsuccessful');
        progress.textContent='Local DeepSeek is processing a source-grounded report…';
      }
      throw new Error('The local model took too long. Try again later.');
    }catch(error){progress.textContent=String(error.message||error);}
    finally{button.disabled=false;input.value='';}
  }
  for(const btn of document.querySelectorAll('[data-example]')){
    btn.addEventListener('click',()=>{$('question').value=btn.dataset.example;$('question').focus();});
  }
  $('research-form').addEventListener('submit',event=>{event.preventDefault();submit();});
  const tabs=Array.from(document.querySelectorAll('[data-tab]'));
  for(const btn of tabs){
    btn.addEventListener('click',()=>selectTab(btn.dataset.tab));
    btn.addEventListener('keydown',event=>{
      if(event.key!=='ArrowRight'&&event.key!=='ArrowLeft')return;
      event.preventDefault();const delta=event.key==='ArrowRight'?1:-1;
      const next=tabs[(tabs.indexOf(btn)+delta+tabs.length)%tabs.length];selectTab(next.dataset.tab);next.focus();
    });
  }
  setTabs();
})();
</script>
</body></html>'''
