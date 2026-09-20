/* Again: the browser renders evidence; the backend owns retrieval and decisions. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const list = (value) => Array.isArray(value) ? value : [];
  const text = (value) => typeof value === 'string' ? value : '';
  const numeric = (value) => typeof value === 'number' && Number.isFinite(value);
  const make = (tag, className, content) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (content !== undefined) element.textContent = String(content);
    return element;
  };
  const state = { examples: [], teachingExample: null, health: null, recallBusy: false, teachBusy: false, forgetting: false, healthTimer: null, sources: new Map(), lastTeaching: null };
  const statusLabels = {
    resolved_in_recorded_environment: ['Resolved', 'green'], resolved: ['Resolved', 'green'], diagnosed: ['Diagnosed', 'blue'],
    partially_resolved: ['Partially resolved', 'amber'], unresolved: ['Unresolved', 'amber'],
    user_reported: ['User reported', 'muted'], user_reported_resolved: ['User reported', 'muted'],
    synthetic_user_reported_resolved: ['Fictional / user reported', 'amber'], synthetic_user_reported: ['Fictional / user reported', 'amber']
  };
  const stageFallbacks = [
    ['unelevated_worker_ready', 'Ordinary worker launch'], ['administrator_preflight', 'Administrator preflight'],
    ['controller_startup_wait', 'Controller startup confirmation'], ['moss_authentication', 'Moss authentication'],
    ['native_sdk_bootstrap', 'Native SDK initialization'], ['first_dense_query', 'First dense query'],
    ['extraction_ram_preflight', 'Extraction RAM preflight'], ['browser_connect', 'Browser connection']
  ];
  function announce(message) { $('announcer').textContent = message; }
  function note(id, message, isError = false) {
    const element = $(id); element.textContent = message; element.hidden = !message; element.classList.toggle('error-message', isError);
  }
  function updateCount() { $('query-count').textContent = `${$('query').value.length.toLocaleString()} / 4,000`; }
  function elapsed(value) { return numeric(value) && value >= 0 ? `${value < 10 ? value.toFixed(2) : value.toFixed(1)} ms` : 'Not reported'; }
  function chevron() { const node = make('span', 'chevron'); node.setAttribute('aria-hidden', 'true'); return node; }
  function badge(status, synthetic = false) {
    const pair = synthetic ? ['Fictional / user reported', 'amber'] : (statusLabels[status] || [text(status).replaceAll('_', ' ') || 'Status not reported', 'muted']);
    const node = make('span', 'status-badge', pair[0]); node.dataset.tone = pair[1];
    if (status === 'resolved_in_recorded_environment') node.title = 'Resolved in the recorded environment; not a universal fix.';
    return node;
  }
  function paragraphs(parent, values, tag = 'p', className = '') { list(values).forEach(value => { if (typeof value === 'string') parent.append(make(tag, className, value)); }); }
  async function request(path, body, timeoutMs = 45000) {
    const controller = new AbortController(); const timer = window.setTimeout(() => controller.abort(), timeoutMs);
    const started = performance.now();
    try {
      const response = await fetch(path, { method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin', cache: 'no-store',
        headers: body === undefined ? { Accept: 'application/json' } : { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: body === undefined ? undefined : JSON.stringify(body), signal: controller.signal });
      const data = await response.json().catch(() => null);
      const browserMs = performance.now() - started;
      if (!response.ok) {
        const detail = text(data?.detail) || text(data?.message);
        throw new Error(detail || `The server returned ${response.status}. Please try again.`);
      }
      if (!data || typeof data !== 'object') throw new Error('The server returned an unreadable response. Please try again.');
      return { data, browserMs };
    } catch (error) {
      if (error.name === 'AbortError') throw new Error('This request timed out. Nothing is being shown as a completed result. Please try again.');
      if (error instanceof TypeError) throw new Error('Cannot reach the demo server. Check your connection and try again.');
      throw error;
    } finally { window.clearTimeout(timer); }
  }
  function updateButtons() {
    $('recall-button').disabled = state.recallBusy || state.teachBusy || state.forgetting;
    $('teach-button').disabled = state.teachBusy || state.recallBusy || state.forgetting || state.health?.teaching_enabled === false;
    $('forget-button').disabled = state.forgetting || state.teachBusy || state.recallBusy;
    $('memory-enabled').disabled = state.recallBusy;
    $('recall-button-label').textContent = state.recallBusy ? ($('memory-enabled').checked ? 'Recalling...' : 'Checking without memory...') : 'Recall a fix';
  }
  async function refreshHealth() {
    window.clearTimeout(state.healthTimer);
    try {
      const { data } = await request('/api/health', undefined, 10000); state.health = data;
      const ready = data.ready === true; const starting = !ready && ['starting', 'initializing', 'loading'].includes(data.status);
      $('health-pill').dataset.state = ready ? 'ready' : starting ? 'starting' : 'error';
      $('health-label').textContent = ready ? 'Moss ready' : starting ? 'Moss starting' : 'Moss unavailable';
      $('health-pill').title = text(data.message) || (ready ? 'The backend reports readiness after a genuine Moss query.' : 'Retrieval is not ready yet.');
      if (Number.isInteger(data.seed_count)) $('memory-count').textContent = `${data.seed_count} recorded incidents${Number.isInteger(data.session_count) && data.session_count > 0 ? ` + ${data.session_count} yours` : ''}`;
      if (data.teaching_enabled === false) note('teach-message', text(data.teaching_message) || 'Teaching is unavailable in this deployment. The recorded sample memories remain available.');
      updateButtons();
    } catch (error) { state.health = null; $('health-pill').dataset.state = 'error'; $('health-label').textContent = 'Server unreachable'; $('health-pill').title = error.message; }
    state.healthTimer = window.setTimeout(refreshHealth, state.health?.ready ? 20000 : 5000);
  }
  function addStage(value, label) {
    if (!value || [...$('stage').options].some(option => option.value === value)) return;
    const option = make('option', '', label || value); option.value = value; $('stage').append(option);
  }
  async function loadExamples() {
    try {
      const { data } = await request('/api/examples', undefined, 15000);
      state.examples = list(data.examples); state.teachingExample = data.teaching_example || null;
      list(data.stages).forEach(stage => { if (typeof stage === 'string') addStage(stage, stage.replaceAll('_', ' ')); else addStage(text(stage.value), text(stage.label)); });
      state.examples.forEach((example, index) => { const option = make('option', '', text(example.label) || text(example.title) || `Incident ${index + 1}`); option.value = String(index); $('example-select').append(option); });
      $('try-example').disabled = state.examples.length === 0;
      $('fill-teaching').disabled = !state.teachingExample;
    } catch (error) { $('try-example').disabled = true; $('fill-teaching').disabled = true; note('example-feedback', 'Examples could not be loaded. You can still describe an error.', true); }
  }
  function chooseExample(example) {
    if (!example || state.recallBusy) return;
    $('query').value = text(example.query);
    if (example.stage) addStage(text(example.stage), text(example.stage).replaceAll('_', ' '));
    $('stage').value = text(example.stage); $('conditions').value = Array.isArray(example.conditions) ? example.conditions.join('\n') : text(example.conditions);
    $('condition-preset').value = ''; $('context-details').open = Boolean(example.stage || example.conditions);
    updateCount(); note('recall-error', ''); note('example-feedback', 'Example filled. Select Recall a fix to search the live memory.');
    $('query').focus(); announce('Real incident filled. Select Recall a fix to search.');
  }
  function showSource(id) {
    const target = state.sources.get(id); if (!target) return;
    let parent = target; while (parent) { if (parent.tagName === 'DETAILS') parent.open = true; parent = parent.parentElement; }
    target.querySelector('summary')?.focus({ preventScroll: true }); target.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'nearest' });
  }
  function sourceLinks(ids) {
    const wrapper = make('div', 'step-evidence-links');
    [...new Set(list(ids))].forEach(id => {
      if (!state.sources.has(id)) return;
      const source = state.sources.get(id); const link = make('button', 'source-link', `Source ${source.dataset.number}`); link.type = 'button'; link.title = source.dataset.label || id;
      link.addEventListener('click', () => showSource(id)); wrapper.append(link);
    });
    return wrapper;
  }
  function renderEvidence(evidence) {
    state.sources.clear(); $('evidence-list').replaceChildren(); $('evidence-panel').hidden = evidence.length === 0;
    $('evidence-count').textContent = `${evidence.length} ${evidence.length === 1 ? 'RECORD' : 'RECORDS'}`;
    let sourceNumber = 0;
    evidence.forEach((record) => {
      const details = make('details', 'evidence-record'); const summary = make('summary'); const heading = make('span');
      heading.append(make('span', 'evidence-record-title', text(record.title) || text(record.id)));
      const meta = make('span', 'evidence-record-meta'); meta.append(badge(record.status, record.is_synthetic === true));
      if (record.applicable === true) meta.append(make('span', 'evidence-applicability', 'APPLICABLE'));
      heading.append(meta); summary.append(heading, chevron()); details.append(summary);
      const body = make('div', 'evidence-body'); body.append(make('p', 'evidence-stage', `${text(record.id)}${record.stage ? ` / ${record.stage}` : ''}`));
      if (list(record.observations).length) { const observations = make('ul', 'evidence-observations'); paragraphs(observations, record.observations, 'li'); body.append(observations); }
      list(record.sources).forEach(source => {
        sourceNumber += 1;
        const excerpt = make('details', 'source-excerpt'); excerpt.dataset.number = String(sourceNumber).padStart(2, '0'); excerpt.dataset.label = `${text(source.document)} / ${text(source.section)}`;
        const title = make('summary'); title.append(make('span', '', `Source ${excerpt.dataset.number} / ${text(source.document) || 'Recorded note'}`), chevron());
        excerpt.append(title, make('blockquote', '', text(source.excerpt)));
        const type = text(source.excerpt_type).replaceAll('_', ' ');
        excerpt.append(make('p', 'source-caption', `${text(source.section)}${type ? ` / ${type}` : ''}. Supplied excerpt; the full source is not hosted here.`));
        if (source.id && !state.sources.has(source.id)) state.sources.set(source.id, excerpt);
        body.append(excerpt);
      });
      if (list(record.limits).length) { const limits = make('div', 'evidence-limits'); limits.append(make('strong', '', 'What this record does not establish')); paragraphs(limits, record.limits); body.append(limits); }
      details.append(body); $('evidence-list').append(details);
    });
  }
