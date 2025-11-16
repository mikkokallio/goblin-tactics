# Goblin Tactics - Requirements Specification

## 1. Overview

A text-based tactical simulation where AI-controlled knights battle AI-controlled goblins in procedurally generated dungeons. The system uses machine learning to evolve goblin tactics over time through reinforcement learning, allowing weaker goblins to learn strategies that compensate for their individual disadvantage against stronger knights.

## 2. Core Concept

- **Visual Style**: ASCII/text-based display similar to NetHack or Dwarf Fortress
- **Autonomous**: Both sides AI-controlled, no player input during battles
- **Learning System**: Goblins learn and improve tactics through reinforcement learning across multiple battles
- **Tactical Advantage**: Dungeon layout provides opportunities for goblins to use superior positioning and numbers

## 3. Game Entities

### 3.1 Knights
- **Quantity**: 4 per battle
- **Attributes**:
  - High health (e.g., 20-30 HP)
  - High attack damage (e.g., 5-8 damage per hit)
  - High defense/armor
  - Movement: 1 square per turn (orthogonal and diagonal)
  - Line of Sight (LoS): 3 squares in all directions
- **Behavior**: Simple AI - rush toward closest enemy, attack when adjacent, explore when no enemies detected
- **Advantage**: Individual strength and durability

### 3.2 Goblins
- **Quantity**: Variable, significantly outnumber knights (e.g., 12-20 per battle)
- **Attributes**:
  - Low health (e.g., 3-6 HP)
  - Low attack damage (e.g., 1-2 damage per hit)
  - Low defense
  - Movement: 1 square per turn (orthogonal and diagonal)
  - Line of Sight (LoS): 3 squares in all directions
- **Behavior**: Initially simple (rush closest enemy), evolves through machine learning
- **Advantage**: Numbers and tactical learning capability

### 3.3 Shared Vision System
- **Individual LoS**: Each creature sees 3 squares from their position
- **Allied Communication**: Creatures that can see allies also gain access to what those allies see
- **Vision Sharing Rules**:
  - If Creature A can see Creature B (ally), A gains all vision information B has
  - Transitive sharing through vision chains
  - Updates each turn based on current positions
- **Implementation Note**: The observer/renderer sees everything, but each creature's decision-making only uses information from their LoS network

### 3.4 Memory System
- **Terrain Memory**: Each creature remembers all terrain tiles they have ever seen
  - Persists throughout the battle
  - Used for pathfinding through familiar areas
  - Enables scouting as a tactical advantage
- **Enemy Tracking**: Each creature remembers the last known position of each enemy
  - Updated whenever an enemy is seen (directly or through allied vision)
  - Shows last position and how many turns ago it was seen
  - Allows pursuit, prediction, and tactical positioning
  - Goblins track individual knights separately (not just "nearest knight")
- **Tactical Applications**:
  - Scouts can explore and share map knowledge with allies
  - Units can navigate through previously-seen corridors
  - Ambushes can be set up at remembered chokepoints
  - Last-known enemy positions enable flanking and prediction

## 4. Environment

### 4.1 Dungeon Generation
- **Algorithm**: Use Binary Space Partitioning (BSP) or Cellular Automata for dungeon generation
  - **BSP Recommended**: Creates connected rooms with corridors, ideal for tactical positioning
  - Alternative: Simple room-corridor generation with guaranteed connectivity
- **Structure**:
  - Multiple rooms of varying sizes (small: 3x3, medium: 5x7, large: 8x10)
  - Connecting corridors (1-2 tiles wide)
  - Narrow chokepoints that favor defenders
  - Open areas that favor numbers
- **Size**: Approximately 40x40 to 60x60 tiles
- **Guaranteed Features**:
  - All areas connected and reachable
  - No isolated zones
  - Starting zones for both sides (opposite ends of dungeon)

### 4.2 Terrain Types
- **Floor** (`.`): Passable, no special effects
- **Wall** (`#`): Impassable, blocks line of sight
- **Difficult Terrain** (`~`): Passable but costs 2 movement (or reduces movement speed), uncommon (5-10% of floor tiles)
- **Rubble** (`%`): Difficult terrain variant, provides minor cover bonus (optional)
- **Door** (`+`): Passable, can be closed/opened (optional future feature)
- **Water/Pit** (`≈`): Impassable like walls but visually distinct (optional)

## 5. Combat System

### 5.1 Turn Structure
- **Turn-based**: All units act in initiative order each round
- **Initiative**: Randomized or based on simple stat (e.g., speed = base value + random(1-3))
- **Action Economy**: Each unit gets 1 action per turn
  - Move OR Attack
  - Or: Move AND Attack (if attack is against adjacent target)

