"""
Simple NumPy-based Deep Q-Network implementation
No PyTorch/TensorFlow required!
"""
import numpy as np
import json
from pathlib import Path
from typing import List, Tuple, Dict
import random
from collections import deque

class DenseLayer:
    """Fully connected layer with activation"""
    
    def __init__(self, input_size: int, output_size: int, activation='relu'):
        # Xavier initialization
        limit = np.sqrt(6 / (input_size + output_size))
        self.weights = np.random.uniform(-limit, limit, (input_size, output_size))
        self.bias = np.zeros(output_size)
        self.activation = activation
        
        # For backprop
        self.input = None
        self.output = None
        
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass"""
        self.input = x
        z = np.dot(x, self.weights) + self.bias
        
        if self.activation == 'relu':
            self.output = np.maximum(0, z)
        elif self.activation == 'linear':
            self.output = z
        else:
            raise ValueError(f"Unknown activation: {self.activation}")
        
        return self.output
    
    def backward(self, grad: np.ndarray, learning_rate: float) -> np.ndarray:
        """Backward pass with gradient descent"""
        # Activation gradient
        if self.activation == 'relu':
            grad = grad * (self.output > 0)
        
        # Compute gradients
        grad_weights = np.dot(self.input.T, grad)
        grad_bias = np.sum(grad, axis=0)
        grad_input = np.dot(grad, self.weights.T)
        
        # Update weights
        self.weights -= learning_rate * grad_weights
        self.bias -= learning_rate * grad_bias
        
        return grad_input

class SimpleNN:
    """Simple feedforward neural network"""
    
    def __init__(self, input_size: int, hidden_sizes: List[int], output_size: int):
        self.layers = []
        
        # Input to first hidden
        prev_size = input_size
        for hidden_size in hidden_sizes:
            self.layers.append(DenseLayer(prev_size, hidden_size, 'relu'))
            prev_size = hidden_size
        
        # Last hidden to output (linear activation for Q-values)
        self.layers.append(DenseLayer(prev_size, output_size, 'linear'))
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass through network"""
        for layer in self.layers:
            x = layer.forward(x)
        return x
    
    def backward(self, grad: np.ndarray, learning_rate: float):
        """Backward pass through network"""
        for layer in reversed(self.layers):
            grad = layer.backward(grad, learning_rate)
    
    def predict(self, x: np.ndarray) -> np.ndarray:
        """Predict without storing gradients"""
        return self.forward(x)
    
    def copy_weights_from(self, other: 'SimpleNN'):
        """Copy weights from another network (for target network)"""
        for self_layer, other_layer in zip(self.layers, other.layers):
            self_layer.weights = other_layer.weights.copy()
            self_layer.bias = other_layer.bias.copy()
    
    def save(self, path: str):
        """Save network weights"""
        weights = []
        for layer in self.layers:
            weights.append({
                'weights': layer.weights.tolist(),
                'bias': layer.bias.tolist()
            })
        
        with open(path, 'w') as f:
            json.dump(weights, f)
    
    def load(self, path: str):
        """Load network weights"""
        with open(path, 'r') as f:
            weights = json.load(f)
        
        for layer, weight_dict in zip(self.layers, weights):
            layer.weights = np.array(weight_dict['weights'])
            layer.bias = np.array(weight_dict['bias'])

class ReplayBuffer:
    """Experience replay buffer"""
    
    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)
    
    def add(self, state, action, reward, next_state, done):
        """Add experience to buffer"""
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size: int) -> Tuple:
        """Sample random batch"""
        batch = random.sample(self.buffer, min(batch_size, len(self.buffer)))
        
        states = np.array([exp[0] for exp in batch])
        actions = np.array([exp[1] for exp in batch])
        rewards = np.array([exp[2] for exp in batch])
        next_states = np.array([exp[3] for exp in batch])
        dones = np.array([exp[4] for exp in batch])
        
        return states, actions, rewards, next_states, dones
    
    def __len__(self):
        return len(self.buffer)

