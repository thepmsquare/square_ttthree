from environment import ttthreeEnvironment
from agent import qlearningagent

def render_board(board):
    """prints the board in a user-friendly format."""
    symbols = {0: " ", 1: "x", -1: "o"}
    rows = []
    for i in range(0, 9, 3):
        rows.append(f" {symbols[board[i]]} | {symbols[board[i+1]]} | {symbols[board[i+2]]} ")
    print("\n" + "\n---+---+---\n".join(rows) + "\n")

def run_debug_game():
    print("starting debug game. the agent will play against itself.")
    print("you will see how q-values change after every single move.")
    print("press enter to proceed through each step.\n")
    
    env = ttthreeEnvironment()
    # we use a high learning rate (alpha=0.5) so you can see numbers jump significantly!
    agent = qlearningagent(alpha=0.5, gamma=0.9, epsilon=0.3)
    
    # let's pre-initialize a state to show you how values look before updates.
    # state: empty board
    env.reset()
    
    # keep track of each player's last state and action
    # player 1 is X, player -1 is O
    prev_states = {1: None, -1: None}
    prev_actions = {1: None, -1: None}
    
    step_count = 0
    done = False
    
    while not done:
        step_count += 1
        current_player = env.current_player
        player_symbol = "x" if current_player == 1 else "o"
        
        # 1. get normalized state (from current player's perspective)
        state = env.get_state()
        valid_moves = env.get_valid_moves()
        
        print("=" * 50)
        print(f"step {step_count}: player {player_symbol}'s turn")
        print(f"raw board representation: {env.board}")
        print(f"normalized state (from {player_symbol}'s perspective): {state}")
        render_board(env.board)
        
        # print current q-values for this state
        q_values = agent.get_q_values(state)
        print("current q-values for all 9 spaces:")
        for idx, val in enumerate(q_values):
            status = "occupied" if idx not in valid_moves else f"q={val:.4f}"
            print(f"  space {idx}: {status}")
            
        # 2. select action
        action = agent.get_action(state, valid_moves, explore=True)
        is_random = action != q_values.index(max(q_values[i] for i in valid_moves))
        exploration_type = "random (exploration)" if is_random else "greedy (exploitation)"
        print(f"\nplayer {player_symbol} chooses space {action} via {exploration_type}")
        
        # 3. update the player's PREVIOUS move
        # since it is now our turn again, we can evaluate how good our last move was
        if prev_states[current_player] is not None:
            prev_s = prev_states[current_player]
            prev_a = prev_actions[current_player]
            old_q = agent.get_q_values(prev_s)[prev_a]
            
            # temporal difference update for the intermediate state
            agent.update(
                state=prev_s,
                action=prev_a,
                reward=0.0,
                next_state=state,
                next_valid_moves=valid_moves,
                done=False
            )
            new_q = agent.get_q_values(prev_s)[prev_a]
            print(f"\nupdating player {player_symbol}'s previous move:")
            print(f"  state: {prev_s}")
            print(f"  action (space): {prev_a}")
            print(f"  q-value: {old_q:.4f} -> {new_q:.4f} (change: {new_q - old_q:+.4f})")
            
        # save current state and action for next time
        prev_states[current_player] = state
        prev_actions[current_player] = action
        
        # 4. execute step in environment
        input("\npress enter to execute move and see what happens...")
        next_state, reward, done = env.step(action)
        
        # 5. if game is over, we update the outcomes immediately
        if done:
            print("\n" + "#" * 50)
            print("game over!")
            render_board(env.board)
            
            # the active player who just moved gets the final reward
            active_prev_s = prev_states[current_player]
            active_prev_a = prev_actions[current_player]
            active_old_q = agent.get_q_values(active_prev_s)[active_prev_a]
            
            agent.update(
                state=active_prev_s,
                action=active_prev_a,
                reward=reward,  # +1.0 for win, 0.0 for draw
                next_state=next_state,
                next_valid_moves=[],
                done=True
            )
            active_new_q = agent.get_q_values(active_prev_s)[active_prev_a]
            print(f"updating winner/draw player {player_symbol}'s final move:")
            print(f"  q-value: {active_old_q:.4f} -> {active_new_q:.4f} (change: {active_new_q - active_old_q:+.4f})")
            
            # the opponent player who is waiting gets the opposite reward
            opponent = -current_player
            opp_symbol = "x" if opponent == 1 else "o"
            if prev_states[opponent] is not None:
                opp_prev_s = prev_states[opponent]
                opp_prev_a = prev_actions[opponent]
                opp_old_q = agent.get_q_values(opp_prev_s)[opp_prev_a]
                
                agent.update(
                    state=opp_prev_s,
                    action=opp_prev_a,
                    reward=-reward,  # -1.0 for loss, 0.0 for draw
                    next_state=next_state,
                    next_valid_moves=[],
                    done=True
                )
                opp_new_q = agent.get_q_values(opp_prev_s)[opp_prev_a]
                print(f"\nupdating loser/draw player {opp_symbol}'s final move:")
                print(f"  q-value: {opp_old_q:.4f} -> {opp_new_q:.4f} (change: {opp_new_q - opp_old_q:+.4f})")
                
    print("\nfirst debug game finished!")
    print("as you play more games, these values will build up and propagate further back.")

if __name__ == "__main__":
    run_debug_game()
