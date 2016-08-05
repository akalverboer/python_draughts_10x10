#!/usr/bin/env python
# -*- coding: utf-8 -*-

#=====================================================================
# Commandline User interface
#=====================================================================

from __future__ import print_function
from __future__ import division
import re
import sys
import time
import mad100
from mad100_moves import Move, gen_moves, hasCapture, clearMoveTable, isLegal, moveTableSize
import mad100_search

# Python 2 compatability
if sys.version_info[0] == 2:
    input = raw_input

# MAD100 doesn't know about colors. Now we have to.
WHITE, BLACK = 0, 1

# FEN examples
FEN_INITIAL = "W:B1-20:W31-50"
FEN_MAD100_1 = "W:W15,19,24,29,32,41,49,50:B5,8,30,35,37,40,42,45."  # P.Lauwen, DP, 4/1977
FEN_MAD100_2 = "W:W17,28,32,33,38,41,43:B10,18-20,23,24,37."
FEN_MAD100_3 = "W:WK3,25,34,45:B38,K47."
FEN_MAD100_4 = "W:W18,23,31,33,34,39,47:B8,11,20,24,25,26,32."       # M.Dalman
FEN_MAD100_5 = "B:B7,11,13,17,20,22,24,30,41:W26,28,29,31,32,33,38,40,48."  # after 30-35 white wins

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

