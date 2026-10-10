"""Sync agent (fixed). Drop-in replacement for adaptive_sync.py.

SYNC_MODE=adaptive (default) -> square-root-law controller
SYNC_MODE=static             -> fixed STATIC_INTERVAL seconds (use for the 30 s baseline
                                and the best-static 0.5 s arm, so every arm uses the SAME
                                copy mechanism)

Fixes vs original:
  * rate no longer computed from last_seq=0 at start-up (the 4e8 updates/s artefact)
  * a restart (sequence going backwards) is handled instead of producing a bogus rate
  * rate is smoothed (EWMA); journal tail is read from the end, not readlines()
  * copy is atomic (temp file + os.replace) so a kill cannot leave a truncated copy
  * ladder matches the paper: {50,100,250,500,1000,2500,5000} ms
  * each sync is logged to sync_log.jsonl so loss at every kill can be computed
"""
import json
import math
import os
import shutil
import time

W1 = float(os.getenv("W1", "0.5"))
W2 = float(os.getenv("W2", "0.5"))
KAPPA = float(os.getenv("KAPPA", "0.1"))          # ASSUMED - calibrate by microbenchmark
LAMBDA = float(os.getenv("LAMBDA", str(1 / 120)))  # ASSUMED - matches chaos schedule
LADDER = [0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
ALPHA = 0.5                                        # EWMA smoothing for the rate

MODE = os.getenv("SYNC_MODE", "adaptive")          # adaptive | static
STATIC_INTERVAL = float(os.getenv("STATIC_INTERVAL", "0.5"))

STATE_FILE = os.getenv("STATE_FILE", "/data/state_journal.log")
SYNC_FILE = os.getenv("SYNC_FILE", "/shared-volume/synced_state.log")
SYNC_LOG = os.getenv("SYNC_LOG", os.path.join(os.path.dirname(SYNC_FILE), "sync_log.jsonl"))
TMP_FILE = SYNC_FILE + ".tmp"


def last_seq():
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


def interval_for(rate):
    if rate <= 0:
        return LADDER[-1]
    opt = math.sqrt((2 * W1 * KAPPA) / (W2 * LAMBDA * rate))
    return min(LADDER, key=lambda x: abs(x - opt))


def sync_once():
    seq = last_seq()
    try:
        shutil.copyfile(STATE_FILE, TMP_FILE)
        os.replace(TMP_FILE, SYNC_FILE)
        with open(SYNC_LOG, "a") as f:
            f.write(json.dumps({"ts": time.time(), "seq": seq}) + "\n")
    except Exception as e:
        print(f"sync error: {e}", flush=True)


def main():
    print(f"Sync agent starting: mode={MODE}", flush=True)
    delta = STATIC_INTERVAL if MODE == "static" else 0.5
    prev_seq, prev_t, rate = last_seq(), time.time(), None
    while True:
        sync_once()
        time.sleep(delta)
        now, seq = time.time(), last_seq()
        if seq >= prev_seq and now > prev_t:       # seq < prev_seq means the app restarted
            inst = (seq - prev_seq) / (now - prev_t)
            rate = inst if rate is None else ALPHA * inst + (1 - ALPHA) * rate
        prev_seq, prev_t = seq, now
        if MODE == "adaptive" and rate is not None:
            delta = interval_for(rate)
        print(f"rate={rate if rate is not None else 0:.1f}/s interval={delta}s", flush=True)


if __name__ == "__main__":
    main()
