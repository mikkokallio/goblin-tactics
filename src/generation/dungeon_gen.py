"""
Dungeon generation using Binary Space Partitioning (BSP)
"""
import random
import numpy as np
from typing import List, Tuple

# Terrain types
FLOOR = 0
WALL = 1
DIFFICULT = 2

class Rect:
    """Rectangle representing a region in the dungeon"""
    def __init__(self, x: int, y: int, w: int, h: int):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.w // 2, self.y + self.h // 2)
    
    @property
    def x2(self) -> int:
        return self.x + self.w
    
    @property
    def y2(self) -> int:
        return self.y + self.h
    
    def intersects(self, other: 'Rect') -> bool:
        """Check if this rectangle intersects with another"""
        return (self.x < other.x2 and self.x2 > other.x and
                self.y < other.y2 and self.y2 > other.y)

class BSPNode:
    """Node in the BSP tree"""
    def __init__(self, rect: Rect):
        self.rect = rect
        self.left = None
        self.right = None
        self.room = None  # Will be a Rect if this is a leaf with a room
    
    def split(self, min_size: int = 8, max_size: int = 20) -> bool:
        """
        Split this node into two children
        Returns True if split successful
        """
        # Already split
        if self.left or self.right:
            return False
        
        # Decide split direction based on aspect ratio
        split_horizontally = random.random() > 0.5
        
        if self.rect.w > self.rect.h and self.rect.w / self.rect.h >= 1.25:
            split_horizontally = False
        elif self.rect.h > self.rect.w and self.rect.h / self.rect.w >= 1.25:
            split_horizontally = True
        
        # Check if we can split
        max_split = (self.rect.h if split_horizontally else self.rect.w) - min_size
        
        if max_split <= min_size:
            return False  # Too small to split
        
        # Choose split position
        split_pos = random.randint(min_size, max_split)
        
        # Create child nodes
        if split_horizontally:
            self.left = BSPNode(Rect(self.rect.x, self.rect.y, self.rect.w, split_pos))
            self.right = BSPNode(Rect(self.rect.x, self.rect.y + split_pos, 
                                     self.rect.w, self.rect.h - split_pos))
        else:
            self.left = BSPNode(Rect(self.rect.x, self.rect.y, split_pos, self.rect.h))
            self.right = BSPNode(Rect(self.rect.x + split_pos, self.rect.y,
                                     self.rect.w - split_pos, self.rect.h))
        
        return True

