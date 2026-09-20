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
    return {'stage': stage or None, 'inferred_stages': inferred, 'facts': facts, 'labels': labels, 'platforms': platforms, 'input_text': text}


# A conservative condition check follows semantic retrieval for new visitor notes.
# It is intentionally not an embedding-score threshold or a success classifier.
_COMMON_TERMS = set("""the and for with from that this these those then than into about after
before during when where which what why how was were are has have had can could would should
will your you our their its not only also just more most some any all but now again please help
error errors failed failure failing fails fail problem issue tried try attempt attempts action
outcome result results recorded reported current same different work works working does did done
app application system says said ready uses used using use need needs happens happened memory
note stored condition conditions symptom symptoms good bad old new still really very much one
last time seem seems show shows get gets got give here there without because other want today
""".split())


def _condition_terms(text):
    return {word for word in re.findall(r'[a-z][a-z0-9_]{2,}', text.lower())
            if word not in _COMMON_TERMS}


def _technical_identifiers(text):
    # Ports in either "localhost:3001" or "port 3001" form, error codes and
    # concrete source/config filenames provide a more specific shared anchor.
    lowered = text.lower()
    result = {'port:' + m.group(1) for m in re.finditer(r'(?:\bport\s*[:=]?\s*|[a-z0-9._-]+:)([0-9]{2,5})\b', lowered)}
    patterns = [r'\b0x[0-9a-f]{4,}\b',
                r'\b(?:http|errno|error)[ _:-]*[0-9]{3,}\b',
                r'\b[a-z0-9_.-]+\.(?:py|js|ts|tsx|jsx|json|yaml|yml|toml|ini|cfg|dll|so|exe)\b']
    for pattern in patterns:
        result.update(re.findall(pattern, lowered))
    result.update(m.lower() for m in re.findall(r'\b[A-Z][A-Z_]{1,}[0-9]{3,}\b', text))
    return result


def visitor_conditions_grounded(record, input_text):
    # search_text is built only from symptom + conditions. Never use a proposed
    # action or claimed outcome to manufacture evidence of current applicability.
    recorded = record.get('search_text', '')
    return (len(_condition_terms(recorded) & _condition_terms(input_text)) >= 2
            or bool(_technical_identifiers(recorded) & _technical_identifiers(input_text)))


def decide(retrieved_records, context):
    empty = {'state': 'no_match', 'headline': 'No applicable memory yet', 'next_step': 'Record the exact failing stage and the conditions you have verified, then recall again.', 'what_matches': [], 'failed_attempts': [], 'matched_id': None}
    if not retrieved_records:
        return empty
    facts = context['facts']
    if 'admin_passed' in facts and ('admin_false' in facts or 'administrator_check_failed' in facts):
        return {**empty, 'state': 'clarify', 'headline': 'These conditions conflict', 'next_step': 'For this attempt, did the administrator check pass or fail? Separate earlier attempts from the current failure before selecting a remedy.'}
    eligible, partial, platform_mismatches, prerequisite_conflicts = [], [], [], []
    for record in retrieved_records:
        if record.get('provenance_class') == 'visitor_reported':
            continue
        rule = record.get('applicability', {})
        stage_matches = (context['stage'] == record['stage']) if context['stage'] else record['stage'] in context['inferred_stages']
        supporting = set(sum(rule.get('required_fact_groups', []), [])) & facts
        if context['stage'] and not stage_matches:
            continue
        if set(rule.get('contradictions', [])) & facts:
            if stage_matches or supporting:
                prerequisite_conflicts.append(record)
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
    if prerequisite_conflicts:
        record = prerequisite_conflicts[0]
        return {**empty, 'state': 'clarify', 'headline': 'The recorded prerequisites do not match', 'next_step': record['applicability']['clarification'], 'what_matches': ['Retrieved history has a prerequisite contradicted by the current input.']}
    if partial:
        record = partial[0]
        return {**empty, 'state': 'clarify', 'headline': 'One detail before a next step', 'next_step': record['applicability']['clarification'], 'what_matches': ['Related history was retrieved, but its conditions are not established.'], 'matched_id': record['id']}
    # Shared permission-error language alone never decides between administrator and worker stages.
    # This check consumes only retrieved record stage data, not a hardcoded example answer.
    stages = list(dict.fromkeys(r['stage'] for r in retrieved_records if r.get('applicability')))
    if not context['stage'] and len(stages) > 1 and context.get('permission_error'):
        return {**empty, 'state': 'clarify', 'headline': 'The failure stage matters', 'next_step': 'Which stage failed: administrator preflight, ordinary-worker launch, or waiting for controller startup?', 'what_matches': ['Similar wording appears in memories with different prerequisites.']}
    taught = next((r for r in retrieved_records if r.get('provenance_class') == 'visitor_reported'), None)
    if taught and retrieved_records[0]['id'] == taught['id'] and visitor_conditions_grounded(taught, context.get('input_text', '')):
        return {**empty, 'state': 'clarify', 'headline': 'A similar outcome you recorded', 'matched_id': taught['id'], 'next_step': 'Do these recorded conditions match your current case? ' + taught['conditions'], 'what_matches': ['Moss retrieved your session memory. Its reported outcome is shown below; it has not been independently verified.']}
    return empty
