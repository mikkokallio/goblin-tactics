"""
Combat system - handles damage resolution and attacks
"""
from src.core.entity import Entity
from typing import Dict, Any

class CombatSystem:
    """Handles combat between entities"""
    
    def __init__(self):
        self.combat_log = []
    
    def attack(self, attacker: Entity, defender: Entity) -> Dict[str, Any]:
        """
        Execute an attack from attacker to defender
        
        Returns:
            Dictionary with combat result information
        """
        if not attacker.alive or not defender.alive:
            return {
                'success': False,
                'reason': 'dead_combatant'
            }
        
        if not attacker.is_adjacent(defender):
            return {
                'success': False,
                'reason': 'not_adjacent'
            }
        
        # Roll damage
        damage = attacker.deal_damage()
        
        # Apply damage
        actual_damage = defender.take_damage(damage)
        
        # Create result
        result = {
            'success': True,
            'attacker': attacker,
            'defender': defender,
            'damage': actual_damage,
            'defender_killed': not defender.alive,
            'defender_hp': defender.hp
        }
        
        # Log combat
        self.combat_log.append(result)
        
        return result
    
    def get_combat_description(self, result: Dict[str, Any]) -> str:
        """Get a text description of combat result"""
        if not result['success']:
            return f"Attack failed: {result.get('reason', 'unknown')}"
        
        attacker = result['attacker']
        defender = result['defender']
        damage = result['damage']
        
        desc = f"{attacker.__class__.__name__}#{attacker.id} attacks {defender.__class__.__name__}#{defender.id} for {damage} damage"
        
        if result['defender_killed']:
            desc += " (KILLED!)"
        else:
            desc += f" ({defender.hp}/{defender.max_hp} HP remaining)"
        
        return desc
    
    def clear_log(self):
        """Clear the combat log"""
        self.combat_log = []