class DungeonGenerator:
    """Generate dungeons using BSP algorithm"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.map = np.ones((height, width), dtype=np.int8) * WALL
        self.rooms: List[Rect] = []
        
    def generate(self, max_depth: int = 4, min_room_size: int = 5, 
                 max_room_size: int = 12, difficult_chance: float = 0.08) -> np.ndarray:
        """
        Generate a dungeon
        
        Args:
            max_depth: Maximum BSP tree depth
            min_room_size: Minimum room dimension
            max_room_size: Maximum room dimension
            difficult_chance: Probability of difficult terrain on floor tiles
            
        Returns:
            2D numpy array representing the dungeon
        """
        # Create root node
        root = BSPNode(Rect(1, 1, self.width - 2, self.height - 2))
        
        # Build BSP tree
        self._split_node(root, max_depth, min_room_size)
        
        # Create rooms in leaf nodes
        self._create_rooms(root, min_room_size, max_room_size)
        
        # Connect rooms with corridors
        self._connect_rooms(root)
        
        # Add difficult terrain
        self._add_difficult_terrain(difficult_chance)
        
        return self.map
    
    def _split_node(self, node: BSPNode, depth: int, min_size: int):
        """Recursively split BSP nodes"""
        if depth <= 0:
            return
        
        if node.split(min_size):
            self._split_node(node.left, depth - 1, min_size)
            self._split_node(node.right, depth - 1, min_size)
    
    def _create_rooms(self, node: BSPNode, min_size: int, max_size: int):
        """Create rooms in leaf nodes"""
        if node.left or node.right:
            # Not a leaf, recurse
            if node.left:
                self._create_rooms(node.left, min_size, max_size)
            if node.right:
                self._create_rooms(node.right, min_size, max_size)
        else:
            # Leaf node, create a room
            max_w = min(max_size, node.rect.w - 2)
            max_h = min(max_size, node.rect.h - 2)
            
            # Ensure we have valid range
            if max_w < min_size or max_h < min_size:
                return  # Can't create room, space too small
            
            w = random.randint(min_size, max_w)
            h = random.randint(min_size, max_h)
            x = node.rect.x + random.randint(1, max(1, node.rect.w - w - 1))
            y = node.rect.y + random.randint(1, max(1, node.rect.h - h - 1))
            
            room = Rect(x, y, w, h)
            node.room = room
            self.rooms.append(room)
            
            # Carve out the room
            self._carve_room(room)
    
    def _carve_room(self, room: Rect):
        """Carve out a room in the map"""
        for y in range(room.y, room.y2):
            for x in range(room.x, room.x2):
                if 0 <= y < self.height and 0 <= x < self.width:
                    self.map[y, x] = FLOOR
    
    def _connect_rooms(self, node: BSPNode):
        """Connect rooms with corridors"""
        if node.left and node.right:
            # Get centers of child nodes
            left_center = self._get_node_center(node.left)
            right_center = self._get_node_center(node.right)
            
            # Create corridor
            if left_center and right_center:
                self._carve_corridor(left_center, right_center)
            
            # Recurse
            self._connect_rooms(node.left)
            self._connect_rooms(node.right)
    
    def _get_node_center(self, node: BSPNode) -> Tuple[int, int]:
        """Get the center point of a node (or its room if it has one)"""
        if node.room:
            return node.room.center
        elif node.left and node.right:
            left_center = self._get_node_center(node.left)
            right_center = self._get_node_center(node.right)
            if left_center and right_center:
                return ((left_center[0] + right_center[0]) // 2,
                       (left_center[1] + right_center[1]) // 2)
        return node.rect.center
    
    def _carve_corridor(self, start: Tuple[int, int], end: Tuple[int, int]):
        """Carve an L-shaped corridor between two points"""
        x1, y1 = start
        x2, y2 = end
        
        # Randomly choose horizontal-then-vertical or vertical-then-horizontal
        if random.random() < 0.5:
            # Horizontal then vertical
            self._carve_horizontal_tunnel(x1, x2, y1)
            self._carve_vertical_tunnel(y1, y2, x2)
        else:
            # Vertical then horizontal
            self._carve_vertical_tunnel(y1, y2, x1)
            self._carve_horizontal_tunnel(x1, x2, y2)
    
    def _carve_horizontal_tunnel(self, x1: int, x2: int, y: int):
        """Carve a horizontal corridor"""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= y < self.height and 0 <= x < self.width:
                self.map[y, x] = FLOOR
    
    def _carve_vertical_tunnel(self, y1: int, y2: int, x: int):
        """Carve a vertical corridor"""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= y < self.height and 0 <= x < self.width:
                self.map[y, x] = FLOOR
    
    def _add_difficult_terrain(self, chance: float):
        """Add difficult terrain to some floor tiles"""
        for y in range(self.height):
            for x in range(self.width):
                if self.map[y, x] == FLOOR and random.random() < chance:
                    self.map[y, x] = DIFFICULT
    
    def get_random_floor_position(self, exclude_difficult: bool = False) -> Tuple[int, int]:
        """Get a random floor position"""
        attempts = 0
        while attempts < 1000:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            
            if exclude_difficult:
                if self.map[y, x] == FLOOR:
                    return (x, y)
            else:
                if self.map[y, x] in [FLOOR, DIFFICULT]:
                    return (x, y)
            
            attempts += 1
        
        # Fallback: find any floor tile
        for y in range(self.height):
            for x in range(self.width):
                if self.map[y, x] in [FLOOR, DIFFICULT]:
                    return (x, y)
        
        raise Exception("No floor tiles found in dungeon!")
    
    def get_starting_positions(self, count: int, side: str = 'left') -> List[Tuple[int, int]]:
        """
        Get starting positions for units on one side of the map
        
        Args:
            count: Number of positions needed
            side: 'left' or 'right' side of the map
        """
        positions = []
        
        # Determine search area
        if side == 'left':
            search_rooms = [r for r in self.rooms if r.center[0] < self.width // 3]
        else:
            search_rooms = [r for r in self.rooms if r.center[0] > 2 * self.width // 3]
        
        # If no rooms in that third, expand search
        if not search_rooms:
            if side == 'left':
                search_rooms = [r for r in self.rooms if r.center[0] < self.width // 2]
            else:
                search_rooms = [r for r in self.rooms if r.center[0] >= self.width // 2]
        
        # Get positions from rooms
        attempts = 0
        while len(positions) < count and attempts < 1000:
            room = random.choice(search_rooms)
            x = random.randint(room.x, room.x2 - 1)
            y = random.randint(room.y, room.y2 - 1)
            
            if self.map[y, x] in [FLOOR, DIFFICULT] and (x, y) not in positions:
                positions.append((x, y))
            
            attempts += 1
        
        return positions

def generate_dungeon(width: int, height: int, **kwargs) -> Tuple[np.ndarray, List[Rect]]:
    """
    Convenience function to generate a dungeon
    
    Returns:
        (map_array, list_of_rooms)
    """
    gen = DungeonGenerator(width, height)
    dungeon_map = gen.generate(**kwargs)
    return dungeon_map, gen.rooms
