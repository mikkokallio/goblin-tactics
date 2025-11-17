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
        # Priority 0: Flee storm if in danger zone
        if not world.is_in_safe_zone(goblin.x, goblin.y):
            # Calculate direction to center
            cx, cy = world.safe_zone_center if world.safe_zone_center else (world.width // 2, world.height // 2)
            
            # Try to move toward center
            next_pos = get_next_move(world, goblin.position, (cx, cy), goblin)
            if next_pos and world.can_move_to(*next_pos):
                return {
                    'action': 'move',
                    'position': next_pos
                }
        
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
    """
    
    def __init__(self, agent=None, training: bool = True):
        self.agent = agent
        self.training = training
        self.simple_fallback = SimpleGoblinAI()
        
        # Directive usage statistics
        self.directive_stats = {}
        
        # If no agent provided, fall back to simple AI
        if self.agent is None:
            self.use_learning = False
        else:
            self.use_learning = True
    
    def decide_action(self, goblin: Goblin, world: World) -> dict:
        """
        Decide action using learned policy with tactical directives
        """
        if not self.use_learning:
            return self.simple_fallback.decide_action(goblin, world)
        
        # Get state representation
        from src.simulation.recorder import create_state_representation
        state_dict = create_state_representation(goblin, world, 
                                                 world.entity_grid.values())
        
        # Convert to vector
        from src.ai.learning import state_dict_to_vector, NUM_ACTIONS
        from src.ai.directives import DIR_ATTACK, DIR_HOLD
        
        state_vector = state_dict_to_vector(state_dict)
        
        # Get directive from agent (not direction!)
        directive_idx = self.agent.get_action(state_vector, training=self.training)
        
        # Track directive usage for statistics
        self.directive_stats[directive_idx] = self.directive_stats.get(directive_idx, 0) + 1
        
        # Store directive on goblin for diversity reward tracking
        goblin.last_directive = directive_idx
        
        # Convert directive to actual game action
        return self._directive_to_game_action(directive_idx, goblin, world)
    
    def _directive_to_game_action(self, directive: int, goblin: Goblin, 
                                   world: World) -> dict:
        """Convert directive index to game action using tactical reasoning"""
        from src.ai.directives import (
            DIR_ATTACK, DIR_HOLD, DIRECTIVE_NAMES,
            calculate_movement_from_directive
        )
        
        # Attack directive - check if enemy is adjacent
        if directive == DIR_ATTACK:
            adjacent_enemies = world.get_adjacent_entities(goblin, enemies_only=True)
            if adjacent_enemies:
                target = min(adjacent_enemies, key=lambda e: e.hp)
                return {'action': 'attack', 'target': target}
            # Can't attack, hold position
            return {'action': 'wait'}
        
        # Hold directive
        if directive == DIR_HOLD:
            return {'action': 'wait'}
        
        # Movement directive - calculate position from tactical reasoning
        move_pos = calculate_movement_from_directive(directive, goblin, world)
        
        if move_pos and world.can_move_to(*move_pos):
            return {'action': 'move', 'position': move_pos}
        
        # Directive couldn't be executed, use fallback
        return self.simple_fallback.decide_action(goblin, world)
    
    def get_directive_statistics(self) -> dict:
        """Get statistics on which directives were chosen"""
        return self.directive_stats.copy()
    
    def print_directive_statistics(self):
        """Print readable directive usage statistics"""
        from src.ai.directives import DIRECTIVE_NAMES
        
        if not self.directive_stats:
            print("No directive statistics available yet.")
            return
        
        total_actions = sum(self.directive_stats.values())
        print(f"\n📊 Directive Usage Statistics ({total_actions} total actions):")
        print("=" * 60)
        
        # Sort by usage count
        sorted_directives = sorted(self.directive_stats.items(), 
                                   key=lambda x: x[1], reverse=True)
        
        for directive_idx, count in sorted_directives:
            percentage = (count / total_actions) * 100
            directive_name = DIRECTIVE_NAMES.get(directive_idx, f"Unknown({directive_idx})")
            bar_length = int(percentage / 2)  # Scale to 50 chars max
            bar = "█" * bar_length
            print(f"  {directive_idx:2d}. {directive_name:25s} │{bar:50s}│ {count:5d} ({percentage:5.1f}%)")
        print("=" * 60)
    
    def reset_directive_statistics(self):
        """Reset directive usage statistics"""
        self.directive_stats = {}

def create_goblin_ai(use_learning: bool = False, agent=None, training: bool = True):
    """Factory function to create goblin AI"""
    if use_learning:
        return LearningGoblinAI(agent, training)
    else:
        return SimpleGoblinAI()
