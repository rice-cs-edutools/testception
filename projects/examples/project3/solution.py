"""
Monte Carlo Tic-Tac-Toe Player
"""

import random
import poc_ttt_provided as provided

# Constants for Monte Carlo simulator
# Change as desired
NTRIALS = 200
SCORE_CURRENT = 0.5
SCORE_OTHER = 1.0
    
def mc_trial(board, player):
    """
    Play a game randomly starting with
    the given board and given player.
    
    Modifies board.
    """
    curplayer = player
    while board.check_win() == None:
        empty = board.get_empty_squares()
        row, col = random.choice(empty)
        board.move(row, col, curplayer)
        curplayer = provided.switch_player(curplayer)

def mc_update_scores(scores, board, player):
    """
    Update scores with an outcome.
    """
    winner = board.check_win()
    if winner == provided.DRAW:
        return
    elif winner == player:
        mcinc = SCORE_CURRENT
        mcdec = -SCORE_OTHER
    else:
        mcinc = -SCORE_CURRENT
        mcdec = SCORE_OTHER
    dim = board.get_dim()
    for row in range(dim):
        for col in range(dim):
            square = board.square(row, col)
            if square != provided.EMPTY:
                if square == player:
                    scores[row][col] += mcinc
                else:
                    scores[row][col] += mcdec

def get_best_move(board, scores):
    """
    Return an empty square on board that has
    the maximum score in scores.  If multiple
    squares have the maximum score, select one
    at random.
     
    Returns a tuple, (row, col).
    """ 
    empty = board.get_empty_squares()
    maxscore = max([scores[row][col] for row, col in empty])
    maxsquares = []
    for row, col in empty:
        if scores[row][col] == maxscore:
            maxsquares.append((row, col))
    return random.choice(maxsquares)
                        
def mc_move(board, player, trials):
    """
    Make a move on the board.

    Returns the desired move as a tuple, (row, col).
    """
    dim = board.get_dim()
    scores = [[0.0 for dummycol in range(dim)] 
              for dummyrow in range(dim)]

    for dummy in range(trials):
        tmpboard = board.clone()
        mc_trial(tmpboard, player)
        mc_update_scores(scores, tmpboard, player)

    row, col = get_best_move(board, scores)
    return row, col



# Test game with the console or the GUI.
# Uncomment whichever you prefer.
# Both should be commented out when you submit for
# testing to save time.

# provided.play_game(mc_move, NTRIALS, False)        
