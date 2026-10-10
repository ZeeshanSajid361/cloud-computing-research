"""State generator (fixed). Drop-in replacement for app.py.

Changes vs original:
  * sequence number RESUMES from the journal after a pod restart (no reset to 1)
  * every entry carries a timestamp ("ts") so kills can be detected as gaps
  * PROFILE env var gives a non-stationary workload: steady | burst | ramp
  * journal file kept open (line-buffered) instead of reopened per update
"""
import json
import os
import time

PAYLOAD = "A" * 200
STATE_FILE = os.getenv("STATE_FILE", "/data/state_journal.log")
PROFILE = os.getenv("PROFILE", "steady")        # steady | burst | ramp
BASE_RATE = int(os.getenv("UPDATE_RATE", "100"))  # updates/s for 'steady'


def resume_seq():
    """Last committed sequence number in the journal (0 if none)."""
    try:
        with open(STATE_FILE, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - 4096))
            for line in reversed(f.read().splitlines()):
                try:
                    return json.loads(line)["seq"]
                except Exception:
                    continue
    except Exception:
        pass
    return 0


def target_rate(now):
    """Rate (updates/s) as a function of wall-clock time, so it survives restarts."""
    if PROFILE == "burst":                       # alternate 100 / 1000 every 30 s
        return 1000 if int(now // 30) % 2 else 100
    if PROFILE == "ramp":                        # 100 -> 1000 over 10 min, repeating
        return 100 + 900 * ((now % 600) / 600.0)
    return BASE_RATE


def generate_state():
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    seq = resume_seq()
    with open(STATE_FILE, "a", buffering=1) as f:
        while True:
            seq += 1
            now = time.time()
            f.write(json.dumps({"seq": seq, "ts": now, "payload": PAYLOAD}) + "\n")
            time.sleep(1.0 / target_rate(now))


if __name__ == "__main__":
    generate_state()
