#!/usr/bin/env python

#######################################################################################
# Implementation of alternative search functions:
# 1. MTD-bi search
# 2. Forced variation: search only for moves that leads to a capture for the opponent.
# 3. Normal alpha-beta search with aspiration windows
# Implementation of an opening book.
#######################################################################################

import os.path
import re
from random import randint
from collections import OrderedDict, namedtuple
from mad100_moves import gen_moves, hasCapture, Move
from mad100_play import mrender_move, render_pv, mparse_move, mprint_pos
import mad100

TABLE_SIZE = 1e6  # constant of maximum number allowed items in transposition table.

# The MAX_NODES constant controls how much time we spend on looking for optimal moves.
# This is the default max number of nodes searched.
#
MAX_NODES = 1000

# The MATE_VALUE constant is the limit for stop searching 
#   score <= -MATE_VALUE: player won
#   score >=  MATE_VALUE: player lost
# Theoretical the mate value must be greater than the maximum possible score
#
MATE_VALUE = 90000

Entry_pv = namedtuple('Entry_pv', 'pos score move')    # Entry for saving principal variation

###############################################################################
# MTD-bi search
###############################################################################

Entry_tp = namedtuple('Entry_tp', 'depth score gamma move')
tp = OrderedDict()                                     # Transposition Table: dict of Entry

def bound(pos, gamma, depth):
    # Alpha-beta pruning with null-window defined by gamma: [alpha, beta] = [gamma-1, gamma]
    # Parameter gamma is a guess of the exact score. It plays a role in a null-window search
    # with window [gamma-1, gamma]. Cut off childs if the real score >= gamma.
    # 
    global nodes; nodes += 1

    # Look in the tranposition table if we have already searched this position before.
    # We use the table value if it was done with at least as deep a search as ours,
    # and the gamma value is compatible.
    #
    entry = tp.get(pos.key())    # key() is board string
    if entry is not None and depth <= entry.depth and (
          entry.score < entry.gamma and entry.score < gamma or
          entry.score >= entry.gamma and entry.score >= gamma ):
       return entry.score      # Stop searching this node

    # Stop searching if we have won/lost.
    if abs(pos.score) >= MATE_VALUE:
       return pos.score

    # NULL MOVE HEURISTIC. For increasing speed.
    # The idea is that you give the opponent a free shot at you. If your position is still so good
    # that you exceed gamma, you assume that you'd also exceed gamma if you went and searched all of your moves.
    # So you simply return gamma without searching any moves.
    #
    nullswitch = True    ### *** set ON/OFF *** ###
    R = 3 if depth > 8 else 2              # depth reduction
    if depth >= 4 and not hasCapture(pos) and nullswitch:
       child = pos.rotate()    # position of opponent without move of player
       nullscore = -bound(child, 1-gamma, depth-1-R)     # RECURSION
       if nullscore >= gamma:
          return nullscore      # Nullscore high: stop searching this node

    # Evaluate or search further until end-leaves has no capture(s) (QUIESCENCE SEARCH)
    if depth <= 0 and not hasCapture(pos):
       return pos.score    # Evaluate position

    # We generate all possible legal moves and order them to provoke cuts.
    # At the next level of the tree we are going to minimize the score.
    # This can be shown equal to maximizing the negative score, with a slightly
    # adjusted gamma value.
    #
    best, bmove = -MATE_VALUE, None
    moveList = sorted(gen_moves(pos), key=pos.eval_move, reverse=True)

    for move in moveList:
       # Sort and iterate over the generator returned by gen_moves
       score = -1 * bound(pos.domove(move), 1-gamma, depth-1)   # RECURSION
       if score > best:
          best = score
          bmove = move
       if score >= gamma:   # CUT OFF
          break


    # UPDATE TRANSPOSITION TABLE
    # We save the found move together with the score, so we can retrieve it in the play loop.
    # We also trim the transposition table in FILO order.
    # We prefer fail-high moves, as they are the ones we can build our PV (Principal Variation) from.
    # Depth condition: we prefer an entry with higher depth value.
    #    So replace the already retrieved entry if depth >= entry.depth
    #
    if entry is None or ( depth >= entry.depth and best >= gamma ):
        tp[pos.key()] = Entry_tp(depth, best, gamma, bmove)   # key() is board string
        if len(tp) > TABLE_SIZE:
            tp.popitem()  # popitem removes and returns an arbitrary (key,value) pair

    return best

