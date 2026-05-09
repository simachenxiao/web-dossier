const $ = (selector) => document.querySelector(selector);

const state = {
  apiBase: localStorage.getItem('dossier.apiBase') || 'http://127.0.0.1:8000',
  caseId: new URLSearchParams(location.search).get('caseId') || localStorage.getItem('dossier.caseId') || '',
  case: null,
  graph: { elements: [] },
  tasks: [],
  materials: [],
  drafts: [],
  events: [],
  factVersions: [],
};

const elementNames = {
  time: '时间地点',
  consequence: '后果',
  tool: '工具/手段',
  witness: '证人',
  victim: '受害人',
  suspect: '嫌疑人',
  circumstance: '情节',
};

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function toast(message) {
  const el = $('#toast');
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => el.classList.remove('show'), 2400);
}

async function api(path, options = {}) {
  const response = await fetch(state.apiBase + path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || response.statusText);
  }
  return response.status === 204 ? null : response.json();
}

function apiPost(path, payload = {}) {
  return api(path, { method: 'POST', body: JSON.stringify(payload) });
}

function setConnected(ok, text) {
  const el = $('#connectionStatus');
  el.textContent = text;
  el.className = `status-pill ${ok ? 'ok' : 'bad'}`;
}

async function createDemoCase() {
  syncInputs();
  const caseNo = `CASE-FRONT-${crypto.randomUUID()}`;
  const created = await apiPost('/api/cases', {
    case_no: caseNo,
    case_name: '周枫殴打李江案',
    case_type: '殴打他人',
  });
  state.caseId = String(created.id);
  localStorage.setItem('dossier.caseId', state.caseId);
  $('#caseIdInput').value = state.caseId;
  await loadCase();
  toast(`已创建演示案件 #${state.caseId}`);
}

function syncInputs() {
  state.apiBase = $('#apiBaseInput').value.trim().replace(/\/$/, '');
  state.caseId = $('#caseIdInput').value.trim();
  localStorage.setItem('dossier.apiBase', state.apiBase);
  if (state.caseId) localStorage.setItem('dossier.caseId', state.caseId);
}

async function loadCase() {
  syncInputs();
  if (!state.caseId) {
    toast('请先输入 Case ID 或创建演示案件');
    return;
  }
  const [caseInfo, graph, tasks, materials, drafts, events, factVersions] = await Promise.all([
    api(`/api/cases/${state.caseId}`),
    api(`/api/cases/${state.caseId}/graph`),
    api(`/api/cases/${state.caseId}/tasks`),
    api(`/api/cases/${state.caseId}/materials`),
    api(`/api/cases/${state.caseId}/drafts`),
    api(`/api/cases/${state.caseId}/conversations/events`),
    api(`/api/cases/${state.caseId}/fact-versions`),
  ]);
  Object.assign(state, { case: caseInfo, graph, tasks, materials, drafts, events, factVersions });
  renderAll();
  setConnected(true, `已连接 Case #${state.caseId}`);
}

async function refresh() {
  if (!state.caseId) return;
  await loadCase();
}

function renderAll() {
  renderCase();
  renderMetrics();
  renderGraph();
  renderMessages();
  renderDrafts();
  renderTasks();
  renderMaterials();
  renderFactVersions();
}

function renderCase() {
  $('#caseCard').innerHTML = state.case ? `
    <strong>${escapeHtml(state.case.case_name)}</strong>
    <div class="card-meta">${escapeHtml(state.case.case_no)} · ${escapeHtml(state.case.case_type)}</div>
    <div class="card-meta">阶段：${escapeHtml(state.case.stage)} · 事实版本：${escapeHtml(state.case.fact_version)}</div>
  ` : '<div class="muted">尚未加载案件</div>';
}

function renderMetrics() {
  $('#metricElements').textContent = state.graph.elements.length;
  $('#metricTasks').textContent = state.tasks.length;
  $('#metricMaterials').textContent = state.materials.length;
  $('#metricDrafts').textContent = state.drafts.filter((draft) => draft.status === 'pending_confirmation').length;
}

function elementClass(status) {
  if (status === 'conflict') return 'red';
  if (status === 'proved') return 'green';
  return 'yellow';
}

function elementLabel(status) {
  return {
    unknown: '待补强',
    reinforcing: '补强中',
    proved: '已证实',
    conflict: '有矛盾',
  }[status] || status;
}

