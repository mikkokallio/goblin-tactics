"""
High-level tactical directives for goblin AI
Instead of learning low-level directions (N/S/E/W), goblins learn WHEN to use each tactical directive
The directive system then calculates the actual movement direction
"""

from typing import Optional, Tuple, List
import math
from src.core.entity import Goblin
from src.core.world import World

# Directive action indices
DIR_TOWARD_NEAREST_ENEMY = 0
DIR_TOWARD_WEAKEST_ENEMY = 1
DIR_TOWARD_GRAIL_CARRIER = 2
DIR_AWAY_FROM_ENEMIES = 3
DIR_INTERCEPT_ENEMY_PATH = 4
DIR_ENCIRCLE_ENEMY = 5  # Maintain distance while moving radially around enemy

DIR_TOWARD_NEAREST_ALLY = 6
DIR_TOWARD_ALLY_CLUSTER = 7
DIR_AWAY_FROM_ALLIES = 8

DIR_TOWARD_GRAIL = 9
DIR_TOWARD_ENTRANCE = 10
DIR_INTERCEPT_ZONE = 11  # Between grail and entrance
DIR_CUT_OFF_ESCAPE = 12  # Position between enemy and their entrance

DIR_AWAY_FROM_WALLS = 13
DIR_TOWARD_COVER = 14  # Nearest pillar/obstacle

DIR_TO_OPEN_SPACE = 15  # Away from clusters
DIR_TO_UNEXPLORED = 16
DIR_PATROL = 17  # Purposeful wandering
DIR_PURSUE_RETREATING = 18  # Chase enemies moving away from goblins

DIR_ATTACK = 19  # Attack adjacent enemy
DIR_HOLD = 20  # Stay put

NUM_DIRECTIVES = 21

DIRECTIVE_NAMES = {
    DIR_TOWARD_NEAREST_ENEMY: "approach nearest enemy",
    DIR_TOWARD_WEAKEST_ENEMY: "approach weakest enemy",
    DIR_TOWARD_GRAIL_CARRIER: "approach grail carrier",
    DIR_AWAY_FROM_ENEMIES: "retreat from enemies",
    DIR_INTERCEPT_ENEMY_PATH: "intercept enemy path",
    DIR_ENCIRCLE_ENEMY: "encircle enemy",
    DIR_TOWARD_NEAREST_ALLY: "move to nearest ally",
    DIR_TOWARD_ALLY_CLUSTER: "join ally cluster",
    DIR_AWAY_FROM_ALLIES: "spread from allies",
    DIR_TOWARD_GRAIL: "move to grail",
    DIR_TOWARD_ENTRANCE: "move to entrance",
    DIR_INTERCEPT_ZONE: "move to intercept zone",
    DIR_CUT_OFF_ESCAPE: "cut off escape",
    DIR_AWAY_FROM_WALLS: "avoid walls",
    DIR_TOWARD_COVER: "take cover",
    DIR_TO_OPEN_SPACE: "move to open space",
    DIR_TO_UNEXPLORED: "explore",
    DIR_PATROL: "patrol",
    DIR_PURSUE_RETREATING: "pursue retreating",
    DIR_ATTACK: "attack",
    DIR_HOLD: "hold position"
}


