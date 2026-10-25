'use strict';

const state = { user: null, csrf: '', catalog: null, view: '', map: null, toastTimer: null,
  isDemo: false, guided: false, demoStep: 0, faq: '' };
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const tr = text => window.NagrivantaI18n?.translations?.[window.NagrivantaI18n.get()]?.[text] || text;
function localizedNotice(message) {
  const templates = [
    [/^([A-Z0-9-]+) is awaiting municipal review\.$/,'{id} is awaiting municipal review.',['id']],
    [/^([A-Z0-9-]+) was assigned to (.+)\.$/,'{id} was assigned to {department}.',['id','department']],
    [/^([A-Z0-9-]+) is assigned to you\.$/,'{id} is assigned to you.',['id']],
    [/^Field work has started on ([A-Z0-9-]+)\.$/,'Field work has started on {id}.',['id']],
    [/^Repair evidence for ([A-Z0-9-]+) is awaiting review\.$/,'Repair evidence for {id} is awaiting review.',['id']],
    [/^([A-Z0-9-]+) is ready for inspection\.$/,'{id} is ready for inspection.',['id']],
    [/^([A-Z0-9-]+) is awaiting inspection\.$/,'{id} is awaiting inspection.',['id']],
    [/^([A-Z0-9-]+) was approved after inspection\.$/,'{id} was approved after inspection.',['id']],
    [/^([A-Z0-9-]+) was returned for additional work\.$/,'{id} was returned for additional work.',['id']],
    [/^Inspection of ([A-Z0-9-]+) was approved\.$/,'Inspection of {id} was approved.',['id']],
    [/^Inspection of ([A-Z0-9-]+) was returned for rework\.$/,'Inspection of {id} was returned for rework.',['id']]
  ];
  for (const [pattern,key,names] of templates) {
    const match=message.match(pattern);
    if(match) {
      let translated=tr(key);
      names.forEach((name,index)=>{translated=translated.replace(`{${name}}`,match[index+1]);});
      return translated;
    }
  }
  return tr(message);
}
const roleLabels = {citizen:'Citizen',municipal_admin:'Municipal administrator',field_worker:'Field worker',inspector:'Inspector',system_admin:'System administrator'};
const departmentRoles = new Set(['municipal_admin','field_worker','inspector']);
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
      const error = new Error(tr(payload.error || 'The request could not be completed.'));
      error.payload = payload;
      throw error;
    }
    return payload;
  }
  if (!response.ok) throw new Error(tr('The request could not be completed.'));
  return response;
}

