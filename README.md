# Goblin Tactics

A text-based tactical simulation where AI-controlled knights battle AI-controlled goblins in procedurally generated dungeons. The goblins use reinforcement learning to evolve their tactics over time.

## Setup

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
# Run a single battle with visualization
python main.py battle --show

# Train goblins (1000 episodes)
python main.py train --episodes 1000

# Evaluate trained model
python main.py eval --model models/checkpoint.pth --battles 10
```

## Features

- **Procedural Dungeons**: BSP-based generation with rooms, corridors, and chokepoints
- **Tactical Combat**: Knights (strong, few) vs Goblins (weak, many)
- **Shared Vision**: Units see what their allies see
- **Reinforcement Learning**: Goblins learn tactics through Deep Q-Learning
- **Colored ASCII Display**: Beautiful terminal graphics with colorama

## Project Structure

See `REQUIREMENTS.md` for full specification.
