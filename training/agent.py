import random
import json
from typing import Dict, Tuple, List

class qlearningagent:
    def __init__(self, alpha: float = 0.2, gamma: float = 0.9, epsilon: float = 0.3):
        # q_table: maps a state tuple to a list of 9 floats (representing action values)
        self.q_table: Dict[Tuple[int, ...], List[float]] = {}
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

    def get_q_values(self, state: Tuple[int, ...]) -> List[float]:
        """retrieves the q-values list for a state, initializing it if new."""
        if state not in self.q_table:
            self.q_table[state] = [0.0] * 9
        return self.q_table[state]

    def get_action(self, state: Tuple[int, ...], valid_moves: List[int], explore: bool = True) -> int:
        """selects an action using epsilon-greedy strategy."""
        # 1. explore: choose random valid move
        if explore and random.random() < self.epsilon:
            return random.choice(valid_moves)

        # 2. exploit: choose best move according to q-values
        q_vals = self.get_q_values(state)
        
        # shuffle valid moves to break ties randomly if multiple moves have the same q-value
        shuffled_moves = valid_moves.copy()
        random.shuffle(shuffled_moves)
        
        best_action = shuffled_moves[0]
        best_val = -float("inf")
        
        for action in shuffled_moves:
            if q_vals[action] > best_val:
                best_val = q_vals[action]
                best_action = action
                
        return best_action

    def update(
        self, 
        state: Tuple[int, ...], 
        action: int, 
        reward: float, 
        next_state: Tuple[int, ...], 
        next_valid_moves: List[int], 
        done: bool
    ):
        """updates the q-value of the state-action pair using the td target."""
        current_q = self.get_q_values(state)[action]

        if done:
            max_future_q = 0.0
        else:
            next_q_vals = self.get_q_values(next_state)
            max_future_q = max(next_q_vals[a] for a in next_valid_moves)

        # q-learning formula
        target = reward + self.gamma * max_future_q
        self.q_table[state][action] = current_q + self.alpha * (target - current_q)

    def save(self, filepath: str):
        """saves the q-table to a json file with comma-separated string keys."""
        serialized_q = {
            ",".join(map(str, state)): values 
            for state, values in self.q_table.items()
        }
        with open(filepath, "w") as f:
            json.dump(serialized_q, f)

    def load(self, filepath: str):
        """loads a q-table from a json file."""
        with open(filepath, "r") as f:
            serialized_q = json.load(f)
        self.q_table = {}
        for state_str, values in serialized_q.items():
            state = tuple(int(x) for x in state_str.split(","))
            self.q_table[state] = values
