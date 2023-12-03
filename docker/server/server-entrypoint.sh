#!/bin/bash
set -Eeuo pipefail

###############################################
# Start bitcoind
###############################################
echo "Starting bitcoind..."
bitcoind -datadir=/bitcoind -daemon
# Wait for bitcoind startup
until bitcoin-cli -datadir=/bitcoind -rpcwait getblockchaininfo  > /dev/null 2>&1
do
	echo -n "."
	sleep 1
done
echo
echo "bitcoind started"


###############################################
# Prepare a demo wallet to receive mined bitcoins
###############################################
# Create or load the demo wallet
bitcoin-cli -datadir=/bitcoind -named createwallet wallet_name=demo-wallet descriptors=false > /dev/null \
	|| bitcoin-cli -datadir=/bitcoind loadwallet demo-wallet > /dev/null

# Load private key of the demo address into the demo wallet
export privkey=`cat /bitcoind/keys/demo_privkey.txt`
bitcoin-cli -datadir=/bitcoind -rpcwallet=demo-wallet importprivkey $privkey > /dev/null || true


###############################################
# Prepare for creating the JoinMarket wallet
###############################################
# Create or load the JoinMarket watch-only wallet in Bitcoin Core
bitcoin-cli -datadir=/bitcoind -named createwallet wallet_name=jm-test-wallet descriptors=false > /dev/null \
	|| bitcoin-cli -datadir=/bitcoind loadwallet jm-test-wallet > /dev/null


###############################################
# Executing CMD
###############################################
exec "$@"
