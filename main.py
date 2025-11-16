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
    
    battle = Battle(config)
    renderer = Renderer(config) if show else None
    
    print("Starting single battle...")
    result = battle.run(renderer=renderer)
    
    print(f"\n{'='*50}")
    print(f"Battle Result: {result['winner']} wins!")
    print(f"Turns: {result['turns']}")
    print(f"Knights remaining: {result['knights_remaining']}/{config['knights']['count']}")
    print(f"Goblins remaining: {result['goblins_remaining']}")
    print(f"{'='*50}")
    
    return result

def run_training(config, episodes):
    """Run training for goblin AI"""
    print(f"Training not yet implemented. Would run {episodes} episodes.")
    # TODO: Implement training loop

def run_evaluation(config, model_path, battles):
    """Evaluate a trained model"""
    print(f"Evaluation not yet implemented. Would run {battles} battles with {model_path}.")
    # TODO: Implement evaluation

def main():
    parser = argparse.ArgumentParser(description='Goblin Tactics Simulation')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Battle command
    battle_parser = subparsers.add_parser('battle', help='Run a single battle')
    battle_parser.add_argument('--show', action='store_true', help='Show visualization')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train goblin AI')
    train_parser.add_argument('--episodes', type=int, default=1000, help='Number of training episodes')
    
    # Eval command
    eval_parser = subparsers.add_parser('eval', help='Evaluate trained model')
    eval_parser.add_argument('--model', type=str, required=True, help='Path to model checkpoint')
    eval_parser.add_argument('--battles', type=int, default=10, help='Number of battles to run')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Execute command
    if args.command == 'battle':
        run_single_battle(config, show=args.show)
    elif args.command == 'train':
        run_training(config, args.episodes)
    elif args.command == 'eval':
        run_evaluation(config, args.model, args.battles)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
