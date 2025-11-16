"""
Goblin AI - Initially simple, will be replaced with learning-based AI
"""
import random
from typing import Optional, Tuple
from src.core.entity import Goblin, Entity
from src.core.world import World
from src.utils.pathfinding import get_next_move, find_closest_unexplored

class SimpleGoblinAI:
    """
    Simple rule-based AI for goblins (baseline behavior)
    This mimics knight behavior initially
    """
    
    def decide_action(self, goblin: Goblin, world: World) -> dict:
        """
        Decide what action the goblin should take
        
        Returns:
            dict with 'action' and relevant parameters
        """
        # Priority 1: Attack if enemy adjacent
        adjacent_enemies = world.get_adjacent_entities(goblin, enemies_only=True)
        if adjacent_enemies:
            # Attack weakest enemy
            target = min(adjacent_enemies, key=lambda e: e.hp)
            return {
                'action': 'attack',
                'target': target
            }
        
        # Priority 2: Move toward visible enemies
        if goblin.visible_enemies:
            closest_enemy = min(goblin.visible_enemies, key=lambda e: goblin.distance_to(e))
            
            next_pos = get_next_move(world, goblin.position, closest_enemy.position, goblin)
            
            if next_pos and world.can_move_to(*next_pos):
                return {
                    'action': 'move',
                    'position': next_pos
                }
        
        # Priority 3: Move toward last known enemy position
        if goblin.enemy_last_seen:
            # Find most recent sighting
            best_enemy_id = None
            best_staleness = float('inf')
            
            for enemy_id, (x, y, turns_ago) in goblin.enemy_last_seen.items():
                if turns_ago < best_staleness:
                    best_staleness = turns_ago
                    best_enemy_id = enemy_id
            
            if best_enemy_id and best_staleness < 15:
                x, y, _ = goblin.enemy_last_seen[best_enemy_id]
                next_pos = get_next_move(world, goblin.position, (x, y), goblin)
                
                if next_pos and world.can_move_to(*next_pos):
                    return {
                        'action': 'move',
                        'position': next_pos
                    }
        
        # Priority 4: Explore
        unexplored = find_closest_unexplored(world, goblin, search_radius=12)
        if unexplored:
            next_pos = get_next_move(world, goblin.position, unexplored, goblin)
            if next_pos and world.can_move_to(*next_pos):
                return {
                    'action': 'move',
                    'position': next_pos
                }
        
        # Priority 5: Random walk
        neighbors = world.get_neighbors(*goblin.position)
        random.shuffle(neighbors)
        
        for pos in neighbors:
            if world.can_move_to(*pos):
                return {
                    'action': 'move',
                    'position': pos
                }
        
        # Can't move
        return {
            'action': 'wait'
        }

class LearningGoblinAI:
    """
    Learning-based AI for goblins using Deep Q-Network
    TODO: Implement in Phase 3
    """
    
    def __init__(self, model=None):
        self.model = model
        # TODO: Initialize DQN model
    
    def decide_action(self, goblin: Goblin, world: World) -> dict:
        """
        Decide action using learned policy
        TODO: Implement neural network decision making
        """
        # For now, fall back to simple AI
        simple_ai = SimpleGoblinAI()
        return simple_ai.decide_action(goblin, world)
    
    def get_state(self, goblin: Goblin, world: World):
        """
        Extract state representation for neural network
        TODO: Implement state encoding
        """
        pass
    
    def record_experience(self, goblin: Goblin, state, action, reward, next_state, done):
        """
        Record experience for training
        TODO: Implement experience replay buffer
        """
        pass

def create_goblin_ai(use_learning: bool = False, model=None):
    """Factory function to create goblin AI"""
    if use_learning:
        return LearningGoblinAI(model)
    else:
        return SimpleGoblinAI()
