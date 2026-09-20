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
    ['extraction_ram_preflight', 'Extraction RAM preflight']
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
  function renderMetrics(data, browserMs) {
    const container = $('metrics-content'); container.replaceChildren(); $('metrics-panel').hidden = false;
    const grid = make('dl', 'metric-grid'); const timing = data.timings || {};
    const values = [['Moss query + embedding', elapsed(timing.moss_query_ms)], ['Backend API', elapsed(timing.api_ms)], ['Browser round trip', elapsed(browserMs)]];
    values.forEach(([label, value]) => { const item = make('div', 'metric-item'); item.append(make('dt', '', label), make('dd', '', value)); grid.append(item); });
    container.append(grid);
    const counts = Number.isInteger(data.native_query_count) ? ` Native query calls: ${data.native_query_count}.` : '';
    container.append(make('p', 'metric-note', `Actual measurements for this request. Moss timing includes query embedding; browser time includes the network and response parsing.${counts} Scores are retrieval scores, not confidence probabilities.`));
    if (numeric(state.health?.cold_ready_ms)) container.append(make('p', 'metric-note', `Backend cold readiness: ${elapsed(state.health.cold_ready_ms)}, measured separately at startup. Model: ${text(state.health.model) || 'not reported'}.`));
    const retrieved = list(data.retrieved); const rows = make('div', 'retrieved-list');
    if (!retrieved.length) rows.append(make('p', '', data.state === 'memory_off' ? 'Retrieval disabled for this request. No incident IDs returned.' : 'No incident IDs returned.'));
    retrieved.forEach(item => rows.append(make('p', '', `${text(item.id)} / score ${numeric(item.score) ? item.score.toFixed(6) : 'not reported'}`)));
    container.append(rows);
  }
  function renderResult(data, browserMs) {
    const allowed = ['matched', 'clarify', 'no_match', 'memory_off'];
    if (!allowed.includes(data.state) || typeof data.next_step !== 'string') throw new Error('The response did not contain a valid evidence decision. Please try again.');
    const evidence = list(data.evidence); renderEvidence(evidence);
    const selected = evidence.find(item => item.id === data.matched_id) || evidence.find(item => item.applicable === true);
    const content = $('result-content'); content.replaceChildren(); const kind = { matched: 'A relevant memory', clarify: 'One detail first', no_match: 'No applicable memory', memory_off: 'Memory is off' }[data.state];
    const eyebrow = make('div', 'result-eyebrow'); eyebrow.append(make('span', 'result-kind', kind));
    if (selected?.status) eyebrow.append(badge(selected.status, selected.is_synthetic === true));
    content.append(eyebrow, make('h3', 'result-headline', text(data.headline) || { matched: 'Past experience, with context.', clarify: 'Same error. Which stage?', no_match: 'There is no grounded fix to recall yet.', memory_off: 'Past outcomes are unavailable.' }[data.state]));
    const matches = list(data.what_matches);
    if (matches.length) { const section = make('section', 'result-matches'); section.append(make('h4', 'mini-title', 'What matches')); const ul = make('ul', 'match-list'); paragraphs(ul, matches, 'li'); section.append(ul); content.append(section); }
    const next = make('section', 'next-step'); next.append(make('h4', 'mini-title', data.state === 'clarify' ? 'Clarify before another fix' : 'Your next step'), make('p', '', data.next_step));
    if (selected) next.append(sourceLinks(list(selected.sources).map(source => source.id)));
    content.append(next);
    const attempts = list(data.failed_attempts);
    if (attempts.length) {
      const section = make('section', 'attempts-section'); section.append(make('h4', 'mini-title', `Already tried / ${attempts.length} recorded ${attempts.length === 1 ? 'attempt' : 'attempts'}`));
      attempts.forEach(attempt => { const row = make('div', 'attempt'); row.append(make('h4', '', text(attempt.action)), make('p', '', text(attempt.outcome)), sourceLinks(attempt.source_ids)); section.append(row); });
      content.append(section);
    }
    const limits = list(data.limits).length ? data.limits : list(selected?.limits);
    if (limits.length) { const section = make('aside', 'result-limit'); section.append(make('strong', '', 'Keep the limits in view')); const ul = make('ul'); paragraphs(ul, limits, 'li'); section.append(ul); content.append(section); }
    $('result-panel').dataset.state = data.state; $('result-empty').hidden = true; $('result-loading').hidden = true; content.hidden = false; $('result-stale').hidden = true;
    renderMetrics(data, browserMs); if (data.state === 'clarify') $('context-details').open = true;
    $('result-title').focus({ preventScroll: true });
    if (matchMedia('(max-width: 760px)').matches) $('result-panel').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
    announce(`${kind}. ${data.next_step}`);
  }
  function clearResult() {
    $('result-empty').hidden = false; $('result-loading').hidden = true; $('result-content').hidden = true;
    $('result-content').replaceChildren(); $('evidence-list').replaceChildren(); $('evidence-panel').hidden = true; $('metrics-panel').hidden = true; $('result-stale').hidden = true; $('result-panel').dataset.state = 'empty'; state.sources.clear();
  }
  function markStale() { if (!$('result-content').hidden) $('result-stale').hidden = false; }
  async function recall(event) {
    event?.preventDefault(); if (state.recallBusy || state.teachBusy || state.forgetting || !$('recall-form').reportValidity()) return;
    const query = $('query').value.trim(); if (!query) { note('recall-error', 'Describe the error or symptom first.', true); $('query').focus(); return; }
    const memoryEnabled = $('memory-enabled').checked;
    const payload = { query, stage: $('stage').value || null, conditions: $('conditions').value.trim(), memory_enabled: memoryEnabled };
    state.recallBusy = true; updateButtons(); note('recall-error', ''); note('example-feedback', ''); clearResult();
    $('result-panel').dataset.state = 'loading'; $('result-panel').setAttribute('aria-busy', 'true'); $('result-empty').hidden = true; $('result-loading').hidden = false;
    $('loading-title').textContent = memoryEnabled ? 'Recalling your incident memory' : 'Checking without incident memory';
    $('loading-copy').textContent = memoryEnabled ? 'Searching with Moss, then checking the conditions.' : 'Retrieval is disabled for this request.';
    announce(memoryEnabled ? 'Searching the live incident memory.' : 'Submitting with memory disabled.');
    try { const { data, browserMs } = await request('/api/recall', payload); renderResult(data, browserMs); }
    catch (error) { clearResult(); note('recall-error', error.message, true); announce(error.message); }
    finally { state.recallBusy = false; $('result-panel').setAttribute('aria-busy', 'false'); updateButtons(); }
  }
  function fillTeaching() {
    const example = state.teachingExample; if (!example) return;
    $('teach-symptom').value = text(example.symptom); $('teach-conditions').value = text(example.conditions);
    $('teach-action').value = text(example.attempted_action); $('teach-outcome').value = text(example.outcome);
    $('teach-synthetic').checked = true; $('teach-panel').open = true; $('teach-symptom').focus();
    note('teach-message', 'Fictional example filled. Save it to index this new user-reported memory.'); $('recall-taught').hidden = true;
  }
  async function teach(event) {
    event.preventDefault(); if (state.teachBusy || state.recallBusy || state.forgetting || !$('teach-form').reportValidity()) return;
    const payload = { symptom: $('teach-symptom').value.trim(), conditions: $('teach-conditions').value.trim(), attempted_action: $('teach-action').value.trim(), outcome: $('teach-outcome').value.trim(), is_synthetic: $('teach-synthetic').checked };
    if ([payload.symptom, payload.conditions, payload.attempted_action, payload.outcome].some(value => !value)) { note('teach-message', 'Complete all four fields so this memory has useful context.', true); return; }
    state.teachBusy = true; updateButtons(); $('teach-button').textContent = 'Indexing your memory...'; note('teach-message', 'Saving and indexing with Moss.'); $('recall-taught').hidden = true;
    try {
      const { data } = await request('/api/teach', payload, 60000);
      if (data.indexed !== true) throw new Error(text(data.message) || 'The server did not confirm indexing. This outcome has not been shown as saved.');
      state.lastTeaching = { ...payload, id: data.id, providedExample: payload.is_synthetic && ['symptom', 'conditions', 'attempted_action', 'outcome'].every(key => payload[key] === text(state.teachingExample?.[key]).trim()) };
      note('teach-message', `${text(data.message) || 'Indexed with Moss and saved for your session.'} ${payload.is_synthetic ? 'Fictional / user reported.' : 'User reported; not independently verified.'}`);
      $('recall-taught').hidden = false; announce('Your outcome was indexed. Try recalling it in different words.'); await refreshHealth();
    } catch (error) { note('teach-message', error.message, true); }
    finally { state.teachBusy = false; $('teach-button').textContent = 'Save to my memory +'; updateButtons(); }
  }
  async function forget() {
    if (state.forgetting || state.teachBusy || state.recallBusy) return;
    state.forgetting = true; updateButtons(); $('forget-button').textContent = 'Clearing...';
    try {
      const { data } = await request('/api/forget', {}, 30000);
      if (data.ok === false) throw new Error(text(data.message) || 'Your additions could not be cleared.');
      state.lastTeaching = null; $('teach-form').reset(); $('recall-taught').hidden = true; clearResult();
      note('teach-message', text(data.message) || 'Your session additions were cleared. The original recorded incidents remain.'); announce('Your session additions were cleared.'); await refreshHealth();
    } catch (error) { note('teach-message', error.message, true); }
    finally { state.forgetting = false; $('forget-button').textContent = 'Clear my additions'; updateButtons(); }
  }
  $('recall-form').addEventListener('submit', recall); $('teach-form').addEventListener('submit', teach);
  $('query').addEventListener('input', () => { updateCount(); markStale(); });
  [$('stage'), $('conditions')].forEach(input => input.addEventListener('input', markStale));
  $('query').addEventListener('keydown', event => { if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) { event.preventDefault(); $('recall-form').requestSubmit(); } });
  $('memory-enabled').addEventListener('change', () => { $('memory-description').textContent = $('memory-enabled').checked ? 'Retrieve past outcomes with Moss' : 'Next recall will skip retrieval'; markStale(); });
  $('condition-preset').addEventListener('change', () => { if ($('condition-preset').value) { $('conditions').value = $('condition-preset').value; markStale(); } });
  $('try-example').addEventListener('click', () => { chooseExample(state.examples.find(example => example.id === 'elevated_controller_worker_launch_denied') || state.examples[0]); markStale(); });
  $('example-select').addEventListener('change', () => { if ($('example-select').value !== '') { chooseExample(state.examples[Number($('example-select').value)]); markStale(); } });
  $('fill-teaching').addEventListener('click', fillTeaching); $('forget-button').addEventListener('click', forget);
  $('recall-taught').addEventListener('click', () => {
    const suggested = state.lastTeaching?.providedExample ? text(state.teachingExample?.recall_query) : '';
    $('query').value = suggested; $('stage').value = ''; $('conditions').value = suggested ? text(state.teachingExample?.recall_conditions) : ''; $('condition-preset').value = ''; $('context-details').open = true;
    $('memory-enabled').checked = true; $('memory-description').textContent = 'Retrieve past outcomes with Moss';
    $('query').placeholder = 'Describe the saved problem in different words...'; updateCount(); markStale(); $('query').focus();
    $('query').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'center' });
    note('example-feedback', suggested ? 'A different wording is filled. Select Recall a fix to search your live session memory.' : 'Ask in your own words. Include the conditions that made the outcome applicable.');
  });
  const stale = make('p', 'stale-notice', 'Inputs changed. Recall again to update this result.'); stale.id = 'result-stale'; stale.hidden = true; stale.setAttribute('role', 'status'); $('result-panel').children[0].after(stale);
  stageFallbacks.forEach(([value, label]) => addStage(value, label));
  if (/Mac|iPhone|iPad/.test(navigator.platform)) $('submit-shortcut').textContent = '\u2318 \u21b5';
  $('try-example').disabled = true; $('fill-teaching').disabled = true;
  updateCount(); updateButtons(); refreshHealth().then(loadExamples);
  window.addEventListener('pagehide', () => window.clearTimeout(state.healthTimer));
})();
