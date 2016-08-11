
## Tutorial MAD100 engine for 10x10 international draughts

Start the engine in your commandline window. 
You see the initial position of a draughts board.
Below you can enter a command and instruct the engine to perform some action.
Type  **h**  for info about which commands are available.

##1. Let the engine play a game
Type repeatedly  **m**  to let the engine chooses moves.

##2. Play a game against the engine
If you start with white, type alternatively **m move** and **m**
For example type successively the commands:
- **m 32-28**
- **m**
- **m 37-32**
- **m**

If your move is invalid, the engine gives an error message.  
To display all legal moves for a position type the command: **legal**

##3. Initialize an opening book
You can tell the engine to play the first moves from a limited set of opening
scenarios. Each opening is 10 plies deep.  

To init the opening book type: **book**  

Start a new game by entering the command: **new**  

Type repeatedly **m** to let the engine chooses moves. The engine picks randomly 
an opening. Note that the engine answer the first 10 plies very fast.

##4. Searching for the best move
Searching for the best move is the key for a good engine.  
But what is the best move. It depends on how deep the engine can search and the
quality of the evaluation of a position. In case of material profit, the engine
can do the job very well. Let us see how our engine can do it.  

We set up a position with a so called FEN string. Enter the next command:  
**fen W:W18,23,31,33,34,39,47:B8,11,20,24,25,26,32.xxx**  

White can gain material profit. But before we let search the engine for the
best move, we increase the maximum number of nodes the engine gets for searching.  
Enter the command: **nodes 5000**  

Now let the engine search by giving the command: **go**  

Look at the output after finishing.  
First the time used for the search is shown.  
Then the so called Principal Variation (PV) is shown. The PV is the sequence of best
moves for both players. Note the final score. A high plus score is good for white.  
Let's see what the engine has in mind.
To skip forward through the PV, we use the command **p**   
To skip backward, use **p <**  To restart, type **p <<**  
Type repeatedly **p** and see how white wins the game.

##5. Alternative search methods
As a learning experiment, I implemented three search methods. The previous search
is called the MTD-bi search.  

If you type **go f** instead of **go** the engine uses another search method.
It is the method of *forced variation*. Both searches try to find a best move which
leads to the highest score. But the forced variation limits his move sequences to
moves where the opponent is forced to capture. The benefit is speed. But it does
not always lead to the best move.  

A third method is the well known *alpha-beta search*. Type **go ab** instead of
**go** to use this method. It is comparable with the first method. Allthough we
make use of aspiration windows for faster results, the MTD-bi method beats the
alpha-beta search in execution speed.  
Try the three methods in the example described before.

##6. Demo of search capabilities
We show you an example where the best move is based on a search of 21 moves!!  

Setup a position with:  
**fen W:W16,21,25,32,37,38,41,42,45,46,49,50:B8,9,12,17,18,19,26,29,30,33,34,35,36.**  

Set the nodes very high:  
**nodes 300000**  

Let the search start:  
**go**  

It takes some time for the engine to finish. Depending on the implementation, you
have to wait some time. In my case:  
- Python: 35 sec
- Nim :   27 sec
- Ruby:   140 sec

The game ends in a 1x1 position after 21 plies.  
The Principal Variation of the best move is:  
| 49-44 | 36x47 | 46-41 | 47x36 | 32-27 | 36x22 | 37-31 | 26x48 | 44-39 | 34x32   
| 25x3 | 17x26 | 45-40 | 35x44 | 50x17 | 12x21 | 3x37 | 48x31 | 16x36   
| final score:  -10  

##7. Performance issues.
I programmed the engine in three languages. I used the same data structures and
logic for each language. So a comparison of the three engines can learn us about
the execution speed of the three languages.  

The application is not designed for optimal performance. Also the programming
languages Python and Ruby are not suitable for high speed.  

Most critical for speed is move generation. I have performed a test to measure
the speed of move generation.  
To do the test enter **test0 number**. The number is the number of times the
move generation is executed. Use a number like 10000 or 20000.  

Comparing the three implementations for execution speed of move generation,
the order of speed is expected based on the demo at point 6: Nim, Python, Ruby.


