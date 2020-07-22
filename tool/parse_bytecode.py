from instructions import *
from globals_var import *
from loop_patterns import *
from z3 import *


def copy_runtime_parsed_code(start, parsed_code):

    i = start
    temp = []
    base = parsed_code[i]['step']

    while i < len(parsed_code):

        t = copy.deepcopy(parsed_code[i])
        t['step'] = t['step'] - base
        temp.append(copy.deepcopy(t))

        i = i + 1

    return temp

        
def copy_deploy_parsed_code(end, parsed_code):

    i = 0
    temp = []

    while i < end:
        temp.append(copy.deepcopy(parsed_code[i]))
        i = i + 1

    return temp


def check_for_return(pos, parsed_code):
    
    i = pos

    while i  < len(parsed_code):

        if parsed_code[i]['o'] == 'RETURN':
            return 1, i + 1
        elif parsed_code[i]['o'] == 'CODECOPY':
            return -1, i
        
        i = i + 1

    return -2, i

        
def check_for_initial(position, parsed_code):

    i = position

    while i + 2 < len(parsed_code):
        # print(parsed_code[i]['o'])
        if parsed_code[i]['o'] == 'PUSH1':
            if parsed_code[i+1]['o'] == 'PUSH1':
                if parsed_code[i+2]['o'] == 'MSTORE':
                    return 1, i
        
        if parsed_code[i]['o'] == 'CODECOPY':
            return -1, 1
        
        i = i + 1
    
    return -2, 1


##########################################################################
##### Separate runtime and deploy time code based on fixed pattern    ####
########################################################################## 
def separate_runtime_code(parsed_code):

    i = 0
    # print(code_string)
    deploy_parsed_code = ''
    runtime_parsed_code = ''

    while i < len(parsed_code):

        if parsed_code[i]['o'] == 'CODECOPY':

            pstatus, preturn = check_for_return(i+1, parsed_code)
            # print('pstatus ',pstatus, ' ', preturn)
            if pstatus == -1:
                i = preturn

            elif pstatus == -2:
                break

            else:
                pstat, pinitial = check_for_initial(preturn, parsed_code)
                # print(pstat)
                if pstat == -1:
                    i = pinitial

                elif pstat == -2:
                    break

                else:
                    deploy_parsed_code = copy_deploy_parsed_code(pinitial, parsed_code)
                    runtime_parsed_code = copy_runtime_parsed_code(pinitial, parsed_code)
                    break

        else:
            i = i + 1

    return deploy_parsed_code, runtime_parsed_code


##########################################################################
##### Parse code to feed to Custom EVM    ################################
########################################################################## 
def parse(code):
    # global stack
    # stack.append("hello")
    if code[0:2] == '0x':
        code = code[2:]
    # print(code)
    parse_result = []
    i = 0
    while i < len(code):
        # print("begining-", i)
        operand = code[i:i+2]
        input_size = 0
        if operand >= '60' and operand <= '7f':
            input_size = int(operand, 16) - int('60', 16) + 1

        operand = '0x' + operand
        temp_parse = list()
        if operand in cops:
            temp_parse = {'step' : int(i/2), 'operand' : code[i:i+2], 'input' : code[i+2: i + 2 + 2*input_size], 'o' : cops[operand]}
            parse_result.append(temp_parse)
        i = i + 2 + 2*input_size
        # print("end-", i)
    return parse_result

    