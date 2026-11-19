"""Enhance the existing research-search page with a structured evidence view."""

EVIDENCE_HTML = '''
<section id="evidence-tool">
<h2>গবেষণা প্রমাণ বিশ্লেষণ</h2>
<p class="muted">পাঁচ ধাপের উৎস-নির্ভর গবেষণা প্রক্রিয়া: বাংলা প্রশ্ন, প্রাসঙ্গিক নথি, উদ্ধৃতি, সূত্র যাচাই, বাংলা বিবরণ।</p>
<button id="evidence-run" type="button">নির্বাচিত প্রশ্নের প্রমাণ বিশ্লেষণ করুন</button>
<label class="field" style="font-weight:400"><input id="ai-toggle" type="checkbox" disabled> লোকাল DeepSeek বাংলা সারাংশ (শুধু প্রশাসকের জন্য)</label>
<label class="field" for="ai-access-token">Private AI administrator token — শুধু AI ব্যবহারের জন্য</label>
<input id="ai-access-token" type="password" autocomplete="off" spellcheck="false" placeholder="AI synthesis needs your private token" maxlength="256" style="width:100%;padding:10px;border:1px solid #c8d6dc;border-radius:9px">
<p class="muted">মডেল VPS-এ চলে; বাইরের AI API ব্যবহার হয় না। সারাংশ গবেষণার সহায়ক, চিকিৎসা পরামর্শ নয়।</p>
<div id="evidence-status" class="muted" role="status"></div>
<div id="evidence-results" aria-live="polite"></div>
</section>
'''

EVIDENCE_JS = r'''<script>
(()=>{
 const button=document.getElementById('evidence-run');
 const status=document.getElementById('evidence-status');
 const output=document.getElementById('evidence-results');
 const toggle=document.getElementById('ai-toggle');
 function add(tag,content,cls){const el=document.createElement(tag);if(content!==undefined)el.textContent=content;if(cls)el.className=cls;return el}
 fetch('/api/ai/status').then(r=>r.json()).then(d=>{toggle.disabled=!d.configured;}).catch(()=>{});
 button.addEventListener('click',async()=>{
  button.disabled=true;status.textContent='প্রমাণ উদ্ধৃতি ও সূত্র যাচাই চলছে...';output.replaceChildren();
  try{
   const question=document.getElementById('question').value;
   let result;
   if(toggle.checked){
    const token=document.getElementById('ai-access-token').value;
    if(!token)throw new Error('AI administrator token লিখুন।');
    const authHeaders={'Content-Type':'application/json','X-BMS-AI-Token':token};
    const jobResponse=await fetch('/api/ai/jobs',{method:'POST',headers:authHeaders,body:JSON.stringify({question,limit:2,ai_summary:true})});
    const job=await jobResponse.json();if(!jobResponse.ok)throw new Error(typeof job.detail==='string'?job.detail:'AI job failed');
    let finished=false;
    for(let attempt=0;attempt<110;attempt++){
     await new Promise(resolve=>setTimeout(resolve,2000));
     const poll=await fetch('/api/ai/jobs/'+encodeURIComponent(job.job_id),{headers:{'X-BMS-AI-Token':token}});
     const progress=await poll.json();if(!poll.ok)throw new Error(typeof progress.detail==='string'?progress.detail:'AI progress unavailable');
     if(progress.status==='completed'){result=progress.result;finished=true;break;}
     if(progress.status==='failed')throw new Error(progress.detail||'Local AI synthesis failed');
     status.textContent='লোকাল AI মডেল প্রমাণ বিশ্লেষণ করছে...';
    }
    if(!finished)throw new Error('Local model response timed out; try the non-AI evidence view.');
   }else{
    const response=await fetch('/api/evidence',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question,limit:3,ai_summary:false})});
    result=await response.json();if(!response.ok)throw new Error(typeof result.detail==='string'?result.detail:'ত্রুটি হয়েছে');
   }
   output.append(add('p',result.bangla_report,'notice'));
   if(result.ai_report){
    output.append(add('h3','AI-ভিত্তিক বাংলা সারাংশ — চিকিৎসাগতভাবে স্বতন্ত্রভাবে যাচাই করা হয়নি'));
    output.append(add('p',result.ai_report.summary_bn));
    for(const x of result.ai_report.paper_explanations)output.append(add('p','PMID '+x.pmid+': '+x.explanation_bn));
   }
   for(const paper of result.papers){
    const card=add('article',undefined,'paper'); const heading=add('h3');const link=add('a',paper.title_en);link.href=paper.url;link.target='_blank';link.rel='noopener noreferrer';heading.append(link);card.append(heading);
    card.append(add('p','PMID: '+paper.pmid+' · '+paper.year+' · '+paper.journal,'muted'));
    for(const excerpt of paper.evidence){card.append(add('p',excerpt.section.toUpperCase()+': '+excerpt.quote_en,'excerpt'))}
    output.append(card);
   }
   output.append(add('p',result.disclaimer_bn,'notice'));
   status.textContent='প্রমাণ বিশ্লেষণ সম্পন্ন।';
  }catch(e){status.textContent='ত্রুটি: '+e.message}finally{button.disabled=false}
 });
})();
</script>'''


def enhance(page):
    if page.count('</main><script>') != 1 or page.count('</body></html>') != 1:
        raise ValueError('Existing HTML structure changed; refusing injection')
    return (page.replace('</main><script>', EVIDENCE_HTML + '</main><script>')
                .replace('</body></html>', EVIDENCE_JS + '</body></html>'))
