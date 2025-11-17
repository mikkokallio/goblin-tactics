# Curriculum Training Guide

This project now supports **curriculum learning** - training goblins in stages:

## Two Training Modes

### 1. Arena Mode (Simple)
- One large rectangular hall
- Grail at right end, entrance at left
- No navigation complexity - pure combat tactics
- Goblins learn: flanking, pack formation, attacking, defending

### 2. Dungeon Mode (Complex)  
- Multiple rooms with corridors
- Complex navigation required
- Applies learned combat tactics to exploration

## Quick Start - Arena Training

1. **Enable arena mode** in `config.yaml`:
```yaml
simulation:
  arena_mode: true  # Simple rectangular arena
```

2. **Train in arena** (fast tactical learning):
```bash
python main.py train --episodes 100
```

3. **Test arena tactics**:
```bash
python main.py eval --model models/checkpoint_ep100.json --battles 1 --show
```

4. **Switch to dungeon mode** in `config.yaml`:
```yaml
simulation:
  arena_mode: false  # Complex dungeon
```

5. **Continue training in dungeon** (transfer tactics):
```bash
python main.py train --episodes 100 --resume models/checkpoint_ep100.json
```

## Automated Curriculum Training

Run the automated curriculum script:
```bash
python train_curriculum.py
```

This will:
1. Train 100 episodes in arena mode
2. Save checkpoint as `checkpoint_arena_final.json`
3. Switch to dungeon mode
4. Train 100 more episodes starting from arena checkpoint
5. Save final checkpoint as `checkpoint_ep200.json`

## Why Curriculum Learning?

**Arena first** lets goblins focus on pure combat without navigation distractions:
- Faster learning of tactical behaviors
- Clear feedback on combat effectiveness  
- Simple environment = cleaner reward signals

**Then dungeon** applies those tactics to complex scenarios:
- Transfer learned combat skills
- Add navigation and positioning strategy
- More realistic final behavior

## Expected Results

After arena training, goblins should demonstrate:
- ✅ Pack formation when enemies visible
- ✅ Flanking and surrounding behavior
- ✅ Aggressive attacks on isolated knights
- ✅ Coordinated defense of grail

After dungeon training, they should add:
- ✅ Strategic patrol patterns
- ✅ Coverage of grail-to-exit paths
- ✅ Convergence from spread positions
- ✅ Room-to-room tactical movement
