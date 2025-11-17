"""
Battle data recorder - saves battle information for training
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

class BattleRecorder:
    """Records battle data for analysis and training"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.battles_dir = self.data_dir / "battles"
        self.training_dir = self.data_dir / "training"
        
        # Create directories if they don't exist
        self.battles_dir.mkdir(parents=True, exist_ok=True)
        self.training_dir.mkdir(parents=True, exist_ok=True)
        
        # Current battle data
        self.current_battle = None
        self.goblin_experiences = []  # List of (state, action, reward, next_state, done)
        self.turn_data = []
    
    def start_battle(self, battle_id: int, config: dict, dungeon_map, 
                    knights: list, goblins: list):
        """Initialize recording for a new battle"""
        self.current_battle = {
            'battle_id': battle_id,
            'timestamp': datetime.now().isoformat(),
            'config': {
                'knights_count': len(knights),
                'goblins_count': len(goblins),
                'dungeon_size': list(dungeon_map.shape),
                'max_turns': config['simulation']['max_turns_per_battle']
            },
            'initial_state': {
                'knights': [self._serialize_entity(k) for k in knights],
                'goblins': [self._serialize_entity(g) for g in goblins]
            },
            'turns': []
        }
        self.goblin_experiences = []
        self.turn_data = []
    
    def record_turn(self, turn: int, knights: list, goblins: list, 
                   actions: List[Dict], combat_events: List[Dict]):
        """Record data for a single turn"""
        turn_record = {
            'turn': turn,
            'knights_alive': sum(1 for k in knights if k.alive),
            'goblins_alive': sum(1 for g in goblins if g.alive),
            'actions': actions,
            'combat_events': [self._serialize_combat(e) for e in combat_events]
        }
        self.turn_data.append(turn_record)
    
    def record_goblin_experience(self, goblin_id: int, state: dict, 
                                 action: dict, reward: float, 
                                 next_state: dict, done: bool):
        """
        Record a single goblin's experience (for reinforcement learning)
        
        Args:
            goblin_id: Unique goblin identifier
            state: State observation before action
            action: Action taken
            reward: Reward received
            next_state: State after action
            done: Whether episode ended
        """
        experience = {
            'goblin_id': goblin_id,
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state,
            'done': done
        }
        self.goblin_experiences.append(experience)
    
    def end_battle(self, winner: str, turns: int, knights_remaining: int,
                  goblins_remaining: int):
        """Finalize and save battle data"""
        if self.current_battle is None:
            return
        
        self.current_battle['result'] = {
            'winner': winner,
            'turns': turns,
            'knights_remaining': knights_remaining,
            'goblins_remaining': goblins_remaining
        }
        self.current_battle['turns'] = self.turn_data
        
        # Save battle summary
        battle_file = self.battles_dir / f"battle_{self.current_battle['battle_id']:05d}.json"
        with open(battle_file, 'w') as f:
            json.dump(self.current_battle, f, indent=2)
        
        # Save goblin experiences (for training)
        if self.goblin_experiences:
            exp_file = self.training_dir / f"experiences_{self.current_battle['battle_id']:05d}.json"
            with open(exp_file, 'w') as f:
                json.dump({
                    'battle_id': self.current_battle['battle_id'],
                    'winner': winner,
                    'experiences': self.goblin_experiences
                }, f, indent=2)
        
        return battle_file
    
    def _serialize_entity(self, entity) -> dict:
        """Convert entity to serializable dict"""
        return {
            'id': entity.id,
            'type': entity.__class__.__name__,
            'position': [entity.x, entity.y],
            'hp': entity.hp,
            'max_hp': entity.max_hp,
            'team': entity.team.name
        }
    
    def _serialize_combat(self, event: dict) -> dict:
        """Serialize combat event"""
        if not event.get('success'):
            return {'success': False, 'reason': event.get('reason')}
        
        return {
            'attacker_id': event['attacker'].id,
            'attacker_type': event['attacker'].__class__.__name__,
            'defender_id': event['defender'].id,
            'defender_type': event['defender'].__class__.__name__,
            'damage': event['damage'],
            'defender_killed': event['defender_killed']
        }
    
    def get_summary_statistics(self) -> dict:
        """Get summary statistics from all recorded battles"""
        if not self.battles_dir.exists():
            return {}
        
        battles = list(self.battles_dir.glob("battle_*.json"))
        if not battles:
            return {}
        
        knight_wins = 0
        goblin_wins = 0
        total_turns = []
        
        for battle_file in battles:
            with open(battle_file, 'r') as f:
                data = json.load(f)
                if data['result']['winner'] == 'Knights':
                    knight_wins += 1
                elif data['result']['winner'] == 'Goblins':
                    goblin_wins += 1
                total_turns.append(data['result']['turns'])
        
        return {
            'total_battles': len(battles),
            'knight_wins': knight_wins,
            'goblin_wins': goblin_wins,
            'knight_win_rate': knight_wins / len(battles) if battles else 0,
            'avg_turns': sum(total_turns) / len(total_turns) if total_turns else 0,
            'max_turns': max(total_turns) if total_turns else 0,
            'min_turns': min(total_turns) if total_turns else 0
        }

