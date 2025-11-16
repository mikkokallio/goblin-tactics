# Goblin Tactics - Quick Start Guide

## What You Have

A fully functional tactical combat simulation with:

✅ **Procedural Dungeon Generation** - BSP algorithm creates varied tactical environments  
✅ **Smart Vision System** - 3-square LoS with allied vision sharing (transitive)  
✅ **Memory System** - Units remember explored terrain and last-seen enemy positions  
✅ **Intelligent Pathfinding** - A* with memory-based navigation through familiar areas  
✅ **Colored ASCII Display** - Beautiful terminal graphics using colorama  
✅ **Combat System** - Turn-based combat with HP, damage, and death  
✅ **Knight AI** - Rush enemies, explore when blocked, pursue last-known positions  
✅ **Goblin AI** - Baseline behavior (ready for learning enhancement)  

## Running the Simulation

### Setup (Already Done!)
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run a Single Battle
```bash
python main.py battle --show
```

Watch as knights and goblins fight in a procedurally generated dungeon!

## What's Implemented

### Core Features
- **4 Knights** (cyan K) vs **12-20 Goblins** (green g)
- Knights: 20-30 HP, 5-8 damage (strong & durable)
- Goblins: 3-6 HP, 1-2 damage (weak but numerous)
- Difficult terrain (~) costs extra movement
- Vision: 3 squares, shared with visible allies
- Memory: Units remember all seen terrain and enemy positions

### Tactical Behavior
- **Knights**: Rush closest enemy → Pursue last-known position → Explore
- **Goblins**: Same baseline behavior (ready for ML enhancement)
- Both sides use pathfinding through remembered areas
- Explore-when-blocked logic prevents corridor deadlocks

### Display
- Real-time colored ASCII visualization
- HP bars for all units
- Combat log showing recent actions
- Turn counter and statistics

## Next Steps: Machine Learning Phase

The foundation is complete! Ready for Phase 3:

### To Add Reinforcement Learning:
1. **Install PyTorch** (when available for your platform)
2. **Implement State Encoding** in `goblin_ai.py`
   - Encode goblin observations into neural network input
3. **Build DQN Model** 
   - Neural network architecture for Q-learning
4. **Implement Reward System**
   - Track outcomes and assign rewards
5. **Training Loop**
   - Run thousands of battles
   - Update goblin behavior based on success
6. **Experience Replay**
   - Store and learn from past battles

### Key Files to Extend:
- `src/ai/goblin_ai.py` - Add `LearningGoblinAI` implementation
- `src/ai/learning.py` - Create DQN model and training logic
- `src/simulation/recorder.py` - Add battle data recording
- `main.py` - Implement `train` and `eval` commands

## Configuration

Edit `config.yaml` to adjust:
- Battle count and turn limits
- Unit counts and stats
- Dungeon size
- Learning hyperparameters
- Display options

## Current Balance

With simple AI, Knights should win ~90% of frontal charges. The goal of ML is to teach goblins to:
- Use chokepoints defensively
- Coordinate attacks (flanking)
- Scout and set up ambushes
- Retreat when outnumbered
- Trade efficiently using terrain

## Memory System Features

✨ **New Tactical Opportunities**:
- **Scouting**: Send goblins ahead to map dungeon
- **Ambush Setup**: Remember chokepoints for later positioning  
- **Pursuit**: Track individual knights by last-seen position
- **Navigation**: Path through familiar areas even when out of sight
- **Shared Intel**: Allied vision shares enemy tracking info

Example: A goblin sees a knight at position (25, 30), then loses sight. The goblin remembers this position and can pathfind there, potentially setting up an ambush or flanking route.

## Project Structure

```
goblin-tactics/
├── main.py                  # Entry point
├── config.yaml              # Configuration
├── requirements.txt         # Dependencies
├── REQUIREMENTS.md          # Full specification
├── src/
│   ├── core/               # Game entities and systems
│   │   ├── entity.py       # Knights, Goblins (with memory!)
│   │   ├── world.py        # Map management
│   │   ├── combat.py       # Damage resolution
│   │   └── vision.py       # LoS + allied sharing
│   ├── ai/                 # AI controllers
│   │   ├── knight_ai.py    # Simple knight behavior
│   │   └── goblin_ai.py    # Goblin AI (baseline + learning stub)
│   ├── generation/         # Dungeon creation
│   │   └── dungeon_gen.py  # BSP algorithm
│   ├── simulation/         # Battle orchestration
│   │   └── battle.py       # Turn management
│   ├── display/            # Visualization
│   │   └── renderer.py     # Colored ASCII output
│   └── utils/              # Helper functions
│       └── pathfinding.py  # A* with memory support
├── data/                   # Battle recordings (future)
└── models/                 # Saved AI models (future)
```

## Enjoy!

You now have a complete tactical simulation where goblins can learn to overcome stronger opponents through superior tactics! 🎮🧙‍♂️⚔️
