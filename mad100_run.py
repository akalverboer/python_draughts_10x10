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
from mad100 import initial_ext, initial_ext_test, board_ext_problem1, newPos, match_move
from mad100_moves import gen_moves, clearMoveTable, isLegal, moveTableSize
import mad100_search
from mad100_play import mprint_pos, mparse_move, mrender_move, render_pv, parseFEN

# Python 2 compatability
if sys.version_info[0] == 2:
    input = raw_input

WHITE, BLACK = 0, 1

def main():
    print("=============================================================")
    print("| MAD100: Python engine for draughts 100 international rules | ")
    print("=============================================================")

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
               board = initial_ext
            elif b == 1:
               board = initial_ext_test
            elif b == 2:
               board = board_ext_problem1   # test problem solving 1

            pos = newPos(board)
            color = WHITE            # WHITE / BLACK
            mad100_search.clearSearchTables()   # clear transposition tables
            clearMoveTable()
            mprint_pos(color, pos)

        elif comm.startswith('fen'):
            # setup position with fen string (!!! without apostrophes and no spaces !!!)
            if len(comm.split(' ', 1)) != 2: continue
            _, fen = comm.split(' ', 1)
            pos = parseFEN(fen)
            color = BLACK if fen[0] == 'B' else WHITE
            mad100_search.clearSearchTables()   # clear transposition tables
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


        elif comm.startswith('p'):
            if len(comm.split()) == 1:
               stack.append('p >')    # do next move in PV
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
                  lmove = match_move(pos, steps)

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
            print('| p: do moves of PV (principal variation) after go ')
            print('|   p >  : next move  ')
            print('|   p <  : previous move  ')
            print('|   p << : first position  ')
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
            # Most critical for speed is move generation, so we perform a test.
            # If no second argument, the moveTable is not disabled
            # If second argument, the maxtimes is set to the second argument.
            # Note that the speed depends on the position (number of legal moves)
            maxtimes = 10000   # default

            mt_disabled = False if len(comm.split()) == 1 else True
            if len(comm.split()) == 2:
               _, maxtimes = comm.split()
               maxtimes = int(maxtimes)

            t0 = time.time()
            for i in range(1,maxtimes):
               legalMoves = gen_moves(pos)
               if mt_disabled: clearMoveTable()
            t1 = time.time()

            print("Time elapsed for test: ", str(t1 - t0), "  Max times: ", str(maxtimes) )

        elif comm.startswith('test1'):
            # *** test1 ***
            moveTableSize()
        #===================================================================================
        else:
            print("Error (unkown command):", comm)

if __name__ == '__main__':
    main()
