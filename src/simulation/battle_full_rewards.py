"""
Battle simulation - orchestrates the combat between knights and goblins
"""
import random
import time
from collections import deque
from typing import List, Dict, Any
from src.core.entity import Entity, Knight, Goblin, Team, create_knights, create_goblins
from src.core.world import World
from src.core.combat import CombatSystem
from src.core.vision import update_all_vision
from src.generation.dungeon_gen import DungeonGenerator
from src.ai.knight_ai import KnightAI
from src.ai.goblin_ai import SimpleGoblinAI, create_goblin_ai
from src.display.renderer import Renderer
from src.simulation.recorder import BattleRecorder, create_state_representation

class Battle:
    """Manages a single battle simulation"""
    
    def __init__(self, config: dict, battle_id: int = 0, record: bool = None,
                 goblin_agent=None, training: bool = False):
        self.config = config
        self.battle_id = battle_id
        self.max_turns = config['simulation']['max_turns_per_battle']
        self.training = training
        
        # Recording
        if record is None:
            record = config['simulation'].get('record_battles', False)
        self.record = record
        self.recorder = BattleRecorder() if record else None
        
        # Generate dungeon
        dungeon_size = config['simulation']['dungeon_size']
        self.dungeon_gen = DungeonGenerator(dungeon_size[0], dungeon_size[1])
        
        difficult_chance = config['terrain'].get('difficult_terrain_chance', 0.08)
        grail_mode = config['simulation'].get('grail_mode', False)
        arena_mode = config['simulation'].get('arena_mode', False)
        dungeon_map = self.dungeon_gen.generate(difficult_chance=difficult_chance, 
                                                create_entrance=grail_mode,
                                                arena_mode=arena_mode)
        
        self.world = World(dungeon_map)
        
        # Setup grail if enabled
        if grail_mode:
            grail_pos = self.dungeon_gen.get_grail_position()
            self.world.set_grail_position(grail_pos)
            entrance_positions = self.dungeon_gen.get_entrance_positions()
            self.world.set_entrance_positions(entrance_positions)
        
        # Configure storm/safe zone from config
        if config['simulation'].get('storm_enabled', True):
            self.world.storm_damage = config['simulation'].get('storm_damage', 5)
            self.world.safe_zone_start_turn = config['simulation'].get('storm_start_turn', 50)
            self.world.safe_zone_shrink_rate = config['simulation'].get('storm_shrink_rate', 1)
        else:
            # Disable storm by setting start turn to infinity
            self.world.safe_zone_start_turn = float('inf')
        
        # Create entities
        knight_count = config['knights']['count']
        goblin_count = random.randint(config['goblins']['count'][0], 
                                      config['goblins']['count'][1])
        
        # Get starting positions
        if grail_mode and hasattr(self.dungeon_gen, 'entrance_positions'):
            # In grail mode, knights start at entrance
            knight_positions = self.dungeon_gen.get_entrance_positions()[:knight_count]
        else:
            knight_positions = self.dungeon_gen.get_starting_positions(knight_count, 'left')
        
        # Spread goblins across multiple rooms to prevent clustering
        goblin_positions = self.dungeon_gen.get_starting_positions(goblin_count, 'right', spread=True)
        
        # Create entities
        self.knights = create_knights(knight_positions, config)
        self.goblins = create_goblins(goblin_positions, config)
        
        # Place entities in world
        for knight in self.knights:
            self.world.place_entity(knight)
        for goblin in self.goblins:
            self.world.place_entity(goblin)
        
        # Initialize safe zone / storm
        self.world.initialize_safe_zone()
        
        # Initialize AI
        self.knight_ai = KnightAI()
        if goblin_agent:
            self.goblin_ai = create_goblin_ai(use_learning=True, agent=goblin_agent, 
                                             training=training)
        else:
            self.goblin_ai = SimpleGoblinAI()
        
        # Combat system
        self.combat_system = CombatSystem()
        
        # Battle state
        self.turn = 0
        self.combat_log = []
        
        # Start recording if enabled
        if self.recorder:
            self.recorder.start_battle(self.battle_id, config, dungeon_map,
                                      self.knights, self.goblins)
    
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
            
            # Update safe zone
            self.world.update_safe_zone(self.turn)
            
            # Update vision for all entities
            all_entities = self.knights + self.goblins
            update_all_vision(all_entities, self.world)
            
            # Apply storm damage to entities outside safe zone
            storm_events = self.world.apply_storm_damage(all_entities, self.turn)
            if storm_events:
                # Add storm events to combat log for visibility
                for event in storm_events:
                    self.combat_system.combat_log.append({
                        'type': 'storm_damage',
                        'entity_type': event['entity_type'],
                        'entity_id': event['entity_id'],
                        'damage': event['damage'],
                        'killed': event['killed']
                    })
                
                # Remove dead entities from world
                for event in storm_events:
                    if event['killed']:
                        entity_id = event['entity_id']
                        for entity in all_entities:
                            if entity.id == entity_id and not entity.alive:
                                self.world.remove_entity(entity)
            
            # Render if provided
            if renderer:
                recent_log = [self.combat_system.get_combat_description(log) 
                            for log in self.combat_system.combat_log[-5:]]
                
                # Add storm warnings if zone is active
                if self.turn >= self.world.safe_zone_start_turn:
                    storm_msg = f"⚠ STORM ACTIVE | Safe radius: {self.world.safe_zone_radius:.1f}"
                    recent_log.insert(0, storm_msg)
                    
                renderer.render(self.world, all_entities, self.turn, recent_log)
                time.sleep(delay)
            
            # Process turn for all entities
            self._process_turn()
            
            # Check victory conditions
            winner = self._check_victory()
            if winner:
                result = self._create_result(winner)
                
                # End recording
                if self.recorder:
                    self.recorder.end_battle(winner, self.turn,
                                           result['knights_remaining'],
                                           result['goblins_remaining'])
                
                if renderer:
                    renderer.render_victory(winner, self.turn, 
                                          result['knights_remaining'],
                                          result['goblins_remaining'])
                
                return result
        
        # Timeout - determine winner by survivors
        winner = self._determine_timeout_winner()
        result = self._create_result(winner)
        
        # End recording
        if self.recorder:
            self.recorder.end_battle(f"{winner} (timeout)", self.turn,
                                   result['knights_remaining'],
                                   result['goblins_remaining'])
        
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
        
        # Track actions for recording
        turn_actions = []
        
        # Each entity takes their action
        for entity in all_entities:
            if not entity.alive:
                continue
            
            # Record pre-action state for goblins (for ML training)
            if self.recorder and isinstance(entity, Goblin):
                pre_state = create_state_representation(entity, self.world, all_entities)
            
            # Decide action based on entity type
            if isinstance(entity, Knight):
                action = self.knight_ai.decide_action(entity, self.world)
            else:  # Goblin
                action = self.goblin_ai.decide_action(entity, self.world)
            
            # Execute action
            self._execute_action(entity, action)
            
            # Record action (serialize for JSON)
            serialized_action = {
                'entity_id': entity.id,
                'entity_type': entity.__class__.__name__,
                'action_type': action.get('action'),
                'position': [entity.x, entity.y]
            }
            if 'target' in action:
                serialized_action['target_id'] = action['target'].id
            turn_actions.append(serialized_action)
            
            # Record post-action state and experience for goblins
            if self.recorder and isinstance(entity, Goblin):
                post_state = create_state_representation(entity, self.world, all_entities)
                
                # Calculate reward based on actions and outcomes
                reward = 0.0
                
                if not entity.alive:
                    # Death penalty
                    reward = -100.0
                else:
                    # Check if in grail mode
                    grail_mode = self.world.grail_position is not None
                    
                    if grail_mode:
                        # SIMPLIFIED REWARD SYSTEM
                        # 1. Reward attacking based on damage
                        # 2. Reward approaching enemy if allies nearby, staying at range if alone
                        
                        # Detect if ANY goblin can see knights (shared intel through visible_enemies)
                        enemies_visible = len(entity.visible_enemies) > 0
                        
                        # Check if ANY allied goblin sees enemies (simulates communication)
                        allies_see_enemies = any(len(ally.visible_enemies) > 0 for ally in entity.visible_allies)
                        combat_mode = enemies_visible or allies_see_enemies
                        
                        # === ATTACK REWARDS: Based purely on damage dealt ===
                        if action.get('action') == 'attack':
                            recent_combat = self.combat_system.combat_log[-5:] if self.combat_system.combat_log else []
                            for event in recent_combat:
                                if event.get('attacker') == entity:
                                    if event.get('success'):
                                        damage = event.get('damage', 0)
                                        reward += damage * 10.0  # Reward based on damage dealt
                                        
                                        if event.get('defender_killed'):
                                            reward += 100.0  # Bonus for killing enemy
                                    break
                        
                        # === EXPLORATION REWARD: Always reward exploring new tiles ===
                        if action.get('action') == 'move':
                            new_pos = action.get('position')
                            if new_pos and not entity.has_explored(*new_pos):
                                reward += 8.0  # Explore new areas!
                        
                        # === ANTI-CLUSTERING: Penalty if too many goblins nearby with no enemies ===
                        if not entity.visible_enemies:
                            # Count goblins within 5 tiles
                            nearby_goblins = sum(1 for ally in entity.visible_allies 
                                               if entity.distance_to(ally) <= 5)
                            
                            if nearby_goblins >= 5:
                                reward -= 15.0  # Too crowded! Spread out! (increased from -10)
                            elif nearby_goblins >= 3:
                                reward -= 8.0  # Getting crowded (increased from -5)
                        
                        # === MOVEMENT REWARDS: Multiple strategies for different situations ===
                        if action.get('action') == 'move':
                            new_pos = action.get('position')
                            
                            if entity.visible_enemies and new_pos:
                                # Simple - always reward moving toward visible enemy
                                closest_enemy = min(entity.visible_enemies, key=lambda e: entity.distance_to(e))
                                current_dist = entity.distance_to(closest_enemy)
                                new_dist = abs(new_pos[0] - closest_enemy.x) + abs(new_pos[1] - closest_enemy.y)
                                
                                if new_dist < current_dist:
                                    reward += 12.0  # Always reward closing distance to enemy!
                                
                                # Pack formation - reward having allies nearby when in combat
                                nearby_allies = sum(1 for ally in entity.visible_allies if entity.distance_to(ally) <= 4)
                                if nearby_allies >= 1:
                                    reward += 5.0  # Good, you have backup nearby!
                                
                            else:
                                # No enemies visible to me
                                # Shared vision - move toward allies who can see enemies
                                allies_with_vision = [ally for ally in entity.visible_allies if len(ally.visible_enemies) > 0]
                                if allies_with_vision and new_pos:
                                    # Find closest ally who sees enemies
                                    closest_ally_with_vision = min(allies_with_vision, key=lambda a: entity.distance_to(a))
                                    current_ally_dist = entity.distance_to(closest_ally_with_vision)
                                    new_ally_dist = abs(new_pos[0] - closest_ally_with_vision.x) + abs(new_pos[1] - closest_ally_with_vision.y)
                                    
                                    if new_ally_dist < current_ally_dist:
                                        reward += 10.0  # Reinforce allies in combat!
                        
                        # === SPREAD OUT BEHAVIOR: Reward moving away from crowded areas ===
                        elif action.get('action') == 'move' and not entity.visible_enemies:
                            new_pos = action.get('position')
                            if new_pos:
                                # Count how crowded current area is
                                current_crowding = sum(1 for ally in entity.visible_allies 
                                                      if entity.distance_to(ally) <= 5)
                                
                                # Estimate how crowded new position will be
                                new_crowding = sum(1 for ally in entity.visible_allies
                                                  if abs(new_pos[0] - ally.x) + abs(new_pos[1] - ally.y) <= 5)
                                
                                # Reward moving to less crowded areas
                                if new_crowding < current_crowding:
                                    reward += 6.0  # Move to less crowded area!
                        
                        # # === OLD REWARD SYSTEM (COMMENTED OUT) ===
                        # # All the complex positioning, pack, scouting, sector awareness, etc.
                        # # Commented out to test simple reward system
                    
                    else:
                        # STANDARD MODE REWARDS - Aggressive tactics
                        reward += 0.5
                        
                        # Combat rewards
                        if action.get('action') == 'attack':
                            recent_combat = self.combat_system.combat_log[-5:] if self.combat_system.combat_log else []
                            for event in recent_combat:
                                if event.get('attacker') == entity:
                                    if event.get('success'):
                                        damage = event.get('damage', 0)
                                        reward += damage * 2.0
                                        
                                        if event.get('defender_killed'):
                                            reward += 50.0
                                            
                                            nearby_allies = sum(1 for ally in entity.visible_allies 
                                                              if entity.distance_to(ally) <= 3)
                                            if nearby_allies > 0:
                                                reward += 20.0 * nearby_allies
                                    break
                        
                        # Tactical positioning
                        if entity.visible_enemies:
                            min_dist = min(entity.distance_to(e) for e in entity.visible_enemies)
                            nearest_enemy = min(entity.visible_enemies, key=lambda e: entity.distance_to(e))
                            
                            allies_near_target = sum(1 for ally in entity.visible_allies 
                                                    if ally.distance_to(nearest_enemy) <= 3)
                            
                            if allies_near_target > 0:
                                reward += 3.0 * allies_near_target
                            
                            if min_dist <= 1:
                                reward += 5.0
                            elif min_dist <= 2:
                                reward += 3.0
                            elif min_dist <= 4:
                                reward += 1.5
                            elif min_dist <= 7:
                                reward += 0.5
                            
                            if min_dist > 7:
                                reward -= 2.0
                        
                        # Storm penalty
                        if not self.world.is_in_safe_zone(entity.x, entity.y):
                            reward -= 10.0
                        
                        # Wait penalty
                        if action.get('action') == 'wait':
                            reward -= 2.0
                        
                        # Oscillation check
                        if action.get('action') == 'move':
                            new_pos = action.get('position')
                            if not hasattr(entity, 'position_history'):
                                entity.position_history = deque(maxlen=4)
                            
                            if new_pos in entity.position_history:
                                reward -= 5.0
                        
                        entity.position_history.append(new_pos)
                
                # Serialize action for recording
                action_record = {
                    'type': action.get('action'),
                    'position': action.get('position')
                }
                if 'target' in action:
                    action_record['target_id'] = action['target'].id
                self.recorder.record_goblin_experience(
                    entity.id, pre_state, action_record, reward, post_state, not entity.alive
                )
        
        # Record turn data
        if self.recorder:
            self.recorder.record_turn(self.turn, self.knights, self.goblins,
                                     turn_actions, self.combat_system.combat_log)
    
    def _execute_action(self, entity: Entity, action: dict):
        """Execute an entity's action"""
        action_type = action.get('action')
        
        if action_type == 'attack':
            target = action['target']
            result = self.combat_system.attack(entity, target, self.world)
            
            # Remove dead entities from world
            if result.get('defender_killed'):
                self.world.remove_entity(target)
                # If grail carrier was killed, drop the grail
                if hasattr(target, 'carrying_grail') and target.carrying_grail:
                    self.world.drop_grail(target)
        
        elif action_type == 'move':
            position = action['position']
            old_pos = entity.position
            
            # Update facing based on movement direction
            entity.update_facing_from_movement(*position)
            
            entity.move_to(*position)
            self.world.update_entity_position(entity, old_pos)
            
            # Check if knight picked up the grail
            if entity.team == Team.KNIGHT:
                if self.world.try_pickup_grail(entity):
                    # Log grail pickup
                    self.combat_system.combat_log.append({
                        'type': 'grail_pickup',
                        'entity_id': entity.id,
                        'entity_type': entity.__class__.__name__
                    })
        
        elif action_type == 'wait':
            pass  # Do nothing
    
    def _check_victory(self) -> str:
        """
        Check if either side has won
        
        Returns:
            'Knights' or 'Goblins' if someone won, None otherwise
        """
        # Check grail extraction victory
        if self.world.grail_carrier and self.world.is_entrance_position(
            self.world.grail_carrier.x, self.world.grail_carrier.y):
            return 'Knights'  # Knights win immediately by extracting the grail!
        
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
