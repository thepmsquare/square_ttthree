import os
from tqdm import tqdm
from environment import ttthreeEnvironment
from agent import qlearningagent

def train_agent(episodes: int, start_epsilon: float, end_epsilon: float, filename: str):
    print(f"starting self-play training for {filename} ({episodes} episodes)...")
    
    # initialize environment and agent
    env = ttthreeEnvironment()
    agent = qlearningagent(alpha=0.2, gamma=0.9, epsilon=start_epsilon)
    
    for episode in tqdm(range(episodes), desc=f"training {filename}"):
        # decay epsilon linearly as training progresses
        agent.epsilon = start_epsilon - (start_epsilon - end_epsilon) * (episode / episodes)
        
        env.reset()
        prev_states = {1: None, -1: None}
        prev_actions = {1: None, -1: None}
        
        done = False
        while not done:
            current_player = env.current_player
            state = env.get_state()
            valid_moves = env.get_valid_moves()
            
            # select action
            action = agent.get_action(state, valid_moves, explore=True)
            
            # update the player's previous move based on current state transition
            if prev_states[current_player] is not None:
                agent.update(
                    state=prev_states[current_player],
                    action=prev_actions[current_player],
                    reward=0.0,
                    next_state=state,
                    next_valid_moves=valid_moves,
                    done=False
                )
                
            # track this state and action
            prev_states[current_player] = state
            prev_actions[current_player] = action
            
            # step in environment
            next_state, reward, done = env.step(action)
            
            if done:
                # game finished! update active player with final reward
                agent.update(
                    state=prev_states[current_player],
                    action=prev_actions[current_player],
                    reward=reward,
                    next_state=next_state,
                    next_valid_moves=[],
                    done=True
                )
                
                # update waiting player with opposite reward (zero-sum game)
                opponent = -current_player
                if prev_states[opponent] is not None:
                    agent.update(
                        state=prev_states[opponent],
                        action=prev_actions[opponent],
                        reward=-reward,
                        next_state=next_state,
                        next_valid_moves=[],
                        done=True
                    )
                    
    # create the models directory if it doesn't exist
    models_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(models_dir, exist_ok=True)
    
    output_path = os.path.join(models_dir, filename)
    agent.save(output_path)
    print(f"saved model with {len(agent.q_table)} states to {output_path}\n")

if __name__ == "__main__":
    configs = [
        # (episodes, start_epsilon, end_epsilon, filename)
        (1000, 0.80, 0.40, "ttthree_easy.json"),
        (10000, 0.50, 0.15, "ttthree_medium.json"),
        (80000, 0.40, 0.02, "ttthree_hard.json")
    ]
    
    for episodes, start_ep, end_ep, fname in configs:
        train_agent(episodes, start_ep, end_ep, fname)
        
    print("all difficulty models generated successfully!")
