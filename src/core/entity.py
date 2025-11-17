"""
Entity classes for Knights and Goblins
"""
import random
from typing import Tuple, Optional
from enum import Enum

class Team(Enum):
    """Team affiliation"""
    KNIGHT = 0
    GOBLIN = 1

class Entity:
    """Base class for all creatures"""
    
    _next_id = 0
    
    def __init__(self, x: int, y: int, hp: int, damage_range: Tuple[int, int], 
                 team: Team, vision_range: int = 3):
        self.id = Entity._next_id
        Entity._next_id += 1
        
        self.x = x
        self.y = y
        self.max_hp = hp
        self.hp = hp
        self.damage_range = damage_range
        self.team = team
        self.vision_range = vision_range
        self.alive = True
        
        # Vision data (updated each turn)
        self.visible_tiles = set()  # Set of (x, y) tuples
        self.visible_allies = []  # List of Entity objects
        self.visible_enemies = []  # List of Entity objects
        
        # Memory system (persists throughout battle)
        self.remembered_tiles = set()  # All tiles ever seen
        self.enemy_last_seen = {}  # enemy_id -> (x, y, turns_ago)
        self.turn_count = 0  # Track turns for staleness
        
        # Grail carrying status
        self.carrying_grail = False
        
        # Facing direction (0-7 for 8 directions: 0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW)
        self.facing = random.randint(0, 7)
        
    @property
    def position(self) -> Tuple[int, int]:
        """Get entity position as tuple"""
        return (self.x, self.y)
    
    def move_to(self, x: int, y: int):
        """Move entity to new position"""
        self.x = x
        self.y = y
    
    def take_damage(self, damage: int) -> int:
        """
        Take damage and return actual damage taken
        Returns damage amount for logging/rewards
        """
        actual_damage = min(damage, self.hp)
        self.hp -= actual_damage
        
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        
        return actual_damage
    
    def deal_damage(self) -> int:
        """Roll damage dice"""
        return random.randint(self.damage_range[0], self.damage_range[1])
    
    def distance_to(self, other: 'Entity') -> float:
        """Calculate distance to another entity"""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def distance_to_pos(self, x: int, y: int) -> float:
        """Calculate distance to a position"""
        return ((self.x - x) ** 2 + (self.y - y) ** 2) ** 0.5
    
    def update_memory(self):
        """Update memory with current vision"""
        # Remember all visible tiles
        self.remembered_tiles.update(self.visible_tiles)
        
        # Update enemy last-seen positions
        self.turn_count += 1
        for enemy in self.visible_enemies:
            self.enemy_last_seen[enemy.id] = (enemy.x, enemy.y, 0)
        
        # Increment staleness for unseen enemies
        for enemy_id in list(self.enemy_last_seen.keys()):
            x, y, turns_ago = self.enemy_last_seen[enemy_id]
            self.enemy_last_seen[enemy_id] = (x, y, turns_ago + 1)
    
    def get_last_known_position(self, enemy_id: int) -> Optional[Tuple[int, int, int]]:
        """Get last known position of an enemy: (x, y, turns_ago)"""
        return self.enemy_last_seen.get(enemy_id)
    
    def has_explored(self, x: int, y: int) -> bool:
        """Check if this position has been explored"""
        return (x, y) in self.remembered_tiles
    
    def is_adjacent(self, other: 'Entity') -> bool:
        """Check if entity is adjacent (including diagonals)"""
        return abs(self.x - other.x) <= 1 and abs(self.y - other.y) <= 1
    
    def update_facing_from_movement(self, target_x: int, target_y: int):
        """Update facing based on movement direction"""
        dx = target_x - self.x
        dy = target_y - self.y
        
        if dx == 0 and dy == 0:
            return  # No movement
        
        # Map direction to facing (0-7)
        # 0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW
        if dy < 0:  # North
            if dx > 0:
                self.facing = 1  # NE
            elif dx < 0:
                self.facing = 7  # NW
            else:
                self.facing = 0  # N
        elif dy > 0:  # South
            if dx > 0:
                self.facing = 3  # SE
            elif dx < 0:
                self.facing = 5  # SW
            else:
                self.facing = 4  # S
        else:  # East/West
            if dx > 0:
                self.facing = 2  # E
            else:
                self.facing = 6  # W
    
    def update_facing_to_target(self, target: 'Entity'):
        """Update facing to look at target entity"""
        self.update_facing_from_movement(target.x, target.y)
    
    def get_attack_arc(self, attacker: 'Entity') -> str:
        """
        Determine which arc the attacker is in relative to this entity's facing.
        Returns 'front', 'side', or 'rear'
        
        Front = 3 squares (facing, facing±1)
        Sides = 2 squares each (facing±2)
        Rear = 3 squares (facing±3, facing±4)
        """
        # Calculate direction from defender to attacker
        dx = attacker.x - self.x
        dy = attacker.y - self.y
        
        # Map to direction (0-7)
        if dy < 0:  # North
            if dx > 0:
                attacker_dir = 1  # NE
            elif dx < 0:
                attacker_dir = 7  # NW
            else:
                attacker_dir = 0  # N
        elif dy > 0:  # South
            if dx > 0:
                attacker_dir = 3  # SE
            elif dx < 0:
                attacker_dir = 5  # SW
            else:
                attacker_dir = 4  # S
        else:  # East/West
            if dx > 0:
                attacker_dir = 2  # E
            else:
                attacker_dir = 6  # W
        
        # Calculate relative angle (0-7 scale)
        relative_angle = (attacker_dir - self.facing) % 8
        
        # Front: 0, 1, 7 (±1 from facing)
        if relative_angle in [0, 1, 7]:
            return 'front'
        # Rear: 3, 4, 5 (opposite side, ±1)
        elif relative_angle in [3, 4, 5]:
            return 'rear'
        # Sides: 2, 6
        else:
            return 'side'
    
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id}, pos=({self.x},{self.y}), hp={self.hp}/{self.max_hp})"

