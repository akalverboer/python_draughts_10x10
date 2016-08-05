#!/usr/bin/env python

from collections import OrderedDict, namedtuple

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

directions = [NE, SE, SW, NW]

Move = namedtuple('Move', 'steps takes')      # steps/takes are arrays of numbers 

moveTable = OrderedDict()   # dict to remember legal moves of a position for better performance
MOVETABLE_SIZE = 1000000


def bmoves_from_square(board, i):
   # List of moves (non-captures) for square i
   moves = []     # output list
   p = board[i]
   if not p.isupper(): return []  # only moves for player; return empty list

   if p == 'P':
      for d in directions:
         q = board[d[i]]
         if q == '0': continue       # direction empty; try next direction
         if q == '.' and (d[i] == NE[i] or d[i] == NW[i]):
            # move detected; save and continue
            moves.append(Move([ i, d[i] ], []))

   if p == 'K':
      for d in directions:
         take = None
         for j in diagonal(i, d):     # diagonal squares from i in direction d
            q = board[j]
            if q == '0': break         # stay inside the board; stop with this diagonal
            if q != '.': break         # stop this direction if next square not empty
            if q == '.':
               # move detected; save and continue
               moves.append(Move([ i, d[i] ], []))

   return moves
# end bmoves_from_square ======================================


def bcaptures_from_square(board, i):
   # List of one-take captures for square i
   captures = []     # output list
   p = board[i]
   if not p.isupper(): return []    # only captures for player; return empty list

   if p == 'P':
      for d in directions:
         q = board[d[i]]        # first diagonal square
         if q == '0': continue       # direction empty; try next direction
         if q == '.' or q.isupper(): continue

         if q.islower():
            r = board[ d[d[i]] ]     # second diagonal square
            if r == '0': continue         # no second diagonal square; try next direction
            if r == '.':
               # capture detected; save and continue
               captures.append(Move([ i, d[d[i]] ], [ d[i] ]))

   if p == 'K':
      for d in directions:
         take = None
         for j in diagonal(i, d):     # diagonal squares from i in direction d
            q = board[j]
            if q.isupper(): break        # own piece on this diagonal; stop
            if q == '0': break           # stay inside the board; stop with this diagonal
            if q.islower() and take == None:
               take = j      # square number of q
               continue

            if q.islower() and take != None: break 
            if q == '.' and take != None:
               # capture detected; save and continue
               captures.append(Move([i,j], [take]))

   return captures
# end bcaptures_from_square ======================================


def basicMoves(board):
   # Return list of basic moves of board; either captures or normal moves
   # Basic moves are normal moves or one-take captures
   bmoves_of_board = []
   bcaptures_of_board = []
   hasCapture = False

   for i, p in enumerate(board):
      if not p.isupper(): continue
      bcaptures = bcaptures_from_square(board, i)
      if len(bcaptures) > 0: hasCapture = True
      if hasCapture:
         bcaptures_of_board.extend( bcaptures )
      else:
         bmoves = bmoves_from_square(board, i)
         bmoves_of_board.extend( bmoves )

   if len(bcaptures_of_board) > 0:
      return bcaptures_of_board
   else:
      return bmoves_of_board

# end basicMoves


def searchCaptures(board):
   # Capture construction by extending incomplete captures with basic captures

   def boundCaptures(board, capture, depth ):
      # Recursive construction of captures.
      # - board: current board during capture construction
      # - capture: incomplete capture used to extend with basic captures
      # - depth: not used
      bcaptures = bcaptures_from_square(board, capture.steps[-1])   # new extends of capture

      completed = True
      for bcapture in bcaptures: 
         if len(bcapture.takes) == 0: continue         # no capture; nothing to extend
         if bcapture.takes[0] in capture.takes: continue      # do not capture the same piece

         n_from = bcapture.steps[0]
         n_to = bcapture.steps[-1]     # last step

         new_board = list(board)   # clone the board and do the capture without taking pieces
         new_board[n_from] = '.'
         new_board[n_to] = board[n_from]

         new_capture = Move(list(capture.steps), list(capture.takes))  # make copy of capture and extend it

         new_capture.steps.append(bcapture.steps[1])
         new_capture.takes.append(bcapture.takes[0])

         extended = False
         result = boundCaptures(new_board, new_capture, depth + 1)   # RECURSION

      if completed:
         # Update global variables
         global captures
         captures.append(capture)
         global max_takes
         max_takes = len(capture.takes) if len(capture.takes) > max_takes else max_takes

      return 0
   # end boundCaptures

   # ============================================================================
   global captures; captures = []       # result list of captures
   global max_takes; max_takes = 0       # max number of taken pieces

   depth = 0
   bmoves = basicMoves(board)

   for bmove in bmoves:
      if len(bmove.takes) == 0: break    # only moves, no captures; nothing to extend
      n_from = bmove.steps[0]
      n_to = bmove.steps[-1]     # last step

      new_board = list(board)      # clone the board and do the capture without taking pieces
      new_board[n_from] = '.'
      new_board[n_to] = board[n_from]
      result = boundCaptures(new_board, bmove, depth)

   ##print("Max takes: " + str(max_takes))

   result = [cap for cap in captures if len(cap.takes) == max_takes]
   return result

# end searchCaptures


def hasCapture(pos):     # PUBLIC
   # Returns True if capture for white found for position else False.
   for i, p in enumerate(pos.board):
      if not p.isupper(): continue
      bcaptures = bcaptures_from_square(pos.board, i)
      if len(bcaptures) > 0: return True 
   return False
# end hasCapture


def gen_moves(pos):       # PUBLIC
   # Returns list of all legal moves of a board for player white (capital letters).
   # Move is a named tuple with array of steps and array of takes
   #
   entry = moveTable.get(pos.key())
   if entry is not None: return entry 

   if hasCapture(pos):
      legalMoves = searchCaptures(pos.board)
   else:
      legalMoves = basicMoves(pos.board)

   moveTable[pos.key()] = legalMoves
   if len(moveTable) > MOVETABLE_SIZE:
      clearTable()
      ## moveTable.popitem()    # popitem removes and returns an arbitrary (key,value) pair

   return legalMoves
# end gen_moves ============================================


def isLegal(pos, move):     # PUBLIC
   # Returns True if move for position is legal else False.
   if move in gen_moves(pos):
       ## print('Illegal move: ' +  move)
       return True
   return False
# end isLegal


def clearMoveTable():        # PUBLIC
   # Clear moveTable
   moveTable.clear()


def moveTableSize():     # PUBLIC
   print('moveTable entries: ' + str(len(moveTable)))


# *********************************************************************************
def main():
   print('nothing to do')
   return 0

if __name__ == '__main__':
    main()
