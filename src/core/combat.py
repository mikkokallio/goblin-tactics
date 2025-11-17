"""
Combat system - handles damage resolution and attacks
"""
from src.core.entity import Entity
from typing import Dict, Any

class CombatSystem:
    """Handles combat between entities"""
    
    def __init__(self):
        self.combat_log = []
    
    def attack(self, attacker: Entity, defender: Entity, world=None) -> Dict[str, Any]:
        """
        Execute an attack from attacker to defender
        
        Args:
            attacker: The attacking entity
            defender: The defending entity
            world: Optional world reference for pack tactics calculation
        
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
        
        # Pack tactics: +1 damage per adjacent ally of the same team
        pack_bonus = 0
        if world:
            adjacent_allies = world.get_adjacent_allies(attacker)
            pack_bonus = len(adjacent_allies)
            damage += pack_bonus
        
        # Directional bonus: +0 front, +1 side, +2 rear
        directional_bonus = 0
        attack_arc = defender.get_attack_arc(attacker)
        if attack_arc == 'side':
            directional_bonus = 1
        elif attack_arc == 'rear':
            directional_bonus = 2
        damage += directional_bonus
        
        # Update attacker facing to look at target
        attacker.update_facing_to_target(defender)
        
        # Apply damage
        actual_damage = defender.take_damage(damage)
        
        # Create result
        result = {
            'success': True,
            'attacker': attacker,
            'defender': defender,
            'damage': actual_damage,
            'pack_bonus': pack_bonus,
            'directional_bonus': directional_bonus,
            'attack_arc': attack_arc,
            'defender_killed': not defender.alive,
            'defender_hp': defender.hp
        }
        
        # Log combat
        self.combat_log.append(result)
        
        return result
    
    def get_combat_description(self, result: Dict[str, Any]) -> str:
        """Get a text description of combat result"""
        # Handle storm damage events
        if result.get('type') == 'storm_damage':
            desc = f"⚡ STORM damages {result['entity_type']}#{result['entity_id']} for {result['damage']} damage"
            if result.get('killed'):
                desc += " (KILLED!)"
            return desc
        
        # Handle grail pickup events
        if result.get('type') == 'grail_pickup':
            return f"🏆 {result['entity_type']}#{result['entity_id']} picked up the HOLY GRAIL!"
        
        # Handle regular combat
        if not result.get('success'):
            return f"Attack failed: {result.get('reason', 'unknown')}"
        
        attacker = result['attacker']
        defender = result['defender']
        damage = result['damage']
        pack_bonus = result.get('pack_bonus', 0)
        directional_bonus = result.get('directional_bonus', 0)
        attack_arc = result.get('attack_arc', 'front')
        defender_hp = result.get('defender_hp', 0)
        defender_max_hp = defender.max_hp if hasattr(defender, 'max_hp') else 0
        
        desc = f"{attacker.__class__.__name__}#{attacker.id} attacks {defender.__class__.__name__}#{defender.id} for {damage} damage"
        
        bonuses = []
        if pack_bonus > 0:
            bonuses.append(f"+{pack_bonus} pack")
        if directional_bonus > 0:
            bonuses.append(f"+{directional_bonus} {attack_arc}")
        
        if bonuses:
            desc += f" ({', '.join(bonuses)})"
        
        if result['defender_killed']:
            desc += " (KILLED!)"
        else:
            desc += f" ({defender_hp}/{defender_max_hp} HP remaining)"
        
        return desc
    
    def clear_log(self):
        """Clear the combat log"""
        self.combat_log = []
