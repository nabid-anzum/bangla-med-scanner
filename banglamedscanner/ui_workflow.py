
"""Self-contained visible six-agent orchestration demo."""
PAGE = '''<!doctype html><html lang="bn"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BanglaMedScanner | Research agent workflow</title>
<style>
:root{font:16px/1.5 system-ui,-apple-system,sans-serif;color:#163345;background:#f4f8fa}
*{box-sizing:border-box}body{margin:0}main{max-width:1020px;margin:auto;padding:26px 18px 70px}
a{color:#087581}h1{font-size:27px;margin:10px 0 4px}h2{font-size:19px}
.top{color:#567081;font-size:14px}.panel,.paper{background:white;border:1px solid #d9e5ec;
 border-radius:13px;padding:19px;margin:16px 0;box-shadow:0 2px 10px #16334508}
.warning{background:#fff6df;padding:12px;border-radius:8px;font-size:13px;color:#795413}
textarea{width:100%;min-height:83px;border:1px solid #a3becd;border-radius:8px;padding:12px;
 font:inherit;margin:12px 0 4px}button{background:#087581;color:white;border:0;border-radius:8px;
 padding:12px 18px;font:inherit;font-weight:650;cursor:pointer}button:disabled{opacity:.5}
.flow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:14px 0}
.step{background:#e8f4f2;border:1px solid #c1dfdb;border-radius:11px;padding:12px;
 min-height:104px}.step strong{display:block}.meta{font-size:12px;color:#50727a}
.quote{border-left:3px solid #0d7c76;margin:8px 0;padding:7px 12px;background:#f6fafb;font-size:14px}
.k{font-weight:650}.field{border-bottom:1px solid #e7edef;padding:8px 0}.sm{color:#607583;font-size:13px}
@media(max-width:700px){.flow{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:460px){.flow{grid-template-columns:1fr}}
</style></head><body><main>
<p class="top"><a href="/">Research search</a> · <a href="/structured">PICO extraction</a> · <a href="https://github.com/nabid-anzum/bangla-med-scanner" target="_blank" rel="noopener noreferrer">GitHub source</a></p>
<h1>BanglaMedScanner · agent orchestration</h1>
<p class="top">Demonstrate six auditable software agents. Only the separate administrator-protected synthesis feature uses DeepSeek.</p>
<div class="warning">Research and classroom demonstration only. These agents are deterministic components, not six autonomous LLMs. PICO mentions are candidates requiring review, not clinical findings. Do not submit private patient information.</div>
<section class="panel"><form id="ask">
<label for="question" class="k">Bangla medical literature question</label>
<textarea id="question" minlength="2" maxlength="500" required>ডায়াবেটিসের চিকিৎসায় নতুন গবেষণা কী বলছে?</textarea>
<button id="run" type="submit">Run 6-agent workflow</button>
<p role="status" aria-live="polite" id="status" class="sm"></p></form></section>
<section class="panel" id="results" hidden>
<h2>Agent execution trace</h2><p id="summary" class="sm"></p><div class="flow" id="trace"></div>
<h2>Bangla metadata report</h2><p id="report"></p><p id="meta" class="sm"></p>
<h2>PubMed evidence & source-anchored PICO candidates</h2><div id="papers"></div>
</section>
<section class="panel sm"><strong>AI model:</strong> DeepSeek-R1-Distill-Qwen-1.5B (self-hosted through llama.cpp). It is invoked only by the separate administrator-authenticated AI job feature; this demo uses no model tokens. <a href="https://github.com/deepseek-ai/DeepSeek-R1" target="_blank" rel="noopener noreferrer">Official DeepSeek GitHub</a> · <a href="https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B" target="_blank" rel="noopener noreferrer">Model weights</a>.</section>
</main><script>
const q=id=>document.getElementById(id);
const el=(tag,text,klass)=>{const x=document.createElement(tag);if(text!==undefined)x.textContent=String(text);if(klass)x.className=klass;return x;};
q('ask').addEventListener('submit',async e=>{
 e.preventDefault();q('run').disabled=true;q('status').textContent='Running six source-grounded agents...';
 q('results').hidden=true;q('trace').replaceChildren();q('papers').replaceChildren();
 try{
  const resp=await fetch('/api/orchestrate',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({question:q('question').value,limit:3})});
  const d=await resp.json();if(!resp.ok)throw Error(typeof d.detail==='string'?d.detail:'Workflow unavailable');
  q('summary').textContent='Topic: '+d.topic+' | Search: '+d.english_search_query+' | Papers: '+d.paper_count+' | Request: '+d.request_id;
  for(const [i,agent] of d.agent_trace.entries()){
   const card=el('div',undefined,'step');card.append(el('strong',(i+1)+'. '+agent.agent));
   card.append(el('div',agent.method,'meta'));
   card.append(el('div',agent.status+' · '+agent.elapsed_ms+' ms','meta'));
   q('trace').append(card);
  }
  q('report').textContent=d.bangla_report;
  q('meta').textContent='AI model not called · held-out exposure: '+d.heldout_exposure+' · clinical validation: '+d.clinically_validated;
  const labels={population:'Population',intervention:'Intervention',comparator:'Comparator',outcome:'Outcome',result:'Reported result'};
  for(const p of d.papers){
   const box=el('article',undefined,'paper'),h=el('h2'),a=el('a',p.title_en);
   a.href=p.url;a.target='_blank';a.rel='noopener noreferrer';h.append(a);box.append(h);
   box.append(el('p','PMID '+p.pmid+' · '+p.year+' · '+p.journal,'sm'));
   for(const excerpt of p.evidence){box.append(el('blockquote',excerpt.quote_en,'quote'));}
   for(const [field,label] of Object.entries(labels)){
    const node=el('div',undefined,'field'),item=p.pico[field];node.append(el('span',label+': ','k'));
    node.append(el('span',item?item.quote_en+' [candidate; '+item.section+']':'Not identified with sufficient section evidence','sm'));
    box.append(node);
   }q('papers').append(box);
  }
  q('results').hidden=false;q('status').textContent='Workflow completed. All visible citations have been checked against the source.';
 }catch(error){q('status').textContent='Request unavailable: '+error.message;}
 finally{q('run').disabled=false;}
});
</script></body></html>'''
