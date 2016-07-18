#!/usr/bin/env python

from collections import namedtuple

#=====================================================================
# Move logic for Draughts 100 International Rules
#=====================================================================

# Remember:
# - The internal respresentation of our board is a list (array) of 52 char
# - Moves are always calculated for white (uppercase letters) at high numbers!!
# - If black is to move, black and white are swapped and the board is rotated.

# Directions: external representation; table gives for each square the next square depending on direction
NE_ext = (
   '   00  00  00  00  00   '    # 01 - 05
   ' 01  02  03  04  05     '    # 06 - 10
   '   07  08  09  10  00   '    # 11 - 15
   ' 11  12  13  14  15     '    # 16 - 20
   '   17  18  19  20  00   '    # 21 - 25
   ' 21  22  23  24  25     '    # 26 - 30
   '   27  28  29  30  00   '    # 31 - 35
   ' 31  32  33  34  35     '    # 36 - 40
   '   37  38  39  40  00   '    # 41 - 45
   ' 41  42  43  44  45     '    # 46 - 50
)

NW_ext = (
   '   00  00  00  00  00   '    # 01 - 05
   ' 00  01  02  03  04     '    # 06 - 10
   '   06  07  08  09  10   '    # 11 - 15
   ' 00  11  12  13  14     '    # 16 - 20
   '   16  17  18  19  20   '    # 21 - 25
   ' 00  21  22  23  24     '    # 26 - 30
   '   26  27  28  29  30   '    # 31 - 35
   ' 00  31  32  33  34     '    # 36 - 40
   '   36  37  38  39  40   '    # 41 - 45
   ' 00  41  42  43  44     '    # 46 - 50
)

SE_ext = (
   '   07  08  09  10  00   '    # 01 - 05
   ' 11  12  13  14  15     '    # 06 - 10
   '   17  18  19  20  00   '    # 11 - 15
   ' 21  22  23  24  25     '    # 16 - 20
   '   27  28  29  30  00   '    # 21 - 25
   ' 31  32  33  34  35     '    # 26 - 30
   '   37  38  39  40  00   '    # 31 - 35
   ' 41  42  43  44  45     '    # 36 - 40
   '   47  48  49  50  00   '    # 41 - 45
   ' 00  00  00  00  00     '    # 46 - 50
)

SW_ext = (
   '   06  07  08  09  10   '    # 01 - 05
   ' 00  11  12  13  14     '    # 06 - 10
   '   16  17  18  19  20   '    # 11 - 15
   ' 00  21  22  23  24     '    # 16 - 20
   '   26  27  28  29  30   '    # 21 - 25
   ' 00  31  32  33  34     '    # 26 - 30
   '   36  37  38  39  40   '    # 31 - 35
   ' 00  41  42  43  44     '    # 36 - 40
   '   46  47  48  49  50   '    # 41 - 45
   ' 00  00  00  00  00     '    # 46 - 50
)

# Directions: for example, first square from i in direction NE is NE[i]
NE = [0] + map( int, NE_ext.split() ) + [0]
NW = [0] + map( int, NW_ext.split() ) + [0]
SE = [0] + map( int, SE_ext.split() ) + [0]
SW = [0] + map( int, SW_ext.split() ) + [0]

def diagonal(i, d):
   # Generator for squares from i in direction d
   next = i
   stop = d[next] == 0
   while not stop:
      next = d[next]
      stop = d[next] == 0
      yield next

directions = {
    'P': (NE, SE, SW, NW),    # piece can move forward but captures in all directions
    'K': (NE, SE, SW, NW)     # king can move in all directions
}

Move = namedtuple('Move', 'steps takes')      # steps/takes are arrays of numbers 

