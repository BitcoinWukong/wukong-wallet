#!/bin/bash
set -Eeuo pipefail

##########################################################################
# Init the blockchain
##########################################################################
export demo_address=`cat /bitcoind/keys/demo_address.txt`
bitcoin-cli -datadir=/bitcoind generatetoaddress 101 $demo_address


##########################################################################
# Init the JoinMarket wallet and mock some transactions
##########################################################################
# The JM wallet password
export jm_wallet_pass="eee"
# A few addresses in the JM wallet:
export addr_0_0="bcrt1q5akcthm47ktf00y36wd4huttc6hpx3l404ddsn"
export addr_1_0="bcrt1qaraqssjcrdapq9dj4m5ycszwc4pl0tsyuetz9f"
export addr_2_0="bcrt1qxpdznmduzj3hwxp2dq7yyr0cdzzpacktxtrmug"

# Load the wallet once to perform initial import
python wallet-tool.py --wallet-password-stdin wallet.jmdat <<< $jm_wallet_pass

# Give 20 bitcoins to mixdepth 0, index 0
bitcoin-cli -datadir=/bitcoind -rpcwallet=demo-wallet sendtoaddress $addr_0_0 20
# Mine 6 blocks to confirm the transactions
bitcoin-cli -datadir=/bitcoind generatetoaddress 6 $demo_address

# Send 10 bitcoins to mixdepth 1, index 0
python sendpayment.py --wallet-password-stdin -N 0 -m 0 wallet.jmdat 1000000000 $addr_1_0 <<STDIN
$jm_wallet_pass
y
STDIN

# Mine 6 blocks to confirm the transactions
bitcoin-cli -datadir=/bitcoind generatetoaddress 6 $demo_address

# Resend 5 bitcoins to mixdepth 2, index 0
python sendpayment.py --wallet-password-stdin -N 0 -m 1 wallet.jmdat 500000000 $addr_2_0 <<STDIN
$jm_wallet_pass
y
STDIN
# Mine 6 blocks to confirm the transactions
bitcoin-cli -datadir=/bitcoind generatetoaddress 6 $demo_address


##########################################################################
# Start the Fulcrum service
##########################################################################
/opt/Fulcrum/Fulcrum --bitcoind localhost:18443 --datadir /bitcoind --rpcuser bitcoinrpc --rpcpassword 123456abcdef