def search(pos, maxn=MAX_NODES):
    # Iterative deepening MTD-bi search, the bisection search version of MTD
    # See the term "MTD-f" at wikipedia.

    move = book_searchMove(pos)
    if move is not None:
       print('Move from opening book')
       depth, score, gamma, move = 0, pos.score, None, move
       tp[pos.key()] = Entry_tp(depth, score, gamma, move)
       if len(tp) > TABLE_SIZE:
          tp.popitem()  # popitem removes and returns an arbitrary (key,value) pair
       return move, pos.score

    global nodes; nodes = 0
    print('thinking ....   max nodes: %d' %(maxn) )
    print '%8s %8s %8s %8s' % ('depth', 'nodes', 'gamma', 'score')   # header

    # We limit the depth to some constant, so we don't get a stack overflow in the end game.
    for depth in range(1, 99):
        # The inner loop is a binary search on the score of the position.
        # Inv: lower <= score <= upper
        # However this may be broken by values from the transposition table,
        # as they don't have the same concept of p(score). Hence we just use
        # 'lower < upper - margin' as the loop condition.
        lower, upper = -MATE_VALUE, MATE_VALUE
        while lower < upper - 3: 
            gamma = (lower+upper+1)//2         # bisection !!   gamma === beta
            score = bound(pos, gamma, depth)   # AlphaBetaWithMemory
            if score >= gamma:
                lower = score
            if score < gamma:
                upper = score

        print '%8d %8d %8d %8d' % (depth, nodes, gamma, score)

        # We stop deepening if the global node counter shows we have spent too long for this depth
        if nodes >= maxn:
            break
        # We stop deepening if we have already won/lost the game.
        if abs(score) >= MATE_VALUE:
            break

    # We can retrieve our best move from the transposition table.
    entry = tp.get(pos.key())   # key() is board string
    if entry is not None:
        return entry.move, entry.score
    return None, score       # move unknown

def gen_pv(pos, tp):
    # Returns generator of principal variation list of scores and moves from transposition table
    poskeys = set()   # used to prevent loop
    postemp = pos.clone() 
    while True:
        entry = tp.get(postemp.key())  # get entry of transposition table
        if postemp.key() in poskeys:
           break    # Loop
        if entry is None:
           break
        if entry.move is None:
           yield Entry_pv(postemp, entry.score, entry.move)
           break

        yield Entry_pv(postemp, entry.score, entry.move)
        poskeys.add(postemp.key())
        postemp = postemp.domove(entry.move)


###############################################################################
# Search logic for Principal Variation Forced (PVF)
###############################################################################

Entry_tpf = namedtuple('Entry_tpf', 'depth score move')
tpf = OrderedDict()                   # Transposition table: dict of Entry_tpf

def minimax_pvf(pos, depth, player):
   # Fail soft negamax ab-pruning
   # Parameter player: alternating +1 and -1 (player resp. opponent)
   # Test for dedicated problems shows: can be much faster than MTD-bi search 

   global xnodes; xnodes += 1

   # Read transposition table
   entry = tpf.get(pos.key()) 
   if entry is not None and depth <= entry.depth:
      return entry.score      # Stop searching this node

   # Evaluate or search further until end-leaves has no capture(s) (QUIESCENCE SEARCH)
   if depth <= 0 and not hasCapture(pos):
      return pos.score    # Evaluate position

   best, bmove = -MATE_VALUE, None
   moveList = list(gen_moves(pos))

   #   mCount = sum(1 for x in moveList)   # count moves
   #   if mCount == 0:
   #      return -MATE_VALUE   # no moves at all, lost

   mCount = 0
   for move in moveList:
      child = pos.domove(move)

      if player == 0:
         if len(move.takes) == 0 and not hasCapture(child):
            # Player decides only to look at moves that leads to a capture for the opponent.
            # But captures of the player are always inspected.
            continue

      if player == 1:
         if len(move.takes) == 0:
            # Inspect only captures for opponent 
            continue

      # PRINT TREE
      ## print('===' * depth + '> ' + mrender_move(player, move) )

      mCount += 1
      score = -minimax_pvf(child, depth-1, 1-player)
      if score > best:
         best = score
         bmove = move

   if mCount == 0:      # stop: no moves that leads to a capture for the opponent.
      return pos.score

   # Write transposition table
   if entry is None or depth > entry.depth:
      tpf[pos.key()] = Entry_tpf(depth, best, bmove) 
      if len(tpf) > TABLE_SIZE:
         tpf.popitem()  # popitem removes and returns an arbitrary (key,value) pair

   return best

