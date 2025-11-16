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
        
        Returns:
            dict with 'action' and relevant parameters
        """
        # Priority 1: Attack if enemy adjacent
        adjacent_enemies = world.get_adjacent_entities(knight, enemies_only=True)
        if adjacent_enemies:
            # Attack closest enemy by HP (finish off wounded first)
            target = min(adjacent_enemies, key=lambda e: e.hp)
            return {
                'action': 'attack',
                'target': target
            }
        
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
