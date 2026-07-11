from typing import List, Tuple, Optional


class ttthreeEnvironment:
    def __init__(self):
        # board is flat list of 9 elements:
        # 0 = empty, 1 = player 1 (X), -1 = player 2 (O)
        self.board = [0] * 9
        self.current_player = 1  # 1 goes first

    def reset(self) -> Tuple[int, ...]:

        self.board = [0] * 9
        self.current_player = 1
        return self.get_state()

    def get_state(self) -> Tuple[int, ...]:
        """returns the board from the active player's perspective.

        if self.current_player is -1, we multiply everything by -1.
        this normalizes the board so that the active player's pieces are always 1,
        and the opponent's pieces are always -1.
        """
        return tuple(cell * self.current_player for cell in self.board)

    def get_valid_moves(self) -> List[int]:
        """returns a list of empty indices (0-8) that are valid moves."""
        return [i for i, cell in enumerate(self.board) if cell == 0]

    def check_winner(self) -> Optional[int]:
        """checks if there is a winner or a draw.

        returns:
            1: if the current active player has won.
            -1: if the opponent has won.
            0: if it is a draw.
            None: if the game is still ongoing.
        """
        winning_lines = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
            (0, 4, 8), (2, 4, 6)              # diagonals
        ]
        for line in winning_lines:
            line_sum = sum(self.board[i] for i in line)
            if line_sum == 3 * self.current_player:
                return 1
            if line_sum == -3 * self.current_player:
                return -1

        if 0 not in self.board:
            return 0

        return None

    def step(self, action: int) -> Tuple[Tuple[int, ...], float, bool]:
        """takes a move (0-8) for the current player.

        updates the board, checks if the game has ended, and switches active player.
        returns: (next_state, reward, done)
        """
        if self.board[action] != 0:
            raise ValueError("invalid action: square already occupied")

        self.board[action] = self.current_player
        winner = self.check_winner()

        if winner is not None:
            done = True
            if winner == 1:
                reward = 1.0
            elif winner == -1:
                reward = -1.0
            else:
                reward = 0.0
            return self.get_state(), reward, done

        # switch player and return next state
        self.current_player = -self.current_player
        return self.get_state(), 0.0, False
