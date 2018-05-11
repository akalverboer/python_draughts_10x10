#!/usr/bin/env python
# -*- coding: utf-8 -*-
## Faster with: /usr/bin/env pypy

# =====================================================================================
# MAD100 is a draughts engine for the 100 squares board.
# Inspired by the chess engine "Sunfish" of Thomas Ahle / Denmark.
# Capture rules same as International Draughts for a 10x10 board.
# Numeric representation of squares.
# =====================================================================================

import re
import sys
from mad100_moves import gen_moves
import mad100_search
import mad100_play

# The external respresentation of our board is a 100 character string.

initial_ext = (
    '   p   p   p   p   p '    #  01 - 05
    ' p   p   p   p   p   '    #  06 - 10
    '   p   p   p   p   p '    #  11 - 15
    ' p   p   p   p   p   '    #  16 - 20
    '   .   .   .   .   . '    #  21 - 25
    ' .   .   .   .   .   '    #  26 - 30
    '   P   P   P   P   P '    #  31 - 35
    ' P   P   P   P   P   '    #  36 - 40
    '   P   P   P   P   P '    #  41 - 45
    ' P   P   P   P   P   '    #  46 - 50
)

initial_ext_test = (
    '   .   K   .   .   . '    #  01 - 05
    ' .   .   .   .   .   '    #  06 - 10
    '   p   .   k   .   . '    #  11 - 15
    ' .   .   .   .   p   '    #  16 - 20
    '   .   .   .   .   p '    #  21 - 25
    ' .   .   .   .   .   '    #  26 - 30
    '   .   p   .   .   . '    #  31 - 35
    ' .   .   .   .   .   '    #  36 - 40
    '   .   .   .   p   . '    #  41 - 45
    ' .   .   .   .   .   '    #  46 - 50
)

board_ext_problem1 = (
    '   .   .   .   .   p '    #  01 - 05  P.Lauwen, DP, 4/1977
    ' .   .   p   .   .   '    #  06 - 10
    '   .   .   .   .   P '    #  11 - 15
    ' .   .   .   P   .   '    #  16 - 20
    '   .   .   .   P   . '    #  21 - 25
    ' .   .   .   P   p   '    #  26 - 30
    '   .   P   .   .   p '    #  31 - 35
    ' .   p   .   .   p   '    #  36 - 40
    '   P   p   .   .   p '    #  41 - 45
    ' .   .   .   P   P   '    #  46 - 50
)

# - The internal respresentation of our board is a list (array) of 52 char
# - Moves are always calculated for white (uppercase letters) at high numbers!!
# - If black is to move, black and white are swapped and the board is rotated.
#   This is reflected by the definition of the rotate function.
#   Uppercase is the player, lowercase is the opponent.

###############################################################################
# Evaluation tables
###############################################################################

# Piece Score Table (PST, External Representation) for piece (P) and king (K)
# Because of symmetry the PST is only given for white (uppercase letter)
# Material value for one piece is 1000.

pst_ext = {
  'P': ('    000   000   000   000   000 '    #  01 - 05   PIECE promotion line
        ' 045   050   055   050   045    '    #  06 - 10
        '    040   045   050   045   040 '    #  11 - 15
        ' 035   040   045   040   035    '    #  16 - 20
        '    025   030   030   025   030 '    #  21 - 25   Small threshold to prevent to optimistic behaviour
        ' 025   030   035   030   025    '    #  26 - 30
        '    020   025   030   020   025 '    #  31 - 35
        ' 020   015   025   020   015    '    #  36 - 40
        '    010   015   020   010   015 '    #  41 - 45
        ' 005   010   015   010   005    '    #  46 - 50
        ),
  'K': ('    050   050   050   050   050 '    #  01 - 05 
        ' 050   050   050   050   050    '    #  06 - 10
        '    050   050   050   050   050 '    #  11 - 15
        ' 050   050   050   050   050    '    #  16 - 20
        '    050   050   050   050   050 '    #  21 - 25
        ' 050   050   050   050   050    '    #  26 - 30
        '    050   050   050   050   050 '    #  31 - 35
        ' 050   050   050   050   050    '    #  36 - 40
        '    050   050   050   050   050 '    #  41 - 45
        ' 050   050   050   050   050    '    #  46 - 50
        )
}