def search_pvf(pos, maxn=MAX_NODES):
   # Iterative deepening of forced variation sequence.
   global xnodes; xnodes = 0
   player = 0            # 0 = starting player; 1 = opponent 
   print('thinking ....   max nodes: %d' %(maxn) )
   print '%8s %8s %8s' % ('depth', 'nodes', 'score')   # header

   for depth in range(1, 99):
      best = minimax_pvf(pos, depth, player)

      ## REPORT
      print '%8d %8d %8d' % (depth, xnodes, best)
      #print(render_pv(0, pos, tpf))

      # We stop deepening if the global N counter shows we have spent too long for this depth
      if xnodes >= maxn:
         break

      # Looking for another stop criterium.
      # Sometimes a solution is found but search is going on until max nodes is reached.
      # We like to stop sooner and prevent waiting. But which stop citerium?

   # We can retrieve our best move from the transposition table.
   entry = tpf.get(pos.key()) 
   if entry is not None:
      return entry.move, best
   return None, best       # move unknown

###############################################################################
# Normal alpha-beta search with aspiration windows
###############################################################################

Entry_tpab = namedtuple('Entry_tpab', 'depth score move')
tpab = OrderedDict()              # Transposition table: dict of Entry_tpab

def alphabeta(pos, alpha, beta, depthleft, player):
   # Fail soft: function returns value that may exceed its function call arguments.
   # Separate player code for better understanding.
   # Use of the transposition table tpab 
   # TEST: uses 30-50% MORE nodes than MTD-bi search for getting the same result

   global ynodes; ynodes += 1

   # Read transposition table
   entry = tpab.get(pos.key()) 
   if entry is not None and depthleft <= entry.depth:
      return entry.score      # We know already the result: stop searching this node

   # Stop searching if we have won/lost.
   if abs(pos.score) >= MATE_VALUE:
      return pos.score

   # NULL MOVE HEURISTIC. For increasing speed.
   # The idea is that you give the opponent a free shot at you. If your position is still so good
   # that you exceed beta, you assume that you'd also exceed beta if you went and searched all of your moves.
   # So you simply return beta without searching any moves.
   #
   nullswitch = True    ### *** set ON/OFF *** ###
   R = 3 if depthleft > 8 else 2              # depth reduction
   if depthleft >= 4 and not hasCapture(pos) and nullswitch:
      child = pos.rotate()    # position of opponent without move of player
      nullscore = alphabeta(child, alpha, alpha+1, depthleft-1-R, 1-player)   # RECURSION
      if player == 0:
         if nullscore >= beta:
            return beta      # Nullscore high: stop searching this node
      if player == 1:
         if nullscore <= alpha:
            return alpha      # Nullscore low: stop searching this node

   moveList = sorted(gen_moves(pos), key=pos.eval_move, reverse=True)

   if player == 0:
      # Evaluate or search further until end-leaves has no capture(s) (QUIESCENCE SEARCH)
      if depthleft <= 0 and not hasCapture(pos):
         return pos.score    # Evaluate position

      bestValue = -MATE_VALUE 
      bestMove = None
      alphaMax = alpha            # clone of alpha (we do not want to change input parameter)

      for move in moveList:
         child = pos.domove(move)
         score = alphabeta(child, alphaMax, beta, depthleft-1, 1-player)   # RECURSION

         if score > bestValue:
            bestValue = score                  # bestValue is running max of score
            bestMove = move
         alphaMax = max(alphaMax, bestValue)   # alphaMax is running max of alpha
         if alphaMax >= beta: break            # beta cut-off
   if player == 1:
      # Evaluate or search further until end-leaves has no capture(s) (QUIESCENCE SEARCH)
      if depthleft <= 0 and not hasCapture(pos):
         return -1 * pos.score    # Evaluate position

      bestValue = MATE_VALUE  
      bestMove = None
      betaMin = beta              # clone of beta

      for move in moveList:
         child = pos.domove(move)
         score = alphabeta(child, alpha, betaMin, depthleft-1, 1-player) 
         if score < bestValue:
            bestValue = score                  # bestValue is running min of score
            bestMove = move
         betaMin = min(betaMin, bestValue)     # betaMin is running min of beta
         if betaMin <= alpha: break            # alpha cut-off

   # Write transposition table
   if entry is None or depthleft > entry.depth:
      tpab[pos.key()] = Entry_tpab(depthleft, bestValue, bestMove)  # gamma not used
      if len(tpab) > TABLE_SIZE:
         tpab.popitem()   # popitem removes and returns an arbitrary (key,value) pair

   return bestValue

