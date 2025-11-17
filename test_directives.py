"""
Quick test of the directive system
"""
import sys
sys.path.append('.')

from src.ai.directives import (
    calculate_directive_target,
    calculate_movement_from_directive,
    DIR_TOWARD_NEAREST_ENEMY,
    DIR_TOWARD_GRAIL,
    DIR_AWAY_FROM_ENEMIES,
    DIRECTIVE_NAMES,
    NUM_DIRECTIVES
)

print(f"✅ Directive system loaded successfully!")
print(f"📊 Total directives: {NUM_DIRECTIVES}")
print(f"\n📋 Available directives:")
for i in range(NUM_DIRECTIVES):
    if i in DIRECTIVE_NAMES:
        print(f"  {i}: {DIRECTIVE_NAMES[i]}")

print(f"\n✨ Directive system ready for training!")
