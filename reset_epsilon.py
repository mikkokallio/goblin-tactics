#!/usr/bin/env python3
"""Reset epsilon in a checkpoint to encourage more exploration with new rewards"""
import json
import os
import shutil

checkpoint_path = "models/checkpoint_ep100.json"
output_path = "models/checkpoint_ep100_reset.json"
stats_path = "models/checkpoint_ep100_stats.json"

# The checkpoint is just weights - we need to modify the stats file
print(f"Checkpoint file contains weights - looking for stats file...")

# Load and modify stats
if not os.path.exists(stats_path):
    print(f"Stats file not found at {stats_path}")
    print("Creating new stats file with epsilon=0.9, episode=0")
    stats = {
        'epsilon': 0.9,
        'episode': 0,
        'total_steps': 0
    }
else:
    with open(stats_path, 'r') as f:
        stats = json.load(f)
    
    old_epsilon = stats.get('epsilon', 'N/A')
    old_episode = stats.get('episode', 'N/A')
    
    # Update epsilon to 0.9 (90% exploration)
    stats['epsilon'] = 0.9
    stats['episode'] = 0
    stats['total_steps'] = 0
    
    print(f"Old epsilon: {old_epsilon} -> New epsilon: {stats['epsilon']}")
    print(f"Old episode: {old_episode} -> New episode: {stats['episode']}")

# Save modified stats
output_stats_path = output_path.replace('.json', '_stats.json')
with open(output_stats_path, 'w') as f:
    json.dump(stats, f, indent=2)

# Copy weights to new checkpoint
shutil.copy(checkpoint_path, output_path)

print(f"\nModified checkpoint saved to: {output_path}")
print(f"Modified stats saved to: {output_stats_path}")
print(f"Weights preserved from: {checkpoint_path}")
print(f"\nTo use: python main.py train --episodes 100 --resume {output_path}")

