#!/bin/bash
docker build -t wkwallet-regtest docker/server && docker run -p 50001:50001 -it --rm --name wkwallet wkwallet-regtest
