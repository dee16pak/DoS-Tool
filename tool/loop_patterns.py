# import globals_var

##########################################################################
##### Check loop exit by checking if current block is ####################
##### in loop and jump block is not in same loop      ####################
########################################################################## 
def check_loop_exit(curr_block, jump_block, loops):
    for loop in loops:
        if curr_block in loop:
            if jump_block not in loop:
                return True
    return False



##########################################################################
##### possible calldataload for external function signature     ##########
########################################################################## 
def check_function_calldataload_pattern(pos, parsed_code):

    if pos + 3 < len(parsed_code):

        if parsed_code[pos]['o'].find('PUSH1') >= 0:

            if parsed_code[pos+1]['o'] == 'CALLDATALOAD':

                # if parsed_code[pos+2]['o'] == 'DIV':

                #     if parsed_code[pos+3]['o'] == 'AND':

                return True   
    
    return False


##########################################################################
##### Two possible external function signature check patterns ############
########################################################################## 
def check_external_function_pattern(pos, parsed_code):

    if pos + 4 < len(parsed_code):

        if parsed_code[pos]['o'] == 'PUSH4':

            if parsed_code[pos + 1]['o'] >= 'DUP':

                if parsed_code[pos + 2]['o'] == 'EQ':

                    if parsed_code[pos + 3]['o'] >= 'PUSH':

                        if parsed_code[pos + 4]['o'] == 'JUMPI':

                            return True, 0

    if pos + 3 < len(parsed_code):

        if parsed_code[pos]['o'] == 'PUSH4':

                if parsed_code[pos + 1]['o'] == 'EQ':

                    if parsed_code[pos + 2]['o'] >= 'PUSH':

                        if parsed_code[pos + 3]['o'] == 'JUMPI':

                            return True, 1
            
    return False, 0
