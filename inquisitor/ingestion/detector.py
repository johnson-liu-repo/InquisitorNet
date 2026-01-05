from __future__ import annotations
import re, json
from typing import List, Dict, Any

def compile_rules(rules: List[Dict[str, Any]]):
    """Compile detection rules into regex patterns.

    Args:
        rules (List[Dict[str, Any]]): List of rule definitions.

    Returns:
        List[Dict[str, Any]]: Compiled rules with regex patterns.
    """
    out = []
    for r in rules:
        out.append({
            'id': r['id'],
            'name': r['name'],
            'pattern': re.compile(r['pattern']),
            'weight': float(r.get('weight', 0.5)),
            'exculpatory': [re.compile(p) for p in r.get('exculpatory', [])]
        })
    return out

def explain_noop(mark_score: float, matched: List[str], exculp: List[str], text: str) -> str:
    """Explain the reasoning behind a "no operation" (noop) decision.

    Args:
        mark_score (float): The score assigned to the item.
        matched (List[str]): List of matched rule IDs.
        exculp (List[str]): List of exculpatory rule IDs.
        text (str): The text content being analyzed.

    Returns:
        str: Explanation of the noop decision.
    """
    if matched and not exculp:
        return f"Matched {', '.join(matched)}; no benign context detected."
    if exculp:
        return f"Benign context matched ({', '.join(exculp)}); likely non-heretical."
    return "No strong signals."
    
def run_detector_to_db(settings, conn):
    rules = compile_rules(settings.detector.get('rules', []))
    th_mark = float(settings.detector.get('thresholds', {}).get('mark', 0.65))
    th_acquit = float(settings.detector.get('thresholds', {}).get('acquit', 0.35))
    cur = conn.cursor()
    cur.execute("SELECT item_id, subreddit, body, post_meta_json FROM scrape_hits")
    rows = cur.fetchall()
    n_mark = n_acquit = 0
    for item_id, subreddit, body, post_meta_json in rows:
        matched_ids = []
        exculp_ids = []
        score = 0.0
        for r in rules:
            if r['pattern'].search(body or ''):
                matched_ids.append(r['id'])
                score += r['weight']
            for ex in r['exculpatory']:
                if ex.search(body or ''):
                    exculp_ids.append(r['id'] + ":ex")
                    score -= 0.2  # small deduction for benign context
        score = max(0.0, min(1.0, score))  # clamp
        if score >= th_mark:
            reasoning = explain_noop(score, matched_ids, [], body)
            cur.execute('''INSERT INTO detector_marks (item_id, subreddit, comment_text, post_meta_json, reasoning_for_mark, degree_of_confidence)
                           VALUES (?,?,?,?,?,?)''',
                        (item_id, subreddit, body, post_meta_json, reasoning, score))
            n_mark += 1
        elif score <= th_acquit:
            reasoning = explain_noop(score, [], exculp_ids, body)
            cur.execute('''INSERT INTO detector_acquittals (item_id, subreddit, comment_text, post_meta_json, reasoning_for_acquittal, degree_of_confidence)
                           VALUES (?,?,?,?,?,?)''',
                        (item_id, subreddit, body, post_meta_json, reasoning, 1.0-score))
            n_acquit += 1
        else:
            # hold for later, neither marked nor acquitted (still stored only in scrape_hits)
            pass
    conn.commit()
    return n_mark, n_acquit
