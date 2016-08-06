#!/usr/bin/env python

#=====================================================================
# Module methods for playing a game
#=====================================================================

import re
import mad100
from mad100_moves import Move
import mad100_search

# MAD100 doesn't know about colors. Now we have to.
WHITE, BLACK = 0, 1

# FEN examples
FEN_INITIAL = "W:B1-20:W31-50"
FEN_MAD100_1 = "W:W15,19,24,29,32,41,49,50:B5,8,30,35,37,40,42,45."  # P.Lauwen, DP, 4/1977
FEN_MAD100_2 = "W:W17,28,32,33,38,41,43:B10,18-20,23,24,37."
FEN_MAD100_3 = "W:WK3,25,34,45:B38,K47."
FEN_MAD100_4 = "W:W18,23,31,33,34,39,47:B8,11,20,24,25,26,32."       # M.Dalman
FEN_MAD100_5 = "B:B7,11,13,17,20,22,24,30,41:W26,28,29,31,32,33,38,40,48."  # after 30-35 white wins

# Solution 1x1 after 20 moves!! Mad100 finds solution. Set nodes 300000.
FEN_MAD100_6 = "W:W16,21,25,32,37,38,41,42,45,46,49,50:B8,9,12,17,18,19,26,29,30,33,34,35,36."


def parseFEN(iFen):
   """ Parses a string in Forsyth-Edwards Notation into a Position """
   fen = iFen                  # working copy
   fen = fen.replace(" ", "")  # remove all spaces
   fen = re.sub(r'\..*$', '', fen)   # cut off info (.xxx) at the end
   if fen == '': fen = 'W:B:W'       # empty FEN Position
   if fen == 'W::': fen = 'W:B:W'
   if fen == 'B::': fen = 'B:B:W'
   fen = re.sub(r'.::$', 'W:W:B', fen)
   parts = fen.split(':')

   rlist = list('0'*51)                            # init temp return list
   sideToMove = 'B' if parts[0][0] == 'B' else 'W'
   rlist[0] = sideToMove

   for i in range(1,3):   # process the two sides
      side = parts[i]     # working copy
      color = side[0]
      side = side[1:]     # strip color char
      if len(side) == 0: continue    # nothing to do: next side
      numSquares = side.split(',')   # list of numbers or range of numbers with/without king flag
      for num in numSquares:
         isKing = True if num[0] == 'K' else False
         num = num[1:] if isKing else num       # strip 'K'
         isRange = True if len(num.split('-')) == 2 else False
         if isRange:
            r = num.split('-')
            for j in range( int(r[0]), int(r[1]) + 1 ):
               rlist[j] = color.upper() if isKing else color.lower()
         else:
            rlist[int(num)] = color.upper() if isKing else color.lower()

   # prepare output
   pcode = {'w': 'P', 'W': 'K', 'b': 'p', 'B': 'k', '0': '.'}
   board = ['0'] + [pcode[elem] for elem in rlist[1:]] + ['0']
   pos = mad100.Position(board, 0)
   pos.score = pos.eval_pos()
   return pos if sideToMove == 'W' else pos.rotate()

def mrender_move(color, move):
    # Render move in numeric format (mutual version)
    if move is None: return ''
    steps = move.steps if color == WHITE else map(lambda i: 51-i, move.steps)
    takes = move.takes if color == WHITE else map(lambda i: 51-i, move.takes)
    rmove = Move(steps, takes)
    return mad100.render_move(rmove)

def mparse_move(color, move):
    # Parameter move in numeric format like 17-14 or 10x17.
    # Return list of steps of move/capture in number format depending on color.
    nsteps = mad100.parse_move(move)
    return ( nsteps if color == WHITE else map(lambda i: 51-i, nsteps) )

def mprint_pos(color, pos):
    if color == WHITE:
       mad100.print_pos(pos)
    else:
       mad100.print_pos(pos.rotate())
    print( str(['white', 'black'][color]) + ' to move ')

def render_pv(origc, pos, tp):
    # Returns principal variation string of scores and moves from transposition table tp
    res = []
    color = origc
    res.append('|')
    entry = mad100_search.Entry_pv(None, None, None)
    for entry in mad100_search.gen_pv(pos, tp):
       # res.append(str(entry.pos.score))

       if entry.move is None:
          res.append('null')
       move = mrender_move(color, entry.move)
       res.append(move)

       res.append('|')
       color = 1-color

    res.append(" final score: ")
    if entry.score is not None:
       res.append(str(abs(entry.score)))
    return ' '.join(res)


###############################################################################
def main():
   print('nothing to do')
   return 0

if __name__ == '__main__':
    main()
