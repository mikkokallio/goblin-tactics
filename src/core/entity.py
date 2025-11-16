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