### 5.2 Combat Mechanics
- **Melee Only**: All attacks are melee (adjacent squares, orthogonal or diagonal)
- **Hit Resolution**: 
  - Simple: Attacks always hit
  - Or: Attack roll vs defense (e.g., d20 + attack bonus > armor class)
- **Damage**: Roll damage dice, subtract from target HP
- **Death**: Unit removed from battlefield when HP ≤ 0
- **Flanking/Positioning** (optional): Bonus damage when multiple allies adjacent to target

### 5.3 Victory Conditions
- **Knight Victory**: All goblins eliminated
- **Goblin Victory**: All knights eliminated
- **Timeout**: If battle exceeds N turns (e.g., 200), declare stalemate or award to side with most survivors

## 6. AI System

### 6.1 Knight AI (Simple, Non-Learning)
**Decision Priority**:
1. If enemy adjacent → Attack
2. If enemy detected in LoS network:
   - Try to move toward closest enemy using pathfinding
   - If path is blocked (e.g., by ally in narrow corridor) and cannot reach enemy → Explore/reposition
3. If no enemy detected → Explore (random walk or systematic search pattern)

**Movement**: 
- Use A* pathfinding to navigate toward target
- Avoid walls, respect occupied squares
- If stuck (cannot move toward visible enemy due to blocking), switch to exploration behavior

### 6.2 Goblin AI (Learning-Based)

#### Initial Behavior (Baseline)
Same as knights: rush toward closest enemy, attack when adjacent, explore when no enemies detected

#### Learning Framework
**Approach**: Reinforcement Learning (Q-Learning, Deep Q-Network, or Policy Gradient)

**State Representation** (what each goblin observes):
- Own position (relative or absolute)
- Own HP
- Nearby terrain (walls, floors, corridors) within LoS and memory
- Allied positions and HP within LoS network
- Enemy positions and HP within LoS network
- Last known positions of each knight (with staleness)
- Distance to nearest ally
- Distance to nearest visible enemy
- Distance to nearest last-known enemy position
- Number of visible allies
- Number of visible enemies
- In corridor (boolean)
- In room (boolean)
- In chokepoint (boolean)
- Flanking position available (boolean)
- Amount of explored terrain (as percentage)

**Action Space** (what each goblin can choose):
- Move North/South/East/West/NE/NW/SE/SW
- Attack (if enemy adjacent)
- Hold Position/Defend
- Retreat toward allies
- Coordinate (move to flanking position)

**Reward Function**:
- **Positive Rewards**:
  - +100: Goblin team victory
  - +50: Knight eliminated
  - +10: Knight damaged
  - +5: Survived the turn
  - +3: Flanking position achieved
  - +2: In cover/advantageous position (e.g., chokepoint with allies)
  - +1: Near allies (safety in numbers)
  - +0.5: Explored new terrain (scouting bonus)
- **Negative Rewards**:
  - -100: Goblin team defeat
  - -50: This goblin died
  - -10: Took damage
  - -5: Isolated from allies (>5 squares away)
  - -2: In open area alone with nearby enemies

**Training Process**:
1. Run battle simulation
2. Record each goblin's state, action, and outcome
3. Calculate rewards based on battle results
4. Update learning model (neural network weights or Q-table)
5. Start new battle with updated model
6. Repeat for N episodes (e.g., 1000-10000)

**Model Architecture Options**:
- **Simple**: Q-Table (for discrete state/action spaces)
- **Advanced**: Deep Q-Network (DQN) with neural network
  - Input layer: State representation (flattened vector)
  - Hidden layers: 2-3 layers with 64-128 neurons each
  - Output layer: Q-values for each action
  - Training: Experience replay buffer, target network

## 7. Data Recording

### 7.1 Per-Battle Data
- Battle ID (unique identifier)
- Dungeon layout (map state)
- Initial unit positions
- Battle outcome (winner, turn count, survivors)
- Total damage dealt/received per side

### 7.2 Per-Goblin Data (for learning)
For each goblin, each turn:
- Turn number
- Goblin ID
- Position (x, y)
- HP
- State observation (full state vector)
- Action taken
- Immediate reward
- Next state observation
- Done flag (died/battle ended)

### 7.3 Storage
- Save to file format: JSON, CSV, or binary (pickle/numpy)
- Directory structure:
  ```
  data/
    battles/
      battle_0001.json
      battle_0002.json
      ...
    training/
      experience_replay.pkl
      model_checkpoints/
        model_epoch_100.pth
        model_epoch_200.pth
  ```

## 8. Display/Visualization

### 8.1 ASCII Display
```
#############################################
#.....#     K = Knight (bright cyan/bold)
#..G..#     g = Goblin (green)
#.....####  # = Wall (gray/white)
#..K......# . = Floor (dark gray)
####....G.# ~ = Difficult terrain (yellow/brown)
   #....G#  + = Door (optional)
   #K..G.#  
   #~...##  Colors (using colorama/rich):
   ###G###  - Knights: Bright cyan/blue
     #K#    - Goblins: Green/lime
     ###    - Walls: White/gray
            - Floor: Dark gray/black
            - Difficult: Yellow/brown
            - Health bars: Red to green gradient
```

