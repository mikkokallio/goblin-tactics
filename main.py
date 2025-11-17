#!/usr/bin/env python3
"""
Goblin Tactics - Main entry point
"""
import argparse
import yaml
from pathlib import Path

def load_config():
    """Load configuration from config.yaml"""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def run_single_battle(config, show=True):
    """Run a single battle with visualization"""
    from src.simulation.battle import Battle
    from src.display.renderer import Renderer
    
    battle = Battle(config, battle_id=0, record=True)
    renderer = Renderer(config) if show else None
    
    print("Starting single battle...")
    result = battle.run(renderer=renderer)
    
    print(f"\n{'='*50}")
    print(f"Battle Result: {result['winner']} wins!")
    print(f"Turns: {result['turns']}")
    print(f"Knights remaining: {result['knights_remaining']}/{config['knights']['count']}")
    print(f"Goblins remaining: {result['goblins_remaining']}")
    print(f"Battle data saved to: data/battles/battle_00000.json")
    print(f"{'='*50}")
    
    return result

def run_training(config, episodes, resume_from=None):
    """Run training for goblin AI"""
    from src.simulation.battle import Battle
    from src.ai.learning import DQNAgent, state_dict_to_vector, NUM_ACTIONS
    from src.simulation.recorder import create_state_representation
    import numpy as np
    import os
    
    print(f"Starting training for {episodes} episodes...")
    print("Using NumPy-based Deep Q-Network\n")
    
    # Calculate state size (from state representation)
    # 2 pos + 17 stats (pack, facing, directional, flanking) + 16 sectors (8 allies + 8 enemies) + 25 terrain + 2 (in_zone, turn) + 6 grail = 68
    state_size = 68
    
    # Initialize agent
    agent = DQNAgent(state_size, NUM_ACTIONS, config['learning'])
    
    # Load previous weights if resuming
    if resume_from:
        if os.path.exists(resume_from):
            print(f"Resuming training from: {resume_from}")
            agent.load(resume_from)
            
            # Try to load stats too
            stats_path = resume_from.replace('.json', '_stats.json')
            if os.path.exists(stats_path):
                import json
                with open(stats_path, 'r') as f:
                    stats = json.load(f)
                agent.episode = stats.get('episode', 0)
                agent.epsilon = stats.get('epsilon', agent.epsilon)
                agent.total_steps = stats.get('total_steps', 0)
                print(f"  Loaded stats: episode {agent.episode}, epsilon {agent.epsilon:.3f}")
        else:
            print(f"Warning: Resume file not found: {resume_from}")
            print("Starting from scratch...")
    
    # Training stats
    wins = 0
    losses = 0
    total_rewards = []
    
    for episode in range(episodes):
        # Create battle
        battle = Battle(config, battle_id=episode, record=False,
                       goblin_agent=agent, training=True)
        
        # Run battle without rendering
        result = battle.run(renderer=None, delay=0)
        
        # Update stats
        if result['winner'] == 'Goblins':
            wins += 1
        else:
            losses += 1
        
        # End episode (update target network, decay epsilon)
        agent.end_episode()
        
        # Train on accumulated experiences
        for _ in range(10):  # Multiple training steps per episode
            agent.train_step()
        
        # Print progress
        if (episode + 1) % 10 == 0:
            win_rate = wins / (episode + 1) * 100
            print(f"Episode {episode + 1}/{episodes} | "
                  f"Win Rate: {win_rate:.1f}% | "
                  f"Epsilon: {agent.epsilon:.3f} | "
                  f"Wins: {wins} | Losses: {losses}")
            
            # Save checkpoint every 10 episodes
            checkpoint_path = f"models/checkpoint_ep{episode + 1}.json"
            agent.save(checkpoint_path)
            print(f"  Saved checkpoint: {checkpoint_path}")
    
    # Save final model
    final_path = "models/goblin_dqn_final.json"
    agent.save(final_path)
    print(f"\nTraining complete!")
    print(f"Final win rate: {wins / episodes * 100:.1f}%")
    print(f"Model saved to: {final_path}")

def run_evaluation(config, model_path, battles, show=None):
    """Evaluate a trained model"""
    from src.simulation.battle import Battle
    from src.ai.learning import DQNAgent, NUM_ACTIONS
    from src.display.renderer import Renderer
    
    print(f"Loading model from {model_path}...")
    
    # Initialize agent and load model
    state_size = 68  # Updated with flanking + 8-sector awareness
    agent = DQNAgent(state_size, NUM_ACTIONS, config['learning'])
    agent.load(model_path)
    agent.epsilon = 0.0  # No exploration during evaluation
    
    print(f"Running {battles} evaluation battles...\n")
    
    wins = 0
    total_turns = []
    
    for i in range(battles):
        battle = Battle(config, battle_id=i, record=False,
                       goblin_agent=agent, training=False)
        
        # Show battles if explicitly requested or if only a few battles
        show_this = show if show is not None else (battles <= 5)
        renderer = Renderer(config) if show_this else None
        
        result = battle.run(renderer=renderer, delay=0.05 if show_this else 0)
        
        if result['winner'] == 'Goblins':
            wins += 1
        
        total_turns.append(result['turns'])
        
        print(f"Battle {i+1}/{battles}: {result['winner']} wins in {result['turns']} turns")
    
    print(f"\n{'='*50}")
    print(f"Evaluation Results:")
    print(f"  Win Rate: {wins / battles * 100:.1f}%")
    print(f"  Avg Turns: {sum(total_turns) / len(total_turns):.1f}")
    print(f"{'='*50}")
    
    # Show directive usage statistics if available
    if hasattr(battle, 'goblin_ai') and hasattr(battle.goblin_ai, 'print_directive_statistics'):
        battle.goblin_ai.print_directive_statistics()

def main():
    parser = argparse.ArgumentParser(description='Goblin Tactics Simulation')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Battle command
    battle_parser = subparsers.add_parser('battle', help='Run a single battle')
    battle_parser.add_argument('--show', action='store_true', help='Show visualization')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train goblin AI')
    train_parser.add_argument('--episodes', type=int, default=1000, help='Number of training episodes')
    train_parser.add_argument('--resume', type=str, help='Resume from checkpoint (path to model file)')
    
    # Eval command
    eval_parser = subparsers.add_parser('eval', help='Evaluate trained model')
    eval_parser.add_argument('--model', type=str, required=True, help='Path to model checkpoint')
    eval_parser.add_argument('--battles', type=int, default=10, help='Number of battles to run')
    eval_parser.add_argument('--show', action='store_true', help='Show battle visualization')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Execute command
    if args.command == 'battle':
        run_single_battle(config, show=args.show)
    elif args.command == 'train':
        run_training(config, args.episodes, resume_from=args.resume)
    elif args.command == 'eval':
        run_evaluation(config, args.model, args.battles, show=args.show)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
