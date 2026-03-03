#!/usr/bin/env python3
"""Check for new subscribers and send notifications"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, 'stream-data.json')
LAST_FILE = os.path.join(SCRIPT_DIR, '.last_subscriber')

def check_new_subscribers():
    """Check for new subscribers since last run"""
    if not os.path.exists(DATA_FILE):
        return []
    
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    
    subscribers = data.get('subscribers', [])
    
    # Get last notified subscriber
    last_notified = ""
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, 'r') as f:
            last_notified = f.read().strip()
    
    # Find new ones
    new_subs = []
    for email in subscribers:
        if email == last_notified:
            break
        new_subs.insert(0, email)
    
    # Update last notified
    if subscribers:
        with open(LAST_FILE, 'w') as f:
            f.write(subscribers[0])
    
    return new_subs

if __name__ == '__main__':
    new = check_new_subscribers()
    if new:
        print(f"New subscribers: {new}")
        sys.exit(0)
    else:
        print("No new subscribers")
        sys.exit(1)
