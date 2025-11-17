# Environmental Pressure Mechanics Update

## Problem Identified
The goblins learned a "timeout survival" strategy - hiding and avoiding combat to win by timeout rather than engaging tactically.

## Root Cause
The simple reward structure (+1 for survival, -50 for death) incentivized passive hiding over active combat. The goblins optimized correctly for what they were rewarded!

## Solutions Implemented

### 1. **Spread Initial Spawning**
- **Before:** Goblins spawned clustered in 1-2 rooms
- **After:** Goblins spawn distributed across multiple rooms (one per room when possible)
- **Effect:** Forces individual decision-making and prevents safe clustering from turn 1

### 2. **Shrinking Safe Zone ("Storm" Mechanic)**
- **Battle-royale style** zone that shrinks over time
- **Starts:** Turn 50 (configurable)
- **Damage:** 5 HP/turn outside safe zone (configurable)
- **Shrink rate:** 1 tile/turn (configurable)
- **Center:** Map center
- **Effect:** Forces entities toward center for combat encounters

Configuration in `config.yaml`:
```yaml
simulation:
  storm_enabled: true
  storm_start_turn: 50
  storm_damage: 5
  storm_shrink_rate: 1
```

### 3. **Enhanced Reward Structure**

**New reward breakdown:**
- **Death:** -100 (increased penalty)
- **Survival:** +0.5/turn (reduced from +1.0)
- **Dealing damage:** +2.0 per damage point (NEW)
- **Killing knight:** +50.0 bonus (NEW)
- **Close positioning (≤2 tiles):** +2.0 (NEW)
- **Approach positioning (≤5 tiles):** +1.0 (NEW)
- **Outside safe zone:** -10.0 penalty (NEW)
- **Waiting/holding:** -1.0 penalty (NEW)

**Result:** Combat and aggressive positioning are now highly rewarded while passive hiding is penalized.

### 4. **Extended Turn Limit**
- **Before:** 200 turns
- **After:** 300 turns
- **Effect:** Allows battles to resolve naturally even with storm active

## Expected Behavioral Changes

### What Goblins Should Learn:
✅ **Engage in combat** - damage dealing is rewarded
✅ **Aggressive positioning** - get close to enemies
✅ **Move toward center** - avoid storm damage
✅ **Coordinate attacks** - focus fire for kill bonuses
✅ **Flanking & pincer** - approach from multiple angles
✅ **Strategic retreating** - when low HP, move toward allies

### Tactical Emergence:
- **Early game (turns 1-50):** Goblins spread out, explore, converge on knights
- **Mid game (turns 50-150):** Storm forces both sides toward center, skirmishes begin
- **Late game (turns 150+):** Intense combat in shrinking zone, no escape possible

## Testing Results

**Single battle test (after implementation):**
- **Winner:** Goblins (1 survivor)
- **Turns:** 87
- **Knights eliminated:** 4/4
- **Observation:** Much more aggressive combat behavior even without trained weights

## Next Steps

1. **Retrain from scratch** with new mechanics (100+ episodes)
2. **Monitor win rates** - target 30-50% for balanced gameplay
3. **Observe tactical patterns** - check for clustering, flanking, retreating
4. **Fine-tune storm parameters** if needed:
   - Adjust start turn (earlier = more pressure)
   - Adjust shrink rate (faster = more urgency)
   - Adjust damage (higher = stronger penalty)

## Philosophy

> "Don't blame the agent for optimizing what you rewarded. Change the environment to force the behavior you want to see."

The goblins were smart to hide - we just needed to make hiding impossible!