class Knight(Entity):
    """Knight entity - strong and durable"""
    
    def __init__(self, x: int, y: int, config: dict):
        hp = random.randint(config['knights']['hp'][0], config['knights']['hp'][1])
        damage_range = tuple(config['knights']['damage'])
        vision_range = config['knights']['vision_range']
        
        super().__init__(x, y, hp, damage_range, Team.KNIGHT, vision_range)
        
        # Knight-specific attributes
        self.exploration_mode = False  # Set to True when can't reach enemies
    
    @property
    def symbol(self) -> str:
        return 'K'
    
    @property
    def color(self) -> str:
        return 'cyan'

class Goblin(Entity):
    """Goblin entity - weak but numerous"""
    
    def __init__(self, x: int, y: int, config: dict):
        hp = random.randint(config['goblins']['hp'][0], config['goblins']['hp'][1])
        damage_range = tuple(config['goblins']['damage'])
        vision_range = config['goblins']['vision_range']
        
        super().__init__(x, y, hp, damage_range, Team.GOBLIN, vision_range)
        
        # Goblin-specific attributes (for learning)
        self.last_state = None
        self.last_action = None
        self.cumulative_reward = 0.0
    
    @property
    def symbol(self) -> str:
        return 'g'
    
    @property
    def color(self) -> str:
        return 'green'

def create_knights(positions: list, config: dict) -> list:
    """Create knight entities at given positions"""
    knights = []
    for x, y in positions:
        knight = Knight(x, y, config)
        knights.append(knight)
    return knights

def create_goblins(positions: list, config: dict) -> list:
    """Create goblin entities at given positions"""
    goblins = []
    for x, y in positions:
        goblin = Goblin(x, y, config)
        goblins.append(goblin)
    return goblins
