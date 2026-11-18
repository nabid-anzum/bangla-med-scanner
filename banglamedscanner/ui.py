"""Self-contained Bangla UI, served from localhost by FastAPI."""
PAGE = '''<!doctype html>
<html lang="bn"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BanglaMedScanner · বাংলা মেডিকেল গবেষণা অনুসন্ধান</title>
<style>
:root{font-family:system-ui,-apple-system,'Noto Sans Bengali',sans-serif;color:#132b3a;background:#f4f7fb}
*{box-sizing:border-box}body{margin:0}main{max-width:920px;margin:0 auto;padding:34px 18px 70px}
header{display:flex;align-items:center;gap:12px;margin-bottom:25px}.mark{width:44px;height:44px;background:#116e76;color:#fff;border-radius:13px;display:grid;place-items:center;font-size:24px}
h1{font-size:25px;letter-spacing:-.5px;margin:0}.subtitle{color:#607482;font-size:13px;margin:4px 0 0}
section,.paper{background:white;border:1px solid #e1e8ed;border-radius:16px;padding:22px;box-shadow:0 4px 16px #15324a08;margin-bottom:18px}
label{display:block;font-weight:650;margin-bottom:8px}textarea,select{width:100%;font:inherit;border:1px solid #c8d6dc;background:#fff;border-radius:9px;padding:12px;outline-offset:2px}
textarea{min-height:95px;resize:vertical}select{max-width:320px}.field{margin-top:14px}
button{cursor:pointer;font:inherit;font-weight:650;background:#116e76;color:#fff;border:0;border-radius:9px;padding:12px 20px;margin-top:16px}button:disabled{opacity:.6;cursor:wait}
.muted{color:#607482;font-size:13px}.pill{display:inline-block;padding:5px 10px;border-radius:20px;background:#e5f5f2;color:#125d65;font-size:12px;margin-right:8px}
a{color:#006b83;text-decoration:none}a:hover{text-decoration:underline}h2{font-size:18px;margin:0 0 14px}h3{font-size:16px;line-height:1.5;margin:0 0 7px}.paper{padding:19px}
.excerpt{font-size:13px;line-height:1.7;background:#f5f7fa;border-left:3px solid #8ba4b1;padding:11px;margin-top:12px}
.notice{font-size:13px;color:#7b5939;background:#fff8ed;border-radius:10px;padding:12px;margin-top:16px}#status{padding-top:12px}.hidden{display:none}
</style></head><body><main><header><div class="mark">✚</div><div><h1>BanglaMedScanner</h1><p class="subtitle">বাংলা প্রশ্ন · ইংরেজি গবেষণাপত্র · উৎস-সংযুক্ত ফলাফল</p></div></header>
<section><form id="form"><label for="question">চিকিৎসা গবেষণা সম্পর্কে বাংলায় প্রশ্ন করুন</label><textarea id="question" minlength="2" maxlength="500" required>ডায়াবেটিসের চিকিৎসায় নতুন গবেষণা কী বলছে?</textarea>
<div class="field"><label for="source">অনুসন্ধানের উৎস</label><select id="source"><option value="corpus">স্থানীয় গবেষণা করপাস (ডেভেলপমেন্ট সেট)</option><option value="live">লাইভ PubMed (শুধু মেটাডেটা)</option></select></div><button id="run" type="submit">গবেষণাপত্র খুঁজুন</button><div id="status" class="muted" role="status"></div></form></section>
<section id="results" class="hidden" aria-live="polite"><h2 id="summary"></h2><div id="details" class="muted"></div><p id="disclaimer" class="notice"></p><div id="papers"></div></section>
<p class="muted">MSc research prototype · Research discovery only · Not medical advice · PubMed / NLM sources</p>
</main><script>
const form=document.querySelector('#form'),run=document.querySelector('#run'),status=document.querySelector('#status');
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n}
form.addEventListener('submit',async e=>{
 e.preventDefault();run.disabled=true;status.textContent='গবেষণাপত্র অনুসন্ধান চলছে...';document.querySelector('#results').classList.add('hidden');
 try{
  const r=await fetch('/api/research',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:document.querySelector('#question').value,source:document.querySelector('#source').value,limit:5})});
  const data=await r.json();if(!r.ok)throw Error(typeof data.detail==='string'?data.detail:'অনুসন্ধান ব্যর্থ হয়েছে');
  document.querySelector('#summary').textContent=data.heading_bn;
  document.querySelector('#details').textContent='ইংরেজি অনুসন্ধান: '+data.interpretation.english_search_query+' · উৎস: '+data.method;
  document.querySelector('#disclaimer').textContent=data.limitations_bn;
  const root=document.querySelector('#papers');root.replaceChildren();
  data.papers.forEach(p=>{
   const card=el('article',undefined,'paper');const title=el('h3');const a=el('a',p.title_en);a.href=p.url;a.target='_blank';a.rel='noopener noreferrer';title.append(a);card.append(title);
   card.append(el('div',[p.journal,p.year,p.study_type].filter(Boolean).join(' · '),'muted'));
   if(p.abstract_excerpt_en)card.append(el('p','English abstract excerpt (not verified clinical evidence): '+p.abstract_excerpt_en,'excerpt'));
   card.append(el('div','PMID: '+p.pmid,'muted'));root.append(card)
  });
  document.querySelector('#results').classList.remove('hidden');status.textContent='অনুসন্ধান সম্পন্ন।';
 }catch(err){status.textContent='ত্রুটি: '+err.message}finally{run.disabled=false}
});
</script></body></html>'''
