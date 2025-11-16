"""
Colored ASCII renderer for the dungeon and entities
"""
import os
from colorama import Fore, Back, Style, init
from typing import List, Optional
from src.core.world import World
from src.core.entity import Entity, Team
from src.generation.dungeon_gen import FLOOR, WALL, DIFFICULT

# Initialize colorama
init(autoreset=True)

class Renderer:
    """Renders the game state to terminal with colors"""
    
    def __init__(self, config: dict):
        self.config = config
        self.colors_enabled = config['display'].get('colors_enabled', True)
        self.show_vision = config['display'].get('show_vision', False)
        
    def render(self, world: World, entities: List[Entity], turn: int, 
               combat_log: List[str] = None):
        """Render the complete game state"""
        # Clear screen (Windows and Unix compatible)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Print header
        self._print_header(turn, entities)
        
        # Print map
        self._print_map(world, entities)
        
        # Print combat log
        if combat_log:
            self._print_combat_log(combat_log)
        
        # Print stats
        self._print_stats(entities)
    
    def _print_header(self, turn: int, entities: List[Entity]):
        """Print battle header"""
        knights = [e for e in entities if e.team == Team.KNIGHT and e.alive]
        goblins = [e for e in entities if e.team == Team.GOBLIN and e.alive]
        
        print(f"{Style.BRIGHT}{'='*60}")
        print(f"  GOBLIN TACTICS - Turn {turn}")
        print(f"  {self._colorize('Knights', 'cyan')}: {len(knights)}  " +
              f"{self._colorize('Goblins', 'green')}: {len(goblins)}")
        print(f"{'='*60}{Style.RESET_ALL}\n")
    
    def _print_map(self, world: World, entities: List[Entity]):
        """Print the dungeon map with entities"""
        # Create entity position lookup
        entity_map = {e.position: e for e in entities if e.alive}
        
        # Print map
        for y in range(world.height):
            line = ""
            for x in range(world.width):
                # Check for entity
                if (x, y) in entity_map:
                    entity = entity_map[(x, y)]
                    line += self._get_entity_char(entity)
                else:
                    # Get terrain
                    line += self._get_terrain_char(world, x, y)
            print(line)
        print()
    
    def _get_terrain_char(self, world: World, x: int, y: int) -> str:
        """Get colored character for terrain"""
        if not world.is_in_bounds(x, y):
            return ' '
        
        terrain = world.map[y, x]
        
        if terrain == WALL:
            return self._colorize('#', 'white')
        elif terrain == FLOOR:
            return self._colorize('.', 'dark_gray')
        elif terrain == DIFFICULT:
            return self._colorize('~', 'yellow')
        else:
            return self._colorize('?', 'magenta')
    
    def _get_entity_char(self, entity: Entity) -> str:
        """Get colored character for entity"""
        symbol = entity.symbol
        
        # Color based on team and health
        if entity.team == Team.KNIGHT:
            color = 'cyan'
        else:  # Goblin
            # Vary green shade based on health
            hp_percent = entity.hp / entity.max_hp
            if hp_percent > 0.7:
                color = 'green'
            elif hp_percent > 0.3:
                color = 'yellow'
            else:
                color = 'red'
        
        return self._colorize(symbol, color, bright=True)
    
    def _print_combat_log(self, combat_log: List[str]):
        """Print recent combat events"""
        if not combat_log:
            return
        
        print(f"{Style.BRIGHT}Recent Combat:{Style.RESET_ALL}")
        for log_entry in combat_log[-5:]:  # Last 5 entries
            print(f"  {log_entry}")
        print()
    
    def _print_stats(self, entities: List[Entity]):
        """Print entity statistics"""
        knights = [e for e in entities if e.team == Team.KNIGHT and e.alive]
        goblins = [e for e in entities if e.team == Team.GOBLIN and e.alive]
        
        print(f"{Style.BRIGHT}Knights:{Style.RESET_ALL}")
        for knight in knights:
            hp_bar = self._get_hp_bar(knight)
            print(f"  K#{knight.id}: {hp_bar} {knight.hp}/{knight.max_hp} HP")
        
        print(f"\n{Style.BRIGHT}Goblins:{Style.RESET_ALL}")
        for goblin in goblins[:10]:  # Show first 10
            hp_bar = self._get_hp_bar(goblin)
            print(f"  g#{goblin.id}: {hp_bar} {goblin.hp}/{goblin.max_hp} HP")
        
        if len(goblins) > 10:
            print(f"  ... and {len(goblins) - 10} more goblins")
    
    def _get_hp_bar(self, entity: Entity, width: int = 10) -> str:
        """Get colored HP bar"""
        hp_percent = entity.hp / entity.max_hp
        filled = int(hp_percent * width)
        empty = width - filled
        
        # Color based on HP
        if hp_percent > 0.7:
            color = 'green'
        elif hp_percent > 0.3:
            color = 'yellow'
        else:
            color = 'red'
        
        bar = self._colorize('█' * filled, color) + self._colorize('░' * empty, 'dark_gray')
        return f"[{bar}]"
    
    def _colorize(self, text: str, color: str, bright: bool = False) -> str:
        """Apply color to text"""
        if not self.colors_enabled:
            return text
        
        color_map = {
            'cyan': Fore.CYAN,
            'green': Fore.GREEN,
            'yellow': Fore.YELLOW,
            'red': Fore.RED,
            'white': Fore.WHITE,
            'dark_gray': Fore.LIGHTBLACK_EX,
            'magenta': Fore.MAGENTA,
        }
        
        color_code = color_map.get(color, Fore.WHITE)
        style = Style.BRIGHT if bright else ''
        
        return f"{style}{color_code}{text}{Style.RESET_ALL}"
    
    def render_victory(self, winner: str, turns: int, knights_remaining: int, 
                      goblins_remaining: int):
        """Render victory screen"""
        print(f"\n{Style.BRIGHT}{'='*60}")
        print(f"  BATTLE COMPLETE!")
        print(f"  Winner: {self._colorize(winner.upper(), 'yellow', bright=True)}")
        print(f"  Turns: {turns}")
        print(f"  Knights Remaining: {knights_remaining}")
        print(f"  Goblins Remaining: {goblins_remaining}")
        print(f"{'='*60}{Style.RESET_ALL}\n")

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')
