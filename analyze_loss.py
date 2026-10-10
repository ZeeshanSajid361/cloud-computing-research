"""Compute data loss at EVERY pod-kill from the journal + sync log.

Usage: python analyze_loss.py state_journal.log sync_log.jsonl [gap_seconds]

A kill is detected as a gap in journal timestamps larger than gap_seconds (default 2).
For each kill:  generated = updates produced in that pod life
                synced    = highest seq in the sync log at or before the kill
                loss %    = (seq_at_kill - synced) / generated
"""
import json
import statistics
import sys


def load(path):
    out = []
    with open(path) as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def main():
    journal = load(sys.argv[1])
    syncs = load(sys.argv[2])
    gap = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
    if not journal or not syncs:
        sys.exit("empty input")
    kills, life_start = [], journal[0]["seq"]
    for prev, cur in zip(journal, journal[1:]):
        if cur["ts"] - prev["ts"] > gap:
            seq_kill, t_kill = prev["seq"], prev["ts"]
            synced = max([s["seq"] for s in syncs if s["ts"] <= t_kill + 0.05], default=0)
            generated = seq_kill - life_start + 1
            lost = max(0, seq_kill - synced)
            kills.append((len(kills) + 1, generated, lost, 100.0 * lost / generated))
            life_start = cur["seq"]
    print(f"{'kill':>4} {'generated':>10} {'lost':>8} {'loss %':>8}")
    for k, g, l, p in kills:
        print(f"{k:>4} {g:>10} {l:>8} {p:>8.2f}")
    if kills:
        pct = [k[3] for k in kills]
        q = statistics.quantiles(pct, n=4) if len(pct) >= 2 else [pct[0]] * 3
        print(f"\nkills={len(kills)}  median loss={statistics.median(pct):.2f}%  "
              f"IQR=[{q[0]:.2f}, {q[2]:.2f}]%  mean lost records={statistics.mean(k[2] for k in kills):.0f}")


if __name__ == "__main__":
    main()
