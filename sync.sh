#!/bin/sh
while true; do
    sleep 30
    echo "Synchronizing state to standby twin..."
    cp /data/state_journal.log /shared-volume/synced_state.log
done