from instructions import cops, allops
from parse_bytecode import *
from globals_var import block_blockhash, block_coinbase, block_difficulty, block_gasleft, block_gaslimit, block_number, block_timestamp, balance
from globals_var import address, msg_value, tx_gasprice, tx_origin, code_string, stop_ins
import loop_patterns
from z3 import *
from math import *
import sha3

def power(y, x, n):
    if x == 0: #base case
        return 1
    elif (x%2==0): #x even 
        return power((y*y)%n,x//2,n)%n
    else: #x odd
        return (y*power((y*y)%n,x//2,n))%n

def is_undefined(x):
    return x['type'] == 'undefined'

def is_fixed(x):
    return x['type'] == 'constant' and is_bv_value(simplify(x['z3']))

def execute_instruction(parsed_code,pos, stack, memory, storage, symbolic, caller):

    symcall = 0
    if pos > len(parsed_code):
        # print("pos > len(parsed_code)-position is more than length of parsed code")
        return pos, True, symcall
    
    op = parsed_code[pos]['o']
    step = parsed_code[pos]['step']
    
    if allops[op][1] > len(stack):
        # print("allops[op][1] < len(stack)- stack length is less then required")
        return pos, True, symcall
    
    args = []

    for i in range(allops[op][1]):

        a = copy.deepcopy(stack.pop())
        if 'pre_mod' in a:
            if caller == 1:
                if not is_bv_value(simplify(a['z3'])):
                    a['z3'] = BitVec(str(simplify(a['z3'])).replace('sym-pure', 'sym-mod') , 256)
        args.append(a)

    
    
    if op == "STOP":
        stop_ins = 1
        # print("stop-end of script")
        return pos, True, symcall
    
    elif op in ['ADD', 'MUL', 'DIV', 'SDIV', 'MOD', 'SMOD', 'EXP','AND','OR','XOR', 'LT','GT','SLT','SGT','EQ', 'SUB']:
        exp_else = 1
        if is_undefined(args[0]) or is_undefined(args[1]):
            stack.append({'type' : 'undefined'})
        else:    
            z1 = simplify(args[0]['z3'])
            z2 = simplify(args[1]['z3'])

            if is_fixed(args[0]) and z1.as_long() == 0 and op in ['MUL', 'DIV', 'SDIV', 'AND']:
                stack.append({'type' : 'constant', 'z3' : BitVecVal(0, 256)} )

            elif is_fixed(args[1]) and z2.as_long() == 0 and op in ['MUL', 'AND']:
                stack.append({'type' : 'constant', 'z3' : BitVecVal(0, 256)})

            elif is_fixed(args[1]) and z2.as_long() == 0 and op in ['DIV', 'SDIV']:
                stack.append({'type' : 'undefined'})

            elif is_fixed(args[0]) and z1.as_long() == 0 and op in ['ADD', 'XOR']:
                stack.append(args[1])

            elif is_fixed(args[1]) and z2.as_long() == 0 and op in ['ADD', 'XOR']:
                stack.append(args[0])

            else:
                if op == 'ADD': z3 = z1 + z2
                elif op == 'MUL':   z3 = z1 * z2
                elif op == 'DIV':   z3 = UDiv(z1, z2)
                elif op == 'SDIV':  z3 = z1 / z2
                elif op == 'MOD' :  z3 = URem(z1, z2)
                elif op == 'SMOD' : z3 = z1 % z2
                elif op == 'AND' :  z3 = z1 & z2
                elif op == 'OR' :   z3 = z1 | z2
                elif op == 'XOR' :  z3 = z1 ^ z2
                elif op == 'LT' :   z3 = If(ULT(z1, z2), BitVecVal(1, 256), BitVecVal(0, 256))
                elif op == 'GT' :   z3 = If(UGT(z1, z2), BitVecVal(1, 256), BitVecVal(0, 256))
                elif op == 'SLT' :  z3 = If(z1 < z2, BitVecVal(1, 256), BitVecVal(0, 256))
                elif op == 'SGT' :  z3 = If(z1 > z2, BitVecVal(1, 256), BitVecVal(0, 256))
                elif op == 'EQ' :   z3 = If(z1 == z2, BitVecVal(1, 256), BitVecVal(0, 256))
                elif op == 'SUB' :  z3 = z1 - z2
                elif op == 'EXP' :
                    if is_bv_value(z1) and is_bv_value(z2):
                        z3 = BitVecVal( power (z1.as_long(), z2.as_long(), 2**256), 256 )

                    else: 
                        stack.append({'type':'undefined'})
                        exp_else = 0

                if exp_else:
                    if op in ['LT', 'SLT', 'GT', 'SGT']:
                        stack.append({'type' : 'constant', 'z3' : z3, 'z1' : z1, 'z2' : z2})
                    else:
                        stack.append({'type' : 'constant', 'z3' : z3})

            if 'updated' in args[0] or 'updated' in args[1]:
                temp = stack.pop()
                temp['updated'] = 1
                stack.append(temp)

            if 'caller' in args[0] or 'caller' in args[1]:
                temp = stack.pop()
                temp['caller'] = 1
                stack.append(temp)

            if 'pre_mod' in args[0] or 'pre_mod' in args[1]:
                temp = stack.pop()
                temp['pre_mod'] = 1
                stack.append(temp)

    elif op in ['ISZERO', 'NOT']:

        
        if is_undefined(args[0]):
            stack.append({'type' : 'undefined'})

        else:
            z1 = simplify(args[0]['z3'])

            if op == 'ISZERO' : z3 = If(z1 == 0, BitVecVal(1, 256), BitVecVal(0, 256))
            elif op == 'NOT' :  z3 = ~z1

            if 'z1' in args[0] and 'z2' in args[0]:
                stack.append({'type' : 'constant', 'z3' : z3, 'z1' : args[0]['z1'], 'z2' : args[0]['z2']})
            else:
                stack.append({'type' : 'constant', 'z3' : z3})

            if 'updated' in args[0]:
                temp = stack.pop()
                temp['updated'] = 1
                stack.append(temp)

            if 'caller' in args[0]:
                temp = stack.pop()
                temp['caller'] = 1
                stack.append(temp)

            # if not str(z3).find('sym-pure') >= 0:
            if 'pre_mod' in args[0]:
                temp = stack.pop()
                temp['pre_mod'] = 1
                stack.append(temp)
    
    elif op in ['MULMOD', 'ADDMOD']:
        z1 = simplify(args[0]['z3'])
        z2 = simplify(args[1]['z3'])
        z3 = simplify(args[2]['z3'])

        if args[2]['type'] == 'constant' and is_bv_value(z3) and z3.as_long() == 0:
            stack.append({'tyep' : 'constant', 'z3' : BitVecVal(0, 256)})

        elif op == 'MULMOD':
            stack.append({'type' : 'constant', 'z3' : (z1 * z2) % z3})

        elif op == 'ADDMOD':
            stack.append({'type' : 'constant', 'z3' : (z1 + z2) % z3})

        if 'updated' in args[0] or 'updated' in args[1] or 'updated' in args[2]:
                temp = stack.pop()
                temp['updated'] = 1
                stack.append(temp)

        if 'caller' in args[0] or 'caller' in args[1] or 'updated' in args[2]:
                temp = stack.pop()
                temp['caller'] = 1
                stack.append(temp)

        if 'pre_mod' in args[0] or 'pre_mod' in args[1] or 'pre_mod' in args[2]:
            temp = stack.pop()
            temp['pre_mod'] = 1
            stack.append(temp)

    elif op == 'BYTE':
        nz = args[0]
        xz = args[1]

        if is_undefined(nz) or is_undefined(xz):
            stack.append({'type' : 'undefined'})

        else:
            nz = simplify(nz['z3'])
            xz = simplify(xz['z3'])
            z3 = (0xff << (8*(31 - nz))) & xz
            z3 = z3 >> (8*(31 - nz))
            stack.append({'type' : 'constant', 'z3' : BitVecVal(z3, 256)})

            if 'updated' in args[0]:
                temp = stack.pop()
                temp['updated'] = 1
                stack.append(temp)

            if 'caller' in args[0]:
                temp = stack.pop()
                temp['caller'] = 1
                stack.append(temp)

            if 'pre_mod' in args[0]:
                temp = stack.pop()
                temp['pre_mod'] = 1
                stack.append(temp)
    
    elif op == 'SHA3':
        pz = args[0]
        nz = args[0]

        if(pz['type'] == 'undefined' or nz['type'] == 'undefined'):
            stack.append({'type' : 'undefined'})

        elif is_fixed(pz) and is_fixed(nz):
            pz = simplify(pz['z3']).as_long()
            nz = simplify(nz['z3']).as_long()
            i = pz
            dz = ''
            flag = 1

            while i < pz+nz:
                if str(i) not in memory:
                     
                    stack.append({'type' : 'undefined'})
                    flag = 0
                    break

                elif str(i) in memory and not is_bv_value(memory[str(i)]['z3']):
                    stack.append({'type' : 'undefined'})
                    flag = 0
                    break
                
                dz += '%064x' % simplify(memory[str(i)]['z3']).as_long()
                i += 32
                
                
            if flag:
                k = sha3.keccak_256()
                k.update(dz.encode('utf-8'))
                stack.append({'type' : 'constant', 'z3' : BitVecVal(int(k.hexdigest(),16), 256)})

        else:
            # print("Stoping search to this path because arguments are not fixed")
            return pos, True, symcall

    elif op == 'BLOCKHASH':
        stack.append({'type' : 'constant', 'z3' : BitVecVal(int(block_blockhash, 16), 256)})

    elif op == 'COINBASE':
        stack.append({'type' : 'constant', 'z3' : BitVecVal(int(block_coinbase, 16), 256)})

    elif op == 'DIFFICULTY':
        stack.append({'type' : 'constant', 'z3' : BitVecVal(int(block_difficulty, 16), 256)})

    elif op == 'GASLIMIT':
        stack.append({'type' : 'constant', 'z3' : BitVecVal(int(block_gaslimit, 16), 256)})

    elif op == 'NUMBER':
        stack.append({'type' : 'constant', 'z3' : BitVecVal(int(block_number, 16), 256)})

    elif op == 'TIMESTAMP':
        stack.append({'type' : 'constant', 'z3' : BitVecVal(int(block_timestamp, 16), 256)})

    elif op == 'GAS':
        stack.append({'type' : 'constant', 'z3' : BitVecVal(int(block_gasleft, 16), 256)})

    elif op == 'CALLVALUE':
        
        if caller == 1:
            s = 'sym-mod-' + str(len(symbolic))
        else:
            s = 'sym-pure-' + str(len(symbolic))

        symbolic.append(s)
        s = BitVec(s, 256)

        stack.append({'type' : 'constant', 'z3' : s})
        # stack.append({'type' : 'constant', 'z3' : BitVecVal(int(msg_value, 16), 256)})

    elif op == 'ORIGIN':
        stack.append({'type' : 'constant', 'z3' : BitVecVal(int(tx_origin, 16), 256)})

    elif op == 'GASPRICE':
        stack.append({'type' : 'constant', 'z3' : BitVecVal(int(tx_gasprice, 16), 256)})

    elif op == 'BALANCE':
        stack.append({'type' : 'constant', 'z3' : BitVecVal(int(balance, 16), 256)})

    elif op == 'ADDRESS':
        stack.append({'type' : 'constant', 'z3' : BitVecVal(int(tx_origin, 16), 256)})

    elif op =='CALLER':
        stack.append({'type' : 'constant', 'z3' : BitVecVal(int(address, 16), 256), 'caller' : '1'})

    elif op == 'CALLDATASIZE':
        
        if caller == 1:
            d = 'sym-mod-' + str(len(symbolic))
        else:
            d = 'sym-pure-' + str(len(symbolic))
        symbolic.append(d)

        temp = BitVec(d, 256)
        stack.append({'type' : 'constant', 'z3' : temp})

    elif op == 'CALLDATALOAD':
        
        if args[0]['type'] == 'undefined':
            stack.append({'type' : 'undefined'})

        elif args[0]['type'] == 'constant' and is_bv_value(simplify(args[0]['z3'])):

            # print("inside call data load if constant")

            if caller == 1:
                s = 'sym-mod-' + str(len(symbolic))
            else:
                s = 'sym-pure-' + str(len(symbolic))

            symbolic.append(s)
            s = BitVec(s, 256)

            if caller != 1:
                stack.append({'type' : 'constant', 'z3' : s, 'pre_mod' : 1})
            else:
                stack.append({'type' : 'constant', 'z3' : s})

        elif not is_bv_value(simplify(args[0]['z3'])) and str(simplify(args[0]['z3'])).find('sym') >= 0:

            # print("inside calldataload if data is symbolic")

            if caller == 1:
                s = 'sym-mod-' + str(len(symbolic))
            else:
                s = 'sym-pure-' + str(len(symbolic))

            symbolic.append(s)
            s = BitVec(s, 256)

            if caller != 1:
                stack.append({'type' : 'constant', 'z3' : s, 'pre_mod' : 1})
            else:
                stack.append({'type' : 'constant', 'z3' : s})
    
        else:
            print("Not able to find any situation")
        
    elif op == 'CALLDATACOPY':

        tz = args[0]
        fz = args[1]
        sz = args[2]

        if tz['type'] == 'undefined' or fz['type'] == 'undefined' or sz['type'] == 'undefined':
            # print("call data copy arguments are not defined")
            return pos, True

        else:
            if is_fixed(tz) and is_fixed(fz) and is_fixed(sz):
                
                # print("in the fixed argument condition of calldatacopy")

                if simplify(sz['z3']).as_long() % 32 == 0:

                    # print("in calldatacopy data is 32 byte divisible")

                    temp = int(simplify(sz['z3']).as_long() / 32)

                    # print("temp in calldatacopy = ", temp)

                    for i in range(temp):

                        if caller == 1:
                            s = 'sym-mod-' + str(len(symbolic))
                        else:
                            s = 'sym-pure-' + str(len(symbolic))

                        symbolic.append(s)
                        s = BitVec(s, 256)

                        memory[str(copy.deepcopy(simplify(tz['z3'])).as_long() + i*32)] = {'type' : 'constant', 'z3' : s}

                else:
                    # print("Stoping this search path as calldatacopy arguments are not 32 byte divisible")
                    return pos, True, symcall
            elif is_fixed(tz):

                for i in range(100):

                    if caller == 1:
                        s = 'sym-mod-' + str(len(symbolic))
                    else:
                        s = 'sym-pure-' + str(len(symbolic))

                    symbolic.append(s)
                    s = BitVec(s, 256)

                    memory[str(copy.deepcopy(simplify(tz['z3'])).as_long() + i*32)] = {'type' : 'constant', 'z3' : s}

                # print("Stoping this search path as calldatacopy arguments are symbolic")
            else:
                stop_ins = 1
                # if str(simplify(sz['z3'])).find('sym-pure') >= 0: 
                #     return pos, True, 3
                
                return pos, True, symcall


    elif op == 'CODECOPY':

        tz = args[0]
        fz = args[1]
        sz = args[2]

        if tz['type'] == 'undefined' or fz['type'] == 'undefined' or sz['type'] == 'undefined':
            # print("code copy arguments are not defined")
            return pos, True, symcall

        else:

            if is_bv_value(simplify(tz['z3'])) and is_bv_value(simplify(fz['z3'])) and is_bv_value(simplify(sz['z3'])):

                for i in range(floor(simplify(sz['z3']).as_long() / 32)):
                    
                    tt = 2*copy.deepcopy(simplify(fz['z3'])).as_long() + i*64
                    
                    if tt + 64 < len(code_string):
                        d = code_string[tt:tt+32]
                    else:
                        data = 'sym-constructor-' + str(len(symbolic))
                        symbolic.append(data)
                        d = {'type' : 'constant', 'z3' : BitVec(data, 256)}

                    mempos = simplify(tz['z3']).as_long() + i*32
                    memory[str(mempos)] = d

            else:
                # print("Codecopy arguments are symbolic hence terminating this path search")   
                return pos, True, symcall
    

    elif op == 'CALL' or op == 'CALLCODE':

            # args = []
            
            # for j in range(allops[op][1]):
            #     args.append(stack.pop())

            gz = args[0]
            az = args[1]
            vz = args[2]
            inz = args[3]
            insize = args[4]
            outz = args[5]
            outsize = args[6]

            if gz['type'] == 'undefined' or az['type'] == 'undefined' or vz['type'] == 'undefined' or inz['type'] == 'undefined':
                # print("Cannot call as arguments undefined")
                return pos, True, symcall

            if insize['type'] == 'undefined' or outz['type'] == 'undefined' or outsize['type'] == 'undefined':
                # print("Cannot call as arguments undefined")
                return pos, True, symcall

            # if caller == 1 and 'pre_mod' in az:
            #     symcall = 0
            
            if az['type'] == 'constant' and str(simplify(az['z3'])).find('sym-pure') >= 0:
                # print("Call to address which can be set by anyone !!")
                symcall = 1
            
            if caller == 1:
                d = 'sym-mod-call-' + str(len(symbolic))
            else:
                d = 'sym-pure-call-' + str(len(symbolic))
            
            symbolic.append(d)

            temp = BitVec(d, 256)
            temp = temp & 0x1
            stack.append({'type' : 'constant', 'z3' : temp})

            if is_bv_value(simplify(outsize['z3'])) and is_bv_value(simplify(outz['z3'])):
                for i in range(ceil(int(simplify(outsize['z3']).as_long()) / 32)):
                    memory[str(simplify(outz['z3']).as_long() + 32 * i)] = { 'type':'undefined' }

                
    elif op == 'DELEGATECALL' or op == 'DELEGATECALL':

        # args = []
        
        # for j in range(allops[op][1]):
        #     args.append(stack.pop())

        gz = args[0]
        az = args[1]
        inz = args[2]
        insize = args[3]
        outz = args[4]
        outsize = args[5]

        if gz['type'] == 'undefined' or az['type'] == 'undefined' or inz['type'] == 'undefined':
            # print("Cannot call as arguments undefined")
            return pos, True, symcall

        if insize['type'] == 'undefined' or outz['type'] == 'undefined' or outsize['type'] == 'undefined':
            # print("Cannot call as arguments undefined")
            return pos, True, symcall

        if az['type'] == 'constant' and simplify(az['z3']).find('sym-pure') >= 0:
            print("Call to address which can be set by anyone !!")
            symcall = 1
        
        if caller == 1:
            d = 'sym-mod-call-' + str(len(symbolic))
        else:
            d = 'sym-pure-call-' + str(len(symbolic))
        
        symbolic.append(d)

        temp = BitVec(d, 256)
        temp = temp & 0x1
        stack.append({'type' : 'constant', 'z3' : temp})

        if is_bv_value(simplify(outsize['z3'])) and is_bv_value(simplify(outz['z3'])):
            for i in range(ceil(int(simplify(outsize['z3']).as_long()) / 32)):
                memory[str(simplify(outz['z3']).as_long() + 32 * i)] = { 'type':'undefined' }


    elif op == 'EXTCODESIZE':
        stack.append({'type' : 'constant', 'z3' : BitVecVal(0, 256)})

    elif op == 'EXTCODECOPY':
        pass

    elif op == 'MCOPY':
        pass

    elif op == 'POP':
        pass

    elif op == 'MLOAD':

        pz = args[0]

        if pz['type'] == 'undefined':
            stack.append({'type' : 'undefined'})

        else:
            
            if str(simplify(pz['z3'])) in memory:

                stack.append(copy.deepcopy(memory[str(simplify(pz['z3']))]))
            
            else:
                # print("mload memory not found at location ", simplify(pz['z3']))
                return pos, True, symcall

    elif op == 'MSTORE':

        pz = args[0]
        vz = args[1]

        if is_undefined(pz):
            # print("Stoping search to this path because location to store in memory is undefined")
            return pos, True, symcall

        elif is_fixed(pz):
            memory[str(simplify(pz['z3']))] = copy.deepcopy(vz)

        else:
            # print("Stoping search to this path because location to store in memory is symbolic")
            return pos, True, symcall

    elif op == 'MSTORE8':

        pz = args[0]
        vz = args[1]

        if is_undefined(pz):
            # print("Stoping search to this path because location to store in memory is undefined")
            return pos, True, symcall

        elif is_fixed(pz):
            memory[str(simplify(pz['z3']))] = copy.deepcopy(vz) & 0xff

        else:
            # print("Stoping search to this path because location to store in memory is symbolic")
            return pos, True, symcall

    elif op == 'SLOAD':

        pz = args[0]

        if pz['type'] == 'undefined':
            stack.append({'type' : 'undefined'})

        else:

            if str(simplify(pz['z3'])) in storage:
                stack.append(copy.deepcopy(storage[str(simplify(pz['z3']))]))

            else:
                
                stack.append({'type' : 'constant', 'z3' : BitVecVal(0, 256), 'updated' : 0})
                storage[str(simplify(pz['z3']))] = {'type' : 'constant', 'z3' : BitVecVal(0, 256), 'updated' : '0'}

    elif op == 'SSTORE':

        # args = []
        
        # for j in range(allops[op][1]):
        #     args.append(stack.pop())

        pz = args[0]
        vz = args[1]

        if pz['type'] == 'undefined':
            # print("Stoping search to this path because location to store in memory is undefined")
            return pos, True, symcall

        else:
            temp = copy.deepcopy(vz)

            if 'updated' in temp:
                if vz['updated'] == 1 and is_bv_value(simplify(vz['z3'])):
                    if caller == 1:
                        d = 'sym-mod-' + str(len(symbolic))
                    else:
                        d = 'sym-pure-' + str(len(symbolic))

                    symbolic.append(d)
                    temp['z3'] = BitVec(d, 256)
                    del temp['updated']

            storage[str(simplify(pz['z3']))] = copy.deepcopy(temp)

    elif op == 'JUMP':

        labelz = args[0]

        if labelz['type'] == 'constant' and is_bv_value(simplify(labelz['z3'])) and parsed_code[-1]['step'] >= simplify(labelz['z3']).as_long():

            for i in range(len(parsed_code)):

                if parsed_code[i]['step'] == simplify(labelz['z3']).as_long():
                    pos = i
                    break

            if parsed_code[pos]['o'] == 'JUMPDEST':
                pos = pos - 1
                pass

            else:
                # print("Stoping search on this path because jump position is not valid")
                return pos, True, symcall

        elif labelz['type'] == 'constant' and is_bv_value(simplify(labelz['z3'])) and (parsed_code[-1]['step'] < simplify(labelz['z3']).as_long() or simplify(labelz['z3']).as_long() < 0):
            # print("Stoping search on this path because jump position is either less than zero or greater than parsed code length")
            return pos, True, symcall

        elif labelz['type'] == 'constant' and not is_bv_value(simplify(labelz['z3'])):
            # print("Stoping search on this path because jump position is symbolic")
            return pos, True, symcall

        elif labelz['type'] == 'undefined':
            # print("Stoping search on this path because jump position is undefined")
            return pos, True, symcall

    elif op == 'PC':
        stack.append({'type' : 'constant', 'z3' : BitVecVal(step, 256)})

    elif op == 'MSIZE':
        stack.append({'type' : 'constant', 'z3' : BitVecVal(len(memory), 256)})

    elif op == 'JUMPDEST':
        pass

    elif op == 'SLOADEXT':
        pass

    elif op == 'SSTOREEXT':
        pass

    elif op == 'SLOADBYTESEXT':
        pass

    elif op == 'SSTOREBYTESEXT':
        pass

    elif op == 'CREATE2':
        symcall = 2

    elif op.find('PUSH') >= 0:
        inp = int(parsed_code[pos]['input'], 16)
        stack.append({'type' : 'constant', 'z3' : BitVecVal(inp, 256)})

    elif op.find('DUP') >= 0:

        l = len(args)
        l = l - 1

        while l >= 0:
            stack.append(args[l])
            l = l - 1
        stack.append(args[-1])

    elif op.find('SWAP') >= 0:

        stack.append(args[0])
        l = len(args)
        l = l - 2

        while l > 0:
            # print(l)
            stack.append(args[l])
            l = l - 1
        stack.append(args[-1])


    else:
        # print("abort")
        return pos, True, symcall

    return pos+1, False, symcall