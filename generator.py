from datetime import datetime
from typing import List, Dict

TEMPLATE_PRO = "Expand program: {claim}. Evidence: {evidence_summary}."
TEMPLATE_CON = "Caution against expansion: {claim}. Evidence: {evidence_summary}."


def _summarize_evidence(evidence_items: List[Dict]) -> str:
    # join top headlines or sources in stable order
    parts = []
    for e in evidence_items[:3]:
        parts.append(e.get('headline') or e.get('title') or e.get('source') or e.get('id'))
    return ' | '.join(parts)


def generate_policy_argument(question: str, evidence: List[Dict], top_k: int = 3) -> List[Dict]:
    """Generate a deterministic list of arguments (mix pro/con) from normalized evidence.

    Strategy:
    - Sort evidence by score descending, then date descending.
    - For each argument slot, pick top unused evidence items (up to 3) to build a concise argument.

    Returns a list of dicts: {{title, argument, provenance, sources}}
    """
    args = []
    # sort evidence by score desc, then date (newer first)
    def _key(e):
        score = e.get('score', 0.5)
        date_val = e.get('date')
        date = None
        # tolerate different date formats: datetime, ISO string, or missing
        if hasattr(date_val, 'timestamp'):
            date = date_val
        else:
            # try parse string
            try:
                if isinstance(date_val, str) and date_val:
                    date = datetime.fromisoformat(date_val)
            except Exception:
                date = None
        # fallback to epoch (safe) when missing/malformed
        if date is None:
            date = datetime(1970, 1, 1)
        # safe timestamp
        ts = date.timestamp() if hasattr(date, 'timestamp') else 0
        return (-score, -ts)

    sorted_ev = sorted(evidence, key=_key)

    used_ids = set()
    n = len(sorted_ev)
    # If evidence is small, rotate selection windows to create varied arguments
    for i in range(top_k):
        side = 'pro' if i % 2 == 0 else 'con'
        selected = []
        if n == 0:
            selected = []
        elif n <= 3:
            # rotate a sliding window over sorted_ev to avoid identical picks
            start = (i * 1) % n
            for j in range(min(3, n)):
                e = sorted_ev[(start + j) % n]
                selected.append(e)
        else:
            # prefer unused evidence first
            for e in sorted_ev:
                if e.get('id') in used_ids:
                    continue
                selected.append(e)
                used_ids.add(e.get('id'))
                if len(selected) >= 3:
                    break

        if not selected:
            # fallback: top items
            selected = sorted_ev[:min(3, n)]

        summary = _summarize_evidence(selected)
        claim = f"{question} — {'benefits' if side == 'pro' else 'risks'}"
        template = TEMPLATE_PRO if side == 'pro' else TEMPLATE_CON
        argument = template.format(claim=claim, evidence_summary=summary)
        sources = [e.get('id', '?') for e in selected]
        # provenance: simple average of evidence 'score' field
        prov = sum(e.get('score', 0.5) for e in selected) / max(1, len(selected))
        args.append({
            'title': f"{('For' if side == 'pro' else 'Against')}: {summary[:80]}",
            'argument': argument,
            'provenance': prov,
            'sources': sources,
        })

    return args
