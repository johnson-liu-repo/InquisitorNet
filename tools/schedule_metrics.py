# tools/schedule_metrics.py
from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess, sys

def run_metrics():
    cmd = [
        sys.executable,
        "-m",
        "inquisitor.metrics.metrics_job",
        "--db",
        "inquisitor_net.db",
        "--days",
        "7",
        "--out",
        "reports/metrics",
    ]
    subprocess.run(cmd, check=False)

def main():
    sched = BlockingScheduler()
    # daily at 02:00
    sched.add_job(run_metrics, 'cron', hour=2, minute=0)
    try:
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    main()
