"""
World/Map management
"""
import numpy as np
from typing import List, Tuple, Optional
from src.generation.dungeon_gen import FLOOR, WALL, DIFFICULT
from src.core.entity import Entity, Team

class World:
    """Manages the dungeon map and entity positions"""
    
    def __init__(self, dungeon_map: np.ndarray):
        self.map = dungeon_map
        self.height, self.width = dungeon_map.shape
        
        # Track entity positions for quick lookup
        self.entity_grid = {}  # (x, y) -> Entity
        
        # Holy Grail mechanics
        self.grail_position: Optional[Tuple[int, int]] = None
        self.grail_carrier: Optional[Entity] = None  # Which knight is carrying the grail
        self.entrance_positions: List[Tuple[int, int]] = []  # Entrance corridor tiles
        
        # Shrinking zone mechanics (can be disabled)
        self.storm_damage = 5  # Damage per turn outside safe zone
        self.safe_zone_start_turn = 50  # Turn when zone starts shrinking
        self.safe_zone_shrink_rate = 1  # Tiles per turn
        self.safe_zone_radius = None  # Will be calculated
        self.safe_zone_center = None  # Will be calculated
    
    def is_passable(self, x: int, y: int) -> bool:
        """Check if a tile is passable"""
        if not self.is_in_bounds(x, y):
            return False
        return self.map[y, x] != WALL
    
    def is_in_bounds(self, x: int, y: int) -> bool:
        """Check if coordinates are within map bounds"""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def is_floor(self, x: int, y: int) -> bool:
        """Check if tile is floor (not wall)"""
        if not self.is_in_bounds(x, y):
            return False
        return self.map[y, x] in [FLOOR, DIFFICULT]
    
    def is_difficult_terrain(self, x: int, y: int) -> bool:
        """Check if tile is difficult terrain"""
        if not self.is_in_bounds(x, y):
            return False
        return self.map[y, x] == DIFFICULT
    
    def is_occupied(self, x: int, y: int) -> bool:
        """Check if a tile is occupied by an entity"""
        return (x, y) in self.entity_grid
    
    def get_entity_at(self, x: int, y: int) -> Optional[Entity]:
        """Get entity at position, or None"""
        return self.entity_grid.get((x, y))
    
    def can_move_to(self, x: int, y: int) -> bool:
        """Check if an entity can move to this position"""
        return self.is_passable(x, y) and not self.is_occupied(x, y)
    
    def update_entity_position(self, entity: Entity, old_pos: Tuple[int, int]):
        """Update entity position in the grid"""
        # Remove from old position
        if old_pos in self.entity_grid:
            del self.entity_grid[old_pos]
        
        # Add to new position
        if entity.alive:
            self.entity_grid[entity.position] = entity
    
    def place_entity(self, entity: Entity):
        """Place an entity on the map"""
        self.entity_grid[entity.position] = entity
    
    def remove_entity(self, entity: Entity):
        """Remove an entity from the map"""
        if entity.position in self.entity_grid:
            del self.entity_grid[entity.position]
    
    def get_neighbors(self, x: int, y: int, passable_only: bool = True) -> List[Tuple[int, int]]:
        """
        Get neighboring tiles (8 directions)
        
        Args:
            x, y: Position
            passable_only: Only return passable tiles
            
        Returns:
            List of (x, y) tuples
        """
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                nx, ny = x + dx, y + dy
                
                if passable_only:
                    if self.is_passable(nx, ny):
                        neighbors.append((nx, ny))
                else:
                    if self.is_in_bounds(nx, ny):
                        neighbors.append((nx, ny))
        
        return neighbors
    
    def get_adjacent_entities(self, entity: Entity, allies_only: bool = False, 
                             enemies_only: bool = False) -> List[Entity]:
        """Get entities adjacent to this entity"""
        adjacent = []
        
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                pos = (entity.x + dx, entity.y + dy)
                other = self.get_entity_at(*pos)
                
                if other and other.alive:
                    if allies_only and other.team != entity.team:
                        continue
                    if enemies_only and other.team == entity.team:
                        continue
                    adjacent.append(other)
        
        return adjacent
    
    def get_adjacent_allies(self, entity: Entity) -> List[Entity]:
        """Get allied entities adjacent to this entity (convenience method for pack tactics)"""
        return self.get_adjacent_entities(entity, allies_only=True)
    
    def initialize_safe_zone(self):
        """Initialize the safe zone at map center"""
        self.safe_zone_center = (self.width // 2, self.height // 2)
        # Start with entire map being safe
        self.safe_zone_radius = max(self.width, self.height)
    
    def update_safe_zone(self, turn: int):
        """Update the safe zone radius based on current turn"""
        if turn >= self.safe_zone_start_turn:
            turns_since_start = turn - self.safe_zone_start_turn
            self.safe_zone_radius = max(5, max(self.width, self.height) - 
                                       turns_since_start * self.safe_zone_shrink_rate)
    
    def is_in_safe_zone(self, x: int, y: int) -> bool:
        """Check if position is within the safe zone"""
        if self.safe_zone_center is None or self.safe_zone_radius is None:
            return True  # No zone active yet
        
        cx, cy = self.safe_zone_center
        distance = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        return distance <= self.safe_zone_radius
    
    def apply_storm_damage(self, entities: List[Entity], turn: int) -> List[dict]:
        """Apply damage to entities outside safe zone"""
        damage_events = []
        
        if turn < self.safe_zone_start_turn:
            return damage_events
        
        for entity in entities:
            if entity.alive and not self.is_in_safe_zone(entity.x, entity.y):
                entity.take_damage(self.storm_damage)
                damage_events.append({
                    'entity_id': entity.id,
                    'entity_type': entity.__class__.__name__,
                    'damage': self.storm_damage,
                    'killed': not entity.alive,
                    'reason': 'storm'
                })
        
        return damage_events
    
    def set_grail_position(self, position: Tuple[int, int]):
        """Set the Holy Grail's position"""
        self.grail_position = position
    
    def set_entrance_positions(self, positions: List[Tuple[int, int]]):
        """Set the entrance corridor positions"""
        self.entrance_positions = positions
    
    def is_grail_at_position(self, x: int, y: int) -> bool:
        """Check if the grail is at this position"""
        return self.grail_position == (x, y) and self.grail_carrier is None
    
    def is_entrance_position(self, x: int, y: int) -> bool:
        """Check if this position is part of the entrance corridor"""
        return (x, y) in self.entrance_positions
    
    def try_pickup_grail(self, entity: Entity) -> bool:
        """
        Try to pick up the grail if entity is standing on it.
        Returns True if successful.
        """
        if (self.grail_position == entity.position and 
            self.grail_carrier is None and
            entity.team == Team.KNIGHT):  # Only knights can pick up grail
            self.grail_carrier = entity
            entity.carrying_grail = True
            return True
        return False
    
    def drop_grail(self, entity: Entity):
        """Drop the grail at the entity's current position"""
        if self.grail_carrier == entity:
            self.grail_position = entity.position
            self.grail_carrier = None
            entity.carrying_grail = False
    
    def get_terrain_symbol(self, x: int, y: int) -> str:
        """Get the character to display for this terrain"""
        if not self.is_in_bounds(x, y):
            return ' '
        
        terrain = self.map[y, x]
        if terrain == WALL:
            return '#'
        elif terrain == FLOOR:
            return '.'
        elif terrain == DIFFICULT:
            return '~'
        else:
            return '?'