class DQNAgent:
    """Deep Q-Network agent for goblin learning"""
    
    def __init__(self, state_size: int, action_size: int, config: dict):
        self.state_size = state_size
        self.action_size = action_size
        
        # Hyperparameters
        self.gamma = config.get('gamma', 0.99)
        self.epsilon = config.get('epsilon_start', 1.0)
        self.epsilon_min = config.get('epsilon_end', 0.01)
        self.epsilon_decay = config.get('epsilon_decay', 0.995)
        self.learning_rate = config.get('learning_rate', 0.001)
        self.batch_size = config.get('batch_size', 64)
        self.target_update = config.get('target_update', 10)
        
        # Networks
        hidden_sizes = [128, 64]
        self.q_network = SimpleNN(state_size, hidden_sizes, action_size)
        self.target_network = SimpleNN(state_size, hidden_sizes, action_size)
        self.target_network.copy_weights_from(self.q_network)
        
        # Experience replay
        self.memory = ReplayBuffer(config.get('memory_size', 10000))
        
        # Training stats
        self.episode = 0
        self.total_steps = 0
    
    def get_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        Choose action using epsilon-greedy policy
        
        Args:
            state: Current state observation
            training: If False, always use greedy policy
        """
        if training and random.random() < self.epsilon:
            return random.randint(0, self.action_size - 1)
        
        q_values = self.q_network.predict(state.reshape(1, -1))
        return np.argmax(q_values[0])
    
    def train_step(self):
        """Perform one training step"""
        if len(self.memory) < self.batch_size:
            return
        
        # Sample batch
        states, actions, rewards, next_states, dones = self.memory.sample(self.batch_size)
        
        # Compute Q-values
        current_q = self.q_network.forward(states)
        next_q = self.target_network.predict(next_states)
        
        # Compute target Q-values
        target_q = current_q.copy()
        for i in range(self.batch_size):
            if dones[i]:
                target_q[i, actions[i]] = rewards[i]
            else:
                target_q[i, actions[i]] = rewards[i] + self.gamma * np.max(next_q[i])
        
        # Compute loss gradient (MSE)
        grad = 2 * (current_q - target_q) / self.batch_size
        
        # Backpropagate
        self.q_network.backward(grad, self.learning_rate)
        
        self.total_steps += 1
    
    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay buffer"""
        self.memory.add(state, action, reward, next_state, done)
    
    def update_target_network(self):
        """Copy weights from Q-network to target network"""
        self.target_network.copy_weights_from(self.q_network)
    
    def decay_epsilon(self):
        """Decay exploration rate"""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    def end_episode(self):
        """Call at end of episode"""
        self.episode += 1
        
        # Update target network periodically
        if self.episode % self.target_update == 0:
            self.update_target_network()
        
        # Decay epsilon
        self.decay_epsilon()
    
    def save(self, path: str):
        """Save agent"""
        self.q_network.save(path)
        
        # Save training stats
        stats_path = path.replace('.json', '_stats.json')
        with open(stats_path, 'w') as f:
            json.dump({
                'episode': self.episode,
                'epsilon': self.epsilon,
                'total_steps': self.total_steps
            }, f)
    
    def load(self, path: str):
        """Load agent"""
        self.q_network.load(path)
        self.target_network.copy_weights_from(self.q_network)
        
        # Load training stats
        stats_path = path.replace('.json', '_stats.json')
        if Path(stats_path).exists():
            with open(stats_path, 'r') as f:
                stats = json.load(f)
                self.episode = stats['episode']
                self.epsilon = stats['epsilon']
                self.total_steps = stats['total_steps']

