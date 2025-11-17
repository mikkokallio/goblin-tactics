# Grail Mode - Asymmetric Tactical Combat

## Overview
Grail mode transforms Goblin Tactics from a standard deathmatch into an asymmetric capture-the-flag scenario where knights must steal the Holy Grail and escape, while goblins defend it.

## Game Mechanics

### Map Layout
- **Entrance Corridor**: A 2-tile wide corridor on the left edge where knights spawn
- **Holy Grail**: Placed in a room on the opposite (right) side of the map
- **Entrance highlighted with BLUE background** in the terminal display
- **Grail shown as ★ symbol** in yellow/gold color

### Knight Objectives (Offensive)
1. **Explore** the dungeon to find the Holy Grail (★)
2. **Reach** the grail location and pick it up automatically
3. **Escape** through the entrance corridor with the grail
4. **Knights win** immediately when a knight carrying the grail reaches the entrance

### Knight AI Behavior
- **No grail found**: Explore toward the far side of the map, kill goblins in the way
- **Grail spotted**: Path directly to the grail, engage goblins that block the route
- **Carrying grail**: Sprint to the entrance, fighting only when necessary
- **Grail with ally**: Escort the carrier, clear the path ahead

### Goblin Objectives (Defensive)
1. **Prevent** the grail from leaving the dungeon for as long as possible
2. **Kill** the grail carrier to drop the grail (massive reward)
3. **Block** paths between grail and entrance
4. **Coordinate** defense with allies near the grail

### Goblin Reward Structure
The reward system incentivizes defensive tactics:

#### Positive Rewards
- **+150**: Killing the grail carrier (top priority!)
- **+50**: Killing any knight
- **+10**: Each turn the grail remains in the dungeon
- **+8**: Being within 2 tiles of the grail/carrier (close defense)
- **+5**: Being within 5 tiles of the grail/carrier (zone defense)
- **+4 per ally**: Having allies near grail (coordinated defense bonus)
- **+3**: Engaging enemies near the grail (active defense)
- **+1**: Base survival per turn

#### Penalties
- **-100**: Death
- **-8**: Position oscillation (moving back and forth)
- **-5**: Waiting/inactive play
- **-3**: Being too far from the grail (>10 tiles)

### Visual Indicators
- **★** = Holy Grail (yellow, bright)
- **⚔** = Knight carrying grail (yellow/gold instead of cyan)
- **Blue background** = Entrance corridor tiles
- **K** = Regular knight (cyan)
- **g** = Goblin (green, varies with HP)

## State Representation (44 features)

The goblin AI observes:

### Basic Features (11)
- Position (x, y normalized)
- HP percentage
- Visible allies/enemies count
- Distance to nearest ally/enemy
- Nearest enemy HP
- Allies/enemies within 3 tiles
- Exploration percentage

### Terrain Grid (25)
- 5x5 grid around goblin showing walls, floors, allies, enemies

### Meta (2)
- In safe zone (storm disabled, but code kept)
- Turn count

### Grail Features (6) - NEW
- **Grail location known** (0/1): Can see or remember where grail is
- **Distance to grail**: How far from the objective
- **Grail carrier nearby** (0/1): Can see the knight with the grail
- **Distance to entrance**: How far from the escape route
- **Allies near grail**: Number of friendly goblins defending
- **Enemies near grail**: Number of knights threatening the objective

## Configuration

In `config.yaml`:
```yaml
simulation:
  grail_mode: true        # Enable grail mechanics
  storm_enabled: false    # Disable storm (kept for future)
```

## Tactical Depth

### For Goblins (Learning)
The AI must learn to:
1. **Prioritize the carrier**: The grail carrier is the highest-value target
2. **Zone defense**: Stay near the grail even when no enemies are visible
3. **Coordinated response**: Multiple goblins defending together is more effective
4. **Path blocking**: Position between the grail and entrance
5. **Avoid passivity**: Waiting and oscillating are heavily penalized

### Expected Behaviors
- **Early game**: Goblins spread across the map, knights explore
- **Grail found**: Knights converge, goblins respond to threat
- **Carrier fleeing**: High-intensity chase toward entrance
- **Grail dropped**: Both sides scramble to secure it

## Training Notes

- **Win rate metric**: 0% = Knights always win, 100% = Goblins always defend successfully
- **Expected learning curve**: Goblins should learn defensive positioning over 200-500 episodes
- **Success indicators**: Longer battles, carrier deaths, coordinated interceptions
- **State size**: 44 features (vs 38 in standard mode)

## Comparison to Standard Mode

| Aspect | Standard Mode | Grail Mode |
|--------|---------------|------------|
| Objective | Kill all enemies | Steal grail and escape |
| Pressure | Storm (shrinking zone) | Time + defensive positions |
| Knights | Aggressive rush | Explore → Steal → Escape |
| Goblins | Individual combat | Defensive coordination |
| Win condition | Last team standing | Grail extracted OR knights dead |
| Tactics | Pack hunting | Zone defense, interception |

## Storm Mode Toggle

The storm mechanics are **disabled** but **preserved** in the code. To re-enable:

```yaml
simulation:
  grail_mode: false
  storm_enabled: true
  storm_start_turn: 30
```

This allows future experimentation with combined mechanics (grail + storm).
