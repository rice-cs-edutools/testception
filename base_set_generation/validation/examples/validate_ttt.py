def validate_mm_move(args):
    """
    Checks that this is a valid set of args for mm_move.
    """
    board, player = args

    ## First, check that the board is valid
    retval, num_xs, num_os = validate_board(board)

    if retval:
        ## Then, check that the player is valid given that board
        retval = ((num_os == num_xs and player == "X") \
            or (num_xs == num_os + 1 and player == "O"))

    return retval

def validate_board(board):
    """
    Checks that the proportions of Xs and Os is valid (same number or one
    more X than O).
    """
    num_xs = 0
    num_os = 0

    for row in board._board:
        for elem in row:
            if elem == "X":
                num_xs += 1
            elif elem == "O":
                num_os += 1

    return (num_xs == num_os or num_xs == (num_os + 1)), num_xs, num_os

def validate_mc_update_scores(args):
    """
    Checks that this is a valid set of args for mc_update_scores.
    """
    scores, board, player = args

    ## First, check that the board is valid
    retval, dummy, dummy = validate_board(board)

    if retval:
        ## Then, check that the board is completed
        retval = bool(board.check_win())

    return retval

def validate_get_best_move(args):
    """
    Checks that this is a valid set of args for get_best_move.
    """
    board, scores = args

    ## First, check that the board is valid
    retval, dummy, dummy = validate_board(board)

    if retval:
        ## Then, check that the board is NOT completed
        retval = not bool(board.check_win())

    return retval
