"""
A* pathfinding with support for memory-based navigation
"""
import heapq
from typing import List, Tuple, Optional, Set
from src.core.world import World
from src.core.entity import Entity

class Node:
    """Node for A* pathfinding"""
    def __init__(self, pos: Tuple[int, int], g: float, h: float, parent: Optional['Node'] = None):
        self.pos = pos
        self.g = g  # Cost from start
        self.h = h  # Heuristic to goal
        self.f = g + h  # Total cost
        self.parent = parent
    
    def __lt__(self, other):
        return self.f < other.f

def heuristic(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
    """Manhattan distance heuristic"""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def reconstruct_path(node: Node) -> List[Tuple[int, int]]:
    """Reconstruct path from goal node to start"""
    path = []
    current = node
    while current:
        path.append(current.pos)
        current = current.parent
    return list(reversed(path))

def find_path(world: World, start: Tuple[int, int], goal: Tuple[int, int],
             entity: Entity = None, use_memory: bool = True) -> Optional[List[Tuple[int, int]]]:
    """
    Find path using A* algorithm
    
    Args:
        world: The game world
        start: Starting position (x, y)
        goal: Goal position (x, y)
        entity: The entity pathfinding (optional, for memory-based navigation)
        use_memory: If True and entity provided, only path through explored tiles
        
    Returns:
        List of positions from start to goal, or None if no path
    """
    if start == goal:
        return [start]
    
    if not world.is_passable(*goal):
        return None
    
    # Determine which tiles are valid for pathfinding
    if use_memory and entity:
        # Only path through remembered tiles
        valid_tiles = entity.remembered_tiles
    else:
        valid_tiles = None  # All passable tiles are valid
    
    open_set = []
    heapq.heappush(open_set, Node(start, 0, heuristic(start, goal)))
    
    closed_set = set()
    g_scores = {start: 0}
    
    while open_set:
        current = heapq.heappop(open_set)
        
        if current.pos == goal:
            return reconstruct_path(current)
        
        if current.pos in closed_set:
            continue
        
        closed_set.add(current.pos)
        
        # Explore neighbors
        for neighbor_pos in world.get_neighbors(*current.pos, passable_only=True):
            # Skip if using memory and tile not explored
            if valid_tiles is not None and neighbor_pos not in valid_tiles:
                continue
            
            # Check if occupied
            occupied_entity = world.get_entity_at(*neighbor_pos)
            
            # Calculate cost
            move_cost = 2.0 if world.is_difficult_terrain(*neighbor_pos) else 1.0
            
            # If occupied (and not the goal), add cost based on relationship
            if occupied_entity and neighbor_pos != goal:
                if entity and occupied_entity.team == entity.team:
                    # Ally: high cost to discourage, but allow pathing through
                    move_cost += 10.0
                else:
                    # Enemy: very high cost but still pathable (must fight through)
                    move_cost += 20.0
            
            tentative_g = current.g + move_cost
            
            if neighbor_pos in closed_set:
                if tentative_g >= g_scores.get(neighbor_pos, float('inf')):
                    continue
            
            if tentative_g < g_scores.get(neighbor_pos, float('inf')):
                g_scores[neighbor_pos] = tentative_g
                h = heuristic(neighbor_pos, goal)
                heapq.heappush(open_set, Node(neighbor_pos, tentative_g, h, current))
    
    return None  # No path found

def get_next_move(world: World, start: Tuple[int, int], goal: Tuple[int, int],
                 entity: Entity = None) -> Optional[Tuple[int, int]]:
    """
    Get the next position to move toward goal
    First tries memory-based pathfinding, falls back to exploring if that fails
    
    Returns:
        Next position to move to, or None if can't find path
    """
    # Try pathfinding through explored territory first
    if entity and entity.remembered_tiles:
        path = find_path(world, start, goal, entity, use_memory=True)
        if path and len(path) > 1:
            return path[1]  # Return next step
    
    # Fall back to exploring (don't require memory)
    path = find_path(world, start, goal, entity, use_memory=False)
    if path and len(path) > 1:
        return path[1]
    
    return None

def find_closest_unexplored(world: World, entity: Entity, search_radius: int = 20) -> Optional[Tuple[int, int]]:
    """
    Find the closest unexplored tile for scouting
    
    Args:
        world: The game world
        entity: The entity searching
        search_radius: Maximum distance to search
        
    Returns:
        Position of nearest unexplored tile, or None
    """
    best_pos = None
    best_distance = float('inf')
    
    # Search in a radius around the entity
    for dy in range(-search_radius, search_radius + 1):
        for dx in range(-search_radius, search_radius + 1):
            x = entity.x + dx
            y = entity.y + dy
            
            if not world.is_in_bounds(x, y):
                continue
            
            if not world.is_passable(x, y):
                continue
            
            # Check if unexplored
            if (x, y) not in entity.remembered_tiles:
                distance = abs(dx) + abs(dy)
                if distance < best_distance:
                    # Verify we can path to it
                    path = find_path(world, entity.position, (x, y), entity, use_memory=False)
                    if path:
                        best_pos = (x, y)
                        best_distance = distance
    
    return best_pos

def can_reach(world: World, start: Tuple[int, int], goal: Tuple[int, int],
             entity: Entity = None, max_distance: int = 50) -> bool:
    """
    Check if goal is reachable from start
    
    Args:
        world: The game world
        start: Starting position
        goal: Goal position
        entity: Entity (for memory-based pathfinding)
        max_distance: Maximum path length to consider
        
    Returns:
        True if reachable
    """
    path = find_path(world, start, goal, entity, use_memory=False)
    return path is not None and len(path) <= max_distance
