"""
Curriculum learning: Train in arena mode first, then switch to dungeon mode
This helps goblins learn pure combat tactics before adding navigation complexity
"""
import subprocess
import sys
import yaml
import shutil
from pathlib import Path

def update_config(arena_mode: bool):
    """Update config.yaml to enable/disable arena mode"""
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    config['simulation']['arena_mode'] = arena_mode
    
    with open('config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"Config updated: arena_mode = {arena_mode}")

def train_phase(phase_name: str, episodes: int, resume_from: str = None):
    """Run a training phase"""
    print(f"\n{'='*60}")
    print(f"PHASE: {phase_name}")
    print(f"Episodes: {episodes}")
    if resume_from:
        print(f"Resuming from: {resume_from}")
    print(f"{'='*60}\n")
    
    cmd = ['python', 'main.py', 'train', '--episodes', str(episodes)]
    if resume_from:
        cmd.extend(['--resume', resume_from])
    
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Training failed in phase: {phase_name}")
        sys.exit(1)
    
    print(f"\n{phase_name} complete!")

def main():
    """
    Curriculum learning schedule:
    1. Arena mode (100 episodes) - Learn combat tactics
    2. Dungeon mode (100 episodes) - Apply tactics to navigation
    """
    
    # Phase 1: Arena combat training
    print("\n🏟️  PHASE 1: ARENA COMBAT TRAINING")
    print("Goblins will learn pure combat tactics in a simple rectangular arena")
    update_config(arena_mode=True)
    train_phase("Arena Combat", episodes=100)
    
    # Find the latest checkpoint from arena training
    arena_checkpoint = "models/checkpoint_ep100.json"
    if not Path(arena_checkpoint).exists():
        print(f"Error: Arena checkpoint not found at {arena_checkpoint}")
        sys.exit(1)
    
    # Backup arena checkpoint
    shutil.copy(arena_checkpoint, "models/checkpoint_arena_final.json")
    print(f"\n✅ Arena training complete! Checkpoint saved to checkpoint_arena_final.json")
    
    # Phase 2: Dungeon navigation with combat
    print("\n🏰 PHASE 2: DUNGEON MODE")
    print("Goblins will apply combat tactics to complex dungeon navigation")
    update_config(arena_mode=False)
    train_phase("Dungeon Combat & Navigation", episodes=100, resume_from=arena_checkpoint)
    
    print("\n" + "="*60)
    print("🎉 CURRICULUM LEARNING COMPLETE!")
    print("="*60)
    print("\nCheckpoints saved:")
    print("  - checkpoint_arena_final.json (after arena training)")
    print("  - checkpoint_ep200.json (after dungeon training)")
    print("\nTest with: python main.py eval --model models/checkpoint_ep200.json --battles 1 --show")

if __name__ == '__main__':
    main()