function renderGraph() {
  $('#graph').innerHTML = state.graph.elements.map((element) => `
    <article class="node-card ${elementClass(element.status)}">
      <h3>${escapeHtml(elementNames[element.element_key] || element.name)}</h3>
      <span class="node-status">${escapeHtml(elementLabel(element.status))}</span>
      <div class="node-fact">${escapeHtml(element.key_fact || '暂无关键事实')}</div>
      <div class="node-stats">
        <span>材料 ${element.material_count}</span>
        <span>缺口 ${element.gap_count}</span>
        <span>矛盾 ${element.conflict_count}</span>
      </div>
    </article>
  `).join('') || '<div class="muted">暂无图谱数据</div>';
}

function renderMessages() {
  const eventHtml = state.events.map((event) => `
    <div class="msg ${event.source_role === '民警' ? 'police' : ''}">
      <div class="meta">${escapeHtml(event.source_role)} · ${escapeHtml(event.event_type)}</div>
      <div>${escapeHtml(event.original_text)}</div>
    </div>
  `).join('');
  $('#messages').innerHTML = eventHtml || '<div class="muted">暂无对话。可以发送“请制作李江询问笔录。”</div>';
  $('#messages').scrollTop = $('#messages').scrollHeight;
}

function renderDrafts() {
  const drafts = state.drafts.slice().reverse();
  $('#draftList').innerHTML = drafts.map((draft) => `
    <article class="draft-card ${draft.status === 'pending_confirmation' ? 'pending' : ''}">
      <div class="card-row">
        <div>
          <div class="card-title">${escapeHtml(draft.title)}</div>
          <div class="card-meta">${escapeHtml(draft.draft_type)} · ${escapeHtml(draft.status)} · ${escapeHtml(draft.element_key || '未绑定要素')}</div>
        </div>
        <span class="badge">#${draft.id}</span>
      </div>
      <div class="card-meta">${escapeHtml(JSON.stringify(draft.payload))}</div>
      ${draft.status === 'pending_confirmation' ? `
        <div class="actions">
          <button onclick="confirmDraft(${draft.id})">确认</button>
          <button class="ghost" onclick="rejectDraft(${draft.id})">驳回</button>
        </div>
      ` : ''}
    </article>
  `).join('') || '<div class="muted">暂无 AI 草稿</div>';
}

async function confirmDraft(id) {
  await apiPost(`/api/drafts/${id}/confirm`, { reviewer: '前端工作台' });
  await refresh();
  toast('草稿已确认');
}

async function rejectDraft(id) {
  await apiPost(`/api/drafts/${id}/reject`, { reviewer: '前端工作台', reason: '前端驳回' });
  await refresh();
  toast('草稿已驳回');
}

function statusText(status) {
  return {
    pending: '待启动',
    blocked: '阻塞',
    in_progress: '执行中',
    waiting_upload: '待上传',
    pending_approval: '待审批',
    completed: '已完成',
  }[status] || status;
}

function renderTasks() {
  $('#taskList').innerHTML = state.tasks.slice().reverse().map((task) => `
    <article class="task-card">
      <div class="card-row">
        <div>
          <div class="card-title">${escapeHtml(task.title)}</div>
          <div class="card-meta">${escapeHtml(task.task_type)} · ${escapeHtml(task.source)} · ${escapeHtml(task.element_key || '未绑定要素')}</div>
        </div>
        <span class="badge ${task.priority.toLowerCase()} ${task.status === 'completed' ? 'done' : ''}">${escapeHtml(task.priority)} · ${escapeHtml(statusText(task.status))}</span>
      </div>
      <div class="card-meta">期望材料：${escapeHtml((task.expected_materials || []).join('、') || '无')}<br>执行者：${escapeHtml(task.assignee_name || '未分配')} · 阻塞：${escapeHtml((task.blocked_by || []).join('、') || '无')}</div>
      <div class="actions">
        ${['pending', 'blocked'].includes(task.status) ? `<button onclick="startTask(${task.id})">启动</button>` : ''}
        ${task.status !== 'completed' ? `<button class="ghost" onclick="openResultDialog(${task.id})">回写结果</button>` : ''}
      </div>
    </article>
  `).join('') || '<div class="muted">暂无任务</div>';
}

async function startTask(id) {
  await apiPost(`/api/tasks/${id}/start`);
  await refresh();
  toast('任务已启动');
}

function openResultDialog(id) {
  const task = state.tasks.find((item) => item.id === id);
  $('#dialogTaskId').value = id;
  $('#dialogTitle').textContent = `回写任务结果 · ${task?.title || id}`;
  const materialTitle = task?.expected_materials?.[0] || task?.task_type || '回写材料';
  $('#resultTypeInput').value = defaultResultType(task);
  $('#resultPayloadInput').value = JSON.stringify(defaultPayload(task, materialTitle), null, 2);
  $('#resultDialog').showModal();
}

