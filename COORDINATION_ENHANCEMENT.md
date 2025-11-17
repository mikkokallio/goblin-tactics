# Tactical Coordination Enhancement

## Problem
Goblins were rushing enemies individually and dying without coordinating - no emergent pack tactics.

## Solutions Implemented

### 1. Enhanced State Representation (34 → 36 features)

**New tactical awareness features:**
- `nearest_enemy_hp` (0.0-1.0): HP percentage of closest enemy - helps focus fire on wounded targets
- `allies_within_3` (0.0-1.0): Number of nearby allies (normalized) - awareness of support
- `enemies_within_3` (0.0-1.0): Number of nearby threats (normalized) - danger assessment
- `in_safe_zone` (0/1): Binary flag for storm awareness
- **Storm in terrain grid**: Storm tiles now encoded as value `5` in 5x5 grid

**Why this helps:**
- Goblins can now "see" if they have ally support
- Can assess if enemy is weak (focus fire opportunity)
- Can evaluate local tactical situation (outnumbered? supported?)

### 2. Coordination Reward Structure

**Pack Tactics Bonuses:**
```python
# Kill with allies nearby: +20 per nearby ally
if killed_enemy and allies_within_3 > 0:
    reward += 20.0 * allies_within_3

# Allies attacking same target: +3 per coordinating ally  
if allies_near_same_enemy > 0:
    reward += 3.0 * allies_near_same_enemy
```

**Complete Reward Breakdown:**
- Death: -100
- Survival: +0.5/turn
- Damage dealt: +2 per point
- Kill enemy: +50
- **Kill with pack: +20 per nearby ally (NEW)**
- **Focus fire (allies near target): +3 per ally (NEW)**
- Close positioning (≤2): +2
- Approach (≤5): +1
- Outside storm: -10
- Waiting: -1

### 3. Improved Storm Visibility

**New Storm Parameters:**
- **Start:** Turn 30 (earlier, more visible)
- **Damage:** 2 HP/turn (gentle but persistent)
- **Shrink:** 0.3 tiles/turn (very gradual)

**Storm Progression:**
- Turn 30: 40 tile radius (starts)
- Turn 100: 19 tile radius (noticeable pressure)
- Turn 200: 10 tile radius (strong convergence)

**Visual:** Green background for storm areas makes safe zone clearly visible

## Expected Tactical Behaviors

### Individual Level:
✅ Assess own HP and retreat when low
✅ Identify weak enemies (low HP) for finishing
✅ Stay near allies for support
✅ Avoid storm damage

### Group Level (Emergent):
🎯 **Focus Fire:** Multiple goblins converge on same weak enemy
🎯 **Flanking:** Approach enemy from multiple angles (rewarded via nearby allies)
🎯 **Pack Hunting:** Higher reward when killing with support
🎯 **Tactical Retreat:** Wounded goblins fall back to allies
🎯 **Storm Herding:** Both sides pushed toward center for forced engagement

## Architecture Update

**New Input Layer:** 36 features
- Position: 2
- Core stats: 1 (HP%)
- Tactical awareness: 7 (allies, enemies, distances, enemy_hp, nearby_counts, safe_zone)
- Terrain grid: 25 (5x5 with storm info)
- Time: 1 (turn count)

**Hidden layers:** Still 128 → 64 (sufficient capacity)
**Output:** 10 actions (unchanged)

## Training Strategy

**Start fresh** - old models trained on 34 features, incompatible with 36

**Expected Learning Curve:**
- Episodes 1-50: Random exploration, ~5% win rate
- Episodes 50-100: Basic tactics emerge, ~15% win rate
- Episodes 100-200: Coordination starts, ~25-30% win rate
- Episodes 200-500: Pack tactics solidify, ~40-50% win rate

**Key Metrics to Watch:**
- Win rate trending up
- Average "allies_within_3" when attacking (should increase)
- Kills with support vs solo kills (should shift to supported)

## Why This Should Work

1. **Information availability:** Goblins now have the data needed to coordinate
2. **Direct incentive:** Pack kills rewarded 70-90 points vs 50 for solo kills
3. **Implicit coordination:** Rewarding "allies near same target" creates emergent focus fire
4. **Environmental pressure:** Storm forces engagement, prevents passive hiding
5. **Sufficient capacity:** 128→64 network can learn these multi-agent patterns

The key insight: **Don't just reward the outcome (kill), reward the process (cooperation)**