def main():
    print("=======================================================")
    print("| MAD100: engine for draughts 100 international rules | ")
    print("=======================================================")

    stack = []
    stack.append('new')          # initial board
    stack.append('nodes 1000')   # initial level
    ptr = -1                     # move pointer
    pv_list = []

    while True:
        if stack:
            comm = stack.pop()
        else: 
            comm = input('Command: ' )

        if comm.startswith('q'):  # quit
            break

        elif comm.startswith('legal'):  # show legal moves
            mprint_pos(color, pos)
            lstring = ''
            for lmove in gen_moves(pos):
               lstring += mrender_move(color, lmove) + '  '
            print('Legal moves: ', lstring)

        elif comm.startswith('nodes'):
            # Set max_nodes to search
            if len(comm.split()) == 1:
               max_nodes = mad100_search.MAX_NODES
            elif len(comm.split()) == 2:
               level = int(comm.split()[1])
               max_nodes = int(level) 
            print('   Level max nodes: %d' %(max_nodes) )

        elif comm.startswith('new'):
            # Setup new position
            b = 0  # TEST different positions
            if b == 0:
               board = mad100.initial_ext
            elif b == 1:
               board = mad100.initial_ext_test
            elif b == 2:
               board = mad100.board_ext_problem1   # test problem solving 1

            pos = mad100.newPos(board)
            color = WHITE            # WHITE / BLACK
            mad100_search.tp.clear()   # reset transposition table
            clearMoveTable()
            mprint_pos(color, pos)

        elif comm.startswith('fen'):
            # setup position with fen string (!!! without apostrophes and no spaces !!!)
            if len(comm.split(' ', 1)) != 2: continue
            _, fen = comm.split(' ', 1)
            pos = parseFEN(fen)
            color = BLACK if fen[0] == 'B' else WHITE
            mad100_search.tp.clear()   # reset transposition table
            clearMoveTable()
            mprint_pos(color, pos)

        elif comm == 'eval':
            mprint_pos(color, pos)
            print("Score position: ", pos.score)

        elif comm.startswith('go'):
            if len(comm.split()) == 1:
               # search for next move
               origc = color
               start = time.time()
               move, score = mad100_search.search(pos, maxn=max_nodes)
               finish = time.time()
               print("Time elapsed: ", str(finish - start))

               pv_list = list(mad100_search.gen_pv(pos, mad100_search.tp))
               ptr = -1
               print('Principal Variation: %s' % (render_pv(origc, pos, mad100_search.tp)))
            elif len(comm.split()) == 2:
               _, action = comm.split()

               if action == 'f':
                  # *** search for forced combinations ***
                  origc = color

                  ##mad100_search.tpf = mad100_search.OrderedDict()   # reset transposition table
                  start = time.time()
                  move, score = mad100_search.search_pvf(pos, max_nodes)
                  finish = time.time()
                  print("Time elapsed: ", str(finish - start))

                  pv_list = list(mad100_search.gen_pv(pos, mad100_search.tpf))
                  ptr = -1
                  print('Principal Variation: %s' % (render_pv(origc, pos, mad100_search.tpf)))
               elif action == 'ab':
                  # *** search with alpha-beta pruning ***
                  # search with normal alpha-beta for next move
                  origc = color

                  ##mad100_search.tpab = mad100_search.OrderedDict()   # reset transposition table
                  
                  start = time.time()
                  move, score = mad100_search.search_ab(pos, maxn=max_nodes)
                  finish = time.time()
                  print("Time elapsed: ", str(finish - start))
                  
                  pv_list = list(mad100_search.gen_pv(pos, mad100_search.tpab))
                  ptr = -1
                  print('Principal Variation: %s' % (render_pv(origc, pos, mad100_search.tpab)))

            if move is None:
               print('no move found', ' score: ', score)
            elif score <= -mad100_search.MATE_VALUE:
               print('very low score')
            else:
               print('Best move:', mrender_move(color, move))


        elif comm.startswith('pv'):
            if len(comm.split()) == 1:
               stack.append('pv >')    # do next move in PV
            elif len(comm.split()) == 2:
               _, action = comm.split()
               if len(pv_list) == 0:
                  print("No list of Principal Variation moves")
                  continue
               if action == '>':
                  # do next move in PV
                  if ptr == len(pv_list) -1:
                     print("End of Principal Variation list")
                     continue
                  ptr += 1
                  move = pv_list[ptr].move
                  if move in gen_moves(pos):
                     print('Move done:', mrender_move(color, move))
                     pos = pos.domove(move)
                     color = 1-color      # alternating 0 and 1 (WHITE and BLACK)
                     mprint_pos(color, pos)
                  else:
                     ptr -= 1
                     print("Illegal move; first run go")

               elif action == '<':
                  # to previous position of PV
                  if ptr < 0:
                     print("Begin of Principal Variation list")
                     continue
                  color = 1-color
                  pos = pv_list[ptr].pos
                  mprint_pos(color, pos)
                  ptr -= 1

               elif action == '<<':
                  # reset starting position
                  color = origc
                  ptr = -1
                  pos = pv_list[0].pos
                  mprint_pos(color, pos)
               elif action == '>>':
                  print('not used >>')

        elif comm.startswith('ping'):
            if len(comm.split()) != 2: continue
            _, N = comm.split()
            print('pong', N)

        elif comm.startswith('m'):
            if len(comm.split()) == 1:
               start = time.time()
               move, score = mad100_search.search(pos, maxn=max_nodes)
               finish = time.time()
               print("Time elapsed: ", str(finish - start))
                  
               if move is None:
                  print('no move found', ' score: ', score)
               elif score <= -mad100_search.MATE_VALUE:
                  print('very low score')
               else:
                  print('Principal Variation: %s' % (render_pv(color, pos, mad100_search.tp)))
                  print('Move done:', mrender_move(color, move))
                  pos = pos.domove(move)
                  color = 1-color      # alternating 0 and 1 (WHITE and BLACK)
                  mprint_pos(color, pos)

            elif len(comm.split()) == 2:
               _, smove = comm.split()
               smove = smove.strip()
               match = re.match('(^([0-5]?[0-9][-][0-5]?[0-9])$|^([0-5]?[0-9]([x][0-5]?[0-9])+)$)', smove)
               if match:
                  steps = mparse_move(color, smove)
                  lmove = mad100.match_move(pos, steps)

                  if lmove in gen_moves(pos):
                     ###print('MOVE: ', lmove)
                     pos = pos.domove(lmove)
                     color = 1-color      # alternating 0 and 1 (WHITE and BLACK)
                     mprint_pos(color, pos)
                  else:
                     print("Illegal move; please enter a legal move")
               else:
                  # Inform the user when invalid input is entered
                  print("Please enter a move like 32-28 or 26x37")

        elif comm.startswith('book'):
            # *** init opening book ***
            start = time.time()
            #mad100_search.book_readFile('data/openbook_test15')
            mad100_search.book_readFile('data/mad100_openbook')
            finish = time.time()
            print("Time elapsed: ", str(finish - start))

        elif comm.upper().startswith('H') or comm.startswith('?'):
            print(' _________________________________________________________________  ')
            print('| Use one of these commands:  ')
            print('|  ')
            print('| q:           quit  ')
            print('| h:           this help info  ')
            print('| new:         setup initial position  ')
            print('| fen <fen>:   setup position with fen-string  ')
            print('| eval:        print score of position  ')
            print('| legal:       show legal moves  ')
            print('| nodes <num>: set max number of nodes for search (or default)  ')
            print('|  ')
            print('| m       : let computer search and play a move  ')
            print('| m <move>: do move (format: 32-28, 16x27, etc)  ')
            print('|  ')
            print('| pv: do moves of PV (principal variation) ')
            print('|   pv >  : next move  ')
            print('|   pv <  : previous move  ')
            print('|   pv << : first position  ')
            print('|  ')
            print('| go: search methods for best move and PV generation  ')
            print('|   go    : method 1 > MTD-bi  ')
            print('|   go f  : method 2 > forced variation  ')
            print('|   go ab : method 3 > alpha-beta search  ')
            print('|  ')
            print('| book: init opening book  ')
            print('|_________________________________________________________________  ')
            print()

        elif comm.startswith('test0'):
            # *** test0   Performance ***
            # Most critical for speed is move generation, so we perform a test.
            t0 = time.time()

            lstring = ""
            for i in range(1,3000):
               for lmove in gen_moves(pos):
                  lstring += mrender_move(color, lmove) + "  "

            t1 = time.time()
            print("Time elapsed for test: ", str(t1 - t0))

        elif comm.startswith('test1'):
            # *** test1 ***
            moveTableSize()

        else:
            print("Error (unkown command):", comm)

if __name__ == '__main__':
    main()
