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

/* BMS29: one search, explicit workflow and visible admin authorization */
.mode-section{padding:0;margin:0 0 19px;border:0;min-width:0}
.mode-section legend{font-size:12px;color:#496459;font-weight:740;margin-bottom:10px}
.mode-switch{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}
.mode-option{display:flex;align-items:flex-start;gap:10px;padding:13px 14px;border:1px solid #dce6dd;border-radius:11px;background:#fbfdfb;cursor:pointer}
.mode-option:has(input:checked){background:#eaf5ee;border-color:#69b19a;box-shadow:inset 0 0 0 1px #69b19a}
.mode-option input{accent-color:var(--brand);width:16px;height:16px;flex:none;margin:2px 0 0}
.mode-option strong{font-size:13px;display:block;color:#294238}
.mode-option small{font-size:11px;display:block;color:#6a8174;line-height:1.55;margin-top:4px}
#admin-box{border:1px solid #cbe4d7;background:#f3faf5;padding:15px;border-radius:11px;margin:0 0 16px}
#admin-box label{display:block;font-size:12px;font-weight:710;margin-bottom:7px}
#admin-token,#paper-pmid{width:100%;max-width:435px;min-height:43px;padding:0 12px;border:1px solid #d0dcd3;border-radius:8px;background:#fff}
#admin-box p,.mode-info{font-size:11px;line-height:1.65;color:#668173;margin:6px 0 0}
#paper-ref{padding:12px 0 4px}
#paper-ref label{display:block;font-size:12px;font-weight:710;margin-bottom:6px}
.status-line{padding-top:8px;font-size:12px;color:#5a7968}
.match-kind{display:inline-block;padding:4px 8px;border-radius:50px;background:#e5f2e8;color:#275944;font-size:10px;font-weight:750;margin:7px 0}
.meta-line{font-size:12px;color:#52695c;line-height:1.7;overflow-wrap:anywhere;margin:6px 0}
.claim-excerpt{font-size:13px;line-height:1.85;background:#f6faf7;border-left:3px solid #73aa8d;padding:11px 13px;margin:10px 0;border-radius:0 9px 9px 0}
.page-number{font-weight:760;color:#315a49}
.pill-muted{font-size:10px;color:#6a8272;border:1px solid #e0e8e0;border-radius:50px;padding:4px 8px}
@media(max-width:640px){.mode-switch{grid-template-columns:1fr}#admin-token,#paper-pmid{max-width:100%}}

/* Batch 30: per-paper trace details in the existing minimalist workspace */
.trace-grid.audit-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
.audit-agent{min-width:0}
.audit-tasks{margin-top:13px;border-top:1px solid var(--line);padding-top:10px}
.audit-tasks summary{font-size:12px;font-weight:720;color:#285643;cursor:pointer;line-height:1.5}
.audit-task-list{display:grid;gap:8px;margin-top:12px}
.audit-task{border-left:3px solid #b8d6bd;padding:8px 10px;background:#f5f8f5;border-radius:0 6px 6px 0}
.audit-task strong{font-size:11px;margin-bottom:3px;display:block}
.audit-task p,.audit-source,.audit-empty{font-size:11px;line-height:1.5;color:var(--muted);overflow-wrap:anywhere}
.audit-source{display:block;margin:4px 0}
@media(max-width:780px){.trace-grid.audit-grid{grid-template-columns:1fr}}
</style>
</head>
<body data-bms-unified="v1" data-bms-layout="v29">
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
      প্রমাণ-ভিত্তিক প্রতিবেদন, PICO তথ্য এবং এজেন্টের কাজ এক জায়গায় দেখুন। গবেষণাপত্রে নির্দিষ্ট কোনো বক্তব্য আছে কি না, সেটিও খুঁজতে পারেন।</p>
    </div>
    <aside class="hero-aside" id="how-it-works">
      <strong>From question to source</strong>
      <p>One search connects query interpretation, literature retrieval, evidence extraction,
      source-linked evidence, PICO screening and a truthful execution trace. DeepSeek planning and analysis run only after admin authorization.</p>
      <div class="hero-chips"><span class="hero-chip">Verified evidence</span>
        <span class="hero-chip">PubMed sources</span><span class="hero-chip">Private DeepSeek agents</span></div>
    </aside>
  </section>
  <section class="card search-card" aria-label="Research question">
    <div class="search-head"><h2>Explore the literature</h2>
      <span class="section-tag">Single search workspace</span></div>
    <form id="research-form">
      <fieldset class="mode-section">
        <legend>What are you looking for?</legend>
        <div class="mode-switch">
          <label class="mode-option"><input type="radio" name="task" value="research" checked>
            <span><strong>Research a medical topic</strong><small>Evidence, papers, PICO and workflow</small></span></label>
          <label class="mode-option"><input type="radio" name="task" value="claim">
            <span><strong>Find a statement in papers</strong><small>Search related discussion, author, source and verified PDF page</small></span></label>
        </div>
      </fieldset>
      <fieldset id="analysis-choice" class="mode-section">
        <legend>How should the search run?</legend>
        <div class="mode-switch">
          <label class="mode-option"><input type="radio" name="analysis" value="evidence" checked>
            <span><strong>Evidence only · Public</strong><small>Multiple simultaneous searches; no DeepSeek</small></span></label>
          <label class="mode-option"><input type="radio" name="analysis" value="ai">
            <span><strong>DeepSeek AI · Administrator</strong><small>Real AI analysis; one model job at a time</small></span></label>
        </div>
      </fieldset>
      <div id="admin-box" hidden>
        <label for="admin-token">Private DeepSeek administrator token</label>
        <input type="password" id="admin-token" autocomplete="off" maxlength="256" spellcheck="false" placeholder="Enter administrator token"/>
        <p>Authorization is required to start AI jobs. The token is used only for this request, never saved in the page or browser storage.</p>
      </div>
      <label class="prompt-label" for="question">Question or statement / প্রশ্ন বা বক্তব্য</label>
      <textarea id="question" name="question" minlength="2" maxlength="500" required
       placeholder="উদাহরণ: ডায়াবেটিসের চিকিৎসায় নতুন গবেষণা কী বলছে?">ডায়াবেটিসের চিকিৎসায় নতুন গবেষণা কী বলছে?</textarea>
      <div id="paper-ref" hidden>
        <label for="paper-pmid">Specific paper PMID (optional)</label>
        <input id="paper-pmid" type="text" inputmode="numeric" pattern="[0-9]{1,10}" maxlength="10" placeholder="e.g. 37916757" autocomplete="off">
        <p class="mode-info">Leave blank to search across PubMed, or enter a PMID to inspect one paper.</p>
      </div>
      <div class="examples" aria-label="Example questions">
        <span>Try:</span>
        <button class="example" type="button" data-example="ডায়াবেটিসের চিকিৎসা">ডায়াবেটিস</button>
        <button class="example" type="button" data-example="উচ্চ রক্তচাপের ঝুঁকি">উচ্চ রক্তচাপ</button>
        <button class="example" type="button" data-example="হাঁপানি প্রতিরোধ">হাঁপানি</button>
        <button class="example" type="button" data-example="বিষণ্নতার চিকিৎসা">বিষণ্নতা</button>
        <button class="example" type="button" data-example="সিওপিডি গবেষণা">COPD</button>
      </div>
      <div class="search-bottom">
        <div class="source-control" id="source-group">
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
      <p>One question or statement, one integrated report. The tabs reflect the same execution.</p></div>
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
  const state={task:'research',analysis:'evidence',tab:'overview',data:null,busy:false};
  const PICO={population:'Population',intervention:'Intervention',comparator:'Comparator',outcome:'Outcome',result:'Reported result'};
  const root=$('tab-panel');
  const fromURL=new URLSearchParams(location.search).get('view');
  const initial=location.pathname==='/structured'?'pico':location.pathname==='/workflow'?'trace':fromURL;
  if(['overview','papers','pico','trace'].includes(initial))state.tab=initial;
  function node(tag,text,klass){const e=document.createElement(tag);if(text!==undefined&&text!==null)e.textContent=String(text);if(klass)e.className=klass;return e;}
  function add(p,tag,text,klass){const e=node(tag,text,klass);p.append(e);return e;}
  function clear(p){p.replaceChildren();}
  function status(s,bad=false){$('search-status').textContent=s;$('search-status').classList.toggle('error',bad);}
  function notice(p,s){add(p,'div',s,'notice');}
  function inputValue(name){return document.querySelector('input[name="'+name+'"]:checked')?.value;}
  function setModes(){
    state.task=inputValue('task')||'research';
    if(state.task==='claim'){
      const ai=document.querySelector('input[name="analysis"][value="ai"]');ai.checked=true;
      $('paper-ref').hidden=false;$('source-group').hidden=true;$('analysis-choice').hidden=true;
      $('question').placeholder='e.g. Does this paper discuss that metformin reduces cardiovascular mortality?';
      $('search-submit').querySelector('span').textContent='Find statement in papers';
    }else{
      $('paper-ref').hidden=true;$('source-group').hidden=false;$('analysis-choice').hidden=false;
      $('question').placeholder='উদাহরণ: ডায়াবেটিসের চিকিৎসায় নতুন গবেষণা কী বলছে?';
      $('search-submit').querySelector('span').textContent=inputValue('analysis')==='ai'?'Run DeepSeek research':'Search research papers';
    }
    state.analysis=state.task==='claim'?'ai':inputValue('analysis');
    $('admin-box').hidden=state.analysis!=='ai';
  }
  for(const radio of document.querySelectorAll('input[name="task"],input[name="analysis"]'))radio.addEventListener('change',setModes);
  setModes();
  for(const b of document.querySelectorAll('[data-example]'))b.addEventListener('click',()=>{$('question').value=b.dataset.example;$('question').focus();});
  function tabs(){
    for(const b of document.querySelectorAll('[data-tab]')){
      const selected=b.dataset.tab===state.tab;
      b.setAttribute('aria-selected',selected?'true':'false');b.tabIndex=selected?0:-1;
    }
    $('tab-panel').setAttribute('aria-labelledby','tab-'+state.tab);
    $('tab-pico').textContent=state.task==='claim'?'Statement evidence':'PICO evidence';
  }
  function changeTab(tab){if(!['overview','papers','pico','trace'].includes(tab))return;state.tab=tab;tabs();render();}
  for(const b of document.querySelectorAll('[data-tab]')){
    b.addEventListener('click',()=>changeTab(b.dataset.tab));
    b.addEventListener('keydown',e=>{
      if(!['ArrowLeft','ArrowRight'].includes(e.key))return;
      e.preventDefault();const bs=Array.from(document.querySelectorAll('[data-tab]'));
      const next=bs[(bs.indexOf(b)+(e.key==='ArrowRight'?1:-1)+bs.length)%bs.length];
      changeTab(next.dataset.tab);next.focus();
    });
  }
  function validPubmed(p){return /^\d{1,10}$/.test(String(p?.pmid||''));}
  function cite(p,label){
    const pmid=String(p.pmid||'');if(!/^\d{1,10}$/.test(pmid))return node('span',label);
    const a=node('a',label);a.href='https://pubmed.ncbi.nlm.nih.gov/'+pmid+'/';a.target='_blank';a.rel='noopener noreferrer';return a;
  }
  function paperHeader(p,paper,idx){
    const top=add(p,'div',undefined,'paper-top'), info=add(top,'div');
    add(info,'h3',undefined,'paper-title').append(cite(paper,paper.title_en||'Untitled paper'));
    add(info,'p','PMID '+String(paper.pmid||'?')+' · '+String(paper.journal||'Journal unavailable')+' · '+String(paper.year||''),'paper-meta');
    add(top,'div',String(idx+1).padStart(2,'0'),'paper-index');
    if(paper.authors_display)add(info,'p','Authors: '+paper.authors_display,'meta-line');
  }
  function sourceLink(p,link,label,kind='pmc'){
    if(typeof link!=='string')return;
    let u;try{u=new URL(link);}catch{return;}
    if(u.protocol!=='https:')return;
    if(kind==='pmc'&&!(u.hostname==='pmc.ncbi.nlm.nih.gov'&&/^\/articles\/PMC\d+\/$/.test(u.pathname)))return;
    if(kind==='pdf'&&!(u.hostname==='pmc-oa-opendata.s3.amazonaws.com'&&/\.pdf$/.test(u.pathname)))return;
    const a=add(p,'a',label);a.href=link;a.target='_blank';a.rel='noopener noreferrer';
  }
  function matchCard(parent,p,idx){
    const card=add(parent,'article',undefined,'paper');paperHeader(card,p,idx);
    add(card,'span',p.statement_explicitly_present?'Exact statement present in source':'Related discussion · claim not confirmed','match-kind');
    if(p.discussion_assessment)add(card,'p',String(p.discussion_assessment),'note');
    add(card,'p','Location: '+String(p.page_label||'Page number unavailable')+' · '+String(p.section||'Section unavailable'),'meta-line page-number');
    const q=add(card,'blockquote',p.quote_en||'No excerpt','claim-excerpt');q.setAttribute('lang','en');
    const links=add(card,'p',undefined,'meta-line');
    if(p.full_text_url)sourceLink(links,p.full_text_url,'Read full text (PMC)');
    if(p.pdf_url&&Number.isInteger(p.page_number)&&p.page_number>=1){if(links.childNodes.length)add(links,'span','  ·  ');sourceLink(links,p.pdf_url+'#page='+p.page_number,'Open verified PDF viewer page','pdf');}
    add(card,'p',String(p.page_verification_status||'Page not checked')+' · Source passage exists; medical truth is not established.','note');
  }
  function papersView(p,data){
    add(p,'h3',data.report_mode==='claim'?'Matching research papers':'Research papers & citations','pane-title');
    const papers=Array.isArray(data.papers)?data.papers:[];
    if(!papers.length){add(p,'p',data.report_mode==='claim'?'No verifiable passage match in the retrieved, accessible material. This is not proof that the claim is absent from all papers.':'No papers found. Try a different question.','subtle');return;}
    papers.slice(0,data.report_mode==='claim'?5:5).forEach((paper,idx)=>{
      if(data.report_mode==='claim'){matchCard(p,paper,idx);return;}
      const card=add(p,'article',undefined,'paper');paperHeader(card,paper,idx);
      const evidence=Array.isArray(paper.evidence)?paper.evidence:[];
      for(const ev of evidence.slice(0,3)){
        const block=add(card,'blockquote',undefined,'excerpt');
        add(block,'span',String(ev.section||'Abstract')+' · source passage','eyeline');
        add(block,'span',String(ev.quote_en||''));
      }
      if(!evidence.length)add(card,'p',paper.evidence_scope==='metadata_only'?'Abstract unavailable for source-linked PICO extraction.':'No reliable short source excerpt was selected.','note');
    });
  }
  function picoView(p,data){
    if(data.report_mode==='claim'){
      add(p,'h3','Statement evidence & source locations','pane-title');
      add(p,'p','Evidence is matched against actual available passages. A PDF page is displayed only when the excerpt was found in that page’s extracted text.','subtle');
      papersView(p,data);return;
    }
    add(p,'h3','Structured PICO evidence','pane-title');
    add(p,'p',data.model_used?'DeepSeek extracted candidates; each displayed quotation was mechanically checked against a retrieved abstract.':'Source-anchored lexical candidates from accessible PubMed abstracts; no DeepSeek used.','subtle');
    const papers=Array.isArray(data.papers)?data.papers:[];
    if(!papers.length){add(p,'p','No source papers to inspect.','subtle');return;}
    papers.forEach((paper,idx)=>{
      const card=add(p,'article',undefined,'paper');paperHeader(card,paper,idx);
      const fields=paper.pico||paper.pico_ai_candidates||paper.structured?.pico||{};
      const grid=add(card,'div',undefined,'pico-grid');
      for(const [key,label] of Object.entries(PICO)){
        const row=add(grid,'div',undefined,'pico-row');add(row,'span',label,'pico-key');
        const val=fields[key];const txt=add(row,'div',val?.quote_en||'Not identified','pico-text'+(!val?' empty':''));
        if(val)add(txt,'span',String(val.section||'Abstract')+' · candidate, not clinically validated','pico-section');
      }
    });
    notice(p,'An exact excerpt confirms what is written in an abstract, not whether the medical statement is correct.');
  }
  function traceView(p,data){
    add(p,'h3','Agent execution · step by step','pane-title');
    add(p,'p',data.model_used?'The workflow lists real DeepSeek calls and every source check. Open a stage to see which papers were used or rejected.':'Public search uses software-only retrieval, evidence screening and verification.','subtle');
    const traces=Array.isArray(data.agent_trace)?data.agent_trace:[];
    if(!traces.length){notice(p,'No execution record available.');return;}
    const totals=add(p,'div',undefined,'source-note');
    add(totals,'strong','Execution summary');
    add(totals,'p',String(data.model_invocations||0)+' DeepSeek HTTP request(s) · '+String(data.paper_count||0)+' reported paper(s) · '+String(traces.length)+' stages');
    if(data.relevance_audit){const a=data.relevance_audit;
      add(totals,'p','PubMed candidates inspected: '+String(a.candidates_examined||0)+' · Accepted: '+String(a.accepted_candidates||0)+' · Rejected: '+String(a.rejected_candidates||0));
    }
    const grid=add(p,'div',undefined,'trace-grid');grid.classList.add('audit-grid');
    traces.forEach((stage,idx)=>{
      const box=add(grid,'article',undefined,'agent audit-agent');
      add(box,'div',String(idx+1).padStart(2,'0'),'agent-number');
      add(box,'strong',String(stage.agent||'Processing stage'));
      add(box,'p',String(stage.method||''));
      const foot=add(box,'div',undefined,'agent-foot');
      add(foot,'span',stage.model_invoked?'DeepSeek: '+String(stage.model_attempts||1)+' request(s)':'Software only');
      add(foot,'span',String(stage.elapsed_ms||0)+' ms');
      const jobs=Array.isArray(stage.jobs)?stage.jobs:[];
      if(jobs.length){
        const detail=add(box,'details',undefined,'audit-tasks');
        const summary=add(detail,'summary',jobs.length+' recorded task(s) · view details');
        const list=add(detail,'div',undefined,'audit-task-list');
        jobs.slice(0,10).forEach(job=>{
          const item=add(list,'div',undefined,'audit-task');
          add(item,'strong',String(job.action||'Processing task'));
          if(job.pmid) add(item,'span','PMID '+String(job.pmid)+(job.title?' · '+String(job.title):''),'audit-source');
          add(item,'p',String(job.outcome||'Completed'));
        });
      }else add(box,'p','No individual-paper task recorded for this stage.','audit-empty');
    });
    notice(p,'A PMID, excerpt or PDF page can be mechanically checked. Medical correctness and DeepSeek semantic judgments still require expert review.');
  }
  function overviewView(p,data){
    add(p,'h3',data.report_mode==='claim'?'Statement search overview':'Research overview','pane-title');
    const summary=data.report_mode==='claim'?(data.ai_report?.summary_bn||'No verifiable passage match.'):
      (data.ai_report?.summary_bn||data.bangla_report||'Source-linked research results.');
    add(p,'p',summary,'report');
    add(p,'p','English PubMed search: '+String(data.english_search_query||'Not available'),'subtle');
    const info=add(p,'div',undefined,'sources-grid');
    const notes=data.report_mode==='claim'?[
      ['Source papers searched',String(data.searched_papers||0)+' PubMed papers (search is not exhaustive)'],
      ['Verified matching passages',String(data.paper_count||0)+' papers · maximum five'],
      ['Page references','Verified PDF viewer page only; otherwise explicitly unavailable']
    ]:[
      ['Papers',String(data.paper_count||0)+' PubMed source records'],
      ['Evidence',String(data.abstracts_retrieved??data.paper_count??0)+' abstracts or development records'],
      ['Analysis',data.model_used?'Real local DeepSeek inference · administrator-authorized':'Deterministic software extraction · public']
    ];
    for(const [k,v] of notes){const item=add(info,'div',undefined,'source-note');add(item,'strong',k);add(item,'p',v);}
    if(data.report_mode==='claim'&&Array.isArray(data.papers)&&data.papers.length){
      add(p,'h4','Top matches','pane-title');data.papers.slice(0,2).forEach((paper,idx)=>matchCard(p,paper,idx));
    }
    notice(p,data.disclaimer||'Research prototype; no clinical or medical accuracy validation.');
  }
  function render(){
    if(!state.data)return;clear(root);
    if(state.tab==='papers')papersView(root,state.data);
    else if(state.tab==='pico')picoView(root,state.data);
    else if(state.tab==='trace')traceView(root,state.data);
    else overviewView(root,state.data);
  }
  function resultMetrics(data){
    clear($('metrics'));function metric(k,v){const div=add($('metrics'),'div',undefined,'metric');add(div,'span',k,'metric-label');add(div,'strong',String(v??'—'),'metric-value');}
    metric('Report',data.report_mode==='claim'?'Statement location':'Medical literature');
    metric('Papers',data.paper_count||0);
    metric('Analysis',data.model_used?'DeepSeek · '+String(data.model_invocations||0)+' requests':'Evidence only');
    $('result-state').textContent=data.model_used?'Local DeepSeek used':'Source-linked research';
    $('results').hidden=false;tabs();render();
    $('results').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});
  }
  async function json(response){
    const payload=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(typeof payload.detail==='string'?payload.detail:'Research request could not be completed (HTTP '+response.status+').');
    return payload;
  }
  async function regular(question,source){
    const ac=new AbortController(),timeout=setTimeout(()=>ac.abort(),40000);
    try{
      return await json(await fetch('/api/report/search',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({question,source,limit:5}),signal:ac.signal,cache:'no-store'}));
    }finally{clearTimeout(timeout);}
  }
  async function privateAI(question,token,task,pmid){
    const path=task==='claim'?'/api/ai/claims/jobs':'/api/ai/research/jobs';
    const body=task==='claim'?{statement:question,limit:5,...(pmid?{pmid}:{})}:{question,limit:2};
    const headers={'Content-Type':'application/json','X-BMS-AI-Token':token};
    const start=await json(await fetch(path,{method:'POST',headers,body:JSON.stringify(body),cache:'no-store'}));
    if(!/^[a-zA-Z0-9_-]{10,64}$/.test(String(start.job_id||'')))throw new Error('Unexpected private AI job identifier');
    for(let n=0;n<210;n++){
      await new Promise(resolve=>setTimeout(resolve,3000));
      const reply=await json(await fetch(path+'/'+encodeURIComponent(start.job_id),{
        headers:{'X-BMS-AI-Token':token},cache:'no-store'}));
      if(reply.status==='completed')return reply.result;
      if(reply.status==='failed')throw new Error('DeepSeek did not finish the evidence workflow. No claim result was generated. Try again later.');
      status('DeepSeek is running sequential model stages on the CPU-limited server…');
    }
    throw new Error('Local AI job exceeded the polling window.');
  }
  async function submit(){
    if(state.busy)return;
    setModes();
    const question=$('question').value.trim();
    if(question.length<2||question.length>500){status('Enter a question or statement between 2 and 500 characters.',true);return;}
    const pmid=$('paper-pmid').value.trim();
    if(state.task==='claim'&&pmid&&!/^\d{1,10}$/.test(pmid)){status('The optional PMID must contain 1–10 digits.',true);return;}
    const token=$('admin-token').value.trim();
    if(state.analysis==='ai'&&!token){status('Enter your private DeepSeek administrator token above.',true);$('admin-token').focus();return;}
    const task=state.task,analysis=state.analysis;
    state.busy=true;state.data=null;$('results').hidden=true;$('search-submit').disabled=true;
    status(analysis==='ai'?'Starting administrator-authorized DeepSeek research…':'Retrieving papers and source-anchored evidence…');
    try{
      const data=analysis==='ai'?await privateAI(question,token,task,pmid):await regular(question,$('source').value);
      if(!data||!Array.isArray(data.papers)||!Array.isArray(data.agent_trace))throw Error('Research service returned incomplete data.');
      if(task==='claim'&&data.papers.length>5)throw Error('Statement search exceeded the five-paper limit.');
      if(analysis==='ai'&&data.model_used!==true)throw Error('AI request completed without model usage.');
      state.data=data;state.tab=task==='claim'?'papers':'overview';resultMetrics(data);
      status(analysis==='ai'?'DeepSeek completed '+String(data.model_invocations||0)+' actual inference requests. Review source excerpts and citations.':
          'Research report ready. DeepSeek was not used.');
    }catch(e){status(e.name==='AbortError'?'Research timed out. Please try a narrower query.':String(e.message||e),true);}
    finally{state.busy=false;$('search-submit').disabled=false;$('admin-token').value='';}
  }
  $('research-form').addEventListener('submit',e=>{e.preventDefault();submit();});
  tabs();
})();

</script>
</body></html>'''
