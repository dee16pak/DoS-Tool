from instructions import *
from execute_instruction import *
from z3 import *
import globals_var
import basic_block
# from globals_var import stop_ins, pattern_found, loop_found


def execute_bl(pos, parsed_code, stack, memory, storage, symbolic, curr_block, loops, path_len, v, v_data, visited, adjancy_list, caller, external_fun_list, path_from_ext_fun):
    # global stop_ins, pattern_found, loop_found
    
    i = pos
    while i < len(parsed_code):
        # print(len(stack))
        # print("####################### STACK CONTENT ########################")
        # print(stack)
        # print("##############################################################")
        # print("####################### STORAGE CONTENT ########################")
        # print(storage)
        # print("##############################################################")
        # print("####################### SYMBOLIC CONTENT ########################")
        # print(symbolic)
        # print("##############################################################")
        op = parsed_code[i]['o']
        step = parsed_code[i]['step']
        # print("op= ", op)
        # print("step= ", step)
        if op == 'REVERT':
            # print("Normal revert to this path")
            break
        
        elif op == 'RETURN':
            # print("Normal return to this path")
            break

        elif op == 'JUMPI':
            
            # if i > len(parsed_code):
            #     print("pos > len(parsed_code)")
        
            # if allops[op][1] > len(stack):
            #     print("allops[op][1] < len(stack)")
            
            args = []
           
            for j in range(allops[op][1]):
                args.append(stack.pop())
            ######################################################################################################
            labelz = args[0]
            condz = args[1]

            if condz['type'] == 'undefined':
                # print("Condition to jump is not defined...")
                # print("Terminating Search to this path!!!")
                break

        
            s = Solver()
            # s.push()
            # s.add(simplify(condz['z3']) != 0)

            # if s.check() == sat:

            if labelz['type'] == 'constant' and is_bv_value(simplify(labelz['z3'])):
                
                if parsed_code[-1]['step'] >= simplify(labelz['z3']).as_long():

                    pos = 0

                    for j in range(len(parsed_code)):

                        if parsed_code[j]['step'] == simplify(labelz['z3']).as_long():
                            pos = j
                            break

                    if parsed_code[pos]['o'] == 'JUMPDEST':

                        if parsed_code[pos]['step'] not in adjancy_list[curr_block]:

                            adjancy_list[curr_block].append(parsed_code[pos]['step'])


                        if 'caller' in condz and not str(simplify(condz['z3'])).find('sym-pure') >= 0:
                            caller = 1
                        

                        if condz['type'] == 'constant' and str(simplify(condz['z3'])).find('sym-pure') >= 0 :
                            # print("loop found with symbolic variable condition")

                            rt = {'path' : path_from_ext_fun, 'vulnerability_code' : 1}
                            dtemp = [step, parsed_code[pos]['step'], rt]

                            if curr_block in v_data:
                                if dtemp not in v_data[curr_block]:
                                    v_data[curr_block].append(dtemp)
                            else:
                                v_data[curr_block] = [dtemp]

                            # rt = {'path' : path_from_ext_fun, 'vulnerability_code' : 1}
                            # if rt not in globals_var.result:
                            #     globals_var.result.append(rt)
                        
                        pos = pos - 1
                        stack2 = copy.deepcopy(stack)
                        memory2 = copy.deepcopy(memory)
                        symbolic2 = copy.deepcopy(symbolic)
                        # visited2 = copy.deepcopy(visited)
                        v2 = copy.deepcopy(v)
                        v_data2 = copy.deepcopy(v_data)
                        caller2 = copy.deepcopy(caller)
                        path_from_ext_fun2 = copy.deepcopy(path_from_ext_fun)
                        
                        if is_bv_value(simplify(condz['z3'])):
                            if 'z1' in condz and 'z2' in condz and is_bv_value(simplify(condz['z1'])) and is_bv_value(simplify(condz['z2'])):
                                # print(simplify(condz['z3']))
                                if simplify(condz['z1']).as_long() <= 10000 and simplify(condz['z2']).as_long() <= 10000 and basic_block.check_in_loop(curr_block, loops):
                                    execute_bl(pos + 1, parsed_code, stack2, memory2, storage, symbolic2, curr_block, loops, path_len, v2, v_data2, visited, adjancy_list, caller2, external_fun_list, path_from_ext_fun2)
                                    i = i + 1
                                else:
                                    i = i + 1
                            else:
                                s.push()
                                s.add(simplify(condz['z3']) != 0)
                                if s.check() == sat:
                                    execute_bl(pos + 1, parsed_code, stack2, memory2, storage, symbolic2, curr_block, loops, path_len, v2, v_data2, visited, adjancy_list, caller2, external_fun_list, path_from_ext_fun2)
                                    i = i + 1
                                else:
                                    i = i + 1
                                
                                s.pop() 

                        else:
                        
                            s.push()
                            s.add(simplify(condz['z3']) != 0)
                            if s.check() == sat:
                                execute_bl(pos + 1, parsed_code, stack2, memory2, storage, symbolic2, curr_block, loops, path_len, v2, v_data2, visited, adjancy_list, caller2, external_fun_list, path_from_ext_fun2)
                                i = i + 1
                            else:
                                i = i + 1
                            
                            s.pop() 

                    else:
                        # print("invalid jumpi position within the code and hence aborting this branch")
                        i = i + 1

            elif labelz['type'] == 'constant' and is_bv_value(simplify(labelz['z3'])) and parsed_code[-1]['step'] < simplify(labelz['z3']) or simplify(labelz['z3']) < 0:
                # print("Jumpi position is out of code scope and hence aborting this branch")
                i = i + 1

            elif labelz['type'] == 'constant' and not is_bv_value(simplify(labelz['z3'])):
                # print("jumpi position is symbolic and hence can result in problem and hence we are not exploring this branch further")
                i = i + 1

            elif labelz['type'] == 'undefined':
                # print("jumpi position is not defined and hence quitting this branch")
                i = i + 1
        
            # else:
            #     i = i + 1
            # s.pop()
            ######################################################################################################################
            s.push()
            s.add(simplify(condz['z3']) == 0)
            
            if s.check() == sat:
                
                stack2 = copy.deepcopy(stack)
                memory2 = copy.deepcopy(memory)
                symbolic2 = copy.deepcopy(symbolic)
                # visited2 = copy.deepcopy(visited)
                v2 = copy.deepcopy(v)
                v_data2 = copy.deepcopy(v_data)
                caller2 = copy.deepcopy(caller) 
                path_from_ext_fun2 = copy.deepcopy(path_from_ext_fun)
                
                execute_bl(i, parsed_code, stack2, memory2, storage, symbolic2, curr_block, loops, path_len, v2, v_data2, visited, adjancy_list, caller2, external_fun_list, path_from_ext_fun2)
                break
            
            else:
                # print("jumpi condition == 0 is not satisfiable and hence cannot explore normal branch, at pos = ", pos)
                s.pop()
                break
            
            s.pop()

        elif op == 'JUMP':
            
            args = []

            for j in range(allops[op][1]):
                args.append(stack.pop())

            ###################################################################################

            labelz = args[0]
            if labelz['type'] == 'constant' and is_bv_value(simplify(labelz['z3'])) and parsed_code[-1]['step'] >= simplify(labelz['z3']).as_long():

                for i in range(len(parsed_code)):

                    if parsed_code[i]['step'] == simplify(labelz['z3']).as_long():

                        pos = i
                        break

                if parsed_code[pos]['o'] == 'JUMPDEST':
                    # for deep in  adjancy_list:
                    #     print(deep, adjancy_list[deep])
                    if parsed_code[pos]['step'] not in adjancy_list[curr_block]:

                        adjancy_list[curr_block].append(parsed_code[pos]['step'])
                    
                    i = pos
                    pass
                
                else:
                    # print("Stoping search on this path because jump position is not valid")
                    break

            elif labelz['type'] == 'constant' and is_bv_value(simplify(labelz['z3'])) and (parsed_code[-1]['step'] < simplify(labelz['z3']).as_long() or simplify(labelz['z3']).as_long() < 0):
                # print("Stoping search on this path because jump position is either less than zero or greater than parsed code length")
                break

            elif labelz['type'] == 'constant' and not is_bv_value(simplify(labelz['z3'])):
                
                # print("Stoping search on this path because jump position is symbolic")
                break

            elif labelz['type'] == 'undefined':
                # print("Stoping search on this path because jump position is undefined")
                break

        elif op == 'JUMPDEST':

            args = []
            
            for j in range(allops[op][1]):
                args.append(stack.pop())


            if step not in visited:
                visited.append(step)

            curr_block = step
            # print(curr_block)
            v.insert(0, curr_block)
            # print(v)
            path_len += 1
            if path_len >= globals_var.max_path_len:
                break
            

            if curr_block in globals_var.block_visit_count:
                globals_var.block_visit_count[curr_block] = globals_var.block_visit_count[curr_block] + 1
            else:
                globals_var.block_visit_count[curr_block] = 1


            tl = list(filter(lambda block: block['fun_block'] == curr_block, external_fun_list))
            if len(tl) > 0:
                for ttl in tl:
                    path_from_ext_fun.append(ttl)
            # print(path_from_ext_fun)

            ltemp = copy.deepcopy(basic_block.check_for_loop(v, curr_block))

            ltemp.sort()
            if ltemp not in loops and len(ltemp) > 0:
                # print("loop found")
                loops.append(ltemp)

            if len(ltemp) > 0:
                basic_block.store_vulnerability(v_data, ltemp)

            for l in loops:
                key = ''

                if curr_block in l:
                    
                    for n in l:
                        key += str(n) + ':'

                    if key not in globals_var.loops_from_external_fun:
                        globals_var.loops_from_external_fun[key] = []
                        
                    if path_from_ext_fun not in globals_var.loops_from_external_fun[key]:
                        globals_var.loops_from_external_fun[key].append(path_from_ext_fun)

            i = i + 1

        else:
            j, stop, symcall = execute_instruction(parsed_code, i, stack, memory, storage, symbolic, caller)

            
            
            if symcall == 3:
                rt = {'path' : path_from_ext_fun, 'vulnerability_code' : 1}
                if rt not in globals_var.result:
                    globals_var.result.append(rt)
            if symcall == 1:
                rt = {'path' : path_from_ext_fun, 'vulnerability_code' : 2}
                if rt not in globals_var.result:
                    globals_var.result.append(rt)

                if basic_block.check_in_loop(curr_block, loops) == True:
                    rt = {'path' : path_from_ext_fun, 'vulnerability_code' : 3}
                    if rt not in globals_var.result:
                        globals_var.result.append(rt)
                else:
                    rt = {'path' : path_from_ext_fun, 'vulnerability_code' : 3}
                    dtemp = [rt]
                    if curr_block in v_data:
                        if dtemp not in v_data[curr_block]:
                            v_data[curr_block].append(dtemp)
                    else:
                        v_data[curr_block] = [dtemp]

            if symcall == 2:
                rt = {'path' : path_from_ext_fun, 'vulnerability_code' : 4}
                if rt not in globals_var.result:
                    globals_var.result.append(rt)

            if globals_var.stop_ins == 1:
                globals_var.stop_ins = 0
                # print("Search to this path is over with normal Abort")
                break

            if stop == True:
                globals_var.stop = False
                # print("Abnormal Abort! of path at step = ", parsed_code[i]['step'])
                break


            i = j