def state_dict_to_vector(state: Dict) -> np.ndarray:
    """Convert state dictionary to flat numpy array"""
    vector = []
    
    # Position (2)
    vector.extend(state['position'])
    
    # HP and tactical stats (17) - added flanking position awareness
    vector.append(state['hp_percentage'])
    vector.append(state['num_visible_allies'] / 20.0)  # Normalize
    vector.append(state['num_visible_enemies'] / 4.0)  # Normalize
    vector.append(state.get('pack_allies_count', 0.0))  # Pack tactics feature - already normalized
    vector.append(state.get('facing', 0.0))  # Facing direction - already normalized
    vector.append(state.get('enemies_in_front', 0.0))  # Directional threats - already normalized
    vector.append(state.get('enemies_on_sides', 0.0))
    vector.append(state.get('enemies_behind', 0.0))
    # NEW: Tactical position relative to enemies (for flanking rewards)
    vector.append(state.get('attacking_from_behind', 0.0))  # Am I backstabbing?
    vector.append(state.get('attacking_from_sides', 0.0))   # Am I flanking?
    vector.append(state.get('attacking_from_front', 0.0))   # Am I in direct combat?
    vector.append(state['distance_to_nearest_ally'])
    vector.append(state['distance_to_nearest_enemy'])
    vector.append(state['nearest_enemy_hp'])
    vector.append(state['allies_within_3'])  # Already normalized
    vector.append(state['enemies_within_3'])  # Already normalized
    vector.append(state['explored_percentage'])  # Added back
    
    # Sector awareness (16) - 8 sectors for allies, 8 for enemies
    sector_allies = state.get('sector_allies', [0.0] * 8)
    sector_enemies = state.get('sector_enemies', [0.0] * 8)
    vector.extend(sector_allies)   # N, NE, E, SE, S, SW, W, NW ally presence
    vector.extend(sector_enemies)  # N, NE, E, SE, S, SW, W, NW enemy presence
    
    # Terrain grid (25) - normalized to 0-1 (now includes storm as value 5)
    terrain = np.array(state['terrain_grid']) / 5.0
    vector.extend(terrain)
    
    # Safe zone and turn (2)  
    vector.append(state['in_safe_zone'])
    vector.append(min(state['turn_count'] / 200.0, 1.0))  # Normalize
    
    # Grail mode features (6) - new for defensive tactics
    vector.append(state.get('grail_location_known', 0.0))
    vector.append(state.get('distance_to_grail', 1.0))  # Already normalized
    vector.append(state.get('grail_carrier_nearby', 0.0))
    vector.append(state.get('distance_to_entrance', 1.0))  # Already normalized
    vector.append(state.get('allies_near_grail', 0.0))  # Already normalized
    vector.append(state.get('enemies_near_grail', 0.0))  # Already normalized
    
    return np.array(vector, dtype=np.float32)

# Action space mapping - using high-level tactical directives
# Instead of learning low-level directions, goblins learn WHEN to use each directive
from src.ai.directives import (
    DIR_TOWARD_NEAREST_ENEMY, DIR_TOWARD_WEAKEST_ENEMY, DIR_TOWARD_GRAIL_CARRIER,
    DIR_AWAY_FROM_ENEMIES, DIR_INTERCEPT_ENEMY_PATH, DIR_ENCIRCLE_ENEMY,
    DIR_TOWARD_NEAREST_ALLY, DIR_TOWARD_ALLY_CLUSTER, DIR_AWAY_FROM_ALLIES,
    DIR_TOWARD_GRAIL, DIR_TOWARD_ENTRANCE, DIR_INTERCEPT_ZONE, DIR_CUT_OFF_ESCAPE,
    DIR_AWAY_FROM_WALLS, DIR_TOWARD_COVER,
    DIR_TO_OPEN_SPACE, DIR_TO_UNEXPLORED, DIR_PATROL, DIR_PURSUE_RETREATING,
    DIR_ATTACK, DIR_HOLD,
    NUM_DIRECTIVES
)

# Legacy action constants for backward compatibility
ACTION_MOVE_NORTH = DIR_TOWARD_NEAREST_ENEMY  # Repurposed
ACTION_MOVE_SOUTH = DIR_TOWARD_WEAKEST_ENEMY
ACTION_MOVE_EAST = DIR_TOWARD_GRAIL_CARRIER
ACTION_MOVE_WEST = DIR_AWAY_FROM_ENEMIES
ACTION_MOVE_NE = DIR_TOWARD_NEAREST_ALLY
ACTION_MOVE_NW = DIR_TOWARD_ALLY_CLUSTER
ACTION_MOVE_SE = DIR_TOWARD_GRAIL
ACTION_MOVE_SW = DIR_TOWARD_ENTRANCE
ACTION_ATTACK = DIR_ATTACK
ACTION_HOLD = DIR_HOLD

NUM_ACTIONS = NUM_DIRECTIVES
