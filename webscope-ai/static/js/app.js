let currentReport = null;
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function notify(message, type="danger"){const n=$("notice");n.className=`alert alert-${type} mt-3`;n.textContent=message;}
function hideNotice(){$("notice").className="alert d-none mt-3";}
async function api(url, opts={}){const r=await fetch(url,opts);const d=await r.json();if(!r.ok)throw new Error(d.error||"Request failed");return d;}
async function startScrape(){
 hideNotice(); const url=$("urlInput").value.trim(); if(!url){notify("Please enter a website URL.");$("urlInput").focus();return;}
 $("scrapeBtn").disabled=true;$("loading").classList.remove("d-none");
 try{const result=await api("/api/scrape",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url,options:{mode:$("mode").value,max_pages:$("maxPages").value,max_depth:$("maxDepth").value,include:$("include").value,exclude:$("exclude").value}})});
 currentReport=result.report;renderReport(currentReport);await loadHistory();$("results").classList.remove("d-none");$("results").scrollIntoView({behavior:"smooth",block:"start"});notify("Website analysis completed successfully.","success");
 }catch(e){notify(e.message);}finally{$("scrapeBtn").disabled=false;$("loading").classList.add("d-none");}
}
function card(label,value){return `<div class="data-card"><small>${esc(label)}</small><p>${esc(value||"Not Found")}</p></div>`;}
function listTable(items,cols){if(!items?.length)return '<p class="text-secondary small">Not Found</p>';return `<div class="table-responsive"><table class="table table-sm"><thead><tr>${cols.map(c=>`<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${items.map(x=>`<tr>${cols.map(c=>`<td>${esc(typeof x==="string"?x:x[c.toLowerCase()]??x[c]??"")}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;}
function renderReport(r){
 $("resultTitle").textContent=r.name||"Website report";$("resultUrl").textContent=r.url;$("resultUrl").href=r.url;
 document.querySelectorAll(".export-link").forEach(a=>a.href=`/api/export/${r.id}/${a.dataset.fmt}`);
 showTab("overview");document.querySelectorAll("[data-tab]").forEach(b=>b.onclick=()=>showTab(b.dataset.tab));
}
function showTab(tab){
 document.querySelectorAll("[data-tab]").forEach(b=>b.classList.toggle("active",b.dataset.tab===tab));
 const r=currentReport,pages=r.pages||[],c=r.contacts||{},ins=r.insights||{},t=r.technical||{};let html="";
 if(tab==="overview")html=`<div class="data-grid">${card("Website",r.name)}${card("Website category",r.category)}${card("Page title",r.title)}${card("Pages extracted",r.page_count)}${card("Description",r.description)}${card("Crawl completed",r.extracted_at)}</div><h6 class="mt-4">Page discovery</h6>${listTable(pages.map(p=>({url:p.url,title:p.title,status:p.status})),["url","title","status"])}`;
 if(tab==="content")html=pages.map(p=>`<div class="content-page"><h5>${esc(p.title||p.url)}</h5><small class="text-secondary">${esc(p.url)}</small><p class="mt-2">${esc(p.text?.slice(0,1600)||"Not Found")}</p>${Object.entries(p.headings||{}).filter(x=>x[1].length).map(([k,v])=>`<div><b class="small">${k.toUpperCase()}</b> ${v.map(x=>`<span class="tag">${esc(x)}</span>`).join("")}</div>`).join("")}</div>`).join("");
 if(tab==="products")html=`<div class="alert alert-secondary small">Structured product/service extraction is not available for every site. This starter version does not infer product names or prices unless a dedicated structured-data extractor is added. No unsupported product or price claims are shown.</div>`;
 if(tab==="contact")html=`<div class="data-grid">${card("Email addresses",c.emails?.join(", "))}${card("Phone numbers",c.phones?.join(", "))}${card("Social links",c.social_links?.join(", "))}</div>`;
 if(tab==="links")html=listTable(r.links||[],["url","text","type"]);
 if(tab==="media")html=listTable(r.images||[],["url","alt"]);
 if(tab==="seo")html=`<div class="data-grid">${card("HTTP status",t.http_status)}${card("Language",t.language)}${card("Canonical URL",t.canonical)}${card("Robots meta",t.robots_meta)}${card("robots.txt",t.robots_txt)}</div>`;
 if(tab==="insights")html=`<div class="data-card mb-3"><small>WEBSITE SUMMARY</small><p>${esc(ins.summary)}</p></div><div class="data-card mb-3"><small>LIKELY PURPOSE</small><p>${esc(ins.purpose)}</p></div><h6>Keywords</h6>${(ins.keywords||[]).map(x=>`<span class="tag">${esc(x)}</span>`).join("")}<h6 class="mt-4">Suggested FAQs</h6>${(ins.faq||[]).map(x=>`<div class="content-page"><b>${esc(x.question)}</b><p>${esc(x.answer)}</p></div>`).join("")}<ul class="small text-secondary mt-3">${(ins.limitations||[]).map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`;
 if(tab==="raw")html=`<pre class="code-view">${esc(JSON.stringify(r,null,2))}</pre>`;
 $("tabContent").innerHTML=html||'<p class="text-secondary">No data available.</p>';
}
async function loadHistory(){
 try{const items=await api("/api/history");$("historyList").innerHTML=items.length?items.map(x=>`<div class="history-row"><div><b>${esc(x.url)}</b><small>${esc(x.created_at)}</small></div><div class="d-flex gap-2"><button class="btn btn-sm btn-outline-primary" onclick="openReport(${x.id})">Open</button><button class="btn btn-sm btn-outline-danger" onclick="deleteReport(${x.id})">Delete</button></div></div>`).join(""):'<div class="empty-state">No reports yet. Analyze a website to get started.</div>';
 let pages=0;items.forEach(x=>{});$("statSites").textContent=items.length;$("statSuccess").textContent=items.length;
 }catch(e){console.error(e);}
}
async function openReport(id){try{const x=await api(`/api/reports/${id}`);currentReport=x.data;currentReport.id=x.id;renderReport(currentReport);$("results").classList.remove("d-none");$("results").scrollIntoView({behavior:"smooth"});}catch(e){notify(e.message);}}
async function deleteReport(id){if(!confirm("Delete this saved report?"))return;await api(`/api/reports/${id}`,{method:"DELETE"});loadHistory();}
$("scrapeBtn").addEventListener("click",startScrape);$("urlInput").addEventListener("keydown",e=>{if(e.key==="Enter")startScrape();});$("refreshHistory").onclick=loadHistory;
$("themeBtn").onclick=()=>{const root=document.documentElement;root.dataset.bsTheme=root.dataset.bsTheme==="dark"?"light":"dark";};
loadHistory();
