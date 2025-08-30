import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
import json

class SupplyChainEnvironment:
    """Simplified RL environment for inventory management"""
    
    def _init_(self, product_id: str, historical_data: List[Dict]):
        self.product_id = product_id
        self.historical_data = historical_data
        self.current_step = 0
        self.max_steps = len(historical_data) - 30 if len(historical_data) > 30 else 10
        
        # State parameters
        self.inventory_level = 100  # Starting inventory
        self.max_inventory = 500
        self.holding_cost = 0.1  # Cost per unit per day
        self.stockout_penalty = 5.0  # Penalty for stockout
        self.order_cost = 10.0  # Fixed cost per order
        
        # Action space: [0, 1, 2, 3] -> [no order, small order, medium order, large order]
        self.action_space_size = 4
        self.order_quantities = [0, 20, 50, 100]
        
        self.reset()
    
    def reset(self):
        """Reset environment to initial state"""
        self.current_step = 0
        self.inventory_level = 100
        self.total_cost = 0.0
        self.orders_pending = []  # (arrival_day, quantity)
        
        if len(self.historical_data) > 0:
            self.demand_pattern = [d.get('quantity', 1) for d in self.historical_data[-30:]]
        else:
            self.demand_pattern = [1] * 30
        
        return self._get_state()
    
    def _get_state(self) -> np.ndarray:
        """Get current state representation"""
        # State includes: inventory_level, pending_orders, recent_demand_pattern, day_of_week
        pending_qty = sum([qty for _, qty in self.orders_pending])
        
        # Recent demand (last 7 days)
        recent_demand = self.demand_pattern[-7:] if len(self.demand_pattern) >= 7 else [1] * 7
        
        # Day of week (cyclical encoding)
        day_of_week = self.current_step % 7
        dow_sin = np.sin(2 * np.pi * day_of_week / 7)
        dow_cos = np.cos(2 * np.pi * day_of_week / 7)
        
        state = np.array([
            self.inventory_level / self.max_inventory,  # Normalized inventory
            pending_qty / 100,  # Normalized pending orders
            dow_sin, dow_cos,  # Day of week encoding
            *[d/50 for d in recent_demand[:7]]  # Normalized recent demand
        ])
        
        return state.astype(np.float32)
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """Execute one step in environment"""
        # Process incoming orders (lead time = 3 days)
        incoming_qty = 0
        self.orders_pending = [(day, qty) for day, qty in self.orders_pending if day != self.current_step]
        for day, qty in self.orders_pending:
            if day == self.current_step:
                incoming_qty += qty
        
        self.inventory_level += incoming_qty
        self.inventory_level = min(self.inventory_level, self.max_inventory)
        
        # Place new order if action > 0
        if action > 0:
            order_qty = self.order_quantities[action]
            arrival_day = self.current_step + 3  # 3-day lead time
            self.orders_pending.append((arrival_day, order_qty))
        
        # Generate demand
        if self.current_step < len(self.demand_pattern):
            demand = max(0, int(self.demand_pattern[self.current_step] + np.random.normal(0, 0.5)))
        else:
            # Use average demand with noise
            avg_demand = np.mean(self.demand_pattern) if self.demand_pattern else 5
            demand = max(0, int(avg_demand + np.random.normal(0, 1)))
        
        # Calculate costs
        cost = 0.0
        
        # Holding cost
        cost += self.inventory_level * self.holding_cost
        
        # Ordering cost
        if action > 0:
            cost += self.order_cost
        
        # Serve demand or penalty for stockout
        if self.inventory_level >= demand:
            self.inventory_level -= demand
        else:
            # Stockout penalty
            stockout_qty = demand - self.inventory_level
            cost += stockout_qty * self.stockout_penalty
            self.inventory_level = 0
        
        self.total_cost += cost
        reward = -cost  # Negative cost as reward
        
        # Update state
        self.current_step += 1
        done = self.current_step >= self.max_steps
        
        info = {
            "inventory": self.inventory_level,
            "demand": demand,
            "cost": cost,
            "total_cost": self.total_cost
        }
        
        return self._get_state(), reward, done, info

