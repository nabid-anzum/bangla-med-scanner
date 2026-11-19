"""Static, no-third-party-assets UI for source-anchored structured research."""
PAGE = '''<!doctype html>
<html lang="bn"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Structured Evidence | BanglaMedScanner</title>
<style>
:root{font:16px/1.55 system-ui,-apple-system,sans-serif;color:#193449;background:#f3f7fa}
*{box-sizing:border-box}body{margin:0}main{max-width:980px;margin:auto;padding:30px 16px 60px}
h1{font-size:25px;margin:0 0 8px}h2{font-size:18px;margin:16px 0 8px}p{margin:8px 0 15px}
.panel,.paper{border:1px solid #dce5eb;border-radius:14px;padding:20px;background:#fff;margin:15px 0}
label{display:block;font-weight:700;margin:12px 0 7px}textarea{width:100%;font:inherit;padding:12px;
min-height:92px;border:1px solid #9fb7c5;border-radius:9px;resize:vertical}
button{margin-top:12px;border:0;border-radius:9px;padding:12px 20px;background:#126a72;color:white;
font:inherit;font-weight:700;cursor:pointer}button:disabled{opacity:.65;cursor:wait}
a{color:#126a72}.secondary{color:#5b6f7e;font-size:14px}.warning{background:#fff5e8;padding:12px;
border-radius:9px;color:#80551e;font-size:13px}.field{padding:9px 0;border-bottom:1px solid #e7edf1}
.field:last-child{border-bottom:0}.name{display:inline-block;min-width:120px;font-weight:650}
blockquote{margin:6px 0 5px;padding:10px 13px;background:#f5f8fa;border-left:3px solid #126a72;
font-size:14px;overflow-wrap:anywhere}.empty{font-style:italic;color:#6e7e87}.state{margin-top:12px}
</style></head><body><main>
<p><a href="/">Main research demo</a></p>
<h1>BanglaMedScanner: structured evidence candidates</h1>
<p class="secondary">Bangla questions, English PubMed abstracts, citation-anchored PICO fields.</p>
<div class="warning">Research prototype only. This view flags candidate text; it does not validate
medical claims, infer treatment effectiveness, or give medical advice. Do not enter private patient details.</div>
<section class="panel"><form id="f">
<label for="q">Medical research question (Bangla or supported English topic)</label>
<textarea id="q" minlength="2" maxlength="500" required
placeholder="Enter a Bangla question about diabetes, asthma, hypertension, COPD or depression"></textarea>
<button type="submit" id="go">Extract structured candidates</button>
<div id="status" role="status" aria-live="polite" class="state secondary"></div>
</form></section>
<section id="output" hidden aria-live="polite"><h2 id="heading"></h2>
<p class="secondary" id="query"></p><div id="papers"></div></section>
<p class="secondary">Only the development split is searched. All candidate fields require human review.
The separate local DeepSeek feature remains administrator-protected on the main demo.</p>
</main><script>
const form=document.getElementById('f'),btn=document.getElementById('go'),
 status=document.getElementById('status'),root=document.getElementById('papers');
const labels={population:'Population',intervention:'Intervention',comparator:'Comparator',
 outcome:'Outcome',result:'Reported result candidate'};
const make=(tag,text,cls)=>{let e=document.createElement(tag);if(text!==undefined)e.textContent=text;
 if(cls)e.className=cls;return e;};
form.addEventListener('submit',async(ev)=>{
 ev.preventDefault();btn.disabled=true;status.textContent='Searching source abstracts...';
 document.getElementById('output').hidden=true;root.replaceChildren();
 try{
  const response=await fetch('/api/structured',{method:'POST',
   headers:{'Content-Type':'application/json'},body:JSON.stringify({question:document.getElementById('q').value,limit:3})});
  const data=await response.json();
  if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'Research request failed');
  document.getElementById('heading').textContent='Studies retrieved: '+data.paper_count;
  document.getElementById('query').textContent='English query: '+data.english_search_query;
  for(const paper of data.papers){
   const card=make('article',undefined,'paper'),headline=make('h2');
   const link=make('a',paper.title_en);link.href=paper.url;link.target='_blank';link.rel='noopener noreferrer';
   headline.append(link);card.append(headline);
   card.append(make('p','PMID: '+paper.pmid+' | '+paper.year+' | '+paper.journal,'secondary'));
   for(const [key,field] of Object.entries(paper.structured.pico)){
    const line=make('div',undefined,'field');line.append(make('span',labels[key]||key,'name'));
    if(field){line.append(make('blockquote',field.quote_en));
     line.append(make('div','Abstract section: '+field.section+' | Candidate, not a validated finding','secondary'));}
    else line.append(make('span','Not identified from abstract','empty'));
    card.append(line);
   }
   card.append(make('p','Metadata study type: '+(paper.structured.study_design.publication_type_metadata||'Unspecified')+'. Not independently appraised.','secondary'));
   root.append(card);
  }
  document.getElementById('output').hidden=false;
  status.textContent='Extraction completed. Verify each candidate against the original article.';
 }catch(error){status.textContent='Error: '+error.message;}
 finally{btn.disabled=false;}
});
</script></body></html>'''
