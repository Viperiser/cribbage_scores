# Cribbage Skill Estimator
This is a utility for calculating MLE skill scores given some cribbage results. This has been designed specifically for four people, so will only work with exactly four players.

## Input Data
The input data are two files, 'participation' and 'scores'.

* 'participation' has a game_id column, and a column for each player. Each entry is 1 or 0 depending on whether that player played in that game.
* 'scores' has the same structured, but the entries correspond to whether that player won (or was on the winning team in a 4-player game).

## Output Data
The output is written to .json with the top level structure:
* played - a dict of numbers of games played by each player
* wins - a dict of numbers of wins by each player
* skills - a dict of MLE skill value for each player
* matches - for each combination of players, predicted outcomes and actual outcomes (where they exist).

index.html displays this data.

## Scripts
There is only one script - analysis.py. It calculates all the output data and assembles it in json form.