# Internal representation of PST with zeros at begin and end (rotation-symmetry)
PST = {'P': [], 'K': []}
PST['P'] = [0] + map( int, pst_ext['P'].split() ) + [0]
PST['K'] = [0] + map( int, pst_ext['K'].split() ) + [0]

PMAT = {'P': 1000, 'K': 3000}   # piece material values

###############################################################################
# Draughts logic
###############################################################################

class Position:
    # A state of a draughts100 game
    # - board: a list of 52 char; first and last index unused ('0') rotation-symmetry
    # - score: the board evaluation
    # 

    def __init__(self, board, score):
       self.board = board
       self.score = score

    def key(self):
        pos_key = ''.join(self.board)    # array to string
        return pos_key

    def rotate(self):
        rotBoard = [ x.swapcase() for x in self.board[::-1] ]  # clone!
        return Position(rotBoard, -self.score)

    def clone(self):
        return Position(self.board, self.score)

    def domove(self, move):
        # Move is named tuple with list of steps and list of takes
        # Returns new rotated position object after moving.
        # Calculates the score of the returned position.
        # Remember: move is always done with white
        if move is None: return self.rotate()     # turn to other player

        board = list(self.board)    # clone board

        # Actual move
        i, j = move.steps[0], move.steps[-1]    # first, last (NB. sometimes i==j !)
        p =  board[i]

        # Move piece and promote to white king
        promotion_line = range(1,6)
        board[i] = '.'
        if j in promotion_line and (p != 'K'):
           board[j] = 'K'
        else:
           board[j] = p

        # Capture
        for k in move.takes:
           board[k] = '.'

        # We increment the score of the new position depending on the move.
        score = self.score + self.eval_move(move) 

        # The incremental update of the score depending on the move is not always
        # possible for evaluation measures like mobility, patterns, etc.
        # If needed we can re-compute the score of the whole position by:
        #      posnew.score = posnew.eval_pos() 
        # The incremental update depending on the move is much faster.

        # We rotate the returned position, so it's ready for the next player
        posnew = Position(board, score).rotate()

        return posnew

    def eval_move(self, move):
        # Returns increment of board score by this move (neg or pos)
        # Simulate the move and compute increment of the score
        i, j = move.steps[0], move.steps[-1]
        p =  self.board[i]   # move always done for uppercase char!

        # Actual move: increment of score by move
        promotion_line = range(1,6)
        if j in promotion_line and (p != 'K'):
           from_val = PST[p][i] + PMAT[p]
           to_val = PST['K'][j] + PMAT['K']    # piece promoted to king
           score = to_val - from_val
        else:
           from_val = PST[p][i] + PMAT[p]
           to_val = PST[p][j] + PMAT[p]
           score = to_val - from_val

        # Increase of score because of captured pieces
        for k in move.takes:
           q = self.board[k].upper()
           score += PST[q][51-k] + PMAT[q]   # profit from perspective of other player

        return score

    def eval_pos(self):
       # Computes the board score and returns it
       score1 = sum(PST[p][i] + PMAT[p] for i,p in enumerate(self.board) if i>0 and i<52 and p.isupper())
       rotBoard = [ c.swapcase() for c in self.board[::-1] ]
       score2 = sum(PST[p][i] + PMAT[p] for i,p in enumerate(rotBoard) if i>0 and i<52 and p.isupper())

       score = score1 - score2
       ##print('Total score: ', str(score))
       return score


# *** END class Position ***


###############################################################################
# User interface
###############################################################################

# Python 2 compatability
if sys.version_info[0] == 2:
    input = raw_input

def parse_move(move):
    # Parameter move in alfanumeric format like 32-28 or 26x37.
    # Return list of steps of move/capture in number format.
    nsteps = map( int, re.split('[-x]', move) )
    return nsteps

