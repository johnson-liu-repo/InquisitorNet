# inquisitor/metrics/metrics_job.py
import argparse, sqlite3, csv
from pathlib import Path
from datetime import datetime, timedelta

def compute_metrics(conn, days=7):
    cur = conn.cursor()
    cur.execute("""
        SELECT label, COUNT(*) FROM labels
        WHERE created_at >= datetime('now', ?)
        GROUP BY label
    """, (f'-{days} days',))
    counts = {row[0]: row[1] for row in cur.fetchall()}
    tp = counts.get('TP',0); fp = counts.get('FP',0); tn = counts.get('TN',0); fn = counts.get('FN',0)
    precision = tp / (tp + fp) if (tp+fp) else 0.0
    recall = tp / (tp + fn) if (tp+fn) else 0.0
    f1 = 2*precision*recall/(precision+recall) if (precision+recall) else 0.0
    return {"tp":tp,"fp":fp,"tn":tn,"fn":fn,"precision":precision,"recall":recall,"f1":f1}

def write_metrics_to_db(conn, metrics: dict, day: str | None = None) -> None:
    if day is None:
        day = datetime.utcnow().strftime('%Y-%m-%d')
    conn.execute(
        """
        INSERT OR REPLACE INTO metrics_detector_daily
        (day, precision, recall, f1, tp, fp, tn, fn)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            day,
            metrics["precision"],
            metrics["recall"],
            metrics["f1"],
            metrics["tp"],
            metrics["fp"],
            metrics["tn"],
            metrics["fn"],
        ),
    )
    conn.commit()

def write_reports(metrics: dict, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime('%Y%m%d')
    # CSV
    with (out_dir / f'metrics_{ts}.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['tp','fp','tn','fn','precision','recall','f1'])
        w.writerow([metrics[k] for k in ['tp','fp','tn','fn','precision','recall','f1']])
    # Markdown
    md = f"""# Detector Metrics ({ts})
- TP: {metrics['tp']}
- FP: {metrics['fp']}
- TN: {metrics['tn']}
- FN: {metrics['fn']}
- Precision: {metrics['precision']:.3f}
- Recall: {metrics['recall']:.3f}
- F1: {metrics['f1']:.3f}
"""
    (out_dir / f'metrics_{ts}.md').write_text(md)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='inquisitor_net.db')
    ap.add_argument('--days', type=int, default=7)
    ap.add_argument('--out', default='reports/metrics')
    ap.add_argument('--write-db', action='store_true', help='Persist metrics to DB table')
    args = ap.parse_args()
    with sqlite3.connect(args.db) as conn:
        m = compute_metrics(conn, days=args.days)
        if args.write_db:
            write_metrics_to_db(conn, m)
    write_reports(m, Path(args.out))
    print("Metrics written to", args.out)

if __name__ == '__main__':
    main()
