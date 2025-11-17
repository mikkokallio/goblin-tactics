#!/usr/bin/env python3
"""Quick test to visualize goblin spawn spreading"""
import yaml
from src.simulation.battle import Battle
from src.display.renderer import Renderer

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create battle
battle = Battle(config, battle_id=0, record=False)
renderer = Renderer(config)

# Show initial state (turn 0)
print("\n" + "="*60)
print("INITIAL GOBLIN SPAWN POSITIONS")
print("="*60)
renderer.render(battle.world, battle.knights, battle.goblins, battle.turn)

# Count goblins per room (approximate by clustering)
goblin_positions = [(g.x, g.y) for g in battle.goblins]
print(f"\nTotal goblins: {len(goblin_positions)}")
print(f"Goblin positions: {goblin_positions[:10]}...")  # Show first 10

# Calculate spread metric (average distance to nearest neighbor)
min_distances = []
for i, (x1, y1) in enumerate(goblin_positions):
    distances = []
    for j, (x2, y2) in enumerate(goblin_positions):
        if i != j:
            distances.append(abs(x1 - x2) + abs(y1 - y2))
    if distances:
        min_distances.append(min(distances))

if min_distances:
    avg_nearest = sum(min_distances) / len(min_distances)
    print(f"Average distance to nearest goblin: {avg_nearest:.1f} tiles")
    print(f"Min distance between any two goblins: {min(min_distances)} tiles")
    print(f"Max distance to nearest neighbor: {max(min_distances)} tiles")
