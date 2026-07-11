import os
import random
import argparse
from environment import ttthreeEnvironment
from agent import qlearningagent

def render_board(board):
    """prints the board in a user-friendly format in lowercase."""
    symbols = {0: " ", 1: "x", -1: "o"}
    rows = []
    for i in range(0, 9, 3):
        rows.append(f" {symbols[board[i]]} | {symbols[board[i+1]]} | {symbols[board[i+2]]} ")
    print("\n" + "\n---+---+---\n".join(rows) + "\n")

def evaluate_agent(difficulty: str, num_games: int = 1000):
    env = ttthreeEnvironment()
    agent = qlearningagent()
    
    # load the appropriate model
    model_path = os.path.join(os.path.dirname(__file__), "models", f"ttthree_{difficulty}.json")
    if not os.path.exists(model_path):
        print(f"model file not found: {model_path}. please run training first.")
        return
        
    agent.load(model_path)
    
    wins = 0
    losses = 0
    draws = 0
    
    for _ in range(num_games):
        env.reset()
        # randomly decide who goes first
        agent_player = random.choice([1, -1])
        
        # we track the mapping of current player in environment to agent's perspective
        # env.current_player: 1 or -1
        # if agent_player matches env.current_player, it is the agent's turn.
        
        done = False
        while not done:
            current_player = env.current_player
            valid_moves = env.get_valid_moves()
            
            if current_player == agent_player:
                # agent's turn: play greedily (explore=False)
                state = env.get_state()
                action = agent.get_action(state, valid_moves, explore=False)
            else:
                # random player's turn
                action = random.choice(valid_moves)
                
            _, reward, done = env.step(action)
            
            if done:
                # reward is returned from the perspective of the player who made the final move.
                # if agent made the final move (current_player == agent_player):
                #   reward +1.0 -> agent won, reward -1.0 -> agent lost, 0.0 -> draw
                # if opponent made the final move:
                #   reward +1.0 -> opponent won (agent lost), reward -1.0 -> agent won, 0.0 -> draw
                if reward == 0.0:
                    draws += 1
                elif current_player == agent_player:
                    if reward == 1.0:
                        wins += 1
                    else:
                        losses += 1
                else:
                    if reward == 1.0:
                        losses += 1
                    else:
                        wins += 1
                        
    win_rate = (wins / num_games) * 100
    loss_rate = (losses / num_games) * 100
    draw_rate = (draws / num_games) * 100
    
    print(f"evaluation results for {difficulty} model over {num_games} games:")
    print(f"  wins: {wins} ({win_rate:.1f}%)")
    print(f"  losses: {losses} ({loss_rate:.1f}%)")
    print(f"  draws: {draws} ({draw_rate:.1f}%)")

def play_human(difficulty: str):
    env = ttthreeEnvironment()
    agent = qlearningagent()
    
    model_path = os.path.join(os.path.dirname(__file__), "models", f"ttthree_{difficulty}.json")
    if not os.path.exists(model_path):
        print(f"model file not found: {model_path}. please run training first.")
        return
        
    agent.load(model_path)
    
    print(f"starting game against {difficulty} agent!")
    print("you are 'x' (player 1) and the agent is 'o' (player 2).")
    print("spaces are indexed 0 to 8 as follows:")
    print(" 0 | 1 | 2 \n---+---+---\n 3 | 4 | 5 \n---+---+---\n 6 | 7 | 8 \n")
    
    env.reset()
    # human goes first (1 = X), agent is second (-1 = O)
    agent_player = -1
    
    done = False
    while not done:
        current_player = env.current_player
        valid_moves = env.get_valid_moves()
        
        if current_player == agent_player:
            print("agent is thinking...")
            state = env.get_state()
            action = agent.get_action(state, valid_moves, explore=False)
            print(f"agent chooses space {action}")
        else:
            render_board(env.board)
            action = -1
            while action not in valid_moves:
                try:
                    user_input = input(f"your turn! enter an empty space {valid_moves}: ")
                    action = int(user_input)
                except ValueError:
                    print("invalid input. please enter a number.")
                    
        _, reward, done = env.step(action)
        
        if done:
            render_board(env.board)
            if reward == 0.0:
                print("game over! it's a draw.")
            elif env.current_player == agent_player:
                # current player in step is returned as switched player unless it was the final step.
                # actually, step() switches the player unless it is done.
                # since game is done, env.current_player represents the player who made the final move.
                if reward == 1.0:
                    print("game over! the agent wins.")
                else:
                    print("game over! you win.")
            else:
                if reward == 1.0:
                    print("game over! you win.")
                else:
                    print("game over! the agent wins.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="evaluate or play against the ttthree agents.")
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["evaluate", "play"], 
        default="evaluate",
        help="mode: 'evaluate' to run simulations against random player, or 'play' to play against the agent."
    )
    parser.add_argument(
        "--difficulty", 
        type=str, 
        choices=["easy", "medium", "hard"], 
        default="hard",
        help="difficulty level to play against (only applicable for 'play' mode)."
    )
    args = parser.parse_args()
    
    # ensure mode values are processed
    mode = args.mode.lower()
    difficulty = args.difficulty.lower()
    
    if mode == "evaluate":
        print("evaluating all difficulty models...")
        for diff in ["easy", "medium", "hard"]:
            evaluate_agent(diff)
            print()
    elif mode == "play":
        play_human(difficulty)
