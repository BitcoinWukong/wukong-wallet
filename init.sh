#!/bin/bash
set -euo pipefail

#############################
# Create venv
#############################
# if [[ "$OSTYPE" == "linux-gnu"* ]]; then
#     sudo apt install python3.9-venv
# fi

python3.9 -m venv venv
source venv/bin/activate
pip install --upgrade pip

#############################
# macos:
#############################
if [[ $OSTYPE == 'darwin'* ]]; then
    pip install --upgrade certifi
    # Needed for zbarcam:
    # brew install -v zbar
fi

#############################
# Ubuntu
#############################
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Needed for zbarcam:
    # sudo apt-get install -y zbar-tools
    echo
fi

#############################
# Install dependencies
#############################
# Wheel is needed for pycoin, connectrum and peewee
pip install --upgrade wheel setuptools

# Install all dependencies
pip install --requirement requirements.txt
