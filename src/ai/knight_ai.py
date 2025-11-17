"""
Knight AI - Simple rush and attack behavior
"""
import random
from typing import Optional, Tuple
from src.core.entity import Knight, Entity
from src.core.world import World
from src.utils.pathfinding import get_next_move, find_closest_unexplored, can_reach

class KnightAI:
    """Simple AI for knights"""
    
    def decide_action(self, knight: Knight, world: World) -> dict:
        """
        Decide what action the knight should take
        
        In grail mode:
        - If carrying grail: prioritize getting to entrance, kill blockers
        - If grail seen: prioritize reaching grail, kill blockers
        - Otherwise: explore to find grail, kill goblins encountered
        
        Returns:
            dict with 'action' and relevant parameters
        """
        # Check if in grail mode
        grail_mode = world.grail_position is not None
        
        # Priority 0: Flee storm if in danger zone (only if storm is active)
        if world.safe_zone_start_turn != float('inf') and not world.is_in_safe_zone(knight.x, knight.y):
            # Calculate direction to center
            cx, cy = world.safe_zone_center if world.safe_zone_center else (world.width // 2, world.height // 2)
            
            # Try to move toward center
            next_pos = get_next_move(world, knight.position, (cx, cy), knight)
            if next_pos and world.can_move_to(*next_pos):
                return {
                    'action': 'move',
                    'position': next_pos
                }
        
        # Priority 1: Attack if enemy adjacent (always important)
        adjacent_enemies = world.get_adjacent_entities(knight, enemies_only=True)
        if adjacent_enemies:
            # Attack closest enemy by HP (finish off wounded first)
            target = min(adjacent_enemies, key=lambda e: e.hp)
            return {
                'action': 'attack',
                'target': target
            }
        
        # GRAIL MODE LOGIC
        if grail_mode:
            # Priority 1.5: Get out of the way if carrier needs to pass and no enemies nearby
            if (world.grail_carrier and 
                world.grail_carrier != knight and 
                world.grail_carrier in knight.visible_allies):
                
                carrier = world.grail_carrier
                
                # If carrier is adjacent and trying to escape, move aside (unless enemies nearby)
                if knight.is_adjacent(carrier) and not adjacent_enemies:
                    # Calculate direction from carrier to entrance
                    if world.entrance_positions:
                        entrance = world.entrance_positions[0]
                        
                        # Check if we're blocking the carrier's path
                        carrier_to_entrance_dx = entrance[0] - carrier.x
                        carrier_to_entrance_dy = entrance[1] - carrier.y
                        
                        my_dx = knight.x - carrier.x
                        my_dy = knight.y - carrier.y
                        
                        # If I'm roughly between carrier and entrance, move aside
                        same_direction_x = (my_dx * carrier_to_entrance_dx > 0) if carrier_to_entrance_dx != 0 else False
                        same_direction_y = (my_dy * carrier_to_entrance_dy > 0) if carrier_to_entrance_dy != 0 else False
                        
                        if same_direction_x or same_direction_y:
                            # Move perpendicular to escape path
                            perpendicular_moves = []
                            for nx, ny in world.get_neighbors(*knight.position):
                                if world.can_move_to(nx, ny):
                                    # Check if this moves us away from blocking position
                                    new_dx = nx - carrier.x
                                    new_dy = ny - carrier.y
                                    new_same_x = (new_dx * carrier_to_entrance_dx > 0) if carrier_to_entrance_dx != 0 else False
                                    new_same_y = (new_dy * carrier_to_entrance_dy > 0) if carrier_to_entrance_dy != 0 else False
                                    
                                    # Prefer moves that get us out of the way
                                    if not new_same_x and not new_same_y:
                                        perpendicular_moves.append((nx, ny))
                            
                            if perpendicular_moves:
                                # Pick move that's furthest from carrier's path
                                best_move = max(perpendicular_moves, 
                                              key=lambda pos: abs(pos[0] - carrier.x - carrier_to_entrance_dx) + 
                                                             abs(pos[1] - carrier.y - carrier_to_entrance_dy))
                                return {
                                    'action': 'move',
                                    'position': best_move
                                }
            
            # If carrying the grail, get to entrance ASAP
            if knight.carrying_grail:
                if world.entrance_positions:
                    entrance = world.entrance_positions[0]  # Head for first entrance tile
                    next_pos = get_next_move(world, knight.position, entrance, knight)
                    
                    if next_pos and world.can_move_to(*next_pos):
                        return {
                            'action': 'move',
                            'position': next_pos
                        }
            
            # If we can see the grail and it's not carried, go get it
            elif world.grail_position in knight.visible_tiles and world.grail_carrier is None:
                next_pos = get_next_move(world, knight.position, world.grail_position, knight)
                
                if next_pos and world.can_move_to(*next_pos):
                    return {
                        'action': 'move',
                        'position': next_pos
                    }
            
            # If we remember where the grail is (saw it before), head there
            elif world.grail_position in knight.remembered_tiles and world.grail_carrier is None:
                next_pos = get_next_move(world, knight.position, world.grail_position, knight)
                
                if next_pos and world.can_move_to(*next_pos):
                    return {
                        'action': 'move',
                        'position': next_pos
                    }
            
            # Follow ally carrying grail to provide escort
            elif world.grail_carrier and world.grail_carrier in knight.visible_allies:
                carrier_pos = world.grail_carrier.position
                # Only escort if we're the closest knight - otherwise explore ahead
                other_escorts = [k for k in knight.visible_allies 
                               if k.distance_to_pos(*carrier_pos) <= 3]
                
                # If already have 2+ escorts, go clear the path ahead instead
                if len(other_escorts) >= 2:
                    # Path toward entrance to clear goblins
                    if world.entrance_positions:
                        entrance = world.entrance_positions[len(world.entrance_positions) // 2]
                        next_pos = get_next_move(world, knight.position, entrance, knight)
                        if next_pos and world.can_move_to(*next_pos):
                            return {
                                'action': 'move',
                                'position': next_pos
                            }
                else:
                    # Stay close but not blocking
                    if knight.distance_to_pos(*carrier_pos) > 3:
                        next_pos = get_next_move(world, knight.position, carrier_pos, knight)
                        if next_pos and world.can_move_to(*next_pos):
                            return {
                                'action': 'move',
                                'position': next_pos
                            }
            
            # Otherwise, aggressively explore toward unexplored far side
            else:
                # Find unexplored tiles on the far side first
                unexplored = find_closest_unexplored(world, knight, search_radius=20)
                
                if unexplored:
                    next_pos = get_next_move(world, knight.position, unexplored, knight)
                    if next_pos and world.can_move_to(*next_pos):
                        return {
                            'action': 'move',
                            'position': next_pos
                        }
                else:
                    # All explored - head toward grail area to search thoroughly
                    grail_x, grail_y = world.grail_position
                    # Pick a random position near the grail (within 10 tiles)
                    target_x = grail_x + random.randint(-5, 5)
                    target_y = grail_y + random.randint(-5, 5)
                    # Clamp to valid map bounds
                    target_x = max(3, min(world.width - 3, target_x))
                    target_y = max(3, min(world.height - 3, target_y))
                    target = (target_x, target_y)
                    
                    next_pos = get_next_move(world, knight.position, target, knight)
                    if next_pos and world.can_move_to(*next_pos):
                        return {
                            'action': 'move',
                            'position': next_pos
                        }
        
        # STANDARD MODE LOGIC (non-grail mode)
        else:
            # Priority 2: Move toward visible enemies (only in non-grail mode)
            pass
        
        # Priority 2: Move toward visible enemies
        if knight.visible_enemies:
            closest_enemy = min(knight.visible_enemies, key=lambda e: knight.distance_to(e))
            
            # Try to path to the enemy
            next_pos = get_next_move(world, knight.position, closest_enemy.position, knight)
            
            if next_pos:
                # Check if we can actually move there (not blocked by ally)
                if world.can_move_to(*next_pos):
                    return {
                        'action': 'move',
                        'position': next_pos
                    }
                else:
                    # Blocked by ally in narrow corridor - switch to exploration
                    knight.exploration_mode = True
            else:
                # Can't find path, explore instead
                knight.exploration_mode = True
        
        # Priority 3: Move toward last known enemy positions (using memory)
        if knight.enemy_last_seen:
            # Find the most recently seen enemy
            best_enemy_id = None
            best_staleness = float('inf')
            
            for enemy_id, (x, y, turns_ago) in knight.enemy_last_seen.items():
                if turns_ago < best_staleness:
                    best_staleness = turns_ago
                    best_enemy_id = enemy_id
            
            if best_enemy_id and best_staleness < 10:  # Only pursue if seen recently
                x, y, _ = knight.enemy_last_seen[best_enemy_id]
                next_pos = get_next_move(world, knight.position, (x, y), knight)
                
                if next_pos and world.can_move_to(*next_pos):
                    return {
                        'action': 'move',
                        'position': next_pos
                    }
        
        # Priority 4: Explore - find unexplored areas
        unexplored = find_closest_unexplored(world, knight, search_radius=15)
        if unexplored:
            next_pos = get_next_move(world, knight.position, unexplored, knight)
            if next_pos and world.can_move_to(*next_pos):
                return {
                    'action': 'move',
                    'position': next_pos
                }
        
        # Priority 5: Random walk if nothing else to do
        neighbors = world.get_neighbors(*knight.position)
        random.shuffle(neighbors)
        
        for pos in neighbors:
            if world.can_move_to(*pos):
                return {
                    'action': 'move',
                    'position': pos
                }
        
        # Can't move anywhere
        return {
            'action': 'wait'
        }

def create_knight_ai() -> KnightAI:
    """Factory function to create knight AI"""
    return KnightAI()