### 8.2 Vision Overlay (Observer View)
Option to display each unit's LoS:
- Use color coding or separate panels
- Show what each knight/goblin can see
- Highlight shared vision from allies

### 8.3 Statistics Display
Real-time or end-of-battle stats:
```
Turn: 45
Knights: 3/4 (HP: 18, 12, 24)
Goblins: 8/16 (Total HP: 31)
Battle Time: 45 turns
```

### 8.4 Battle Replay
- Option to replay battles step-by-step
- Speed controls (slow/normal/fast)
- Pause and inspect state at any turn

## 9. Simulation Control

### 9.1 Configuration
**Config File** (YAML or JSON):
```yaml
simulation:
  num_battles: 1000
  max_turns_per_battle: 200
  dungeon_size: [50, 50]
  
knights:
  count: 4
  hp: [20, 30]
  damage: [5, 8]
  
goblins:
  count: [12, 20]
  hp: [3, 6]
  damage: [1, 2]
  
learning:
  algorithm: "DQN"
  learning_rate: 0.001
  epsilon_start: 1.0
  epsilon_end: 0.01
  epsilon_decay: 0.995
  
display:
  show_battles: true
  update_frequency: 10  # Show every Nth battle
  replay_speed: "normal"
```

### 9.2 Modes
- **Training Mode**: Run many battles rapidly, minimal visualization
- **Evaluation Mode**: Run battles with specific model, full visualization
- **Single Battle Mode**: Step through one battle with detailed inspection
- **Statistics Mode**: Analyze saved data, plot learning curves

### 9.3 Commands (CLI)
```bash
# Run training
python main.py train --episodes 1000

# Evaluate trained model
python main.py eval --model checkpoints/model_1000.pth --battles 10

# Single battle with visualization
python main.py battle --show

# Analyze results
python main.py analyze --data data/battles/
```

## 10. Performance Metrics

### 10.1 Training Metrics
- Win rate per N episodes (rolling average)
- Average turns to victory/defeat
- Average goblin survival rate
- Learning curve (rewards over time)

### 10.2 Tactical Metrics
- Chokepoint utilization frequency
- Flanking success rate
- Damage dealt per goblin
- Average distance between goblins (coordination measure)
- Isolation incidents (goblins caught alone)

### 10.3 Visualization of Progress
- Graphs showing win rate improvement
- Heatmaps of goblin positioning preferences
- Action distribution over training

## 11. Technical Requirements

### 11.1 Language & Libraries
**Recommended**: Python 3.8+

**Core Libraries**:
- `numpy`: Numerical operations, array handling
- `torch` (PyTorch): Deep learning for DQN implementation
- `colorama` or `rich`: Colored terminal output for enhanced ASCII display
- `matplotlib` or `plotly`: Visualization of metrics

**Optional Libraries**:
- `pygame` or `curses`: Enhanced ASCII display (alternative to colorama)
- `pandas`: Data analysis
- `pyyaml`: Configuration management
- `tqdm`: Progress bars
- `jsonlines`: Efficient data storage

### 11.2 Architecture
```
goblin-tactics/
  src/
    core/
      entity.py         # Knight, Goblin classes
      world.py          # Dungeon, map management
      combat.py         # Combat resolution
      vision.py         # LoS calculations
    ai/
      knight_ai.py      # Simple knight behavior
      goblin_ai.py      # Learning-based goblin behavior
      learning.py       # RL algorithms (DQN, etc.)
    generation/
      dungeon_gen.py    # BSP or other generation
    simulation/
      battle.py         # Battle orchestration
      recorder.py       # Data logging
    display/
      renderer.py       # ASCII display
      stats.py          # Statistics display
    utils/
      pathfinding.py    # A* implementation
      config.py         # Config loading
  data/                 # Generated data
  models/               # Saved models
  config.yaml           # Configuration
  main.py               # Entry point
  requirements.txt      # Dependencies
  README.md
  REQUIREMENTS.md       # This document
```

## 12. Development Phases

### Phase 1: Core Foundation
- [ ] Dungeon generation (BSP algorithm)
- [ ] Entity classes (Knight, Goblin)
- [ ] Basic movement and pathfinding
- [ ] ASCII rendering
- [ ] Simple combat system

### Phase 2: AI Basics
- [ ] Knight simple AI
- [ ] Goblin baseline AI (same as knights)
- [ ] Line of Sight calculations
- [ ] Allied vision sharing
- [ ] Battle simulation loop

### Phase 3: Learning System
- [ ] State representation design
- [ ] Reward function implementation
- [ ] Choose RL algorithm (Q-Learning or DQN)
- [ ] Training infrastructure
- [ ] Data recording system

