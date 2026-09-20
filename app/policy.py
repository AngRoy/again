"""A small applicability policy. Facts gate native-retrieved memories, never replace retrieval."""
import re


def analyze(records, query, conditions='', stage=None):
    text = re.sub(r'\s+', ' ', f'{query} {conditions}')
    facts, labels = set(), {}
    inferred = set()
    for record in records:
        rule = record.get('applicability', {})
        for pattern in rule.get('stage_aliases', []):
            if re.search(pattern, text, re.I):
                inferred.add(record['stage'])
        for signal in rule.get('signals', []):
            if any(re.search(p, text, re.I) for p in signal['any']):
                facts.add(signal['fact'])
                labels[signal['fact']] = signal['label']
    # Environment is a prerequisite too. Merely mentioning a recorded Windows
    # error must not authorize its repair for an explicitly different host.
    platforms = set()
    aliases = {'Windows': r'\b(?:windows|win32|win64)\b',
               'Linux': r'\b(?:linux|ubuntu|debian|fedora|centos|alpine)\b',
               'macOS': r'\b(?:macos|mac\s*os|os\s*x|darwin)\b'}
    for name, pattern in aliases.items():
        for match in re.finditer(pattern, text, re.I):
            before = text[max(0, match.start()-25):match.start()]
            if not re.search(r'\b(?:not|never)(?:\s+(?:on|running|using))?\s*$', before, re.I):
                platforms.add(name)
    # An explicit stage identifies a stage, not the truth of its prerequisites.
    return {'stage': stage or None, 'inferred_stages': inferred, 'facts': facts, 'labels': labels, 'platforms': platforms}


def decide(retrieved_records, context):
    empty = {'state': 'no_match', 'headline': 'No applicable memory yet', 'next_step': 'Record the exact failing stage and the conditions you have verified, then recall again.', 'what_matches': [], 'failed_attempts': [], 'matched_id': None}
    if not retrieved_records:
        return empty
    facts = context['facts']
    if 'admin_passed' in facts and ('admin_false' in facts or 'administrator_check_failed' in facts):
        return {**empty, 'state': 'clarify', 'headline': 'These conditions conflict', 'next_step': 'For this attempt, did the administrator check pass or fail? Separate earlier attempts from the current failure before selecting a remedy.'}
    eligible, partial, platform_mismatches = [], [], []
    for record in retrieved_records:
        if record.get('provenance_class') == 'visitor_reported':
            continue
        rule = record.get('applicability', {})
        stage_matches = (context['stage'] == record['stage']) if context['stage'] else record['stage'] in context['inferred_stages']
        supporting = set(sum(rule.get('required_fact_groups', []), [])) & facts
        if set(rule.get('contradictions', [])) & facts:
            continue
        if context['stage'] and not stage_matches:
            continue
        groups_ok = all(set(group) & facts for group in rule.get('required_fact_groups', []))
        platforms = context.get('platforms', set())
        recorded_os = record.get('environment', {}).get('os')
        if (stage_matches or supporting) and recorded_os and platforms and platforms != {recorded_os}:
            platform_mismatches.append(record)
            continue
        if stage_matches and groups_ok:
            eligible.append((record, supporting))
        elif stage_matches or supporting:
            partial.append(record)
    if eligible:
        # Native ranking selects among records whose conditions actually apply.
        record, supporting = eligible[0]
        return {'state': 'matched', 'headline': record['title'], 'next_step': record['next_step'], 'what_matches': [f"Stage: {record['stage']}", *[context['labels'][f] for f in sorted(supporting)]], 'failed_attempts': record.get('failed_attempts', []), 'matched_id': record['id']}
    if platform_mismatches:
        recorded_os = platform_mismatches[0]['environment']['os']
        return {**empty, 'state': 'clarify', 'headline': 'Check the affected environment', 'next_step': f'This memory was observed on {recorded_os}. Which operating system runs the failing component in your current attempt? Its recorded repair has not been validated for a different environment.', 'what_matches': ['Related history was retrieved, but the reported platform does not establish the recorded environment.']}
    if partial:
        record = partial[0]
        return {**empty, 'state': 'clarify', 'headline': 'One detail before a next step', 'next_step': record['applicability']['clarification'], 'what_matches': ['Related history was retrieved, but its conditions are not established.'], 'matched_id': record['id']}
    # Shared permission-error language alone never decides between administrator and worker stages.
    # This check consumes only retrieved record stage data, not a hardcoded example answer.
    stages = list(dict.fromkeys(r['stage'] for r in retrieved_records if r.get('applicability')))
    if not context['stage'] and len(stages) > 1 and context.get('permission_error'):
        return {**empty, 'state': 'clarify', 'headline': 'The failure stage matters', 'next_step': 'Which stage failed: administrator preflight, ordinary-worker launch, or waiting for controller startup?', 'what_matches': ['Similar wording appears in memories with different prerequisites.']}
    taught = next((r for r in retrieved_records if r.get('provenance_class') == 'visitor_reported'), None)
    if taught and retrieved_records[0]['id'] == taught['id']:
        return {**empty, 'state': 'clarify', 'headline': 'A similar outcome you recorded', 'matched_id': taught['id'], 'next_step': 'Do these recorded conditions match your current case? ' + taught['conditions'], 'what_matches': ['Moss retrieved your session memory. Its reported outcome is shown below; it has not been independently verified.']}
    return empty
