"""
World/Map management
"""
import numpy as np
from typing import List, Tuple, Optional
from src.generation.dungeon_gen import FLOOR, WALL, DIFFICULT
from src.core.entity import Entity

class World:
    """Manages the dungeon map and entity positions"""
    
    def __init__(self, dungeon_map: np.ndarray):
        self.map = dungeon_map
        self.height, self.width = dungeon_map.shape
        
        # Track entity positions for quick lookup
        self.entity_grid = {}  # (x, y) -> Entity
    
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
