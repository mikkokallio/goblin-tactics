# Training Guide: Making Goblins Intelligent

## How Training Works

### Current State
- **Each training run starts fresh** with randomly initialized weights
- Training does NOT automatically continue from previous runs
- Checkpoints are saved but not automatically loaded

### What Gets Saved
- **Model checkpoints**: `models/checkpoint_ep50.json`, `checkpoint_ep100.json`, etc.
- **Final model**: `models/goblin_dqn_final.json`
- **Training stats**: `models/*_stats.json` (episode count, epsilon, total steps)

## Best Practices for Maximum Intelligence

### 1. **Progressive Training (RECOMMENDED)**

Train in stages, building on previous learning:

```bash
# Stage 1: Initial learning (100 episodes)
python main.py train --episodes 100

# Stage 2: Continue learning (resume from final model)
python main.py train --episodes 100 --resume models/goblin_dqn_final.json

# Stage 3: Further refinement
python main.py train --episodes 100 --resume models/goblin_dqn_final.json

# Or resume from specific checkpoint
python main.py train --episodes 200 --resume models/checkpoint_ep100.json
```

### 2. **Long Single Training Run**

For uninterrupted learning:

```bash
# Train for many episodes in one go
python main.py train --episodes 500

# Checkpoints auto-saved at episodes 50, 100, 150, 200, etc.
```

### 3. **Curriculum Learning**

Start with easier scenarios and gradually increase difficulty by modifying `config.yaml`:

```yaml
# Stage 1: Easier (fewer, weaker knights)
knights:
  count: 3
  hp: [15, 20]
  
# Stage 2: Normal (current settings)
knights:
  count: 4
  hp: [20, 30]
  
# Stage 3: Hard (more, stronger knights)
knights:
  count: 5
  hp: [25, 35]
```

## Understanding Learning Progress

### Epsilon Decay
- **Start**: `epsilon = 1.0` (100% random exploration)
- **During training**: Gradually decreases by 0.995 each episode
- **End**: `epsilon = 0.01` (1% random, 99% learned strategy)

### Win Rate Targets
- **0-5%**: Random behavior (no learning yet)
- **10-20%**: Basic tactics emerging (what you achieved in 20 episodes!)
- **30-50%**: Competent tactics (flanking, retreating, positioning)
- **50-70%**: Strong performance (good target for balanced game)
- **70%+**: Goblins dominating (may need difficulty adjustment)

### When to Resume vs. Start Fresh
- **Resume** (`--resume`): When you want continuous improvement
- **Fresh start**: When testing different hyperparameters or strategies

## Monitoring Training

### During Training
Watch for:
- **Win rate trending up**: Good learning
- **Epsilon decreasing**: Less exploration, more exploitation
- **Win rate plateau**: May need more episodes or hyperparameter tuning

### Example Output
```
Episode 100/500 | Win Rate: 25.0% | Epsilon: 0.606 | Wins: 25 | Losses: 75
  Saved checkpoint: models/checkpoint_ep100.json
```

## Testing Your Model

```bash
# Watch trained goblins fight (1 battle with visualization)
python main.py eval --model models/goblin_dqn_final.json --battles 1 --show

# Evaluate performance (10 battles, no visualization)
python main.py eval --model models/goblin_dqn_final.json --battles 10

# Compare checkpoints
python main.py eval --model models/checkpoint_ep50.json --battles 10
python main.py eval --model models/checkpoint_ep100.json --battles 10
```

## Recommended Training Strategy

### Quick Start (Testing)
```bash
python main.py train --episodes 50
python main.py eval --model models/goblin_dqn_final.json --battles 5 --show
```

### Full Training (Best Results)
```bash
# Train for 500 episodes (takes ~30-60 minutes)
python main.py train --episodes 500

# If interrupted, resume from last checkpoint
python main.py train --episodes 500 --resume models/checkpoint_ep200.json

# Evaluate final performance
python main.py eval --model models/goblin_dqn_final.json --battles 20
```

### Iterative Improvement
```bash
# Cycle 1
python main.py train --episodes 200
python main.py eval --model models/goblin_dqn_final.json --battles 10

# Cycle 2 (continue learning)
python main.py train --episodes 200 --resume models/goblin_dqn_final.json
python main.py eval --model models/goblin_dqn_final.json --battles 10

# Cycle 3 (more learning)
python main.py train --episodes 200 --resume models/goblin_dqn_final.json
```

## Hyperparameter Tuning (Advanced)

Edit `config.yaml` to adjust learning:

```yaml
learning:
  learning_rate: 0.001      # Lower = more stable, slower learning
  gamma: 0.99               # Higher = values long-term rewards more
  epsilon_decay: 0.995      # Lower = explores longer
  batch_size: 64            # Larger = more stable but slower
  memory_size: 10000        # More memory = better learning from past
  target_update: 10         # Update target network every N episodes
```

## Summary

**To make goblins as intelligent as possible:**

1. ✅ Use `--resume` to build on previous learning
2. ✅ Train for 500+ episodes total (can be split into multiple runs)
3. ✅ Monitor win rate and adjust if needed
4. ✅ Test at checkpoints to see progress
5. ✅ Consider curriculum learning (easy → hard scenarios)

**Current Status:**
- After 20 episodes: 15% win rate (basic tactics emerging)
- Ready for longer training runs!
