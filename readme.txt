The tool starts by executing execute_bytecode.py

3 arguments are needed for execution


Smart contract's bytecode in txt file

max_invocation => integer value (usually between 1 - 10)

max_pathlength => integer value (usually between 10 - 100)


Suppose we have bytecode of a smart contract stored in "sample.txt"

then command to run code will be

"python3 execute_byteode.py sample.txt max_invocation max_pathlength"



#############################################################################
parse_bytecode.py

conains functions to parse bytecode to opcode view and code separator functions



loop_patterns.py

checks for some fixed patterns: external function patterns etc



globals_var.py

contains state variables of the EVM and some more global variables



instructions.py

contains all instructions of the EVM and their corresponding hexadecimal values



execute_instruction.py

conatains execution of every EVM instructions for the symbolic analysis



execute_block.py

BFS for symbolic analysis which branches with JUMPI instructions



basic_block.py

Contains functions for creating basic blocks, create control flow graph adjacency list,
finding loops in control flow graph, count total path, store vulnerabilities etc




