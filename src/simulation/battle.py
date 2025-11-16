"""
Battle simulation - orchestrates the combat between knights and goblins
"""
import random
import time
from typing import List, Dict, Any
from src.core.entity import Entity, Knight, Goblin, Team, create_knights, create_goblins
from src.core.world import World
from src.core.combat import CombatSystem
from src.core.vision import update_all_vision
from src.generation.dungeon_gen import DungeonGenerator
from src.ai.knight_ai import KnightAI
from src.ai.goblin_ai import SimpleGoblinAI
from src.display.renderer import Renderer

class Battle:
    """Manages a single battle simulation"""
    
    def __init__(self, config: dict):
        self.config = config
        self.max_turns = config['simulation']['max_turns_per_battle']
        
        # Generate dungeon
        dungeon_size = config['simulation']['dungeon_size']
        self.dungeon_gen = DungeonGenerator(dungeon_size[0], dungeon_size[1])
        
        difficult_chance = config['terrain'].get('difficult_terrain_chance', 0.08)
        dungeon_map = self.dungeon_gen.generate(difficult_chance=difficult_chance)
        
        self.world = World(dungeon_map)
        
        # Create entities
        knight_count = config['knights']['count']
        goblin_count = random.randint(config['goblins']['count'][0], 
                                      config['goblins']['count'][1])
        
        # Get starting positions
        knight_positions = self.dungeon_gen.get_starting_positions(knight_count, 'left')
        goblin_positions = self.dungeon_gen.get_starting_positions(goblin_count, 'right')
        
        # Create entities
        self.knights = create_knights(knight_positions, config)
        self.goblins = create_goblins(goblin_positions, config)
        
        # Place entities in world
        for knight in self.knights:
            self.world.place_entity(knight)
        for goblin in self.goblins:
            self.world.place_entity(goblin)
        
        # Initialize AI
        self.knight_ai = KnightAI()
        self.goblin_ai = SimpleGoblinAI()
        
        # Combat system
        self.combat_system = CombatSystem()
        
        # Battle state
        self.turn = 0
        self.combat_log = []
    
    def run(self, renderer: Renderer = None, delay: float = 0.1) -> Dict[str, Any]:
        """
        Run the battle simulation
        
        Args:
            renderer: Optional renderer for visualization
            delay: Delay between turns in seconds
            
        Returns:
            Battle result dictionary
        """
        while self.turn < self.max_turns:
            self.turn += 1
            
            # Update vision for all entities
            all_entities = self.knights + self.goblins
            update_all_vision(all_entities, self.world)
            
            # Render if provided
            if renderer:
                recent_log = [self.combat_system.get_combat_description(log) 
                            for log in self.combat_system.combat_log[-5:]]
                renderer.render(self.world, all_entities, self.turn, recent_log)
                time.sleep(delay)
            
            # Process turn for all entities
            self._process_turn()
            
            # Check victory conditions
            winner = self._check_victory()
            if winner:
                result = self._create_result(winner)
                
                if renderer:
                    renderer.render_victory(winner, self.turn, 
                                          result['knights_remaining'],
                                          result['goblins_remaining'])
                
                return result
        
        # Timeout - determine winner by survivors
        winner = self._determine_timeout_winner()
        result = self._create_result(winner)
        
        if renderer:
            renderer.render_victory(f"{winner} (timeout)", self.turn,
                                  result['knights_remaining'],
                                  result['goblins_remaining'])
        
        return result
    
    def _process_turn(self):
        """Process one turn for all entities"""
        # Get all living entities
        all_entities = [e for e in (self.knights + self.goblins) if e.alive]
        
        # Shuffle for random initiative (could be improved with proper initiative system)
        random.shuffle(all_entities)
        
        # Each entity takes their action
        for entity in all_entities:
            if not entity.alive:
                continue
            
            # Decide action based on entity type
            if isinstance(entity, Knight):
                action = self.knight_ai.decide_action(entity, self.world)
            else:  # Goblin
                action = self.goblin_ai.decide_action(entity, self.world)
            
            # Execute action
            self._execute_action(entity, action)
    
    def _execute_action(self, entity: Entity, action: dict):
        """Execute an entity's action"""
        action_type = action.get('action')
        
        if action_type == 'attack':
            target = action['target']
            result = self.combat_system.attack(entity, target)
            
            # Remove dead entities from world
            if result.get('defender_killed'):
                self.world.remove_entity(target)
        
        elif action_type == 'move':
            position = action['position']
            old_pos = entity.position
            entity.move_to(*position)
            self.world.update_entity_position(entity, old_pos)
        
        elif action_type == 'wait':
            pass  # Do nothing
    
    def _check_victory(self) -> str:
        """
        Check if either side has won
        
        Returns:
            'Knights' or 'Goblins' if someone won, None otherwise
        """
        knights_alive = sum(1 for k in self.knights if k.alive)
        goblins_alive = sum(1 for g in self.goblins if g.alive)
        
        if knights_alive == 0:
            return 'Goblins'
        elif goblins_alive == 0:
            return 'Knights'
        
        return None
    
    def _determine_timeout_winner(self) -> str:
        """Determine winner on timeout based on remaining units"""
        knights_alive = sum(1 for k in self.knights if k.alive)
        goblins_alive = sum(1 for g in self.goblins if g.alive)
        
        if knights_alive > goblins_alive:
            return 'Knights'
        elif goblins_alive > knights_alive:
            return 'Goblins'
        else:
            return 'Draw'
    
    def _create_result(self, winner: str) -> Dict[str, Any]:
        """Create battle result dictionary"""
        knights_alive = sum(1 for k in self.knights if k.alive)
        goblins_alive = sum(1 for g in self.goblins if g.alive)
        
        return {
            'winner': winner,
            'turns': self.turn,
            'knights_remaining': knights_alive,
            'goblins_remaining': goblins_alive,
            'knights_total': len(self.knights),
            'goblins_total': len(self.goblins),
            'combat_log': self.combat_system.combat_log
        }
