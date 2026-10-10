import time
import shutil
import math
import json

# Architectural constants from your C1 Proposal
W1 = 0.5      # Weight for CPU overhead
W2 = 0.5      # Weight for State Loss
KAPPA = 0.1   # Fixed CPU cost per sync event
LAMBDA = 1.0 / 120.0  # Failure hazard (1 failure per 120s based on our Chaos profile)

# The discrete action ladder from your methodology
INTERVAL_LADDER = [0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0] 

state_file = "/data/state_journal.log"
sync_file = "/shared-volume/synced_state.log"

def get_current_sequence():
    try:
        with open(state_file, 'r') as f:
            lines = f.readlines()
            if not lines: return 0
            return json.loads(lines[-1].strip()).get("seq", 0)
    except Exception:
        return 0

def calculate_optimal_interval(rate):
    if rate <= 0: 
        return INTERVAL_LADDER[-1] # Default to 30s if idle
    
    # The Square-Root Law optimization formula from your proposal
    val = (2 * W1 * KAPPA) / (W2 * LAMBDA * rate)
    optimal_delta = math.sqrt(val)
    
    # Snap the raw calculation to the nearest valid interval in your ladder
    best_interval = min(INTERVAL_LADDER, key=lambda x: abs(x - optimal_delta))
    return best_interval

def main():
    print("Starting Telemetry-Driven Adaptive Scheduler...")
    last_seq = 0
    last_time = time.time()
    
    while True:
        current_time = time.time()
        current_seq = get_current_sequence()
        
        # Calculate state generation rate (r)
        time_diff = current_time - last_time
        rate = (current_seq - last_seq) / time_diff if time_diff > 0 else 0
        
        # Dynamically calculate the next sync interval
        delta = calculate_optimal_interval(rate)
        print(f"Data Rate: {rate:.2f} updates/s -> Adapting Sync Interval to: {delta}s")
        
        # Perform Synchronization
        try:
            shutil.copy2(state_file, sync_file)
        except Exception:
            pass
            
        last_seq = current_seq
        last_time = current_time
        
        # Sleep for the dynamic interval rather than a static 30 seconds
        time.sleep(delta)

if __name__ == "__main__":
    main()