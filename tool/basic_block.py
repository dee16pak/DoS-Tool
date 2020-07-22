from math import *
from z3 import *
from loop_patterns import check_function_calldataload_pattern, check_external_function_pattern
import globals_var


##########################################################################
##### Basic block data structure{
#       start_pos
#       start_step
#       end_pos
#       end_step
#       exits : []
#     }     
##### where exits is a list of dictionary where current block can jump{
#           step : step of operand from where branch starts
#           step_pos : pos of step of operand from where branch starts
#           operand 'o' : operand of curr block from where branch starts
#           exit_to_block : branched block step     
#      }
########################################################################## 
def create_basic_block(parsed_code):
    block_list = []
    block = {'start_pos' : 0, 'start_step' : 0, 'end_pos' : 0, 'end_step' : 0, 'exits' : []}

    for i in range(len(parsed_code)):

        if parsed_code[i]['o'] == 'JUMPDEST':

            if parsed_code[i-1]['o'] not in ['INVALID', 'JUMP', 'RETURN', 'STOP', 'REVERT']:
                branch = {'step' : parsed_code[i-1]['step'], 'step_pos' : i-1, 'o' : parsed_code[i-1]['o'], 'exit_to_block' : parsed_code[i]['step']}
                block['exits'].append(branch)

            block_list.append(block)
            block = {'start_pos' : i, 'start_step' : parsed_code[i]['step'], 'end_pos' : i, 'end_step' : parsed_code[i]['step'], 'exits' : []}

        elif parsed_code[i]['o'] == 'INVALID':
            pass

        elif parsed_code[i]['o'] == 'JUMP' or parsed_code[i]['o'] == 'JUMPI':

            if parsed_code[i-1]['o'].find('PUSH') >= 0:
                branch = {'step' : parsed_code[i]['step'], 'step_pos' : i, 'o' : parsed_code[i]['o'], 'exit_to_block' : int(parsed_code[i-1]['input'], 16)}
            else:
                branch = {'step' : parsed_code[i]['step'], 'step_pos' : i, 'o' : parsed_code[i]['o'], 'exit_to_block' : -1}

            block['exits'].append(branch)
            block['end_step'] = parsed_code[i]['step']
            block['end_pos'] = i
    
        elif parsed_code[i]['o'] == 'STOP':

            block['end_step'] = parsed_code[i]['step']
            block['end_pos'] = i
            block_list.append(block)
            if i + 1 < len(parsed_code):
                block = {'start_pos' : i+1, 'start_step' : parsed_code[i+1]['step'], 'end_pos' : i+1, 'end_step' : parsed_code[i+1]['step'], 'exits' : []}
            else:
                break


        else:
            block['end_step'] = parsed_code[i]['step']
            block['end_pos'] = i
    block_list.append(block)
    
    # for i in block_list:
    #     print(i)
    return make_graph(block_list)


##########################################################################
##### Reverse the control flow graph     #################################
########################################################################## 
def reverse_adjacency_list(adjancy_list):

    reversed_adjacency_list = {}
    for i in adjancy_list:
        for j in adjancy_list[i]:
            if j not in reversed_adjacency_list:
                reversed_adjacency_list[j] = [i]
            elif i not in reversed_adjacency_list[j]:
                reversed_adjacency_list[j].append(i)

    for i in adjancy_list:
        if i not in reversed_adjacency_list:
            reversed_adjacency_list[i] = []
    # sorted(reversed_adjacency_list)

    # for i in reversed_adjacency_list:
    #     print(i, reversed_adjacency_list[i])
    
    return reversed_adjacency_list

        
##########################################################################
##### Create control flow graph from basic block list     ################
########################################################################## 
def make_graph(basic_block_list):

    adjancy_list = {}
    for i in range(len(basic_block_list)):
        aj = []
        for j in basic_block_list[i]['exits']:
            if j['exit_to_block'] != -1 and j['exit_to_block'] not in aj:
                aj.append(j['exit_to_block'])
        adjancy_list[basic_block_list[i]['start_step']] = aj

    # for i in adjancy_list:
    #     print(i, adjancy_list[i])

    return adjancy_list
    # reverse_adjacency_list(adjancy_list)
    # generate_strongly_connected_components(adjancy_list)



def dfs_helper(node, adjancy_list, st, visited, record_component, st_temp):

    st_temp.append(node)
    if node in adjancy_list:
        for i in adjancy_list[node]:
            if i not in visited:
                visited.append(i)
                dfs_helper(i, adjancy_list, st, visited, record_component, st_temp)
    if record_component:
        if st_temp not in st:
            st.append(st_temp)
    else: 
        if node not in st:  
            st.append(node)


def dfs(l, adjancy_list, record_component):
    st = []
    
    visited = []
    for i in l:
        st_temp = []
        if i not in visited:
            visited.append(i)
            dfs_helper(i, adjancy_list, st, visited, record_component, st_temp)
    
    return st



def generate_strongly_connected_components(adjancy_list):

    
    l = []
    for i in adjancy_list:
        l.append(i)
    st = dfs(l, adjancy_list, False)
    # for i in st:
    #     print(i)
    st.reverse()
    # print(st)
    reversed_adjacency_list = reverse_adjacency_list(adjancy_list)
    s = dfs(st, reversed_adjacency_list, True)
    # print(s)
    se = all_cycles_johnson_algo(s, adjancy_list)
    return se