def calculate_directive_target(directive: int, goblin: Goblin, world: World) -> Optional[Tuple[int, int]]:
    """
    Calculate target position for a given directive
    Returns None if directive cannot be executed
    """
    
    # ENEMY-BASED DIRECTIVES
    if directive == DIR_TOWARD_NEAREST_ENEMY:
        if goblin.visible_enemies:
            nearest = min(goblin.visible_enemies, key=lambda e: goblin.distance_to(e))
            return (nearest.x, nearest.y)
        return None
    
    if directive == DIR_TOWARD_WEAKEST_ENEMY:
        if goblin.visible_enemies:
            weakest = min(goblin.visible_enemies, key=lambda e: e.hp)
            return (weakest.x, weakest.y)
        return None
    
    if directive == DIR_TOWARD_GRAIL_CARRIER:
        if world.grail_carrier and world.grail_carrier in goblin.visible_enemies:
            return (world.grail_carrier.x, world.grail_carrier.y)
        return None
    
    if directive == DIR_AWAY_FROM_ENEMIES:
        if goblin.visible_enemies:
            # Calculate center of mass of enemies
            avg_x = sum(e.x for e in goblin.visible_enemies) / len(goblin.visible_enemies)
            avg_y = sum(e.y for e in goblin.visible_enemies) / len(goblin.visible_enemies)
            # Move opposite direction
            dx = goblin.x - avg_x
            dy = goblin.y - avg_y
            # Normalize and scale
            dist = math.sqrt(dx*dx + dy*dy) or 1
            target_x = goblin.x + int(5 * dx / dist)
            target_y = goblin.y + int(5 * dy / dist)
            return (target_x, target_y)
        return None
    
    if directive == DIR_INTERCEPT_ENEMY_PATH:
        # If grail carrier exists, intercept path from carrier to entrance
        if world.grail_carrier and world.grail_carrier in goblin.visible_enemies:
            carrier_x, carrier_y = world.grail_carrier.x, world.grail_carrier.y
            if world.entrance_positions:
                entrance_x, entrance_y = world.entrance_positions[0]
                # Point between carrier and entrance
                mid_x = (carrier_x + entrance_x) // 2
                mid_y = (carrier_y + entrance_y) // 2
                return (mid_x, mid_y)
        return None
    
    # ALLY-BASED DIRECTIVES
    if directive == DIR_TOWARD_NEAREST_ALLY:
        if goblin.visible_allies:
            nearest = min(goblin.visible_allies, key=lambda a: goblin.distance_to(a))
            return (nearest.x, nearest.y)
        return None
    
    if directive == DIR_TOWARD_ALLY_CLUSTER:
        if goblin.visible_allies:
            # Find cluster (area with most allies in 5-tile radius)
            best_pos = None
            best_count = 0
            for ally in goblin.visible_allies:
                count = sum(1 for a in goblin.visible_allies 
                           if abs(a.x - ally.x) <= 5 and abs(a.y - ally.y) <= 5)
                if count > best_count:
                    best_count = count
                    best_pos = (ally.x, ally.y)
            return best_pos
        return None
    
    if directive == DIR_ENCIRCLE_ENEMY:
        # Move radially around nearest enemy while maintaining distance
        if goblin.visible_enemies:
            enemy = min(goblin.visible_enemies, key=lambda e: goblin.distance_to(e))
            ex, ey = enemy.x, enemy.y
            
            # Vector from enemy to goblin
            dx = goblin.x - ex
            dy = goblin.y - ey
            current_dist = math.sqrt(dx*dx + dy*dy) or 1
            
            # Ideal encirclement distance (attack range + 1)
            ideal_dist = 4
            
            if current_dist < ideal_dist - 1:
                # Too close - move away radially
                target_x = ex + int(ideal_dist * dx / current_dist)
                target_y = ey + int(ideal_dist * dy / current_dist)
            elif current_dist > ideal_dist + 2:
                # Too far - move closer radially
                target_x = ex + int(ideal_dist * dx / current_dist)
                target_y = ey + int(ideal_dist * dy / current_dist)
            else:
                # Good distance - move perpendicular to encircle
                target_x = ex + int(ideal_dist * (-dy) / current_dist)
                target_y = ey + int(ideal_dist * dx / current_dist)
            
            return (target_x, target_y)
        return None
    
    if directive == DIR_AWAY_FROM_ALLIES:
        if goblin.visible_allies:
            # Move away from ally center of mass
            avg_x = sum(a.x for a in goblin.visible_allies) / len(goblin.visible_allies)
            avg_y = sum(a.y for a in goblin.visible_allies) / len(goblin.visible_allies)
            dx = goblin.x - avg_x
            dy = goblin.y - avg_y
            dist = math.sqrt(dx*dx + dy*dy) or 1
            target_x = goblin.x + int(5 * dx / dist)
            target_y = goblin.y + int(5 * dy / dist)
            return (target_x, target_y)
        return None
    
    # OBJECTIVE-BASED DIRECTIVES
    if directive == DIR_TOWARD_GRAIL:
        if world.grail_carrier:
            return (world.grail_carrier.x, world.grail_carrier.y)
        return world.grail_position
    
    if directive == DIR_TOWARD_ENTRANCE:
        if world.entrance_positions:
            return world.entrance_positions[0]
        return None
    
    if directive == DIR_INTERCEPT_ZONE:
        # Midpoint between grail and entrance
        grail_pos = world.grail_carrier.position if world.grail_carrier else world.grail_position
        if world.entrance_positions:
            entrance_pos = world.entrance_positions[0]
            mid_x = (grail_pos[0] + entrance_pos[0]) // 2
            mid_y = (grail_pos[1] + entrance_pos[1]) // 2
            return (mid_x, mid_y)
        return None
    
    if directive == DIR_CUT_OFF_ESCAPE:
        # Position between enemy and their entrance
        if goblin.visible_enemies and world.entrance_positions:
            enemy = min(goblin.visible_enemies, key=lambda e: goblin.distance_to(e))
            entrance_pos = world.entrance_positions[0]
            # Position 1/3 of the way from enemy to entrance
            cut_x = enemy.x + (entrance_pos[0] - enemy.x) // 3
            cut_y = enemy.y + (entrance_pos[1] - enemy.y) // 3
            return (cut_x, cut_y)
        return None
    
    # TACTICAL POSITIONING
    if directive == DIR_AWAY_FROM_WALLS:
        # Move toward center of open area
        # Simple: move toward map center
        center_x = world.width // 2
        center_y = world.height // 2
        return (center_x, center_y)
    
    if directive == DIR_TOWARD_COVER:
        # Find nearest pillar (2x2 obstacle)
        best_dist = float('inf')
        best_pos = None
        for dy in range(-10, 11):
            for dx in range(-10, 11):
                x, y = goblin.x + dx, goblin.y + dy
                if 0 <= x < world.width and 0 <= y < world.height:
                    if not world.is_passable(x, y):  # Obstacle
                        dist = abs(dx) + abs(dy)
                        if dist < best_dist:
                            best_dist = dist
                            # Target position adjacent to obstacle
                            best_pos = (goblin.x + dx // 2, goblin.y + dy // 2)
        return best_pos
    
    if directive == DIR_TO_OPEN_SPACE:
        # Find nearby area with fewest entities
        best_pos = None
        best_count = float('inf')
        for dy in range(-5, 6):
            for dx in range(-5, 6):
                x, y = goblin.x + dx, goblin.y + dy
                if world.is_passable(x, y):
                    # Count nearby entities
                    count = sum(1 for e in world.entity_grid.values()
                               if abs(e.x - x) <= 2 and abs(e.y - y) <= 2)
                    if count < best_count:
                        best_count = count
                        best_pos = (x, y)
        return best_pos
    
    if directive == DIR_TO_UNEXPLORED:
        # Move to tile that hasn't been seen much
        # For now, just move to tiles not in visible_tiles history
        for dy in range(-10, 11):
            for dx in range(-10, 11):
                x, y = goblin.x + dx, goblin.y + dy
                if world.is_passable(x, y):
                    if (x, y) not in goblin.remembered_tiles:
                        return (x, y)
        # All explored, pick random direction
        return (goblin.x + 5, goblin.y + 5)
    
    if directive == DIR_PATROL:
        # Random but purposeful movement
        import random
        dx = random.randint(-5, 5)
        dy = random.randint(-5, 5)
        return (goblin.x + dx, goblin.y + dy)
    
    if directive == DIR_PURSUE_RETREATING:
        # Target enemies that are moving away from goblin groups
        if goblin.visible_enemies:
            # Find enemy furthest from nearest ally cluster
            best_enemy = None
            best_score = -float('inf')
            
            for enemy in goblin.visible_enemies:
                # Find distance from enemy to nearest goblin
                min_goblin_dist = min(
                    (abs(enemy.x - g.x) + abs(enemy.y - g.y) 
                     for g in [goblin] + goblin.visible_allies),
                    default=float('inf')
                )
                
                # Prioritize enemies far from goblins (likely retreating)
                score = min_goblin_dist
                if score > best_score:
                    best_score = score
                    best_enemy = enemy
            
            if best_enemy:
                return (best_enemy.x, best_enemy.y)
        return None
    
    return None


def calculate_movement_from_directive(directive: int, goblin: Goblin, world: World) -> Optional[Tuple[int, int]]:
    """
    Calculate actual movement position from directive using A* pathfinding
    Returns (x, y) position to move to, or None if cannot execute
    """
    # Special cases: attack and hold
    if directive == DIR_ATTACK:
        return None  # Handled separately
    
    if directive == DIR_HOLD:
        return None  # Handled separately
    
    # Get target from directive
    target = calculate_directive_target(directive, goblin, world)
    if target is None:
        return None
    
    # Use A* pathfinding to find next move toward target
    # This properly handles obstacles, other goblins, and avoids blocking
    from src.utils.pathfinding import get_next_move
    
    next_pos = get_next_move(world, goblin.position, target, goblin)
    
    # If A* succeeds, return the next position
    if next_pos:
        return next_pos
    
    # A* failed (target unreachable?) - fall back to greedy movement with fog penalty
    target_x, target_y = target
    best_move = None
    best_score = float('inf')
    
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            
            new_x, new_y = goblin.x + dx, goblin.y + dy
            
            if not world.can_move_to(new_x, new_y):
                continue
            
            # Calculate distance to target
            dist = abs(new_x - target_x) + abs(new_y - target_y)
            
            # Fog of war penalty: add 0.3 to distance if tile not visible
            if (new_x, new_y) not in goblin.visible_tiles:
                dist += 0.3
            
            if dist < best_score:
                best_score = dist
                best_move = (new_x, new_y)
    
    return best_move
