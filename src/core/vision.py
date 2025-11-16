"""
Line of Sight (LoS) calculations with allied vision sharing
"""
from typing import Set, Tuple, List
from src.core.entity import Entity, Team
from src.core.world import World

def calculate_los(entity: Entity, world: World) -> Set[Tuple[int, int]]:
    """
    Calculate line of sight for an entity
    Uses simple raycasting for visibility
    
    Returns:
        Set of (x, y) tuples that are visible
    """
    visible = set()
    cx, cy = entity.x, entity.y
    vision_range = entity.vision_range
    
    # Always see own position
    visible.add((cx, cy))
    
    # Cast rays in all directions
    for dx in range(-vision_range, vision_range + 1):
        for dy in range(-vision_range, vision_range + 1):
            if dx == 0 and dy == 0:
                continue
            
            target_x = cx + dx
            target_y = cy + dy
            
            # Check if target is within range
            distance = (dx * dx + dy * dy) ** 0.5
            if distance > vision_range:
                continue
            
            # Cast ray to this point
            if has_line_of_sight(world, cx, cy, target_x, target_y):
                visible.add((target_x, target_y))
    
    return visible

def has_line_of_sight(world: World, x1: int, y1: int, x2: int, y2: int) -> bool:
    """
    Check if there's line of sight between two points using Bresenham's algorithm
    Returns False if a wall blocks the view
    """
    # Bresenham's line algorithm
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    
    x, y = x1, y1
    
    while True:
        # Check if we've reached the target
        if x == x2 and y == y2:
            return True
        
        # Check if current position blocks vision (but not the starting position)
        if (x != x1 or y != y1) and not world.is_floor(x, y):
            return False
        
        # Move to next point
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

def update_entity_vision(entity: Entity, world: World, all_entities: List[Entity]):
    """
    Update an entity's vision including what they can see and what allies share
    """
    # Calculate own vision
    entity.visible_tiles = calculate_los(entity, world)
    
    # Find visible allies and enemies
    entity.visible_allies = []
    entity.visible_enemies = []
    
    for other in all_entities:
        if not other.alive or other == entity:
            continue
        
        if other.position in entity.visible_tiles:
            if other.team == entity.team:
                entity.visible_allies.append(other)
            else:
                entity.visible_enemies.append(other)

def update_shared_vision(entity: Entity, visited: Set[int] = None):
    """
    Recursively update vision by sharing with visible allies
    This allows transitive vision sharing: if A sees B and B sees C, then A can see C
    
    Args:
        entity: The entity whose vision to expand
        visited: Set of entity IDs already visited (prevents infinite recursion)
    """
    if visited is None:
        visited = set()
    
    if entity.id in visited:
        return
    
    visited.add(entity.id)
    
    # Share vision from all visible allies
    for ally in entity.visible_allies:
        # Add ally's visible tiles to our own
        entity.visible_tiles.update(ally.visible_tiles)
        
        # Add ally's visible enemies to our list (avoid duplicates)
        for enemy in ally.visible_enemies:
            if enemy not in entity.visible_enemies:
                entity.visible_enemies.append(enemy)
        
        # Recursively share from this ally's allies
        update_shared_vision(ally, visited)
        
        # After recursion, get any new tiles the ally might have gained
        entity.visible_tiles.update(ally.visible_tiles)

def update_all_vision(entities: List[Entity], world: World):
    """
    Update vision for all entities including shared vision
    
    Process:
    1. Calculate individual LoS for each entity
    2. Identify visible allies and enemies
    3. Share vision transitively through allied networks
    4. Update memory for each entity
    """
    # Step 1 & 2: Calculate individual vision
    for entity in entities:
        if entity.alive:
            update_entity_vision(entity, world, entities)
    
    # Step 3: Share vision through allied networks
    for entity in entities:
        if entity.alive:
            update_shared_vision(entity)
    
    # Step 4: Update memory
    for entity in entities:
        if entity.alive:
            entity.update_memory()

def get_visible_entities(entity: Entity, team: Team = None) -> List[Entity]:
    """
    Get all entities visible to this entity
    
    Args:
        entity: The viewing entity
        team: Filter by team (None = all, Team.KNIGHT, Team.GOBLIN)
    
    Returns:
        List of visible entities
    """
    if team is None:
        return entity.visible_allies + entity.visible_enemies
    elif team == entity.team:
        return entity.visible_allies
    else:
        return entity.visible_enemies
