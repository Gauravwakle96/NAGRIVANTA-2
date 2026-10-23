'use strict';

const state = { user: null, csrf: '', catalog: null, view: '', map: null, toastTimer: null };
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const roleLabels = {citizen:'Citizen',municipal_admin:'Municipal administrator',field_worker:'Field worker',inspector:'Inspector',system_admin:'System administrator'};
const statusLabels = {submitted:'Submitted',assigned:'Assigned',in_progress:'Work in progress',repair_submitted:'Awaiting inspection',needs_rework:'Rework required',verified:'Resolved'};
const navByRole = {
  citizen:[['home','My complaints','▤'],['new','Report an issue','＋'],['heritage','Heritage watch','⌖'],['notifications','Notifications','♧']],
  municipal_admin:[['home','Operations','▦'],['heritage','Heritage watch','⌖'],['analytics','Analytics','◷'],['notifications','Notifications','♧']],
  field_worker:[['home','My work queue','▤'],['heritage','Heritage watch','⌖'],['notifications','Notifications','♧']],
  inspector:[['home','Inspection queue','✓'],['heritage','Heritage watch','⌖'],['notifications','Notifications','♧']],
  system_admin:[['home','Administration','⚙'],['heritage','Heritage watch','⌖'],['analytics','Analytics','◷'],['notifications','Notifications','♧']]
};

async function api(path, options = {}) {
  const method = options.method || 'GET';
  const headers = new Headers(options.headers || {});
  if (options.body && typeof options.body !== 'string') {
    headers.set('Content-Type','application/json');
    options.body = JSON.stringify(options.body);
  }
  if (method !== 'GET' && method !== 'HEAD' && !path.startsWith('/api/auth/login') && !path.startsWith('/api/auth/register') && path !== '/api/triage') {
    headers.set('X-CSRF-Token', state.csrf);
  }
  const response = await fetch(path,{...options,method,headers,credentials:'same-origin'});
  const type = response.headers.get('content-type') || '';
  if (type.includes('application/json')) {
    const payload = await response.json();
    if (!response.ok) {
      if (response.status === 401 && state.user && !path.startsWith('/api/auth/')) signOutLocal('Your session expired. Please sign in again.');
      throw new Error(payload.error || 'The request could not be completed.');
    }
    return payload;
  }
  if (!response.ok) throw new Error('The request could not be completed.');
  return response;
}

function showAuth(message = '') {
  state.user = null; state.csrf = '';
  $('#appShell').classList.add('hidden'); $('#authShell').classList.remove('hidden');
  $('#authMessage').textContent = message;
  $('#loginForm').classList.remove('hidden'); $('#registerForm').classList.add('hidden');
  setAuthTab('login');
}
function signOutLocal(message = '') { showAuth(message); }
function setAuthTab(mode) {
  const login = mode === 'login';
  $('#loginTab').classList.toggle('active',login); $('#registerTab').classList.toggle('active',!login);
  $('#loginTab').setAttribute('aria-selected',String(login)); $('#registerTab').setAttribute('aria-selected',String(!login));
  $('#loginForm').classList.toggle('hidden',!login); $('#registerForm').classList.toggle('hidden',login);
  $('#authHeading').textContent = login ? 'Sign in to your workspace' : 'Create a citizen account';
  $('#authMessage').textContent = '';
}
function initials(name) { return String(name || 'N').split(/\s+/).slice(0,2).map(x=>x[0]||'').join('').toUpperCase(); }
function showToast(message, error = false) {
  const toast = $('#toast'); toast.textContent = message; toast.classList.remove('hidden','error');
  if (error) toast.classList.add('error');
  clearTimeout(state.toastTimer); state.toastTimer = setTimeout(()=>toast.classList.add('hidden'),4200);
}
function statusBadge(status) { return `<span class="status-badge status-${escapeHTML(status)}">${escapeHTML(statusLabels[status] || status)}</span>`; }
function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value); return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'});
}
function evidenceLink(id, label) {
  if (!id) return `<div class="evidence-placeholder">No ${escapeHTML(label.toLowerCase())} attached</div>`;
  return `<a class="evidence-link" href="/api/evidence/${encodeURIComponent(id)}" target="_blank" rel="noopener"><img src="/api/evidence/${encodeURIComponent(id)}" alt="${escapeHTML(label)}" loading="lazy" /><span>${escapeHTML(label)} · open</span></a>`;
}