def gen_bmoves(board, i):   # PRIVATE ============================
   # Generator for moves or one-take captures for square i
   moves, captures = [], []     # output lists
   p = board[i]
   if not p.isupper(): return   # only moves for player
   for d in directions[p]:
      if p == 'P':
         q = board[d[i]]
         if q == '0': continue       # direction empty; try next direction
         if q == '.' and (d[i] == NE[i] or d[i] == NW[i]):
            # move detected; save and continue
            moves.append(Move([ i, d[i] ], []))

         if q.islower():
            r = board[ d[d[i]] ]     # second diagonal square
            if r == '0': continue    # no second diagonal square; try next direction
            if r == '.':
               # capture detected; save and continue
               captures.append(Move([ i, d[d[i]] ], [ d[i] ]))
      if p == 'K':
         take = None
         for j in diagonal(i, d):     # diagonal squares from i in direction d
            q = board[j]
            if q.isupper(): break     # own piece on this diagonal; stop
            if q == '0': break        # stay inside the board; stop with this diagonal
            if q == '.' and take == None:
               # move detected; save and continue
               moves.append(Move([i,j], []))
            if q.islower() and take == None:
               take = j      # square of q
               continue

            if q.islower() and take != None: break
            if q == '.' and take != None:
               # capture detected; save and continue
               captures.append(Move([i,j], [take]))
   # output generator
   if captures != []: 
      for m in captures: yield m
   elif moves != []: 
      for m in moves: yield m
# END def gen_bmoves ============================================

def gen_extend_move(board, move):   # PRIVATE ===================
   # move is capture and maybe incomplete; try to extend it with basic captures
   # return generator of extended captures

   if move.steps == []: return   # empty move; return empty generator
   if move.takes == []: return   # no capture; return empty generator
   n_from = move.steps[0]
   n_to = move.steps[-1]     # last step
   new_board = list(board)   # clone of the board after doing the capture without taking the pieces
   new_board[n_from] = '.'
   new_board[n_to] = board[n_from]

   for bmove in gen_bmoves(new_board, n_to):
      new_move = Move(list(move.steps), list(move.takes))  # make copy of move and extend it
      if bmove.takes == []: continue                 # no capture; nothing to extend
      if bmove.takes[0] in move.takes: continue      # do not capture the same piece
      new_move.steps.append(bmove.steps[1])
      new_move.takes.append(bmove.takes[0])
      yield new_move

# END gen_extend_move ============================================

def gen_moves_of_square(board, i):  # PRIVATE ====================
   # Make list with completed moves of square i

   def gen_extend_next(board, move):
      # Make generator of all moves that can extend given move (only for captures, use recursion)
      # If move is not a capture, return generator of one move
      thing_generated = False
      for new_move in gen_extend_move(board, move):
         thing_generated = True
         for val in gen_extend_next(board, new_move): yield val     # RECURSION
      if not thing_generated:
         #print('ready', move)
         yield move
   # gen_extend_next

   for bmove in gen_bmoves(board, i):
      for move in gen_extend_next(board, bmove):   # make move complete 
         #print('OUT: ', move)
         yield move
# END gen_moves_of_square ============================================

def gen_moves_of_board(board):  # PRIVATE ============================
   for i, p in enumerate(board):
      if not p.isupper(): continue
      for move in gen_moves_of_square(board, i):
         yield move
# END gen_moves_of_board =============================================


def gen_moves(pos):  # PUBLIC
   # Returns generator of all legal moves of a board for player white (capital letters).
   # Move is a named tuple with list of steps and list of takes
   # Implementation detail: multiple use of the generator function
   # Change: performance enhancement, moveList; 18-07-2016

   moveList = []
   max_takes = 0
   for move in gen_moves_of_board(pos.board):
      max_takes = max(max_takes, len(move.takes))
      moveList.append(move)

   for move in moveList:
      #print('MAX/MOVE: ', max_takes, move.takes)
      if len(move.takes) == max_takes:
         yield move

# END gen_moves ============================================

def hasCapture(pos):  # PUBLIC
   # Returns true if capture found for position else false.
   for i, p in enumerate(pos.board):
      if not p.isupper(): continue
      for move in gen_bmoves(pos.board, i):
         if len(move.takes) > 0: return True
   return False

# END hasCapture ============================================

def test1(pos, i):  # PUBLIC
   for bmove in gen_bmoves(pos.board, i):
      yield bmove

def test2(pos):  # PUBLIC
   move = Move([25,18], [22])
   for emove in gen_extend_move(pos.board, move):
      yield emove

def test3(pos,i):  # PUBLIC
   for move in gen_moves_of_square(pos.board, i):
      yield move

def main():
   print('nothing to do')
   return 0

if __name__ == '__main__':
    main()