visited = []
visited_map = {}
cycle = []
def unblock(node):
    # visited.remove(node)
    temp = node
    while(temp in visited_map):
        if temp in visited:
            visited.remove(temp)
        temp2 = visited_map[temp]
        del visited_map[temp]
        temp = temp2
    if temp in visited:
        visited.remove(temp)



def all_cycles_johnson_algo_helper(startnode, node, graph_stack, adjancy_list, scc):
    
    if node in adjancy_list:
        for i in adjancy_list[node]:
            if i in scc:
                if i == startnode:
                    # graph_stack2 = copy.deepcopy(graph_stack)
                    cycle.append(copy.deepcopy(graph_stack))
                    # print("cycle")
                    
                elif i not in visited:
                    visited.append(i)
                    graph_stack.append(i)
                    # print(i,node)
                    all_cycles_johnson_algo_helper(startnode, i, graph_stack, adjancy_list, scc)
                    graph_stack.pop()
                elif i in visited and i != startnode:
                    # print("helo")
                    visited_map[i] = node
                # print("cycle", cycle)
        unblock(node)
            

##########################################################################
##### All simple cycle Johnson Algorithm    ##############################
##########################################################################   
def all_cycles_johnson_algo(strongly_connected_component, adjancy_list):
    
    cycle.clear()
    for scc in strongly_connected_component:
        for node in scc:
            graph_stack = []
            visited.clear()
            visited_map.clear()
            visited.append(node)
            graph_stack.append(node)
            all_cycles_johnson_algo_helper(node, node, graph_stack, adjancy_list, scc)
            scc.remove(node) 
    cycle_temp = copy.deepcopy(cycle)  
    return cycle_temp


def external_function_values(pos, parsed_code, pattern):

    if pattern == 0:
        return parsed_code[pos]['input'], int(parsed_code[pos + 3]['input'], 16)
    elif pattern == 1:
        return parsed_code[pos]['input'], int(parsed_code[pos + 2]['input'], 16)


##########################################################################
##### list of dict og External function signature and starting block   ###
########################################################################## 
def find_external_function(parsed_code):

    pat_found = False
    calldataload_found = False
    external_function = []

    for i in range(len(parsed_code)):
        # print(parsed_code[i]['step'])
        if parsed_code[i]['o'] == 'JUMPDEST':

            if pat_found:
                break

            calldataload_found = False

        elif calldataload_found == False:

            if parsed_code[i]['o'] == 'PUSH1' and parsed_code[i]['input'] == '00':

                calldataload_found = check_function_calldataload_pattern(i, parsed_code)

        elif calldataload_found == True:

            if parsed_code[i]['o'] == 'PUSH4':

                external_function_pattern, pattern = check_external_function_pattern(i, parsed_code)

                if external_function_pattern:

                    pat_found = True
                    external_function_signature, function_block = external_function_values(i, parsed_code, pattern)
                    external_function.append({'fun_sig' : external_function_signature, 'fun_block' : function_block})

    return external_function


def bfs(adjancy_list, source_node):

    queue = []
    visited = []
    queue.append(source_node)

    while len(queue) != 0:

        elem = queue.pop(0)
        if elem not in visited:

            visited.append(elem)
            if elem in adjancy_list:
                for i in adjancy_list[elem]:
                    queue.append(i)

    return visited


##########################################################################
##### List of external functions from where we can reach the block    ####
########################################################################## 
def block_reachable_from_external_fun(adjancy_list, external_function_list):

    p = {}
    for i in external_function_list:

        visited = bfs(adjancy_list, i['fun_block'])

        for j in visited:
            if j not in p:
                p[j] = [i['fun_block']]
            else:
                p[j].append(i['fun_block'])

    return p
         

##########################################################################
##### Updated Control flow graph after symbolic phase    #################
########################################################################## 
def updated_adjacency_list(visited, adjacency_list):
    
    temp = {}
    temp.clear()

    for i in adjacency_list:
        if i in visited:
            temp[i] = []
            for j in adjacency_list[i]:
                if j in visited:
                    temp[i].append(j)
    
    return temp


##########################################################################
##### Check current block is in loop    ##################################
########################################################################## 
def check_in_loop(curr_block, loops):

    for i in loops:
        
        if curr_block in i:
            return True

    return False

# count = 0
def count_total_path_helper(node, visited, adjacency_list, count):

    visited.append(node)
    var = True

    if node in adjacency_list:
        for i in adjacency_list[node]:
            if i not in visited:
                var = False
                count_total_path_helper(i, visited, adjacency_list, count)
    
        if var:
            count[0] = count[0] + 1



def count_total_path(adjacency_list):

    count = [0]
    visited = []
    
    for node in adjacency_list:
        if node not in visited:
            # visited.append(node)
            count_total_path_helper(node, visited, adjacency_list, count)

    return count



def check_for_loop(vt, curr_block):
    v = copy.deepcopy(vt)
    v.pop(0)
    l = []
    for node in v:
        if node == curr_block:
            l.append(copy.deepcopy(node))
            return l
        elif node in l:
            return []
        l.append(copy.deepcopy(node))
    
    return []

def store_vulnerability(v_data, loop):

    # print(loop)
    # print(v_data)
    for node in loop:
        if node in v_data:
            for vuln in v_data[node]:
                if len(vuln) == 3:
                    if vuln[1] not in loop:
                        if vuln[2] not in globals_var.result:
                            globals_var.result.append(vuln[2])
                else:
                    if vuln[0] not in globals_var.result:
                        globals_var.result.append(vuln[2])
 

            