async function enterApp(payload) {
  state.user = payload.user; state.csrf = payload.csrf_token;
  $('#authShell').classList.add('hidden'); $('#appShell').classList.remove('hidden');
  $('#userName').textContent = state.user.display_name; $('#userRole').textContent = roleLabels[state.user.role] || state.user.role;
  $('#userInitials').textContent = initials(state.user.display_name);
  state.catalog = await api('/api/catalog');
  renderNav();
  await goTo(navByRole[state.user.role][0][0]);
  refreshNotifications().catch(()=>{});
}
function renderNav() {
  $('#roleNav').innerHTML = navByRole[state.user.role].map(([key,label,icon])=>`<button class="nav-item ${state.view===key?'active':''}" type="button" data-view="${key}"><span aria-hidden="true">${icon}</span>${label}</button>`).join('');
}
async function goTo(view) {
  state.view = view; state.map = null; renderNav();
  const root = $('#viewRoot'); root.innerHTML = '<div class="loading-card"><span class="spinner"></span> Loading your workspace…</div>';
  try {
    if (view === 'new' && state.user.role === 'citizen') return renderCitizenForm();
    if (view === 'heritage') return await renderHeritage();
    if (view === 'notifications') return await renderNotifications();
    if (view === 'analytics') return await renderAnalytics();
    if (state.user.role === 'system_admin') return await renderAdmin();
    if (state.user.role === 'municipal_admin') return await renderMunicipal();
    if (state.user.role === 'field_worker') return await renderWorker();
    if (state.user.role === 'inspector') return await renderInspector();
    return await renderCitizenHome();
  } catch (error) {
    root.innerHTML = `<div class="empty-state"><span class="empty-icon">!</span><h2>Could not load this view</h2><p>${escapeHTML(error.message)}</p><button class="button secondary" data-action="refresh">Try again</button></div>`;
  }
}
function heading(eyebrow,title,description,action='') {
  return `<div class="page-heading"><div><div class="eyebrow">${escapeHTML(eyebrow)}</div><h1>${escapeHTML(title)}</h1><p>${escapeHTML(description)}</p></div>${action}</div>`;
}
function categoryOptions() {
  return (state.catalog?.categories || []).map(group=>`<optgroup label="${escapeHTML(group.name)}">${group.subcategories.map(sub=>`<option value="${escapeHTML(JSON.stringify([group.name,sub.name]))}">${escapeHTML(sub.name)}</option>`).join('')}</optgroup>`).join('');
}
function statusTimeline(events=[]) {
  if (!events.length) return '<p class="muted">No workflow history yet.</p>';
  return `<ol class="timeline">${events.map(item=>`<li><span class="timeline-dot"></span><div><b>${escapeHTML(item.action)}</b><time>${escapeHTML(formatDate(item.at))}</time>${item.note?`<p>${escapeHTML(item.note)}</p>`:''}</div></li>`).join('')}</ol>`;
}
function reportCard(report,extra='') {
  const history = report.repair_history?.length || report.inspection_history?.length;
  const detailedHistory = history ? `<details class="history"><summary>Repair and inspection history · ${(report.repair_history?.length||0)+(report.inspection_history?.length||0)} records</summary>${(report.repair_history||[]).map(r=>`<div class="note-box"><b>Repair by ${escapeHTML(r.worker)} · ${escapeHTML(formatDate(r.created_at))}</b><p>${escapeHTML(r.repair_note)}</p>${evidenceLink(r.evidence_id,'Submitted repair evidence')}</div>`).join('')}${(report.inspection_history||[]).map(i=>`<div class="note-box"><b>${i.approved?'Approved':'Rework requested'} by ${escapeHTML(i.inspector)} · ${escapeHTML(formatDate(i.created_at))}</b><p>${escapeHTML(i.notes)}</p></div>`).join('')}</details>` : '';
  return `<article class="report-card" data-report="${escapeHTML(report.id)}"><div class="report-card-top"><div><div class="eyebrow">${escapeHTML(report.id)}${report.synthetic?' · SYNTHETIC':''}</div><h3>${escapeHTML(report.title)}</h3></div>${statusBadge(report.status)}</div><p class="report-summary">${escapeHTML(report.description)}</p><div class="report-meta"><span>⌖ ${escapeHTML(report.area)} · ${escapeHTML(report.address)}</span><span>${escapeHTML(report.category_group || report.category)}${report.subcategory?` / ${escapeHTML(report.subcategory)}`:''}</span><span>Updated ${escapeHTML(formatDate(report.updated_at))}</span>${report.department?`<span>Department: ${escapeHTML(report.department)}</span>`:''}${report.priority?`<span>Priority ${escapeHTML(report.priority)}</span>`:''}</div><div class="evidence-row">${evidenceLink(report.before_evidence_id,'Reported evidence')}${report.after_evidence_id?evidenceLink(report.after_evidence_id,'Repair evidence'):''}</div>${report.repair_note?`<div class="note-box"><b>Repair note</b><p>${escapeHTML(report.repair_note)}</p></div>`:''}${report.verification?`<div class="note-box"><b>Inspection · ${report.verification.approved?'Approved':'Rework requested'}</b><p>${escapeHTML(report.verification.notes)}</p></div>`:''}${extra}${report.events?`<details class="history"><summary>Complaint timeline</summary>${statusTimeline(report.events)}</details>`:''}${detailedHistory}</article>`;
}
async function renderCitizenHome() {
  const root=$('#viewRoot'); const {reports}=await api('/api/reports');
  const sorted=reports;
  root.innerHTML=heading('CITIZEN PORTAL','Your civic reports','Track updates from submission through field work and inspection.',`<button class="button primary" data-view="new">＋ Report an issue</button>`)+
    `<section class="stat-grid compact"><div class="stat-card"><small>Your reports</small><b>${sorted.length}</b><span>All statuses</span></div><div class="stat-card"><small>In progress</small><b>${sorted.filter(r=>!['verified','submitted'].includes(r.status)).length}</b><span>Assigned or being reviewed</span></div><div class="stat-card"><small>Resolved</small><b>${sorted.filter(r=>r.status==='verified').length}</b><span>Inspection-approved</span></div></section>`+
    `<div class="section-heading"><div><h2>Complaint history</h2><p>Your submissions only</p></div><div class="filter-controls"><input id="reportSearch" aria-label="Search my complaints" placeholder="Search your reports" /><select id="reportStatus" aria-label="Filter by status"><option value="">All statuses</option>${Object.entries(statusLabels).map(([key,label])=>`<option value="${key}">${label}</option>`).join('')}</select></div></div>`+
    `<div class="report-list" id="citizenReports">${sorted.length?sorted.map(r=>reportCard(r)).join(''):'<div class="empty-state"><span class="empty-icon">＋</span><h2>No complaints yet</h2><p>Submit a civic issue to begin tracking the response.</p><button class="button primary" data-view="new">Report an issue</button></div>'}</div>`;
  const filter=()=>{const q=$('#reportSearch').value.toLowerCase(),s=$('#reportStatus').value;$$('#citizenReports .report-card').forEach(card=>{const match=card.textContent.toLowerCase().includes(q)&&(!s||card.querySelector('.status-badge')?.classList.contains('status-'+s));card.classList.toggle('hidden',!match);});};
  $('#reportSearch').addEventListener('input',filter); $('#reportStatus').addEventListener('change',filter);
}
function renderCitizenForm() {
  const root=$('#viewRoot');
  root.innerHTML=heading('CITIZEN PORTAL','Report a civic issue','Share a clear location and supporting evidence. Recommendations are reviewed by municipal staff.')+
    `<form id="reportForm" class="form-card"><div class="form-grid"><label>Issue category and subcategory<select id="issueCategory" required><option value="" disabled selected>Select a category and issue</option>${categoryOptions()}</select></label><div class="field-hint" id="routeHint">Suggested department appears after you select an issue.</div><label>Short title<input name="title" required maxlength="100" placeholder="e.g. Blocked drain near the clinic" /></label><label>Ward or locality<input name="area" required maxlength="100" placeholder="Ward, neighborhood or locality" /></label><label class="span-two">Specific location<input name="address" required maxlength="240" placeholder="Street, landmark or nearest public place" /></label><label class="span-two">What is happening?<textarea name="description" rows="4" required maxlength="1200" placeholder="Describe the issue, when you noticed it and any public safety concern."></textarea></label><div class="span-two triage-box"><button class="button secondary small" id="triageButton" type="button">Suggest category · rule-based</button><span id="triageHint">A transparent keyword suggestion; not an AI model or an official decision.</span></div><label>Latitude <span class="hint">optional</span><input name="latitude" type="number" step="any" min="-90" max="90" placeholder="e.g. 18.5204" /></label><label>Longitude <span class="hint">optional</span><input name="longitude" type="number" step="any" min="-180" max="180" placeholder="e.g. 73.8567" /></label><label class="span-two upload-field">Photo evidence <small>PNG, JPEG or WebP · max 1 MB · avoid faces and private information</small><input name="photo" type="file" accept="image/png,image/jpeg,image/webp" required /></label></div><div class="form-bottom"><p class="muted">Do not use this form for emergencies. No official government connection is implied.</p><button class="button primary" type="submit">Submit complaint <span aria-hidden="true">→</span></button></div><p id="reportMessage" class="form-message" role="alert"></p></form>`;
  const category=$('#issueCategory'); const hint=$('#routeHint');
  const updateRoute=()=>{try{const [group,sub]=JSON.parse(category.value);const detail=state.catalog.categories.find(x=>x.name===group)?.subcategories.find(x=>x.name===sub);hint.innerHTML=`Suggested route: <b>${escapeHTML(detail?.department||'Municipal review')}</b> · human review required`; }catch{}};
  category.addEventListener('change',updateRoute); updateRoute();
  $('#triageButton').addEventListener('click',async()=>{const desc=$('#reportForm [name="description"]').value; if(!desc.trim()){showToast('Add a description before requesting a suggestion.',true);return;}try{const result=await api('/api/triage',{method:'POST',body:{description:desc}});const r=result.recommendation;$('#triageHint').textContent=r.category?`Rule matched ${r.category} / ${r.subcategory}; ${r.explanation}`:r.explanation;if(r.category){const value=JSON.stringify([r.category,r.subcategory]);if([...category.options].some(o=>o.value===value))category.value=value;updateRoute();}}catch(e){showToast(e.message,true);}});
  $('#reportForm').addEventListener('submit',submitComplaint);
}
async function fileToDataURL(file) {
  if(!file) throw new Error('Choose a photo before submitting.');
  if(!['image/png','image/jpeg','image/webp'].includes(file.type)) throw new Error('Upload a PNG, JPEG or WebP image.');
  if(file.size>1_000_000) throw new Error('Choose an image that is 1 MB or smaller.');
  return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=()=>reject(new Error('Could not read the selected image.'));reader.readAsDataURL(file);});
}
async function submitComplaint(event) {
  event.preventDefault(); const form=event.currentTarget,button=$('button[type="submit"]',form),message=$('#reportMessage');
  button.disabled=true; button.textContent='Submitting…'; message.textContent='';
  try {
    const fd=new FormData(form),[category,subcategory]=JSON.parse(fd.get('category')||$('#issueCategory').value),photo=await fileToDataURL(fd.get('photo'));
    const payload={title:fd.get('title'),description:fd.get('description'),area:fd.get('area'),address:fd.get('address'),category,subcategory,before_photo:photo,latitude:fd.get('latitude')||null,longitude:fd.get('longitude')||null};
    const result=await api('/api/reports',{method:'POST',body:payload});
    showToast(`Complaint ${result.report.id} submitted.`); await goTo('home');
  } catch(error) { message.textContent=error.message; showToast(error.message,true); }
  finally { button.disabled=false; button.innerHTML='Submit complaint <span aria-hidden="true">→</span>'; }
}
function statCard(label,value,sub) { return `<div class="stat-card"><small>${escapeHTML(label)}</small><b>${value===null||value===undefined?'—':escapeHTML(value)}</b><span>${escapeHTML(sub)}</span></div>`; }
async function renderMunicipal() {
  const [data,reportData,workerData]=await Promise.all([api('/api/analytics'),api('/api/reports?limit=100'),api('/api/workers')]);
  const a=data.analytics,reports=reportData.reports,workers=workerData.workers;
  const departments=state.catalog.departments.map(d=>`<option value="${escapeHTML(d.name)}">${escapeHTML(d.name)}</option>`).join('');
  const workerOptions=workers.map(w=>`<option value="${escapeHTML(w.id)}">${escapeHTML(w.display_name)} · ${escapeHTML(w.email)}</option>`).join('');
  const root=$('#viewRoot');
  root.innerHTML=heading('MUNICIPAL PORTAL','Operations overview','Review real stored cases, assign active field workers and monitor the workflow.')+
    `<section class="stat-grid">${statCard('Total complaints',a.total,'Database records')}${statCard('Awaiting assignment',a.awaiting_assignment,'Submitted')}${statCard('High priority',a.high_priority,'Illustrative score ≥ 70')}${statCard('Awaiting inspection',a.awaiting_inspection,'Repair evidence submitted')}${statCard('Verified resolutions',a.verified_resolutions,'Inspection approved')}${statCard('Overdue',a.overdue,'Category escalation threshold')}</section>`+
    `<div class="section-heading"><div><h2>Complaint queue</h2><p>Use filters to focus the review queue.</p></div><div class="filter-controls"><input id="opsSearch" placeholder="Search title, ward, location" aria-label="Search complaints"/><select id="opsStatus" aria-label="Filter by status"><option value="">All statuses</option>${Object.entries(statusLabels).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></div></div>`+
    `<div class="report-list" id="opsReports">${reports.length?reports.map(r=>{let extra='';if(['submitted','needs_rework'].includes(r.status)){extra=`<form class="assign-form" data-form="assign"><label>Department<select name="department" required>${departments}</select></label><label>Assign field worker<select name="worker_id" required><option value="">Choose an active worker</option>${workerOptions}</select></label><button class="button primary small" data-action="assign">Assign work</button></form>`;}return reportCard(r,extra);}).join(''):'<div class="empty-state"><h2>No complaints in your view</h2><p>Records appear here when citizens submit reports.</p></div>'}</div>`;
  bindListFilters('opsReports','opsSearch','opsStatus');
  $$('#opsReports [data-action="assign"]').forEach(btn=>btn.addEventListener('click',async e=>{e.preventDefault();const card=btn.closest('[data-report]'),form=card.querySelector('[data-form="assign"]');try{await api(`/api/reports/${encodeURIComponent(card.dataset.report)}`,{method:'POST',body:{action:'assign',department:form.department.value,worker_id:form.worker_id.value}});showToast('Work order assigned.');await renderMunicipal();}catch(err){showToast(err.message,true);}}));
}
function bindListFilters(listId,searchId,statusId) {
  const filter=()=>{const q=$(`#${searchId}`)?.value.toLowerCase()||'',s=$(`#${statusId}`)?.value||'';$$(`#${listId} .report-card`).forEach(card=>card.classList.toggle('hidden',!card.textContent.toLowerCase().includes(q)||(s&&!card.querySelector('.status-badge')?.classList.contains('status-'+s))));};
  $(`#${searchId}`)?.addEventListener('input',filter);$(`#${statusId}`)?.addEventListener('change',filter);
}
async function renderWorker() {
  const {reports}=await api('/api/reports?limit=100'); const root=$('#viewRoot');
  root.innerHTML=heading('FIELD WORKER PORTAL','My work queue','Only work assigned to your account appears in this queue.')+
    `<div class="report-list">${reports.length?reports.map(r=>{let extra='';if(['assigned','needs_rework'].includes(r.status))extra=`<div class="action-row"><button class="button primary small" data-action="start-work">Start work</button></div>`;if(r.status==='in_progress')extra=`<form class="repair-form"><label>Completion notes<textarea name="repair_note" rows="3" required maxlength="1000" placeholder="Describe work completed and any remaining issues."></textarea></label><label class="upload-field">After photo evidence<input name="after_photo" type="file" accept="image/png,image/jpeg,image/webp" required /></label><button class="button primary small" data-action="submit-repair">Submit for inspection</button></form>`;return reportCard(r,extra);}).join(''):'<div class="empty-state"><h2>No assigned work</h2><p>New assignments will appear here.</p></div>'}</div>`;
  $$('#viewRoot [data-action="start-work"]').forEach(btn=>btn.addEventListener('click',async()=>{const id=btn.closest('[data-report]').dataset.report;try{await api(`/api/reports/${encodeURIComponent(id)}`,{method:'POST',body:{action:'work_start'}});showToast('Work started.');await renderWorker();}catch(e){showToast(e.message,true);}}));
  $$('#viewRoot [data-action="submit-repair"]').forEach(btn=>btn.addEventListener('click',async e=>{e.preventDefault();const card=btn.closest('[data-report]'),form=btn.closest('form');btn.disabled=true;try{const image=await fileToDataURL(form.after_photo.files[0]);await api(`/api/reports/${encodeURIComponent(card.dataset.report)}`,{method:'POST',body:{action:'repair',repair_note:form.repair_note.value,after_photo:image}});showToast('Repair evidence submitted for inspection.');await renderWorker();}catch(err){showToast(err.message,true);btn.disabled=false;}}));
}
async function renderInspector() {
  const {reports}=await api('/api/reports?status=repair_submitted&limit=100'); const root=$('#viewRoot');
  const checklist=['Work matches the reported issue','Repair evidence shows the completed work','Location appears consistent with the complaint','No visible safety concern remains','Repair notes describe the work adequately'];
  root.innerHTML=heading('INSPECTOR PORTAL','Inspection queue','Assess the original report and submitted repair evidence. All five checks must pass for approval.')+
   `<div class="report-list">${reports.length?reports.map(r=>reportCard(r,`<form class="inspection-form"><fieldset><legend>Five inspection checks</legend>${checklist.map((item,index)=>`<label class="check-row"><input type="checkbox" name="check${index+1}" /><span>${escapeHTML(item)}</span></label>`).join('')}</fieldset><label>Inspection notes<textarea name="notes" rows="3" required maxlength="1000" placeholder="Record what was inspected and any concerns."></textarea></label><div class="action-row"><button class="button primary small" data-action="approve">Approve resolution</button><button class="button danger small" data-action="reject">Return for rework</button></div></form>`)).join(''):'<div class="empty-state"><span class="empty-icon">✓</span><h2>No repairs awaiting inspection</h2><p>Submitted field repairs will appear here.</p></div>'}</div>`;
  $$('#viewRoot [data-action="approve"], #viewRoot [data-action="reject"]').forEach(btn=>btn.addEventListener('click',async e=>{e.preventDefault();const card=btn.closest('[data-report]'),form=btn.closest('form'),checks={};for(let i=1;i<=5;i++)checks[String(i)]=form[`check${i}`].checked;const approved=btn.dataset.action==='approve';try{await api(`/api/reports/${encodeURIComponent(card.dataset.report)}`,{method:'POST',body:{action:'verify',approved,checks,notes:form.notes.value}});showToast(approved?'Resolution verified.':'Repair returned for rework.');await renderInspector();}catch(err){showToast(err.message,true);}}));
}
async function renderHeritage() {
  const {reports}=await api('/api/reports?heritage=1&limit=100'); const root=$('#viewRoot');
  root.innerHTML=heading('HERITAGE WATCH','Reported heritage concerns','Map shows submitted complaint locations only. No official heritage register or asset locations are connected.')+
    `<div class="map-toolbar"><label>Status<select id="heritageStatus"><option value="">All statuses</option>${Object.entries(statusLabels).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label><label>Priority<select id="heritagePriority"><option value="">All priorities</option><option value="high">High (70+)</option><option value="normal">Below 70</option></select></label></div><div class="map-panel"><div id="heritageMap" class="map-canvas" role="region" aria-label="Map of submitted heritage complaints"></div><div id="mapFallback" class="map-fallback hidden">Map library is unavailable. Use the complaint list below.</div><p class="map-attribution">Map tiles © OpenStreetMap contributors. Submitted locations are not official heritage asset data.</p></div><div class="section-heading"><div><h2>Heritage-related reports</h2><p>${reports.length} accessible complaint${reports.length===1?'':'s'} · missing coordinates remain in the list.</p></div></div><div class="report-list" id="heritageReports">${reports.length?reports.map(r=>reportCard(r)).join(''):'<div class="empty-state"><h2>No heritage complaints in your view</h2><p>Reported issues will be shown here when they match your account permissions.</p></div>'}</div>`;
  const update=()=>{const status=$('#heritageStatus').value,priority=$('#heritagePriority').value;const filtered=reports.filter(r=>(!status||r.status===status)&&(!priority||(priority==='high'?r.priority>=70:r.priority<70)));$$('#heritageReports .report-card').forEach(card=>{const match=filtered.some(r=>r.id===card.dataset.report);card.classList.toggle('hidden',!match);});if(state.map){state.map.eachLayer(layer=>{if(layer instanceof L.Marker)state.map.removeLayer(layer);});filtered.filter(r=>Number.isFinite(r.latitude)&&Number.isFinite(r.longitude)).forEach(r=>{const marker=L.marker([r.latitude,r.longitude]).addTo(state.map);marker.bindPopup(`<b>${escapeHTML(r.id)}</b><br>${escapeHTML(r.title)}<br>${escapeHTML(statusLabels[r.status]||r.status)} · priority ${escapeHTML(r.priority)}`);});}};
  $('#heritageStatus').addEventListener('change',update);$('#heritagePriority').addEventListener('change',update);
  if(window.L){const map=L.map('heritageMap',{scrollWheelZoom:false}).setView([20,0],2);state.map=map;L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(map);const points=reports.filter(r=>Number.isFinite(r.latitude)&&Number.isFinite(r.longitude));points.forEach(r=>L.marker([r.latitude,r.longitude]).addTo(map).bindPopup(`<b>${escapeHTML(r.id)}</b><br>${escapeHTML(r.title)}<br>${escapeHTML(statusLabels[r.status]||r.status)} · priority ${escapeHTML(r.priority)}`));if(points.length)map.fitBounds(points.map(r=>[r.latitude,r.longitude]),{padding:[28,28],maxZoom:14});setTimeout(()=>map.invalidateSize(),100);update();}else{$('#heritageMap').classList.add('hidden');$('#mapFallback').classList.remove('hidden');}
}
async function refreshNotifications() {
  const data=await api('/api/notifications'); const badge=$('#notificationCount');badge.textContent=data.unread_count;badge.classList.toggle('hidden',!data.unread_count);
}
async function renderNotifications() {
  const data=await api('/api/notifications');const root=$('#viewRoot');
  root.innerHTML=heading('YOUR ACCOUNT','Notifications','Updates are visible only to their intended account.')+
    `<div class="notification-list">${data.notifications.length?data.notifications.map(n=>`<article class="notification ${n.read_at?'read':''}"><div class="notification-dot"></div><div class="notification-body"><div class="notification-title"><b>${escapeHTML(n.title)}</b>${n.report_id?`<span class="eyebrow">${escapeHTML(n.report_id)}</span>`:''}</div><p>${escapeHTML(n.message)}</p><time>${escapeHTML(formatDate(n.created_at))}</time></div>${!n.read_at?`<button class="button quiet small" data-read="${escapeHTML(n.id)}">Mark read</button>`:''}</article>`).join(''):'<div class="empty-state"><h2>You are all caught up</h2><p>Relevant workflow updates will appear here.</p></div>'}</div>`;
  $$('[data-read]').forEach(btn=>btn.addEventListener('click',async()=>{try{await api(`/api/notifications/${encodeURIComponent(btn.dataset.read)}`,{method:'POST',body:{}});await renderNotifications();await refreshNotifications();}catch(e){showToast(e.message,true);}}));
}
async function renderAnalytics() {
  const {analytics:a}=await api('/api/analytics');const root=$('#viewRoot');
  const workload=a.department_workload.map(d=>`<div class="workload-row"><span>${escapeHTML(d.department)}</span><b>${d.complaint_count}</b><div class="workload-track"><i style="width:${a.total?Math.min(100,d.complaint_count/a.total*100):0}%"></i></div></div>`).join('');
  root.innerHTML=heading('MEASUREMENT','Operational analytics','Calculated from persisted complaint and inspection records; values are not fabricated.')+
    `<section class="stat-grid">${statCard('Resolution rate',a.resolution_rate===null?'—':`${a.resolution_rate}%`,'Verified / all reports')}${statCard('Average resolution',a.average_resolution_hours===null?'—':`${a.average_resolution_hours} h`,'Verified complaints only')}${statCard('Inspection approval',a.inspection_approval_rate===null?'—':`${a.inspection_approval_rate}%`,'Approved / inspections')}${statCard('Rework rate',a.rework_rate===null?'—':`${a.rework_rate}%`,'Rejected / inspections')}${statCard('Awaiting assignment',a.awaiting_assignment,'Submitted')}${statCard('Overdue',a.overdue,'Configured escalation thresholds')}</section><section class="panel"><div class="section-heading"><div><h2>Department workload</h2><p>Open complaints by current or suggested department</p></div></div>${workload||'<p class="empty-copy">No records are available yet.</p>'}</section><details class="definitions"><summary>Metric definitions and caveats</summary><ul>${Object.entries(a.definitions).map(([key,value])=>`<li><b>${escapeHTML(key.replaceAll('_',' '))}:</b> ${escapeHTML(value)}</li>`).join('')}</ul></details>`;
}
async function renderAdmin() {
  const [users,config,audit,notificationData]=await Promise.all([api('/api/admin/users'),api('/api/admin/config'),api('/api/admin/audit'),api('/api/admin/notifications')]);const root=$('#viewRoot');
  const deptOptions=config.departments.filter(d=>d.active).map(d=>`<option value="${escapeHTML(d.id)}">${escapeHTML(d.name)}</option>`).join('');
  const userRows=users.users.map(u=>`<tr data-user="${escapeHTML(u.id)}"><td><b>${escapeHTML(u.display_name)}</b><small>${escapeHTML(u.email)}</small></td><td><select class="user-role" aria-label="Role for ${escapeHTML(u.display_name)}">${Object.entries(roleLabels).map(([k,v])=>`<option value="${k}" ${u.role===k?'selected':''}>${v}</option>`).join('')}</select></td><td><label class="switch"><input class="user-active" type="checkbox" ${u.active?'checked':''} aria-label="Active ${escapeHTML(u.display_name)}"><span>${u.active?'Active':'Inactive'}</span></label></td><td><button class="button secondary small" data-save-user>Save</button></td></tr>`).join('');
  const categoryRows=config.categories.map(c=>`<tr><td>${escapeHTML(c.category)}<small>${escapeHTML(c.subcategory)}</small></td><td>${escapeHTML(c.department)}</td><td>${c.default_priority}</td><td>${c.escalation_hours} h</td><td>${c.active?'Active':'Inactive'}</td></tr>`).join('');
  const departmentRows=config.departments.map(d=>`<tr><td>${escapeHTML(d.name)}</td><td>${escapeHTML(d.id)}</td><td>${d.active?'Active':'Inactive'}</td></tr>`).join('');
  const auditRows=audit.events.slice(0,25).map(e=>`<tr><td>${escapeHTML(formatDate(e.created_at))}</td><td>${escapeHTML(e.actor||'System')}</td><td>${escapeHTML(e.action)}</td><td>${escapeHTML(e.entity_type)} ${escapeHTML(e.entity_id||'')}</td></tr>`).join('');
  const notificationRows=notificationData.notification_metrics.map(n=>`<tr><td>${escapeHTML(n.kind)}</td><td>${n.total}</td><td>${n.unread||0}</td><td>${escapeHTML(formatDate(n.latest))}</td></tr>`).join('');
  root.innerHTML=heading('SYSTEM ADMINISTRATION','Configuration and access','Manage user roles, routing rules and review the auditable system activity.')+
    `<section class="panel"><div class="section-heading"><div><h2>Create staff account</h2><p>Only system administrators can create privileged accounts.</p></div></div><form id="userCreateForm" class="inline-form"><label>Display name<input name="display_name" required minlength="2" maxlength="80"></label><label>Email<input name="email" type="email" required maxlength="254"></label><label>Temporary password<input name="password" type="password" required minlength="12" maxlength="256"></label><label>Role<select name="role">${Object.entries(roleLabels).filter(([k])=>k!=='citizen').map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label><button class="button primary small" type="submit">Create account</button></form></section>`+
    `<section class="panel"><div class="section-heading"><div><h2>User access</h2><p>Role changes take effect on the next authenticated request.</p></div></div><div class="table-wrap"><table><thead><tr><th>Account</th><th>Role</th><th>Access</th><th></th></tr></thead><tbody>${userRows||'<tr><td colspan="4">No users available.</td></tr>'}</tbody></table></div></section>`+
    `<section class="panel"><div class="section-heading"><div><h2>Departments</h2><p>Configure the departments available to complaint routing and assignment.</p></div></div><form id="departmentForm" class="inline-form"><label>Department name<input name="name" required minlength="2" maxlength="100"></label><label>Department ID <small>Optional; generated from name</small><input name="id" maxlength="80" pattern="[a-z0-9-]{2,80}"></label><label class="switch"><input name="active" type="checkbox" checked><span>Active</span></label><button class="button primary small" type="submit">Save department</button></form><div class="table-wrap"><table><thead><tr><th>Name</th><th>ID</th><th>Status</th></tr></thead><tbody>${departmentRows}</tbody></table></div></section>`+
    `<section class="panel"><div class="section-heading"><div><h2>Routing configuration</h2><p>Rule-based suggestions, not an AI model. Department decisions require human review.</p></div></div><form id="categoryForm" class="inline-form"><label>Category<input name="category" required maxlength="120"></label><label>Subcategory<input name="subcategory" required maxlength="160"></label><label>Department<select name="department_id">${deptOptions}</select></label><label>Default priority 0–100<input name="default_priority" type="number" min="0" max="100" value="40" required></label><label>Escalation hours<input name="escalation_hours" type="number" min="1" max="8760" value="168" required></label><label>Keywords<input name="keywords" maxlength="500" placeholder="e.g. pothole road damage"></label><label class="switch"><input name="active" type="checkbox" checked><span>Active</span></label><button class="button primary small" type="submit">Save routing rule</button></form><div class="table-wrap"><table><thead><tr><th>Category</th><th>Current department</th><th>Priority</th><th>Escalation</th><th>Status</th></tr></thead><tbody>${categoryRows}</tbody></table></div></section>`+
    `<section class="panel"><div class="section-heading"><div><h2>Notification monitoring</h2><p>Delivery is in-app only; no email, SMS or external service is configured.</p></div></div><div class="table-wrap"><table><thead><tr><th>Event type</th><th>Total</th><th>Unread</th><th>Latest</th></tr></thead><tbody>${notificationRows||'<tr><td colspan="4">No notification records.</td></tr>'}</tbody></table></div></section>`+
    `<section class="panel"><div class="section-heading"><div><h2>Recent audit events</h2><p>Most recent 25 of up to 200 retained events</p></div></div><div class="table-wrap"><table><thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Record</th></tr></thead><tbody>${auditRows||'<tr><td colspan="4">No audit events recorded.</td></tr>'}</tbody></table></div></section>`;
  $('#userCreateForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.currentTarget);try{await api('/api/admin/users',{method:'POST',body:Object.fromEntries(f)});showToast('Account created.');await renderAdmin();}catch(err){showToast(err.message,true);}});
  $('#categoryForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.currentTarget);const body=Object.fromEntries(f);body.default_priority=Number(body.default_priority);body.escalation_hours=Number(body.escalation_hours);body.active=f.has('active');try{await api('/api/admin/config/categories',{method:'POST',body});showToast('Routing rule saved.');await renderAdmin();}catch(err){showToast(err.message,true);}});
  $('#departmentForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.currentTarget);const body=Object.fromEntries(f);body.active=f.has('active');if(!body.id)delete body.id;try{await api('/api/admin/config/departments',{method:'POST',body});showToast('Department saved.');await renderAdmin();}catch(err){showToast(err.message,true);}});
  $$('[data-save-user]').forEach(btn=>btn.addEventListener('click',async()=>{const row=btn.closest('[data-user]');try{await api(`/api/admin/users/${encodeURIComponent(row.dataset.user)}`,{method:'POST',body:{role:$('.user-role',row).value,active:$('.user-active',row).checked}});showToast('User access updated.');}catch(err){showToast(err.message,true);}}));
}

$('#loginTab').addEventListener('click',()=>setAuthTab('login'));
$('#registerTab').addEventListener('click',()=>setAuthTab('register'));
$('#loginForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.currentTarget);try{const result=await api('/api/auth/login',{method:'POST',body:Object.fromEntries(f)});$('#authMessage').textContent='';await enterApp(result);}catch(err){$('#authMessage').textContent=err.message;}});
$('#registerForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.currentTarget);try{const result=await api('/api/auth/register',{method:'POST',body:Object.fromEntries(f)});await enterApp(result);}catch(err){$('#authMessage').textContent=err.message;}});
$('#logoutButton').addEventListener('click',async()=>{try{await api('/api/auth/logout',{method:'POST',body:{}});}catch{}showAuth('You have signed out.');});
$('#changePasswordButton').addEventListener('click',()=>{$('#passwordMessage').textContent='';$('#passwordForm').reset();$('#passwordDialog').showModal();});
$('#cancelPassword').addEventListener('click',()=>$('#passwordDialog').close());
$('#passwordForm').addEventListener('submit',async e=>{e.preventDefault();const form=e.currentTarget;const body=Object.fromEntries(new FormData(form));try{const result=await api('/api/auth/password',{method:'POST',body});state.csrf=result.csrf_token;form.reset();$('#passwordDialog').close();showToast('Password updated. Other active sessions were signed out.');}catch(error){$('#passwordMessage').textContent=error.message;}});
$('#notificationsButton').addEventListener('click',()=>goTo('notifications'));
document.addEventListener('click',e=>{const view=e.target.closest('[data-view]');if(view){e.preventDefault();goTo(view.dataset.view);}const retry=e.target.closest('[data-action="refresh"]');if(retry)goTo(state.view);});

(async function init(){
  try {const me=await api('/api/auth/me');if(!me.authenticated){showAuth();return;}state.user=me.user;state.csrf=me.csrf_token;$('#authShell').classList.add('hidden');$('#appShell').classList.remove('hidden');$('#userName').textContent=state.user.display_name;$('#userRole').textContent=roleLabels[state.user.role]||state.user.role;$('#userInitials').textContent=initials(state.user.display_name);state.catalog=await api('/api/catalog');renderNav();await goTo(navByRole[state.user.role][0][0]);refreshNotifications().catch(()=>{});}
  catch { showAuth(); }
})();
