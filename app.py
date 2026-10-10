import time
import os
import json

# Simulates 256-byte state generation
PAYLOAD = "A" * 200  
state_file = "/data/state_journal.log"
rate = int(os.getenv("UPDATE_RATE", 100)) # updates per second

def generate_state():
    sequence = 0
    os.makedirs("/data", exist_ok=True)
    while True:
        sequence += 1
        entry = json.dumps({"seq": sequence, "payload": PAYLOAD})
        with open(state_file, "a") as f:
            f.write(entry + "\n")
        time.sleep(1.0 / rate)

if __name__ == "__main__":
    generate_state()