def search_ab(pos, maxn=MAX_NODES):
    # Iterative deepening alpha-beta search enhanced with aspiration windows

    global ynodes; ynodes = 0
    lower, upper = -MATE_VALUE, MATE_VALUE
    valWINDOW = 50         # ASPIRATION WINDOW: tune for optimal results

    print('thinking ....   max nodes: %d' %(maxn) )
    print '%8s %8s %8s %8s %8s' % ('depth', 'nodes', 'score', 'alpha', 'beta')   # header

    # We limit the depth to some constant, so we don't get a stack overflow in the end game.
    alpha, beta = lower, upper
    depthleft = 1
    while depthleft < 100:
        player = 0            # 0 = starting player is max; 1 = opponent 
        score = alphabeta(pos, alpha, beta, depthleft, player)

        print '%8d %8d %8d %8d %8d' % (depthleft, ynodes, score, alpha, beta)

        # We stop deepening if the global N counter shows we have spent too long for this depth
        if ynodes >= maxn:
            break

        # We stop deepening if we have already won/lost the game.
        if abs(score) >= MATE_VALUE:
            break

        if score <= alpha or score >= beta:
           alpha, beta = lower, upper
           continue   # sadly we must repeat with same depthleft

        alpha, beta = score - valWINDOW, score + valWINDOW
        depthleft += 1

    # We can retrieve our best move from the transposition table.
    entry = tpab.get(pos.key())
    if entry is not None:
       return entry.move, entry.score
    return None, score       # move unknown

###############################################################################
# Logic Opening book
###############################################################################
Entry_open = namedtuple('Entry_open', 'freq')
tp_open = OrderedDict()           # Transposition Table: dict of Entry
WHITE, BLACK = 0, 1

def book_isPresent(f):
   return True if os.path.isfile(f) else False

def book_readFile(f):
   # Read opening book
   if not book_isPresent(f):
      print('Opening book not available: ' + f)
      return 0    # no opening book found

   print("Reading opening book <" + f + ">  ....")
   global tp_open; tp_open = OrderedDict()   # reset transposition table
   file = open(f, 'r')
   linecount = 0
   movecount = 0
   for line in file:
      linecount += 1
      line = line.rstrip('\n').strip()
      if line == '': continue
      movecount += book_addLine(line)
   file.close
   print("Opening book read: " + str(linecount) + " lines and " + str(movecount) + " positions")

def book_addLine(line):
   # Each line is an opening. Add entries to transposition table
   pos_start = mad100.newPos(mad100.initial_ext)  # starting position
   smoves = re.split(' ', line)

   ##print('add new opening')
   pos = pos_start
   color = WHITE
   movecount = 0
   for smove in smoves:
      smove = re.sub(r'[123456789]?[123456789]\.', '' , smove)  # remove move number '99.'

      steps = mparse_move(color, smove)
      move = mad100.match_move(pos, steps)

      success, pos = book_addEntry(pos, move)
      if not success:
         print('Illegal move in opening book', smove, line)
         break
      color = 1 - color      # alternating 0 and 1 (WHITE and BLACK)
      movecount += 1
   return movecount

def book_addEntry(pos, move):
   # Add entry for opening book to transposition table
   if move not in gen_moves(pos):
      print('Illegal move:', move)
      return False, None

   posnew = pos.domove(move)
   entry = tp_open.get(posnew.key()) 
   if entry is None:
      freq = 1
      ##print('New entry:', move, freq)
      tp_open[posnew.key()] = Entry_open(freq) 
   else:
      freq = entry.freq + 1
      ##print('New entry:', move, freq)
      tp_open[posnew.key()] = Entry_open(freq) 
   return True, posnew

def book_searchMove(pos):
   candidates = []    # list of candidate moves
   entry_cand = namedtuple('entry_cand', 'move freq')
   for move in gen_moves(pos):
      posnew = pos.domove(move)
      entry = tp_open.get(posnew.key()) 
      if entry is not None:
         ##print('move:', move)
         candidates.append(entry_cand(move, entry.freq))         

   if len(candidates) > 0:
      # Two strategies to select one candidate move
      # 1. Select move with highest frequence
      # 2. Select a random candidate move
      candidates.sort(key=lambda x: x.freq, reverse=True)

      s = 1       # make choice
      if s == 0:
         high_i = 0                                        # highest freq after sort
         sel_move = candidates[high_i].move 
         ##print('candidate highest freq:', candidates[high_i].move, candidates[high_i].freq ) 

      if s == 1:
         rand_i = randint( 0, len(candidates) - 1 )        # random
         sel_move = candidates[rand_i].move
         ##print('candidate random:', candidates[rand_i].move, candidates[rand_i].freq ) 

      return sel_move
   else:
      return None

###############################################################################
def main():
   print('nothing to do')
   return 0

if __name__ == '__main__':
    main()
