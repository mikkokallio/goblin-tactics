"""
Dungeon generation using Binary Space Partitioning (BSP)
"""
import random
import numpy as np
from typing import List, Tuple, Set
from collections import deque

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
    
    def generate_arena(self) -> np.ndarray:
        """
        Generate a simple rectangular arena for combat training
        One big hall with grail and entrance on opposite random edges
        Perfect for learning pure combat tactics without navigation complexity
        Randomizes entrance/grail positions each time to avoid directional bias
        
        Returns:
            2D numpy array representing the arena
        """
        # Create one large rectangular room (leave 2-tile border for walls)
        hall_x = 2
        hall_y = 2
        hall_w = self.width - 4
        hall_h = self.height - 4
        
        # Carve out the hall
        for y in range(hall_y, hall_y + hall_h):
            for x in range(hall_x, hall_x + hall_w):
                self.map[y, x] = FLOOR
        
        # Store as single room for positioning logic
        self.rooms = [Rect(hall_x, hall_y, hall_w, hall_h)]
        
        # Randomly choose entrance side (0=left, 1=top, 2=right, 3=bottom)
        self.entrance_side = random.randint(0, 3)
        
        # Store entrance positions for spawning and visualization
        self.entrance_positions = []
        
        # Randomize entrance position along the edge (not always centered)
        # This creates variety in entrance-to-grail angles for better generalization
        if self.entrance_side == 0:  # Left
            # Random position along left edge (25%-75% of height)
            entrance_y = random.randint(self.height // 4, 3 * self.height // 4 - 1)
            self.map[entrance_y, 0] = FLOOR
            self.map[entrance_y, 1] = FLOOR
            self.map[entrance_y + 1, 0] = FLOOR
            self.map[entrance_y + 1, 1] = FLOOR
            self.entrance_positions = [(0, entrance_y), (1, entrance_y), 
                                       (0, entrance_y + 1), (1, entrance_y + 1),
                                       (2, entrance_y), (2, entrance_y + 1)]
        elif self.entrance_side == 1:  # Top
            # Random position along top edge (25%-75% of width)
            entrance_x = random.randint(self.width // 4, 3 * self.width // 4 - 1)
            self.map[0, entrance_x] = FLOOR
            self.map[1, entrance_x] = FLOOR
            self.map[0, entrance_x + 1] = FLOOR
            self.map[1, entrance_x + 1] = FLOOR
            self.entrance_positions = [(entrance_x, 0), (entrance_x, 1),
                                       (entrance_x + 1, 0), (entrance_x + 1, 1),
                                       (entrance_x, 2), (entrance_x + 1, 2)]
        elif self.entrance_side == 2:  # Right
            # Random position along right edge (25%-75% of height)
            entrance_y = random.randint(self.height // 4, 3 * self.height // 4 - 1)
            self.map[entrance_y, self.width - 1] = FLOOR
            self.map[entrance_y, self.width - 2] = FLOOR
            self.map[entrance_y + 1, self.width - 1] = FLOOR
            self.map[entrance_y + 1, self.width - 2] = FLOOR
            self.entrance_positions = [(self.width - 1, entrance_y), (self.width - 2, entrance_y),
                                       (self.width - 1, entrance_y + 1), (self.width - 2, entrance_y + 1),
                                       (self.width - 3, entrance_y), (self.width - 3, entrance_y + 1)]
        else:  # Bottom
            # Random position along bottom edge (25%-75% of width)
            entrance_x = random.randint(self.width // 4, 3 * self.width // 4 - 1)
            self.map[self.height - 1, entrance_x] = FLOOR
            self.map[self.height - 2, entrance_x] = FLOOR
            self.map[self.height - 1, entrance_x + 1] = FLOOR
            self.map[self.height - 2, entrance_x + 1] = FLOOR
            self.entrance_positions = [(entrance_x, self.height - 1), (entrance_x, self.height - 2),
                                       (entrance_x + 1, self.height - 1), (entrance_x + 1, self.height - 2),
                                       (entrance_x, self.height - 3), (entrance_x + 1, self.height - 3)]
        
        # Add randomized 2x2 pillar obstacles for tactical variety
        # This teaches goblins about walls, cover, and navigation
        num_pillars = 20  # Fixed number, randomly placed each time
        
        for _ in range(num_pillars):
            # Try to place pillar in valid location (not near entrance/grail/edges)
            attempts = 0
            while attempts < 20:
                # Random position with buffer from edges
                pillar_x = random.randint(hall_x + 3, hall_x + hall_w - 5)
                pillar_y = random.randint(hall_y + 3, hall_y + hall_h - 5)
                
                # Check if area is clear (no entrance positions nearby)
                area_clear = True
                for px in range(pillar_x, pillar_x + 2):
                    for py in range(pillar_y, pillar_y + 2):
                        # Check distance from entrance positions
                        for ex, ey in self.entrance_positions[:4]:  # Check first 4 entrance tiles
                            if abs(px - ex) < 4 and abs(py - ey) < 4:
                                area_clear = False
                                break
                        if not area_clear:
                            break
                    if not area_clear:
                        break
                
                if area_clear:
                    # Place 2x2 pillar
                    for px in range(pillar_x, pillar_x + 2):
                        for py in range(pillar_y, pillar_y + 2):
                            self.map[py, px] = WALL
                    break
                
                attempts += 1
        
        return self.map
        
    def generate(self, max_depth: int = 5, min_room_size: int = 4, 
                 max_room_size: int = 10, difficult_chance: float = 0.08,
                 create_entrance: bool = False, arena_mode: bool = False) -> np.ndarray:
        """
        Generate a dungeon or arena
        
        Args:
            max_depth: Maximum BSP tree depth (higher = more rooms/corridors)
            min_room_size: Minimum room dimension
            max_room_size: Maximum room dimension
            difficult_chance: Probability of difficult terrain on floor tiles
            create_entrance: If True, create a 2-tile wide entrance corridor on the left edge
            arena_mode: If True, generate simple rectangular arena instead of complex dungeon
            
        Returns:
            2D numpy array representing the dungeon
        """
        # Arena mode - simple rectangular hall
        if arena_mode:
            return self.generate_arena()
        
        # Create root node
        root = BSPNode(Rect(1, 1, self.width - 2, self.height - 2))
        
        # Build BSP tree
        self._split_node(root, max_depth, min_room_size)
        
        # Create rooms in leaf nodes
        self._create_rooms(root, min_room_size, max_room_size)
        
        # Connect rooms with corridors
        self._connect_rooms(root)
        
        # Create entrance corridor if requested
        if create_entrance:
            self._create_entrance_corridor()
        
        # Add difficult terrain
        self._add_difficult_terrain(difficult_chance)
        
        # Verify connectivity - if not connected, regenerate
        if not self._is_fully_connected():
            # Try again with a new seed
            return self.generate(max_depth, min_room_size, max_room_size, difficult_chance, create_entrance)
        
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
    
    def _create_entrance_corridor(self):
        """
        Create a 2-tile wide entrance corridor on the left edge.
        The entrance will be roughly centered vertically.
        """
        mid_y = self.height // 2
        entrance_y1 = mid_y - 1  # 2 tiles wide vertically
        entrance_y2 = mid_y + 1
        
        # Store entrance location for later reference
        self.entrance_positions = []
        
        # Carve from left edge (x=0) into the dungeon until we hit a floor tile
        for y in [entrance_y1, entrance_y2]:
            for x in range(self.width):
                self.map[y, x] = FLOOR
                self.entrance_positions.append((x, y))
                
                # Stop when we connect to existing dungeon
                # Check if we have floor tiles adjacent (indicating connection)
                if x > 5:  # Go at least 5 tiles in
                    adjacent_floor = False
                    for dy in [-1, 1]:
                        check_y = y + dy
                        if (0 <= check_y < self.height and 
                            check_y not in [entrance_y1, entrance_y2] and
                            self.map[check_y, x] == FLOOR):
                            adjacent_floor = True
                            break
                    if adjacent_floor:
                        break
    
    def get_entrance_positions(self) -> List[Tuple[int, int]]:
        """Get the entrance corridor positions (for spawning knights)"""
        if not hasattr(self, 'entrance_positions') or not self.entrance_positions:
            # Fallback: return positions near left edge
            mid_y = self.height // 2
            return [(1, mid_y - 1), (1, mid_y), (1, mid_y + 1), (2, mid_y - 1)]
        
        # Return first few positions of the entrance
        return self.entrance_positions[:6]
    
    def get_grail_position(self) -> Tuple[int, int]:
        """
        Get a position for the Holy Grail on the opposite edge from the entrance.
        Ensures grail and entrance are on opposite sides for strategic gameplay.
        In arena mode, places grail on opposite edge from entrance.
        In dungeon mode, falls back to opposite-side room placement.
        """
        # Arena mode: place grail on opposite edge from entrance
        if hasattr(self, 'entrance_side'):
            # Opposite sides: 0(left)↔2(right), 1(top)↔3(bottom)
            grail_side = (self.entrance_side + 2) % 4
            
            # Randomize position along the edge (25%-75%) to create varied diagonal paths
            if grail_side == 0:  # Left edge
                grail_x = 3
                grail_y = random.randint(self.height // 4, 3 * self.height // 4)
            elif grail_side == 1:  # Top edge
                grail_x = random.randint(self.width // 4, 3 * self.width // 4)
                grail_y = 3
            elif grail_side == 2:  # Right edge
                grail_x = self.width - 4
                grail_y = random.randint(self.height // 4, 3 * self.height // 4)
            else:  # Bottom edge
                grail_x = random.randint(self.width // 4, 3 * self.width // 4)
                grail_y = self.height - 4
            
            return (grail_x, grail_y)
        
        # Dungeon mode: Get rooms on the right third of the map
        right_rooms = [r for r in self.rooms if r.center[0] > 2 * self.width // 3]
        
        # If no rooms, expand search
        if not right_rooms:
            right_rooms = [r for r in self.rooms if r.center[0] > self.width // 2]
        
        if not right_rooms:
            # Ultimate fallback: rightmost floor tile
            for x in range(self.width - 1, 0, -1):
                for y in range(self.height):
                    if self.map[y, x] == FLOOR:
                        return (x, y)
        
        # Choose a random room on the right side
        room = random.choice(right_rooms)
        
        # Place grail in center of room
        return room.center
    
    def _is_fully_connected(self) -> bool:
        """
        Check if all floor tiles are reachable from any starting floor tile
        Uses flood fill algorithm
        """
        # Find first floor tile
        start_pos = None
        total_floor_tiles = 0
        
        for y in range(self.height):
            for x in range(self.width):
                if self.map[y, x] in [FLOOR, DIFFICULT]:
                    total_floor_tiles += 1
                    if start_pos is None:
                        start_pos = (x, y)
        
        if start_pos is None or total_floor_tiles == 0:
            return False
        
        # Flood fill from start position
        visited: Set[Tuple[int, int]] = set()
        queue = deque([start_pos])
        visited.add(start_pos)
        
        while queue:
            x, y = queue.popleft()
            
            # Check 4 adjacent tiles
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (0 <= nx < self.width and 0 <= ny < self.height and
                    (nx, ny) not in visited and
                    self.map[ny, nx] in [FLOOR, DIFFICULT]):
                    
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        
        # Check if all floor tiles were reached
        return len(visited) == total_floor_tiles
    
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
    
    def get_starting_positions(self, count: int, side: str = 'left', spread: bool = False) -> List[Tuple[int, int]]:
        """
        Get starting positions for units on one side of the map
        
        Args:
            count: Number of positions needed
            side: 'left' or 'right' side of the map
            spread: If True, spread units across multiple rooms (for goblins)
        """
        positions = []
        
        # Special handling for arena mode (single large room)
        if len(self.rooms) == 1:
            room = self.rooms[0]
            
            if side == 'left':
                # Knights: place in left third as usual
                x_min = room.x
                x_max = room.x + room.w // 3
                
                for i in range(count):
                    attempts = 0
                    while attempts < 100:
                        x = random.randint(x_min, x_max - 1)
                        y = random.randint(room.y, room.y2 - 1)
                        
                        if self.map[y, x] in [FLOOR, DIFFICULT] and (x, y) not in positions:
                            positions.append((x, y))
                            break
                        attempts += 1
            else:
                # Goblins: spread across ENTIRE arena except within 3 tiles of entrance
                # Entrance is on the left edge, centered vertically
                entrance_y = self.height // 2
                
                if spread:
                    # Maximum spacing algorithm for spread spawning
                    min_spacing = 12
                    
                    for i in range(count):
                        best_position = None
                        best_min_distance = 0
                        attempts_per_spawn = 50
                        
                        for attempt in range(attempts_per_spawn):
                            x = random.randint(room.x, room.x2 - 1)
                            y = random.randint(room.y, room.y2 - 1)
                            
                            # Exclude area within 3 tiles of entrance (left side)
                            if x < room.x + 3:
                                continue
                            
                            # Also exclude tiles too close to entrance vertically
                            if abs(y - entrance_y) < 2 and x < room.x + 5:
                                continue
                            
                            if self.map[y, x] not in [FLOOR, DIFFICULT] or (x, y) in positions:
                                continue
                            
                            # Calculate minimum distance to any existing goblin
                            if positions:
                                min_dist = min(abs(x - px) + abs(y - py) for px, py in positions)
                            else:
                                min_dist = float('inf')
                            
                            # Keep track of position with maximum minimum distance
                            if min_dist > best_min_distance:
                                best_min_distance = min_dist
                                best_position = (x, y)
                            
                            # If we found a position far enough away, use it immediately
                            if min_dist >= min_spacing:
                                best_position = (x, y)
                                break
                        
                        if best_position:
                            positions.append(best_position)
                else:
                    # Non-spread: just distribute across arena (not just right third)
                    for i in range(count):
                        attempts = 0
                        while attempts < 100:
                            x = random.randint(room.x, room.x2 - 1)
                            y = random.randint(room.y, room.y2 - 1)
                            
                            # Exclude entrance area
                            if x < room.x + 3:
                                continue
                            if abs(y - entrance_y) < 2 and x < room.x + 5:
                                continue
                            
                            if self.map[y, x] in [FLOOR, DIFFICULT] and (x, y) not in positions:
                                positions.append((x, y))
                                break
                            attempts += 1
            
            return positions
        
        # Normal dungeon mode: use rooms
        # Determine search area - use wider area for spreading to get more rooms
        if side == 'left':
            search_rooms = [r for r in self.rooms if r.center[0] < self.width // 3]
        else:
            # For right side with spread, use right HALF of map for more room options
            if spread:
                search_rooms = [r for r in self.rooms if r.center[0] >= self.width // 2]
            else:
                search_rooms = [r for r in self.rooms if r.center[0] > 2 * self.width // 3]
        
        # If no rooms in that third, expand search
        if not search_rooms:
            if side == 'left':
                search_rooms = [r for r in self.rooms if r.center[0] < self.width // 2]
            else:
                search_rooms = [r for r in self.rooms if r.center[0] >= self.width // 2]
        
        # Get positions from rooms
        if spread:
            # Spread units maximally across the search area
            # Strategy: divide area into grid cells and place max one goblin per cell
            available_rooms = search_rooms.copy()
            random.shuffle(available_rooms)
            
            # Create larger spacing by enforcing minimum distance of 12 tiles
            min_spacing = 12
            
            # First pass: place goblins with maximum spacing
            for i in range(count):
                best_position = None
                best_min_distance = 0
                attempts_per_room = 20
                
                # Try multiple rooms to find best position
                rooms_to_try = available_rooms[i % len(available_rooms):][:3]  # Try up to 3 rooms
                
                for room in rooms_to_try:
                    for attempt in range(attempts_per_room):
                        x = random.randint(room.x, room.x2 - 1)
                        y = random.randint(room.y, room.y2 - 1)
                        
                        if self.map[y, x] not in [FLOOR, DIFFICULT] or (x, y) in positions:
                            continue
                        
                        # Calculate minimum distance to any existing goblin
                        if positions:
                            min_dist = min(abs(x - px) + abs(y - py) for px, py in positions)
                        else:
                            min_dist = float('inf')
                        
                        # Keep track of position with maximum minimum distance
                        if min_dist > best_min_distance:
                            best_min_distance = min_dist
                            best_position = (x, y)
                        
                        # If we found a position far enough away, use it immediately
                        if min_dist >= min_spacing:
                            best_position = (x, y)
                            break
                    
                    if best_position and best_min_distance >= min_spacing:
                        break
                
                # Use best position found (even if not ideal)
                if best_position:
                    positions.append(best_position)
                elif len(available_rooms) > 0:
                    # Fallback: just place anywhere in a random room
                    room = random.choice(available_rooms)
                    for attempt in range(100):
                        x = random.randint(room.x, room.x2 - 1)
                        y = random.randint(room.y, room.y2 - 1)
                        if self.map[y, x] in [FLOOR, DIFFICULT] and (x, y) not in positions:
                            positions.append((x, y))
                            break
        else:
            # Original behavior: cluster in fewer rooms
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