### Phase 4: Training & Refinement
- [ ] Run initial training (baseline vs learned)
- [ ] Analyze results, tune hyperparameters
- [ ] Refine reward function
- [ ] Extended training sessions
- [ ] Model checkpointing

### Phase 5: Visualization & Analysis
- [ ] Battle replay system
- [ ] Metrics dashboard
- [ ] Learning curve plots
- [ ] Tactical analysis tools

### Phase 6: Polish & Extensions
- [ ] Configuration system
- [ ] CLI interface improvements
- [ ] Documentation
- [ ] Optional: Web interface for visualization
- [ ] Optional: Multiple goblin strategies (different models)

## 13. Success Criteria

### Minimum Viable Product (MVP)
- Goblins can be trained over 100+ battles
- Measurable improvement in goblin win rate (from ~0% to >30%)
- Evidence of tactical learning (positioning, chokepoint use)
- Stable training (no catastrophic forgetting)

### Stretch Goals
- Goblin win rate >50% against simple knight AI
- Observable emergent tactics (ambushes, coordinated attacks)
- Multiple goblin strategies that can be selected
- Human vs AI mode (player controls knights)
- Tournament mode (different AI strategies compete)

## 14. Future Enhancements

- **Advanced Knight AI**: Make knights also learn and adapt
- **Asymmetric Objectives**: Knights escort VIP, goblins ambush
- **Equipment/Items**: Weapons, armor, potions
- **Terrain Effects**: Difficult terrain, elevation, traps
- **Fog of War**: Limit observer view to simulate discovered areas
- **Multi-Agent Learning**: Explicit team coordination strategies
- **Procedural Knight Tactics**: Different knight formations/strategies
- **Campaign Mode**: Persistent goblins that learn across multiple dungeons

## 15. Open Questions & Design Decisions

1. **Exact RL Algorithm**: Q-Learning (simpler) vs DQN (more powerful)?
2. **Centralized vs Distributed Learning**: One model for all goblins, or individual models?
3. **State Space Size**: How much information to include? Trade-off between richness and complexity.
4. **Action Space**: Discrete actions only, or continuous positioning?
5. **Reward Shaping**: Balance between sparse (only win/loss) and dense (many small rewards)?
6. **Training Stability**: How to prevent catastrophic forgetting as tactics evolve?
7. **Dungeon Variety**: Fixed dungeons for consistent training, or always random?

---

## Appendix A: Example Battle Flow

```
Turn 1:
  - Generate dungeon
  - Place 4 knights in starting area (west side)
  - Place 16 goblins in starting area (east side)
  - Calculate initial vision for all units

Turn 2-N:
  - For each unit in initiative order:
    - Update vision (own LoS + allied shared vision)
    - Decide action (AI or learning model)
    - Execute action (move or attack)
    - Update state
    - Record data (for goblins)
  - Check victory conditions
  - Render display (if enabled)
  
End of Battle:
  - Calculate final rewards
  - Store battle data
  - Update learning model (if training)
  - Display statistics
```

## Appendix B: State Vector Example

For a goblin at position (x, y):
```python
state = [
    normalized_x,           # 0.0 - 1.0
    normalized_y,           # 0.0 - 1.0
    hp_percentage,          # 0.0 - 1.0
    num_visible_allies,     # 0 - 20
    num_visible_enemies,    # 0 - 4
    distance_to_nearest_ally,    # 0.0 - 10.0
    distance_to_nearest_enemy,   # 0.0 - 10.0
    in_corridor,            # 0 or 1
    in_room,                # 0 or 1
    near_chokepoint,        # 0 or 1
    terrain_encoding[0:25], # 5x5 grid around goblin (flattened)
    # Total: ~35-50 features
]
```

## Appendix C: Initial Parameter Suggestions

```python
# Combat Balance
KNIGHT_HP = 25
KNIGHT_DAMAGE = (5, 8)  # random between 5-8
GOBLIN_HP = 4
GOBLIN_DAMAGE = (1, 2)  # random between 1-2
GOBLIN_COUNT = 16  # 4:1 ratio

# Expected outcome with no tactics:
# Knights should win ~90% of frontal charges
# Each knight can kill ~6 goblins before dying
# Total knight HP: 100, Total goblin damage output before death: ~100
# But goblins die fast, so knights usually win

# Learning Parameters
LEARNING_RATE = 0.001
GAMMA = 0.99  # discount factor
EPSILON_START = 1.0
EPSILON_END = 0.01
EPSILON_DECAY = 0.995
BATCH_SIZE = 64
MEMORY_SIZE = 10000
TARGET_UPDATE = 10  # episodes

# Training
NUM_EPISODES = 5000
MAX_TURNS = 200
```

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-16  
**Status**: Initial Draft