function showAuth(message = '') {
  state.user = null; state.csrf = ''; state.isDemo = false;
  $('#appShell').classList.add('hidden'); $('#authShell').classList.remove('hidden');
  $('#demoTools').classList.add('hidden'); $('#demoGuide').classList.add('hidden');
  $('#assistantButton').classList.add('hidden'); $('#assistantPanel').classList.add('hidden');
  $('#authMessage').textContent = tr(message);
  $('#loginForm').classList.remove('hidden'); $('#registerForm').classList.add('hidden');
  setAuthTab('login');
}
function signOutLocal(message = '') { showAuth(message); }
function setAuthTab(mode) {
  $('#demoPanel').classList.add('hidden');
  $$('.auth-tabs,#loginForm,#registerForm,.landing-actions,.privacy-note').forEach(el=>el.classList.remove('hidden'));
  $$('#authShell .language-control').forEach(el=>el.classList.remove('hidden'));
  const login = mode === 'login';
  $('#loginTab').classList.toggle('active',login); $('#registerTab').classList.toggle('active',!login);
  $('#loginTab').setAttribute('aria-selected',String(login)); $('#registerTab').setAttribute('aria-selected',String(!login));
  $('#loginForm').classList.toggle('hidden',!login); $('#registerForm').classList.toggle('hidden',login);
  $('#authHeading').textContent = login ? 'Sign in to your workspace' : 'Create a citizen account';
  $('#authMessage').textContent = '';
}
function initials(name) { return String(name || 'N').split(/\s+/).slice(0,2).map(x=>x[0]||'').join('').toUpperCase(); }
function showToast(message, error = false) {
  const toast = $('#toast'); toast.textContent = tr(message); toast.classList.remove('hidden','error');
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
  state.user = payload.user; state.csrf = payload.csrf_token; state.isDemo = Boolean(payload.user.is_demo);
  $('#authShell').classList.add('hidden'); $('#appShell').classList.remove('hidden');
  $('#userName').textContent = state.user.display_name; $('#userRole').textContent = roleLabels[state.user.role] || state.user.role;
  $('#userInitials').textContent = initials(state.user.display_name);
  state.catalog = await api('/api/catalog');
  $('#demoTools').classList.toggle('hidden',!state.isDemo);
  $('#demoRoleSwitch').value = state.user.role;
  $('#changePasswordButton').classList.toggle('hidden',state.isDemo);
  $('#assistantButton').classList.remove('hidden');
  $('#demoGuide').classList.toggle('hidden',!state.isDemo);
  state.guided = state.isDemo && sessionStorage.getItem('nagrivanta.guided') === '1';
  state.demoStep = Number(sessionStorage.getItem('nagrivanta.demoStep') || 0);
  renderDemoGuide();
  renderNav();
  await goTo(navByRole[state.user.role][0][0]);
  refreshNotifications().catch(()=>{});
}
function renderNav() {
  $('#roleNav').innerHTML = navByRole[state.user.role].map(([key,label,icon])=>`<button class="nav-item ${state.view===key?'active':''}" type="button" data-view="${key}"><span aria-hidden="true">${icon}</span>${label}</button>`).join('');
}
const guidedSteps = [
  {role:'citizen',title:'Step 1 · Citizen',copy:'Review the synthetic sample reports. You can submit a new demo complaint with a clearly synthetic location and photo.'},
  {role:'municipal_admin',title:'Step 2 · Municipal Administrator',copy:'Review the queue and routing suggestion, then assign a road-work sample to the demo field worker.'},
  {role:'field_worker',title:'Step 3 · Field Worker',copy:'Start your assigned sample work, then submit a repair note and synthetic evidence.'},
  {role:'inspector',title:'Step 4 · Inspector',copy:'Review the repair record and checklist. Approve only when every check passes, or request rework.'},
  {role:'citizen',title:'Step 5 · Citizen follow-up',copy:'Review the persisted timeline and notification. A verified sample is available for optional satisfaction feedback.'},
  {role:'system_admin',title:'Step 6 · System Administrator',copy:'Explore synthetic-only operational metrics and audit events. Global account and configuration changes are disabled.'}
];
const roleGuidance = {
  citizen:'Your reports are private to this demo citizen. Submit a sample complaint to see the real workflow and timeline.',
  municipal_admin:'Review synthetic submissions and assign only to the field worker created inside this demo session.',
  field_worker:'Only work assigned to this demo field-worker account appears here. Repair submissions use the real workflow.',
  inspector:'Review synthetic repair submissions. Inspection decisions are persisted and rework history is retained.',
  system_admin:'This restricted demo role can inspect synthetic-only metrics and audit history; global administration is disabled.'
};
function renderDemoGuide() {
  const root=$('#demoGuide');
  if(!state.isDemo){root.classList.add('hidden');root.innerHTML='';return;}
  root.classList.remove('hidden');
  const step=guidedSteps[Math.max(0,Math.min(guidedSteps.length-1,state.demoStep))];
  const title=state.guided?step.title:`Explore freely · ${roleLabels[state.user.role]}`;
  const copy=state.guided?step.copy:roleGuidance[state.user.role];
  const progress=state.guided?state.demoStep+1:guidedSteps.findIndex(item=>item.role===state.user.role)+1;
  root.innerHTML=`<div class="demo-guide-top"><div><span class="demo-ribbon compact">${escapeHTML(tr('INTERACTIVE DEMO — Uses synthetic demonstration data.'))}</span><h2>${escapeHTML(tr(title))}</h2><p>${escapeHTML(tr(copy))}</p></div><div class="demo-progress-wrap"><span>${state.guided?`${escapeHTML(tr('Tour'))} ${progress} ${escapeHTML(tr('of 6'))}`:escapeHTML(tr('Role preview'))}</span><progress max="6" value="${progress}"></progress></div></div>${state.guided?`<button class="button primary small" id="nextTourStep" type="button">${state.demoStep===5?escapeHTML(tr('Finish tour')):escapeHTML(tr('Continue tour →'))}</button>`:`<button class="button secondary small" id="beginTourFromApp" type="button">${escapeHTML(tr('Start Guided Tour'))}</button>`}`;
  $('#nextTourStep')?.addEventListener('click',advanceTour);
  $('#beginTourFromApp')?.addEventListener('click',()=>{state.guided=true;state.demoStep=0;sessionStorage.setItem('nagrivanta.guided','1');sessionStorage.setItem('nagrivanta.demoStep','0');switchDemoRole('citizen');});
}
async function advanceTour() {
  if(state.demoStep>=guidedSteps.length-1){state.guided=false;sessionStorage.removeItem('nagrivanta.guided');renderDemoGuide();showToast('Guided tour complete. You can continue exploring any role.');return;}
  state.demoStep+=1;sessionStorage.setItem('nagrivanta.demoStep',String(state.demoStep));
  await switchDemoRole(guidedSteps[state.demoStep].role);
}
async function switchDemoRole(role) {
  if(!state.isDemo)return;
  try{const result=await api('/api/demo/switch',{method:'POST',body:{role}});await enterApp(result);}
  catch(error){showToast(error.message,true);$('#demoRoleSwitch').value=state.user.role;}
}
async function launchDemo(role,guided=false) {
  try{
    const result=await api('/api/demo/session',{method:'POST',body:{role}});
    state.guided=guided;state.demoStep=0;
    if(guided){sessionStorage.setItem('nagrivanta.guided','1');sessionStorage.setItem('nagrivanta.demoStep','0');}
    else{sessionStorage.removeItem('nagrivanta.guided');sessionStorage.removeItem('nagrivanta.demoStep');}
    await enterApp(result);
  }catch(error){$('#authMessage').textContent=error.message;}
}
async function resetDemo() {
  if(!confirm('Reset only this isolated demo session? Its synthetic activity will be replaced; ordinary accounts and records are not affected.'))return;
  try{await api('/api/demo/reset',{method:'POST',body:{}});showToast('This demo session has been reset.');await goTo('home');}
  catch(error){showToast(error.message,true);}
}
async function renderDemoSystemAdmin() {
  const {analytics:a,audit_events:audit,demo_notice}=await api('/api/demo/overview');
  const satisfaction=a.satisfaction||{};
  const rows=audit.slice(0,20).map(item=>`<tr><td>${escapeHTML(formatDate(item.created_at))}</td><td>${escapeHTML(item.actor||'Demo system')}</td><td>${escapeHTML(item.action)}</td><td>${escapeHTML(item.entity_type)} ${escapeHTML(item.entity_id||'')}</td></tr>`).join('');
  $('#viewRoot').innerHTML=heading('DEMO SYSTEM ADMIN','Synthetic operations overview',demo_notice)+
    `<section class="stat-grid">${statCard('Synthetic reports',a.total,'This isolated session only')}${statCard('Verified samples',a.verified_resolutions,'Not real municipal output')}${statCard('Inspection decisions',a.inspection_count,'Synthetic workflow events')}${statCard('Feedback samples',satisfaction.synthetic_feedback_count,'Synthetic only')}${statCard('Sample average rating',satisfaction.synthetic_average_rating??'—','Not citizen satisfaction data')}</section>`+
    `<section class="panel"><div class="section-heading"><div><h2>Demo audit activity</h2><p>Actions recorded only for this synthetic demo group.</p></div></div><div class="table-wrap"><table><thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Record</th></tr></thead><tbody>${rows||'<tr><td colspan="4">No demo audit activity yet.</td></tr>'}</tbody></table></div></section>`+
    `<aside class="note-box"><b>Restricted public demo</b><p>Account management, global routing configuration, and real-workspace records are not accessible from this synthetic role.</p></aside>`;
}
const faqAnswers = {
  en:{
    submit:'Open “Report an issue,” choose a category, add a concise description and sample location, then attach a PNG, JPEG, or WebP image (up to 1 MB). Review any duplicate warning before deciding whether to continue. The server confirms success and returns a tracking ID.',
    track:'Sign in with the citizen account and open My complaints. The displayed ID, status, persisted timeline, permitted assignment details, repair history, inspection result, and related notifications come from the application database.',
    statuses:'Submitted means waiting for review. Assigned means a field worker has a work order. Work in progress means the worker started. Awaiting inspection means repair evidence was sent for review. Rework required means additional work is requested. Resolved means an inspector verified closure.',
    inspection:'A municipal administrator assigns work to an active field worker. The worker records completion and evidence. An inspector checks five items; every check must pass to verify a resolution. These actions are server-authorized and recorded.',
    rework:'The complaint stays open. The municipal administrator can assign it again, the field worker can start a new attempt, and each repair and inspection decision remains in history.',
    demo:'Choose Explore Live Demo, then Start Guided Tour or a role portal. Demo accounts, records, uploads, and metrics are synthetic and isolated. Role switching is server-authorized; reset affects only this demo group.'
  },
  mr:{
    submit:'“समस्या नोंदवा” उघडा, प्रकार निवडा, संक्षिप्त वर्णन आणि नमुना ठिकाण द्या, नंतर 1 MB पर्यंत PNG, JPEG किंवा WebP जोडा. डुप्लिकेट सूचना पाहून पुढे जायचे ठरवा. सर्व्हर यशाची पुष्टी करून ट्रॅकिंग क्रमांक देतो.',
    track:'नागरिक खात्यात साइन इन करून “माझ्या तक्रारी” उघडा. क्रमांक, स्थिती, जतन केलेली कालरेषा, अधिकृत नियुक्ती माहिती, दुरुस्तीचा इतिहास, तपासणी निकाल आणि संबंधित सूचना डेटाबेसमधून दिसतात.',
    statuses:'नोंदवले म्हणजे पुनरावलोकन बाकी. नियुक्त म्हणजे काम दिले आहे. काम सुरू आहे म्हणजे कर्मचारी कामाला लागला आहे. तपासणी प्रलंबित म्हणजे दुरुस्ती तपासणीसाठी पाठवली आहे. पुन्हा काम आवश्यक म्हणजे अधिक काम हवे. निराकरण झाले म्हणजे निरीक्षकाने बंद केले.',
    inspection:'महानगरपालिका प्रशासक सक्रिय क्षेत्र कर्मचाऱ्याला काम देतो. कर्मचारी काम आणि पुरावे नोंदवतो. निरीक्षक पाच बाबी तपासतो; सर्व पास झाल्यावरच निराकरण प्रमाणित होते. या कृती सर्व्हरवर अधिकृत आणि नोंदवलेल्या असतात.',
    rework:'तक्रार उघडीच राहते. प्रशासक पुन्हा काम देऊ शकतो, कर्मचारी नवा प्रयत्न सुरू करू शकतो आणि प्रत्येक दुरुस्ती व तपासणी इतिहासात राहते.',
    demo:'“थेट डेमो पाहा” निवडा, नंतर मार्गदर्शित फेरफटका किंवा भूमिका पोर्टल उघडा. डेमो खाती, नोंदी, पुरावे आणि मेट्रिक्स कृत्रिम व वेगळे आहेत. भूमिका बदल सर्व्हरवर नियंत्रित आहे; रीसेट फक्त या डेमोवर लागू होतो.'
  },
  hi:{
    submit:'“समस्या दर्ज करें” खोलें, श्रेणी चुनें, संक्षिप्त विवरण और नमूना स्थान दें, फिर 1 MB तक PNG, JPEG या WebP छवि जोड़ें। डुप्लिकेट चेतावनी देखकर तय करें कि आगे बढ़ना है या नहीं। सर्वर पुष्टि करके ट्रैकिंग आईडी देता है।',
    track:'नागरिक खाते से साइन इन करके “मेरी शिकायतें” खोलें। आईडी, स्थिति, सहेजी गई टाइमलाइन, अधिकृत आवंटन जानकारी, मरम्मत इतिहास, निरीक्षण परिणाम और संबंधित सूचनाएँ डेटाबेस से दिखाई जाती हैं।',
    statuses:'दर्ज का अर्थ समीक्षा बाकी है। सौंपा गया का अर्थ फील्ड वर्कर को काम मिला। कार्य जारी का अर्थ काम शुरू हुआ। निरीक्षण लंबित का अर्थ मरम्मत समीक्षा के लिए भेजी गई। पुनः कार्य आवश्यक का अर्थ अतिरिक्त काम चाहिए। समाधान हुआ का अर्थ निरीक्षक ने बंद किया।',
    inspection:'नगरपालिका प्रशासक सक्रिय फील्ड वर्कर को काम देता है। वर्कर कार्य और साक्ष्य दर्ज करता है। निरीक्षक पाँच बातों की जाँच करता है; सभी पास होने पर ही समाधान सत्यापित होता है। ये कार्रवाइयाँ सर्वर द्वारा अधिकृत और दर्ज होती हैं।',
    rework:'शिकायत खुली रहती है। प्रशासक फिर से काम दे सकता है, फील्ड वर्कर नया प्रयास शुरू कर सकता है, और हर मरम्मत तथा निरीक्षण निर्णय इतिहास में रहता है।',
    demo:'“लाइव डेमो देखें” चुनें, फिर निर्देशित परिचय या भूमिका पोर्टल खोलें। डेमो खाते, रिकॉर्ड, साक्ष्य और मेट्रिक्स कृत्रिम तथा अलग हैं। भूमिका परिवर्तन सर्वर नियंत्रित करता है; रीसेट केवल इसी डेमो को प्रभावित करता है।'
  }
};
function faqAnswer(id) {
  const lang=window.NagrivantaI18n?.get()||'en';
  const answers=faqAnswers[lang]||faqAnswers.en;
  $('#assistantAnswer').textContent=answers[id]||'General help only; no private complaint data is available here.';
}
function openDemoPanel() {
  $('#demoPanel').classList.remove('hidden');
  $$('.auth-tabs,#loginForm,#registerForm,.landing-actions,.privacy-note').forEach(el=>el.classList.add('hidden'));
  $$('#authShell .language-control').forEach(el=>el.classList.add('hidden'));
  $('#authHeading').textContent='Explore the interactive demo';
  $('#authMessage').textContent='';
}
async function goTo(view) {
  state.view = view; state.map = null; renderNav();
  const root = $('#viewRoot'); root.innerHTML = '<div class="loading-card"><span class="spinner"></span> Loading your workspace…</div>';
  try {
    if (view === 'new' && state.user.role === 'citizen') return renderCitizenForm();
    if (view === 'heritage') return await renderHeritage();
    if (view === 'notifications') return await renderNotifications();
    if (view === 'analytics') return await renderAnalytics();
    if (state.user.role === 'system_admin' && state.isDemo) return await renderDemoSystemAdmin();
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
  if (!events.length) return `<p class="muted">${escapeHTML(tr('No workflow history yet.'))}</p>`;
  return `<ol class="timeline">${events.map(item=>`<li><span class="timeline-dot"></span><div><b>${escapeHTML(tr(item.action))}</b><time>${escapeHTML(formatDate(item.at))}</time>${item.note?`<p>${escapeHTML(item.note)}</p>`:''}</div></li>`).join('')}</ol>`;
}
function reportCard(report,extra='') {
  const history = report.repair_history?.length || report.inspection_history?.length;
  const detailedHistory = history ? `<details class="history"><summary>Repair and inspection history · ${(report.repair_history?.length||0)+(report.inspection_history?.length||0)} records</summary>${(report.repair_history||[]).map(r=>`<div class="note-box"><b>Repair by ${escapeHTML(r.worker)} · ${escapeHTML(formatDate(r.created_at))}</b><p>${escapeHTML(r.repair_note)}</p>${evidenceLink(r.evidence_id,'Submitted repair evidence')}</div>`).join('')}${(report.inspection_history||[]).map(i=>`<div class="note-box"><b>${i.approved?'Approved':'Rework requested'} by ${escapeHTML(i.inspector)} · ${escapeHTML(formatDate(i.created_at))}</b><p>${escapeHTML(i.notes)}</p></div>`).join('')}</details>` : '';
  const nextStep={submitted:'Next step: municipal review and assignment.',assigned:'Next step: the assigned worker can start the work.',in_progress:'Next step: the field worker submits repair notes for inspection.',repair_submitted:'Next step: an inspector reviews the submitted repair.',needs_rework:'Next step: a worker completes additional work.',verified:'This complaint has been verified and closed.'}[report.status]||'No new update is available yet.';
  const feedback=state.user?.role==='citizen'&&report.feedback_open?`<form class="feedback-form" data-feedback><b>Share satisfaction feedback</b><p>Your rating is separate from the inspection decision and cannot be overwritten after submission.</p><label>Rating<select name="rating" required><option value="">Choose 1–5</option>${[5,4,3,2,1].map(v=>`<option value="${v}">${v} / 5</option>`).join('')}</select></label><label>Optional comment<textarea name="comment" rows="2" maxlength="1000" placeholder="What went well or could improve?"></textarea></label><button class="button secondary small" type="submit">Submit feedback</button></form>`:
    state.user?.role==='citizen'&&report.feedback?`<div class="note-box feedback-recorded"><b>Feedback recorded · ${escapeHTML(report.feedback.rating)} / 5</b><p>${escapeHTML(report.feedback.comment||'No written comment.')}</p><time>${escapeHTML(formatDate(report.feedback.created_at))}</time></div>`:'';
  const notices=report.notifications?.length?`<details class="history"><summary>Related in-app notifications · ${report.notifications.length}</summary>${report.notifications.map(n=>`<div class="note-box"><b>${escapeHTML(tr(n.title))} · ${escapeHTML(formatDate(n.created_at))}</b><p>${escapeHTML(localizedNotice(n.message))}</p></div>`).join('')}</details>`:'';
  return `<article class="report-card" data-report="${escapeHTML(report.id)}"><div class="report-card-top"><div><div class="eyebrow">${escapeHTML(report.id)}${report.synthetic?' · SYNTHETIC':''}</div><h3>${escapeHTML(report.title)}</h3></div>${statusBadge(report.status)}</div><p class="report-summary">${escapeHTML(report.description)}</p><div class="report-meta"><span>⌖ ${escapeHTML(report.area)} · ${escapeHTML(report.address)}</span><span>${escapeHTML(report.category_group || report.category)}${report.subcategory?` / ${escapeHTML(report.subcategory)}`:''}</span><span>Submitted ${escapeHTML(formatDate(report.created_at))}</span><span>Updated ${escapeHTML(formatDate(report.updated_at))}</span>${report.department?`<span>Department: ${escapeHTML(report.department)}</span>`:''}${report.assigned_worker_name?`<span>Assigned worker: ${escapeHTML(report.assigned_worker_name)}</span>`:''}${report.priority?`<span>Priority ${escapeHTML(report.priority)}</span>`:''}</div><div class="next-step"><b>${escapeHTML(tr(nextStep))}</b></div><div class="evidence-row">${evidenceLink(report.before_evidence_id,'Reported evidence')}${report.after_evidence_id?evidenceLink(report.after_evidence_id,'Repair evidence'):''}</div>${report.repair_note?`<div class="note-box"><b>Repair note</b><p>${escapeHTML(report.repair_note)}</p></div>`:''}${report.verification?`<div class="note-box"><b>Inspection · ${report.verification.approved?'Approved':'Rework requested'}</b><p>${escapeHTML(report.verification.notes)}</p></div>`:''}${feedback}${extra}${report.events?`<details class="history"><summary>Complaint timeline</summary>${statusTimeline(report.events)}</details>`:''}${detailedHistory}${notices}</article>`;
}
async function renderCitizenHome() {
  const root=$('#viewRoot'); const {reports}=await api('/api/reports');
  const sorted=reports;
  root.innerHTML=heading('CITIZEN PORTAL','Your civic reports','Track updates from submission through field work and inspection.',`<button class="button quiet small" data-action="refresh">Refresh status</button><button class="button primary" data-view="new">＋ Report an issue</button>`)+
    `<section class="stat-grid compact"><div class="stat-card"><small>Your reports</small><b>${sorted.length}</b><span>All statuses</span></div><div class="stat-card"><small>In progress</small><b>${sorted.filter(r=>!['verified','submitted'].includes(r.status)).length}</b><span>Assigned or being reviewed</span></div><div class="stat-card"><small>Resolved</small><b>${sorted.filter(r=>r.status==='verified').length}</b><span>Inspection-approved</span></div></section>`+
    `<div class="section-heading"><div><h2>Complaint history</h2><p>Your submissions only</p></div><div class="filter-controls"><input id="reportSearch" aria-label="Search my complaints" placeholder="Search your reports" /><select id="reportStatus" aria-label="Filter by status"><option value="">All statuses</option>${Object.entries(statusLabels).map(([key,label])=>`<option value="${key}">${label}</option>`).join('')}</select></div></div>`+
    `<div class="report-list" id="citizenReports">${sorted.length?sorted.map(r=>reportCard(r)).join(''):'<div class="empty-state"><span class="empty-icon">＋</span><h2>No complaints yet</h2><p>Submit a civic issue to begin tracking the response.</p><button class="button primary" data-view="new">Report an issue</button></div>'}</div>`;
  const filter=()=>{const q=$('#reportSearch').value.toLowerCase(),s=$('#reportStatus').value;$$('#citizenReports .report-card').forEach(card=>{const match=card.textContent.toLowerCase().includes(q)&&(!s||card.querySelector('.status-badge')?.classList.contains('status-'+s));card.classList.toggle('hidden',!match);});};
  $('#reportSearch').addEventListener('input',filter); $('#reportStatus').addEventListener('change',filter);
  $$('#citizenReports [data-feedback]').forEach(form=>form.addEventListener('submit',async event=>{
    event.preventDefault();const card=form.closest('[data-report]'),data=new FormData(form);
    try{const result=await api(`/api/reports/${encodeURIComponent(card.dataset.report)}/feedback`,{method:'POST',body:{rating:Number(data.get('rating')),comment:data.get('comment')}});
      showToast(result.message);await renderCitizenHome();}
    catch(error){showToast(error.message,true);}
  }));
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
    const duplicateCheck=await api('/api/duplicates/check',{method:'POST',body:{
      title:payload.title,description:payload.description,category:payload.category,
      subcategory:payload.subcategory,area:payload.area,address:payload.address,
      latitude:payload.latitude,longitude:payload.longitude
    }});
    let acknowledged=false;
    if(duplicateCheck.matches?.length){
      const match=duplicateCheck.matches[0];
      const prompt=`${tr('A similar unresolved report may already exist.')} ${tr('Why it may match:')} ${tr(match.reason)} ${tr('Current status:')} ${tr(statusLabels[match.status]||match.status)}. ${tr('You can continue to submit a separate report. Continue?')}`;
      if(!confirm(prompt))return;
      acknowledged=true;
    }
    payload.duplicate_acknowledged=acknowledged;
    let result;
    try{result=await api('/api/reports',{method:'POST',body:payload});}
    catch(error){
      if(!error.payload?.requires_confirmation)throw error;
      const warning=error.payload.duplicate_warning||{};
      const prompt=`${tr('A similar unresolved report may already exist.')} ${tr('Why it may match:')} ${tr(warning.reason||'similar issue nearby')} ${tr('Current status:')} ${tr(statusLabels[warning.status]||warning.status||'Submitted')}. ${tr('You can continue to submit a separate report. Continue?')}`;
      if(!confirm(prompt))return;
      result=await api('/api/reports',{method:'POST',body:{...payload,duplicate_acknowledged:true}});
    }
    showToast(`Complaint ${result.report.id} submitted${result.duplicate?'; linked as a separate report for review':''}.`); await goTo('home');
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
    `<div class="notification-list">${data.notifications.length?data.notifications.map(n=>`<article class="notification ${n.read_at?'read':''}"><div class="notification-dot"></div><div class="notification-body"><div class="notification-title"><b>${escapeHTML(tr(n.title))}</b>${n.report_id?`<span class="eyebrow">${escapeHTML(n.report_id)}</span>`:''}</div><p>${escapeHTML(localizedNotice(n.message))}</p><time>${escapeHTML(formatDate(n.created_at))}</time></div>${!n.read_at?`<button class="button quiet small" data-read="${escapeHTML(n.id)}">${escapeHTML(tr('Mark read'))}</button>`:''}</article>`).join(''):'<div class="empty-state"><h2>You are all caught up</h2><p>Relevant workflow updates will appear here.</p></div>'}</div>`;
  $$('[data-read]').forEach(btn=>btn.addEventListener('click',async()=>{try{await api(`/api/notifications/${encodeURIComponent(btn.dataset.read)}`,{method:'POST',body:{}});await renderNotifications();await refreshNotifications();}catch(e){showToast(e.message,true);}}));
}
async function renderAnalytics() {
  const {analytics:a}=await api('/api/analytics');const root=$('#viewRoot'),satisfaction=a.satisfaction||{};
  const workload=a.department_workload.map(d=>`<div class="workload-row"><span>${escapeHTML(d.department)}</span><b>${d.complaint_count}</b><div class="workload-track"><i style="width:${a.total?Math.min(100,d.complaint_count/a.total*100):0}%"></i></div></div>`).join('');
  const ratings=[5,4,3,2,1].map(rating=>`<div class="workload-row"><span>${rating} / 5</span><b>${satisfaction.rating_distribution?.[String(rating)]||0}</b><div class="workload-track"><i style="width:${satisfaction.feedback_count?((satisfaction.rating_distribution?.[String(rating)]||0)/satisfaction.feedback_count*100):0}%"></i></div></div>`).join('');
  root.innerHTML=heading('MEASUREMENT','Operational analytics','Calculated from persisted complaint and inspection records; values are not fabricated.')+
    `<section class="stat-grid">${statCard('Resolution rate',a.resolution_rate===null?'—':`${a.resolution_rate}%`,'Verified / all reports')}${statCard('Average resolution',a.average_resolution_hours===null?'—':`${a.average_resolution_hours} h`,'Verified complaints only')}${statCard('Inspection approval',a.inspection_approval_rate===null?'—':`${a.inspection_approval_rate}%`,'Approved / inspections')}${statCard('Rework rate',a.rework_rate===null?'—':`${a.rework_rate}%`,'Rejected / inspections')}${statCard('Awaiting assignment',a.awaiting_assignment,'Submitted')}${statCard('Overdue',a.overdue,'Configured escalation thresholds')}${statCard('Average citizen rating',satisfaction.average_rating??'—',`${satisfaction.feedback_count||0} recorded responses; missing feedback is not zero`)}${statCard('Synthetic demo feedback',satisfaction.synthetic_feedback_count||0,'Excluded from citizen rating')}</section><section class="panel"><div class="section-heading"><div><h2>Department workload</h2><p>Open complaints by current or suggested department</p></div></div>${workload||'<p class="empty-copy">No records are available yet.</p>'}</section><section class="panel"><div class="section-heading"><div><h2>Citizen rating distribution</h2><p>Verified complaints with feedback only; no-response complaints are excluded.</p></div></div>${ratings}</section><details class="definitions"><summary>Metric definitions and caveats</summary><ul>${Object.entries(a.definitions).map(([key,value])=>`<li><b>${escapeHTML(key.replaceAll('_',' '))}:</b> ${escapeHTML(value)}</li>`).join('')}</ul></details>`;
}
async function renderAdmin() {
  const [users,config,audit,notificationData]=await Promise.all([api('/api/admin/users'),api('/api/admin/config'),api('/api/admin/audit'),api('/api/admin/notifications')]);const root=$('#viewRoot');
  const deptOptions=config.departments.filter(d=>d.active).map(d=>`<option value="${escapeHTML(d.id)}">${escapeHTML(d.name)}</option>`).join('');
  const userRows=users.users.map(u=>`<tr data-user="${escapeHTML(u.id)}"><td><b>${escapeHTML(u.display_name)}</b><small>${escapeHTML(u.email)}</small></td><td><select class="user-role" aria-label="Role for ${escapeHTML(u.display_name)}">${Object.entries(roleLabels).map(([k,v])=>`<option value="${k}" ${u.role===k?'selected':''}>${v}</option>`).join('')}</select></td><td><select class="user-department" aria-label="Department for ${escapeHTML(u.display_name)}"><option value="">No department</option>${config.departments.filter(d=>d.active).map(d=>`<option value="${escapeHTML(d.id)}" ${u.department_id===d.id?'selected':''}>${escapeHTML(d.name)}</option>`).join('')}</select></td><td><label class="switch"><input class="user-active" type="checkbox" ${u.active?'checked':''} aria-label="Active ${escapeHTML(u.display_name)}"><span>${u.active?'Active':'Inactive'}</span></label></td><td><button class="button secondary small" data-save-user>Save</button></td></tr>`).join('');
  const categoryRows=config.categories.map(c=>`<tr><td>${escapeHTML(c.category)}<small>${escapeHTML(c.subcategory)}</small></td><td>${escapeHTML(c.department)}</td><td>${c.default_priority}</td><td>${c.escalation_hours} h</td><td>${c.active?'Active':'Inactive'}</td></tr>`).join('');
  const departmentRows=config.departments.map(d=>`<tr><td>${escapeHTML(d.name)}</td><td>${escapeHTML(d.id)}</td><td>${d.active?'Active':'Inactive'}</td></tr>`).join('');
  const auditRows=audit.events.slice(0,25).map(e=>`<tr><td>${escapeHTML(formatDate(e.created_at))}</td><td>${escapeHTML(e.actor||'System')}</td><td>${escapeHTML(e.action)}</td><td>${escapeHTML(e.entity_type)} ${escapeHTML(e.entity_id||'')}</td></tr>`).join('');
  const notificationRows=notificationData.notification_metrics.map(n=>`<tr><td>${escapeHTML(n.kind)}</td><td>${n.total}</td><td>${n.unread||0}</td><td>${escapeHTML(formatDate(n.latest))}</td></tr>`).join('');
  root.innerHTML=heading('SYSTEM ADMINISTRATION','Configuration and access','Manage user roles, routing rules and review the auditable system activity.')+
    `<section class="panel"><div class="section-heading"><div><h2>Create staff account</h2><p>Only system administrators can create privileged accounts. Municipal staff need an active department.</p></div></div><form id="userCreateForm" class="inline-form"><label>Display name<input name="display_name" required minlength="2" maxlength="80"></label><label>Email<input name="email" type="email" required maxlength="254"></label><label>Temporary password<input name="password" type="password" required minlength="12" maxlength="256"></label><label>Role<select name="role">${Object.entries(roleLabels).filter(([k])=>k!=='citizen').map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></label><label>Department<select name="department_id"><option value="">Select a department</option>${deptOptions}</select></label><button class="button primary small" type="submit">Create account</button></form></section>`+
    `<section class="panel"><div class="section-heading"><div><h2>User access</h2><p>Department scope is enforced by the API; legacy staff without a department must be assigned one here.</p></div></div><div class="table-wrap"><table><thead><tr><th>Account</th><th>Role</th><th>Department</th><th>Access</th><th></th></tr></thead><tbody>${userRows||'<tr><td colspan="5">No users available.</td></tr>'}</tbody></table></div></section>`+
    `<section class="panel"><div class="section-heading"><div><h2>Departments</h2><p>Configure the departments available to complaint routing and assignment.</p></div></div><form id="departmentForm" class="inline-form"><label>Department name<input name="name" required minlength="2" maxlength="100"></label><label>Department ID <small>Optional; generated from name</small><input name="id" maxlength="80" pattern="[a-z0-9-]{2,80}"></label><label class="switch"><input name="active" type="checkbox" checked><span>Active</span></label><button class="button primary small" type="submit">Save department</button></form><div class="table-wrap"><table><thead><tr><th>Name</th><th>ID</th><th>Status</th></tr></thead><tbody>${departmentRows}</tbody></table></div></section>`+
    `<section class="panel"><div class="section-heading"><div><h2>Routing configuration</h2><p>Rule-based suggestions, not an AI model. Department decisions require human review.</p></div></div><form id="categoryForm" class="inline-form"><label>Category<input name="category" required maxlength="120"></label><label>Subcategory<input name="subcategory" required maxlength="160"></label><label>Department<select name="department_id">${deptOptions}</select></label><label>Default priority 0–100<input name="default_priority" type="number" min="0" max="100" value="40" required></label><label>Escalation hours<input name="escalation_hours" type="number" min="1" max="8760" value="168" required></label><label>Keywords<input name="keywords" maxlength="500" placeholder="e.g. pothole road damage"></label><label class="switch"><input name="active" type="checkbox" checked><span>Active</span></label><button class="button primary small" type="submit">Save routing rule</button></form><div class="table-wrap"><table><thead><tr><th>Category</th><th>Current department</th><th>Priority</th><th>Escalation</th><th>Status</th></tr></thead><tbody>${categoryRows}</tbody></table></div></section>`+
    `<section class="panel"><div class="section-heading"><div><h2>Notification monitoring</h2><p>Delivery is in-app only; no email, SMS or external service is configured.</p></div></div><div class="table-wrap"><table><thead><tr><th>Event type</th><th>Total</th><th>Unread</th><th>Latest</th></tr></thead><tbody>${notificationRows||'<tr><td colspan="4">No notification records.</td></tr>'}</tbody></table></div></section>`+
    `<section class="panel"><div class="section-heading"><div><h2>Recent audit events</h2><p>Most recent 25 of up to 200 retained events</p></div></div><div class="table-wrap"><table><thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Record</th></tr></thead><tbody>${auditRows||'<tr><td colspan="4">No audit events recorded.</td></tr>'}</tbody></table></div></section>`;
  $('#userCreateForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.currentTarget);const body=Object.fromEntries(f);if(!departmentRoles.has(body.role))body.department_id=null;try{await api('/api/admin/users',{method:'POST',body});showToast('Account created.');await renderAdmin();}catch(err){showToast(err.message,true);}});
  $('#categoryForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.currentTarget);const body=Object.fromEntries(f);body.default_priority=Number(body.default_priority);body.escalation_hours=Number(body.escalation_hours);body.active=f.has('active');try{await api('/api/admin/config/categories',{method:'POST',body});showToast('Routing rule saved.');await renderAdmin();}catch(err){showToast(err.message,true);}});
  $('#departmentForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.currentTarget);const body=Object.fromEntries(f);body.active=f.has('active');if(!body.id)delete body.id;try{await api('/api/admin/config/departments',{method:'POST',body});showToast('Department saved.');await renderAdmin();}catch(err){showToast(err.message,true);}});
  $$('[data-save-user]').forEach(btn=>btn.addEventListener('click',async()=>{const row=btn.closest('[data-user]');const role=$('.user-role',row).value;const departmentId=departmentRoles.has(role)?$('.user-department',row).value||null:null;try{await api(`/api/admin/users/${encodeURIComponent(row.dataset.user)}`,{method:'POST',body:{role,department_id:departmentId,active:$('.user-active',row).checked}});showToast('User access updated.');await renderAdmin();}catch(err){showToast(err.message,true);}}));
}

$('#loginTab').addEventListener('click',()=>setAuthTab('login'));
$('#registerTab').addEventListener('click',()=>setAuthTab('register'));
$('#openDemoButton').addEventListener('click',openDemoPanel);
$('#landingCitizenButton').addEventListener('click',()=>setAuthTab('register'));
$('#landingSignInButton').addEventListener('click',()=>setAuthTab('login'));
$('#closeDemoButton').addEventListener('click',()=>setAuthTab('login'));
$('#startTourButton').addEventListener('click',()=>launchDemo('citizen',true));
$('#exploreFreelyButton').addEventListener('click',()=>{$('#authMessage').textContent='Choose a role card below to open its isolated portal.';$('#demoRoleCards').scrollIntoView({behavior:'smooth',block:'nearest'});});
$$('[data-demo-role]').forEach(button=>button.addEventListener('click',()=>launchDemo(button.dataset.demoRole,false)));
$('#languageSelectAuth').addEventListener('change',event=>window.NagrivantaI18n.set(event.target.value));
$('#languageSelect').addEventListener('change',event=>window.NagrivantaI18n.set(event.target.value));
document.addEventListener('nagrivanta-language-change',()=>{if(state.faq)faqAnswer(state.faq);});
$('#loginForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.currentTarget);try{const result=await api('/api/auth/login',{method:'POST',body:Object.fromEntries(f)});$('#authMessage').textContent='';await enterApp(result);}catch(err){$('#authMessage').textContent=err.message;}});
$('#registerForm').addEventListener('submit',async e=>{e.preventDefault();const f=new FormData(e.currentTarget);try{const result=await api('/api/auth/register',{method:'POST',body:Object.fromEntries(f)});await enterApp(result);}catch(err){$('#authMessage').textContent=err.message;}});
$('#logoutButton').addEventListener('click',async()=>{try{await api('/api/auth/logout',{method:'POST',body:{}});}catch{}sessionStorage.removeItem('nagrivanta.guided');sessionStorage.removeItem('nagrivanta.demoStep');showAuth('You have signed out.');});
$('#demoRoleSwitch').addEventListener('change',event=>{
  const index=guidedSteps.findIndex(item=>item.role===event.target.value);
  if(state.guided&&index>=0){state.demoStep=index;sessionStorage.setItem('nagrivanta.demoStep',String(index));}
  switchDemoRole(event.target.value);
});
$('#resetDemoButton').addEventListener('click',resetDemo);
$('#exitDemoButton').addEventListener('click',async()=>{$('#logoutButton').click();});
$('#changePasswordButton').addEventListener('click',()=>{$('#passwordMessage').textContent='';$('#passwordForm').reset();$('#passwordDialog').showModal();});
$('#cancelPassword').addEventListener('click',()=>$('#passwordDialog').close());
$('#passwordForm').addEventListener('submit',async e=>{e.preventDefault();const form=e.currentTarget;const body=Object.fromEntries(new FormData(form));try{const result=await api('/api/auth/password',{method:'POST',body});state.csrf=result.csrf_token;form.reset();$('#passwordDialog').close();showToast('Password updated. Other active sessions were signed out.');}catch(error){$('#passwordMessage').textContent=error.message;}});
$('#notificationsButton').addEventListener('click',()=>goTo('notifications'));
$('#assistantButton').addEventListener('click',()=>{const panel=$('#assistantPanel'),open=panel.classList.contains('hidden');panel.classList.toggle('hidden',!open);$('#assistantButton').setAttribute('aria-expanded',String(open));});
$('#assistantClose').addEventListener('click',()=>{$('#assistantPanel').classList.add('hidden');$('#assistantButton').setAttribute('aria-expanded','false');});
$$('[data-faq]').forEach(button=>button.addEventListener('click',()=>{state.faq=button.dataset.faq;faqAnswer(state.faq);}));
document.addEventListener('click',e=>{const view=e.target.closest('[data-view]');if(view){e.preventDefault();goTo(view.dataset.view);}const retry=e.target.closest('[data-action="refresh"]');if(retry)goTo(state.view);});

(async function init(){
  try {const me=await api('/api/auth/me');if(!me.authenticated){showAuth();return;}await enterApp(me);}
  catch { showAuth(); }
})();
