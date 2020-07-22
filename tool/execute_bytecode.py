from parse_bytecode import parse, separate_runtime_code
from loop_patterns import check_infinite
from execute_block import execute_bl
import globals_var
import sys
import basic_block
from z3 import *

##########################################################################
##### Reading smart contract bytecode from file input ####################
##########################################################################    
file_name = sys.argv[1]
# print(file_name)
file_open = open(file_name, 'r')

lines = file_open.readlines()

globals_var.code_string = ''
for line in lines:
    globals_var.code_string = globals_var.code_string + line.strip()
# print(globals_var.code_string)

max_invocation = int(sys.argv[2])
globals_var.stop_ins = 0
globals_var.max_path_len = int(sys.argv[3])

##########################################################################
##### Separating deploy and runtime code #################################
##########################################################################
parsed_code = parse(globals_var.code_string)
# for j in parsed_code:
#     print(j)
deploy_parsed_code, runtime_parsed_code = separate_runtime_code(parsed_code)
# print(deploy_code)
# print(runtime_code)
# for j in deploy_parsed_code:
#     print(j)
# for j in runtime_parsed_code:
#     print(j)


##########################################################################
##### Generating first level adjacency list ##############################
##########################################################################
deploy_adjancy_list = basic_block.create_basic_block(deploy_parsed_code)
runtime_adjancy_list = basic_block.create_basic_block(runtime_parsed_code)
# print(deploy_adjancy_list)
paths_before_symbolic_phase = basic_block.count_total_path(runtime_adjancy_list)
# for i in adjancy_list:
#     print(i)
# print(deploy_adjancy_list)
# for i in runtime_adjancy_list:
#     print(i, runtime_adjancy_list[i])


##########################################################################
##### Extracing external function signature ##############################
##########################################################################
external_function = basic_block.find_external_function(runtime_parsed_code)
# print(external_function)


##########################################################################
##### Basic block reachable from external function #######################
##########################################################################
# p = basic_block.block_reachable_from_external_fun(runtime_adjancy_list, external_function)
# print(p)


##########################################################################
##### deploy code symbolic analysis ######################################
##########################################################################
stack = []
memory = {}
storage = {}
symbolic = []
deploy_loops = []
v = [0]
v_data = {}
visited = []
visited.append(0)
globals_var.block_visit_count = {}
globals_var.result = []
# globals_var.loops_from_external_fun = {}
execute_bl(0, deploy_parsed_code, stack, memory, storage, symbolic, 0, deploy_loops, 0, v, v_data, visited, deploy_adjancy_list, 0, external_function, [])
# print(visited)
deploy_adjancy_list = basic_block.updated_adjacency_list(visited, deploy_adjancy_list)
###################################################################################################
for i in storage:
    if 'updated' in storage[i]:
        del storage[i]['updated']

    if 'pre_mod' in storage[i]:
        del storage[i]['pre_mod']
    
    # print(storage[i])
    if str(simplify(storage[i]['z3'])).find('sym-pure') >= 0:
        
        s = str(simplify(storage[i]['z3']))
        s = s.replace('sym-pure', 'sym-constructor')
        storage[i]['z3'] = BitVec(s, 256)
    
    if str(simplify(storage[i]['z3'])).find('sym-mod') >= 0:
        
        s = str(simplify(storage[i]['z3']))
        s = s.replace('sym-mod', 'sym-constructor')
        storage[i]['z3'] = BitVec(s, 256)
        
# print(storage)
####################################################################################################


##########################################################################
##### More than 1 invocations test for runtime code ######################
##########################################################################
visited = []
visited.append(0)
for i in range(max_invocation):
    stack = []
    memory = {}
    symbolic = []
    runtime_loops = []
    v = [0]
    v_data = {}
    # visited = []
    # visited.append(0)
    globals_var.block_visit_count = {}
    globals_var.loops_from_external_fun.clear()

    execute_bl(0, runtime_parsed_code, stack, memory, storage, symbolic, 0, runtime_loops, 0, v, v_data, visited, runtime_adjancy_list, 0, external_function, [])

# paths_after_symbolic_resolve = basic_block.count_total_path(runtime_adjancy_list)
runtime_adjancy_list = basic_block.updated_adjacency_list(visited, runtime_adjancy_list)
paths_after_symbolic_phase = basic_block.count_total_path(runtime_adjancy_list)

# print(globals_var.result)
##########################################################################
##### loops in deploy and runtime code ###################################
##########################################################################
deploy_loops_CFG = basic_block.generate_strongly_connected_components(deploy_adjancy_list)
# print("deploy_loops=", deploy_loops)

runtime_loops_CFG = basic_block.generate_strongly_connected_components(runtime_adjancy_list)
# print("runtime_loops=", runtime_loops)


###################################################################################################
print('Total paths in Control Flow Graph before Symbolic Phase : ', paths_before_symbolic_phase)
# print('Total paths in Control Flow Graph after resolution : ', paths_after_symbolic_resolve)
print('Total paths in Control Flow Graph after Symbolic Phase : ', paths_after_symbolic_phase)
print('\n')

if len(globals_var.loops_from_external_fun) > 0:

    # print(globals_var.loops_from_external_fun)

    for loop in runtime_loops:

        key = ''

        for l in loop:
            key += str(l) + ':'

        if key in globals_var.loops_from_external_fun:

            print('Loop id ', loop, ' can be accessed from:')

            for ext_fun in globals_var.loops_from_external_fun[key]:

                # print(ext_fun)
                for k in ext_fun:
                    # print(k)
                    print('==> ', k['fun_sig'], end = ' ')
                
                print(' |', end = ' ')
            
            print('\n')
    
    print('\n')


if len(globals_var.result) > 0:
    for r in globals_var.result:
        if r['vulnerability_code'] == 1:
            print("Loop with symbolic variable condition found from path : ")
            
            for rt in r['path']:
                print("==>> ", rt['fun_sig'], end = " ")

            print("\n")

        if r['vulnerability_code'] == 2:
            print("Call to address changed by attacker found from path : ")
            
            for rt in r['path']:
                print("==>> ", rt['fun_sig'], end = " ")

            print("\n")

        if r['vulnerability_code'] == 3:
            print("Call to address changed by attacker in loop found from path : ")
            
            for rt in r['path']:
                print("==>> ", rt['fun_sig'], end = " ")

            print("\n")
        
        if r['vulnerability_code'] == 4:
            print("CREATE2 Opcode is found from path : ")
            
            for rt in r['path']:
                print("==>> ", rt['fun_sig'], end = " ")

            print("\n")

else:
    # print(len(deploy_loops))
    # print(runtime_loops)
    print("No Vulnerablilty found !!")
