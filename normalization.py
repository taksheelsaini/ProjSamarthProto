from datetime import datetime

def normalize_evidence(evidence_items):
    """I normalize raw evidence: ensure fields id, date (datetime), source, headline, score.

    My heuristics:
    - Parse date if string in YYYY-MM-DD
    - Assign default score based on recency and presence of `relevance` or `trust` fields
    """
    norm = []
    for i,e in enumerate(evidence_items):
        item = dict(e)
        item.setdefault('id', f"ev{i}")
        # parse date
        d = item.get('date')
        if isinstance(d,str):
            try:
                item['date'] = datetime.fromisoformat(d)
            except Exception:
                item['date'] = None
        # score heuristics
        score = item.get('score')
        if score is None:
            base = 0.5
            # boost for recent
            dt = item.get('date')
            if isinstance(dt, datetime):
                days = (datetime.now() - dt).days
                if days < 365:
                    base += 0.2
                elif days < 365*5:
                    base += 0.1
            # trust/relevance fields
            if item.get('trust'):
                base += 0.1
            if item.get('relevance'):
                base += min(0.3, float(item.get('relevance'))/10.0)
            score = min(1.0, base)
        item['score'] = score
        norm.append(item)
    return norm

def provenance_score(arguments):
    """I aggregate provenance score for generated arguments. Returns dict with mean and weighted.
    Arguments is list of dict containing 'provenance' field.
    """
    vals = [a.get('provenance',0.0) for a in arguments]
    if not vals:
        return {'mean':0.0}
    mean = sum(vals)/len(vals)
    weighted = sum(v*((i+1)/len(vals)) for i,v in enumerate(sorted(vals, reverse=True)))/len(vals)
    return {'mean': mean, 'weighted': weighted}