def render_move(move):
    # Render move in numeric format
    d = '-' if len(move.takes) == 0 else 'x'
    return str(move.steps[0]) + d + str(move.steps[-1])

def match_move(pos, steps):
    # Match list of steps with a legal move. 
    nsteps = map( int, steps )
    lmoves = gen_moves(pos)   # legal moves
    if len(nsteps) == 2:
       for move in lmoves:
          if move.steps[0] == nsteps[0] and move.steps[-1] == nsteps[-1]:
             return move
    else:
       for move in lmoves:
          if set(move.steps) == set(nsteps):
             return move
    return None

def newPos(iBoard):
    # Return position object based on board as string
    board = boardToList(iBoard)   # list of char
    pos = Position(board, 0)   # temp
    score = pos.eval_pos()
    return Position(board, score)

def boardToList(str):
    # Convert board as string to board as list
    board = '0' + str.replace(" ", "") + '0'
    return list(board)

def print_pos(pos):
    # unicodes:  ⛀    ⛁    ⛂    ⛃
    # board is array 0..52; fill 'p', 'P', 'k', 'K', '.'
    numSpaces = 0
    uni_piececode = {'p':'⛂', 'k':'⛃', 'P':'⛀', 'K':'⛁', '.':'·', ' ':' '}  # utf-8
    chr_piececode = {'p':'b', 'k':'B', 'P':'w', 'K':'W', '.':'·', ' ':' '}   # asci
    if 0 == 0:
       piececode = uni_piececode
    else:
       piececode = chr_piececode
    nrows = 10

    print("")
    for i in range(1, nrows+1):
       row_len = 5
       start = (i-1) * (nrows//2) + 1
       row = pos.board[start: start + (nrows//2)]
       numSpaces = 0 if numSpaces == 2 else 2   # alternate
       spaces = ' ' * numSpaces                   # spaces before row of pieces
       numbering = ' %2d - %2d ' %( start, start + nrows//2 - 1)
       pieces = '   '.join(piececode.get(p, p) for p in row)
       print(numbering + '   ' + spaces + pieces)
    print("")

def main():
    print("=======================================================")
    print("| MAD100: engine for draughts 100 international rules | ")
    print("=======================================================")

    WHITE, BLACK = 0, 1
    color = WHITE            # WHITE / BLACK
    pos = newPos(initial_ext)
    print_pos(pos)
    player = 1
    max_nodes = mad100_search.MAX_NODES
    print('   Strength max nodes: %d' %(max_nodes) )

    while True:
        comm = input('Command: ' )

        if comm == 'quit' or comm == 'q':
            break

        elif comm.startswith('n'):
            # Set max_nodes to search
            if len(comm.split()) == 1:
               max_nodes = mad100_search.MAX_NODES
            elif len(comm.split()) == 2:
               level = int(comm.split()[1])
               max_nodes = int(level) 
            print('   Level max nodes: %d' %(max_nodes) )

        elif comm == 'go':
            # let MAD100 search for next move

            move, score = mad100_search.search(pos, maxn=max_nodes)

            # We don't play well once we have detected our death
            if move is None:
                print('no move found', ' score: ', score)
            elif score >= mad100_search.MATE_VALUE:
                print('very high score')
            elif score <= -mad100_search.MATE_VALUE:
                print('very low score')
            else:
                print(mad100_play.mrender_move(color, move))
                pos = pos.domove(move)
                color = 1-color   # alternating 0 and 1 (WHITE and BLACK)
                player = -player
                mad100_play.mprint_pos(color, pos)

        elif comm == 'test':
            # TEST
            pos.eval_pos()

        elif comm.upper().startswith('H') or comm.startswith('?'):
            print(' _________________________________________________________________ ')
            print('| HELP:  ')
            print('| q: quit ')
            print('| h: help info ')
            print('| go: let engine search for the next move')
            print('| n <num>: set max number of nodes for search (or default) ')
            print('|  ')
            print('| Use mad100_play.py for a more advanced user interface. ')
            print('|_________________________________________________________________')
            print()
 
        else:
            print("Error (unkown command):", comm)

    return 0

if __name__ == '__main__':
    main()