class SimpleQLearningAgent:
    """Simple Q-Learning agent for inventory management"""
    
    def _init_(self, state_size: int, action_size: int, learning_rate: float = 0.1):
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.epsilon = 0.1  # Exploration rate
        self.discount_factor = 0.95
        
        # Simple state discretization for Q-table
        self.state_bins = 10
        self.q_table = np.zeros([self.state_bins] * state_size + [action_size])
    
    def _discretize_state(self, state: np.ndarray) -> Tuple:
        """Discretize continuous state to discrete bins"""
        discrete_state = []
        for i, s in enumerate(state):
            # Clamp state values and discretize
            clamped = np.clip(s, -1, 1)
            bin_idx = int((clamped + 1) * (self.state_bins - 1) / 2)
            discrete_state.append(min(bin_idx, self.state_bins - 1))
        return tuple(discrete_state)
    
    def get_action(self, state: np.ndarray, training: bool = True) -> int:
        """Get action using epsilon-greedy policy"""
        discrete_state = self._discretize_state(state)
        
        if training and np.random.random() < self.epsilon:
            return np.random.choice(self.action_size)
        else:
            try:
                return np.argmax(self.q_table[discrete_state])
            except IndexError:
                return np.random.choice(self.action_size)
    
    def update_q_table(self, state: np.ndarray, action: int, reward: float, 
                      next_state: np.ndarray, done: bool):
        """Update Q-table using Q-learning rule"""
        discrete_state = self._discretize_state(state)
        discrete_next_state = self._discretize_state(next_state)
        
        try:
            current_q = self.q_table[discrete_state][action]
            
            if done:
                target_q = reward
            else:
                next_max_q = np.max(self.q_table[discrete_next_state])
                target_q = reward + self.discount_factor * next_max_q
            
            # Q-learning update
            self.q_table[discrete_state][action] += self.learning_rate * (target_q - current_q)
        except IndexError:
            pass  # Skip invalid states

class DeepRLInventoryManager:
    """Deep RL manager that switches from simple models to RL when enough data is available"""
    
    def _init_(self):
        self.agents = {}  # product_id -> agent
        self.environments = {}  # product_id -> environment
        self.training_data = {}  # product_id -> historical data
        self.min_data_for_rl = 100  # Minimum data points to start RL training
        
    def can_use_rl(self, product_id: str) -> bool:
        """Check if we have enough data to use RL for this product"""
        return len(self.training_data.get(product_id, [])) >= self.min_data_for_rl
    
    def add_training_data(self, product_id: str, sales_data: List[Dict]):
        """Add training data for a product"""
        self.training_data[product_id] = sales_data
        
        if self.can_use_rl(product_id):
            self._initialize_rl_agent(product_id)
    
    def _initialize_rl_agent(self, product_id: str):
        """Initialize RL agent and environment for a product"""
        env = SupplyChainEnvironment(product_id, self.training_data[product_id])
        self.environments[product_id] = env
        
        state_size = len(env._get_state())
        action_size = env.action_space_size
        
        agent = SimpleQLearningAgent(state_size, action_size)
        self.agents[product_id] = agent
        
        # Train the agent
        self._train_agent(product_id, episodes=100)
    
    def _train_agent(self, product_id: str, episodes: int = 100):
        """Train the RL agent"""
        if product_id not in self.agents or product_id not in self.environments:
            return
        
        agent = self.agents[product_id]
        env = self.environments[product_id]
        
        for episode in range(episodes):
            state = env.reset()
            total_reward = 0
            
            while True:
                action = agent.get_action(state, training=True)
                next_state, reward, done, _ = env.step(action)
                
                agent.update_q_table(state, action, reward, next_state, done)
                
                state = next_state
                total_reward += reward
                
                if done:
                    break
        
        print(f"RL training completed for product {product_id}")
    
    def get_rl_recommendation(self, product_id: str, current_inventory: int) -> Dict[str, Any]:
        """Get recommendation using RL agent"""
        if not self.can_use_rl(product_id) or product_id not in self.agents:
            return {"error": "RL not available for this product"}
        
        agent = self.agents[product_id]
        env = self.environments[product_id]
        
        # Set current inventory in environment
        env.inventory_level = current_inventory
        state = env._get_state()
        
        # Get action from trained agent
        action = agent.get_action(state, training=False)
        order_qty = env.order_quantities[action]
        
        return {
            "method": "deep_rl",
            "recommended_order_qty": order_qty,
            "action_index": action,
            "confidence": "HIGH" if len(self.training_data[product_id]) > 200 else "MEDIUM"
        }

# Global RL manager instance
rl_manager = DeepRLInventoryManager()

def should_use_deep_rl(product_id: str, data_points: int) -> bool:
    """Determine if we should use Deep RL vs simple linear regression"""
    return data_points >= 100

def get_rl_based_recommendation(product_id: str, current_stock: int, 
                               historical_data: List[Dict]) -> Dict[str, Any]:
    """Get recommendation using Deep RL if enough data, otherwise fallback"""
    if should_use_deep_rl(product_id, len(historical_data)):
        rl_manager.add_training_data(product_id, historical_data)
        return rl_manager.get_rl_recommendation(product_id, current_stock)
    else:
        return {
            "method": "linear_regression",
            "message": "Insufficient data for Deep RL, using linear regression",
            "data_points": len(historical_data),
            "rl_threshold":100
            }