
# Block and Transaction Properties

# block.blockhash(uint blockNumber) returns (bytes32): hash of the given block - only works for 256 most recent, excluding current, blocks - deprecated in version 0.4.22 and replaced by blockhash(uint blockNumber).
block_blockhash = '0x0'
# block.coinbase (address): current block miner’s address
block_coinbase = '0x0'
# block.difficulty (uint): current block difficulty
block_difficulty = '0x0'
# block.gaslimit (uint): current block gaslimit
block_gaslimit = '0x0'
# block.number (uint): current block number
block_number = '0x0'
# block.timestamp (uint): current block timestamp as seconds since unix epoch
block_timestamp = '0x0'
# gasleft() returns (uint256): remaining gas
block_gasleft = '0x0'
# msg.data (bytes): complete calldata
# msg_data = 
# msg.gas (uint): remaining gas - deprecated in version 0.4.21 and to be replaced by gasleft()
# msg_gas = 0
# msg.sender (address): sender of the message (current call)
# msg_sender = 0x0
# msg.sig (bytes4): first four bytes of the calldata (i.e. function identifier)
# msg_sig = 
# msg.value (uint): number of wei sent with the message
msg_value = '0'
# now (uint): current block timestamp (alias for block.timestamp)
# now = 0
# tx.gasprice (uint): gas price of the transaction
tx_gasprice = '0x0'
# tx.origin (address): sender of the transaction (full call chain)
tx_origin = '0x0'
balance = '0x0'
address = '0x0'

# pattern_found = 1
# loop_found = 1
stop_ins = 1
max_path_len = 0
code_string = ''
result = []
block_visit_count = {}
loops_from_external_fun = {}