def create_state_representation(goblin, world, all_entities) -> dict:
    """
    Create state representation for a goblin (for ML training)
    
    Returns dict with all observable features
    """
    # Normalize position
    normalized_x = goblin.x / world.width
    normalized_y = goblin.y / world.height
    
    # HP percentage
    hp_percentage = goblin.hp / goblin.max_hp
    
    # Count visible entities
    num_visible_allies = len(goblin.visible_allies)
    num_visible_enemies = len(goblin.visible_enemies)
    
    # Pack tactics: count adjacent allies (for damage bonus awareness)
    adjacent_allies = world.get_adjacent_allies(goblin)
    pack_allies_count = len(adjacent_allies)
    
    # Facing and directional awareness
    facing_normalized = goblin.facing / 7.0  # Normalize 0-7 to 0-1
    
    # Count enemies by direction (front, side, rear)
    enemies_in_front = 0
    enemies_on_sides = 0
    enemies_behind = 0
    
    # Count if THIS goblin is attacking FROM behind/sides (tactical advantage info)
    attacking_from_behind = 0
    attacking_from_sides = 0
    attacking_from_front = 0
    
    for enemy in goblin.visible_enemies:
        if goblin.is_adjacent(enemy):  # Only count adjacent threats for directional awareness
            # Check what arc the enemy is in from goblin's perspective
            arc = goblin.get_attack_arc(enemy)
            if arc == 'front':
                enemies_in_front += 1
            elif arc == 'side':
                enemies_on_sides += 1
            else:  # rear
                enemies_behind += 1
            
            # NEW: Check what arc the GOBLIN is in from enemy's perspective (flanking info)
            enemy_arc = enemy.get_attack_arc(goblin)
            if enemy_arc == 'rear':
                attacking_from_behind += 1  # Goblin is behind enemy - backstab position!
            elif enemy_arc == 'side':
                attacking_from_sides += 1   # Goblin is on enemy's side - flank position!
            else:
                attacking_from_front += 1   # Goblin is in front - direct combat
    
    # Distances and tactical info
    distance_to_nearest_ally = 99.0
    allies_within_3 = 0  # Allies close enough to support
    for ally in goblin.visible_allies:
        dist = goblin.distance_to(ally)
        if dist < distance_to_nearest_ally:
            distance_to_nearest_ally = dist
        if dist <= 3:
            allies_within_3 += 1
    
    distance_to_nearest_enemy = 99.0
    nearest_enemy_hp = 1.0
    enemies_within_3 = 0  # Nearby threats
    for enemy in goblin.visible_enemies:
        dist = goblin.distance_to(enemy)
        if dist < distance_to_nearest_enemy:
            distance_to_nearest_enemy = dist
            nearest_enemy_hp = enemy.hp / enemy.max_hp
        if dist <= 3:
            enemies_within_3 += 1
    
    # SECTOR AWARENESS: Divide surrounding area into 8 sectors (N, NE, E, SE, S, SW, W, NW)
    # Each sector is 12 tiles away from goblin position (mid-range tactical awareness)
    # Based on shared vision - goblins can communicate about distant positions
    sector_radius = 12
    sector_allies = [0] * 8  # Count of allies in each sector
    sector_enemies = [0] * 8  # Count of enemies in each sector
    
    def get_sector(dx, dy):
        """Get sector index (0-7) for relative position. N=0, clockwise to NW=7"""
        if dx == 0 and dy == 0:
            return None
        # Use atan2-like logic for 8 sectors
        if dx > abs(dy):      return 2  # E
        if dx < -abs(dy):     return 6  # W
        if dy > abs(dx):      return 4  # S
        if dy < -abs(dx):     return 0  # N
        if dx > 0 and dy > 0: return 3  # SE
        if dx < 0 and dy > 0: return 5  # SW
        if dx > 0 and dy < 0: return 1  # NE
        return 7  # NW
    
    # Count allies in sectors (using shared vision from visible_allies)
    for ally in goblin.visible_allies:
        dx = ally.x - goblin.x
        dy = ally.y - goblin.y
        dist = abs(dx) + abs(dy)
        
        # Only count if beyond immediate vicinity (>3 tiles) and within sector range
        if 3 < dist <= sector_radius:
            sector = get_sector(dx, dy)
            if sector is not None:
                sector_allies[sector] += 1
    
    # Count enemies in sectors (using shared vision from visible_enemies)
    for enemy in goblin.visible_enemies:
        dx = enemy.x - goblin.x
        dy = enemy.y - goblin.y
        dist = abs(dx) + abs(dy)
        
        # Only count if beyond immediate vicinity (>3 tiles) and within sector range
        if 3 < dist <= sector_radius:
            sector = get_sector(dx, dy)
            if sector is not None:
                sector_enemies[sector] += 1
    
    # Normalize sector counts (0-1, assuming max 5 units per sector)
    sector_allies_normalized = [min(count, 5.0) / 5.0 for count in sector_allies]
    sector_enemies_normalized = [min(count, 5.0) / 5.0 for count in sector_enemies]
    
    # Terrain context (5x5 grid around goblin)
    terrain_grid = []
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            x, y = goblin.x + dx, goblin.y + dy
            if world.is_in_bounds(x, y):
                # 0 = wall, 1 = floor, 2 = difficult, 3 = ally, 4 = enemy, 5 = storm
                if world.is_occupied(x, y):
                    entity = world.get_entity_at(x, y)
                    terrain_grid.append(3 if entity.team == goblin.team else 4)
                elif not world.is_passable(x, y):
                    terrain_grid.append(0)
                elif not world.is_in_safe_zone(x, y):
                    terrain_grid.append(5)  # Storm visible in local area
                elif world.is_difficult_terrain(x, y):
                    terrain_grid.append(2)
                else:
                    terrain_grid.append(1)
            else:
                terrain_grid.append(0)
    
    # Exploration percentage
    total_passable = sum(1 for y in range(world.height) for x in range(world.width) 
                        if world.is_passable(x, y))
    explored_pct = len(goblin.remembered_tiles) / max(total_passable, 1)
    
    # Storm awareness
    in_safe_zone = 1.0 if world.is_in_safe_zone(goblin.x, goblin.y) else 0.0
    
    # Grail awareness (new features for grail mode)
    grail_location_known = 0.0
    distance_to_grail = 99.0
    grail_carrier_nearby = 0.0
    distance_to_entrance = 99.0
    allies_near_grail = 0
    enemies_near_grail = 0
    
    if world.grail_position is not None:  # Grail mode is active
        # Determine grail location (either at origin or with carrier)
        grail_pos = world.grail_carrier.position if world.grail_carrier else world.grail_position
        
        # Can we see the grail?
        if grail_pos in goblin.visible_tiles or grail_pos in goblin.remembered_tiles:
            grail_location_known = 1.0
            distance_to_grail = goblin.distance_to_pos(*grail_pos)
        
        # Is the grail carrier nearby?
        if world.grail_carrier:
            if world.grail_carrier in goblin.visible_enemies:
                grail_carrier_nearby = 1.0
        
        # Distance to entrance (where knights need to escape)
        if world.entrance_positions:
            closest_entrance = min(world.entrance_positions, 
                                  key=lambda pos: goblin.distance_to_pos(*pos))
            distance_to_entrance = goblin.distance_to_pos(*closest_entrance)
        
        # Count allies and enemies near grail (coordination metrics)
        for ally in goblin.visible_allies:
            if ally.distance_to_pos(*grail_pos) <= 5:
                allies_near_grail += 1
        
        for enemy in goblin.visible_enemies:
            if enemy.distance_to_pos(*grail_pos) <= 5:
                enemies_near_grail += 1
    
    return {
        'position': [normalized_x, normalized_y],
        'hp_percentage': hp_percentage,
        'num_visible_allies': num_visible_allies,
        'num_visible_enemies': num_visible_enemies,
        'pack_allies_count': min(pack_allies_count, 8.0) / 8.0,  # Normalized 0-1
        'facing': facing_normalized,
        'enemies_in_front': min(enemies_in_front, 3.0) / 3.0,
        'enemies_on_sides': min(enemies_on_sides, 3.0) / 3.0,
        'enemies_behind': min(enemies_behind, 3.0) / 3.0,
        # Tactical positioning relative to enemies (flanking info)
        'attacking_from_behind': min(attacking_from_behind, 2.0) / 2.0,
        'attacking_from_sides': min(attacking_from_sides, 2.0) / 2.0,
        'attacking_from_front': min(attacking_from_front, 2.0) / 2.0,
        'distance_to_nearest_ally': min(distance_to_nearest_ally, 20.0) / 20.0,
        'distance_to_nearest_enemy': min(distance_to_nearest_enemy, 20.0) / 20.0,
        'nearest_enemy_hp': nearest_enemy_hp,
        'allies_within_3': min(allies_within_3, 5.0) / 5.0,
        'enemies_within_3': min(enemies_within_3, 5.0) / 5.0,
        # Sector awareness (8 directions, mid-range tactical context)
        'sector_allies': sector_allies_normalized,  # 8 values
        'sector_enemies': sector_enemies_normalized,  # 8 values
        'terrain_grid': terrain_grid,
        'explored_percentage': explored_pct,
        'in_safe_zone': in_safe_zone,
        'turn_count': goblin.turn_count,
        # Grail mode features
        'grail_location_known': grail_location_known,
        'distance_to_grail': min(distance_to_grail, 40.0) / 40.0,
        'grail_carrier_nearby': grail_carrier_nearby,
        'distance_to_entrance': min(distance_to_entrance, 40.0) / 40.0,
        'allies_near_grail': min(allies_near_grail, 5.0) / 5.0,
        'enemies_near_grail': min(enemies_near_grail, 5.0) / 5.0
    }
