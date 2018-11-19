Python script that executes the byzantine generals problem

Each general run as an individual thread.

The script receives 3 arguments:

1) Number of generals
2) Number of faults
3) A number in (0,1) that says if the commander is a traitor. 0 for loyal, 1 otherwise.

Example with 7 generals, 2 faults and the commander is a traitor: 
$python byzantine.py 7 2 1

The implementation uses anytree python library to deal with tree structures.
To install: $pip install anytree

The result decision tree for each process is written to disk with the id name in
the results folder.