function defaultResultType(task) {
  if (task?.status === 'pending_approval' || task?.assignee_type === 'approval') return 'approval';
  if (task?.task_type === '事实更新') return 'fact_update';
  return 'material';
}

function defaultPayload(task, materialTitle) {
  if (defaultResultType(task) === 'approval') {
    return { decision: 'approved', result_text: '领导审批通过。', reviewer: '前端工作台' };
  }
  if (defaultResultType(task) === 'fact_update') {
    return { fact_text: '周枫因殴打李江被处以行政拘留五日。', reviewer: '前端工作台' };
  }
  return {
    title: materialTitle,
    material_type: materialTitle,
    source: task?.assignee_name || '前端回写',
    owner: materialTitle.includes('李江') || materialTitle.includes('诊断') ? '李江' : '周枫',
    extracted_facts: {},
  };
}

async function submitTaskResult(event) {
  event.preventDefault();
  const id = $('#dialogTaskId').value;
  let payload;
  try {
    payload = JSON.parse($('#resultPayloadInput').value || '{}');
  } catch {
    toast('结果 JSON 格式错误');
    return;
  }
  await apiPost(`/api/tasks/${id}/complete`, {
    result_type: $('#resultTypeInput').value,
    payload,
  });
  $('#resultDialog').close();
  await refresh();
  toast('任务结果已回流');
}

function renderMaterials() {
  $('#materialGrid').innerHTML = state.materials.slice().reverse().map((material) => `
    <article class="material-card">
      <div class="card-row">
        <div>
          <div class="card-title">${escapeHtml(material.title)}</div>
          <div class="card-meta">${escapeHtml(material.material_type)} · ${escapeHtml(material.source || '未知来源')} · ${escapeHtml(material.owner || '未登记人员')}</div>
        </div>
        <span class="badge done">${escapeHtml(material.fact_status)}</span>
      </div>
      <div class="card-meta">支撑要素：${escapeHtml((material.supports_elements || []).join('、') || '无')}</div>
      <pre>${escapeHtml(JSON.stringify(material.extracted_facts || {}, null, 2))}</pre>
    </article>
  `).join('') || '<div class="muted">暂无材料</div>';
}

function renderFactVersions() {
  $('#factVersionList').classList.toggle('empty', state.factVersions.length === 0);
  $('#factVersionList').innerHTML = state.factVersions.slice().reverse().map((version) => `
    <article class="version-item">
      <strong>${escapeHtml(version.version)} · ${escapeHtml(version.confirmed_by || '系统')}</strong>
      <p>${escapeHtml(version.fact_summary)}</p>
    </article>
  `).join('') || '暂无事实版本';
}

async function sendMessage() {
  if (!state.caseId) {
    toast('请先加载案件');
    return;
  }
  const text = $('#messageInput').value.trim();
  if (!text) return;
  await apiPost(`/api/cases/${state.caseId}/conversations/messages`, {
    source_role: $('#sourceRoleInput').value,
    original_text: text,
  });
  $('#messageInput').value = '';
  await refresh();
  toast('对话已入池');
}

async function runLoop() {
  if (!state.caseId) return;
  await apiPost(`/api/cases/${state.caseId}/run-loop`);
  await refresh();
  toast('图谱循环已运行');
}

function bindEvents() {
  $('#apiBaseInput').value = state.apiBase;
  $('#caseIdInput').value = state.caseId;
  $('#loadCaseBtn').addEventListener('click', () => loadCase().catch((error) => {
    setConnected(false, '连接失败');
    toast(error.message);
  }));
  $('#createCaseBtn').addEventListener('click', () => createDemoCase().catch((error) => toast(error.message)));
  $('#refreshBtn').addEventListener('click', () => refresh().catch((error) => toast(error.message)));
  $('#sendMessageBtn').addEventListener('click', () => sendMessage().catch((error) => toast(error.message)));
  $('#messageInput').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') sendMessage().catch((error) => toast(error.message));
  });
  $('#runLoopBtn').addEventListener('click', () => runLoop().catch((error) => toast(error.message)));
  $('#submitResultBtn').addEventListener('click', submitTaskResult);
  $('#resultTypeInput').addEventListener('change', () => {
    const task = state.tasks.find((item) => item.id === Number($('#dialogTaskId').value));
    $('#resultPayloadInput').value = JSON.stringify(defaultPayload(task, task?.expected_materials?.[0] || task?.task_type || '回写材料'), null, 2);
  });
}

bindEvents();
renderAll();
if (state.caseId) {
  loadCase().catch((error) => {
    setConnected(false, '连接失败');
    toast(error.message);
  });
}
