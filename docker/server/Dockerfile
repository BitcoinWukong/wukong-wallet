###############################################
# Configurations
###############################################
ARG OS_VER=jammy
ARG BITCOIND_VER=23.0
ARG JOINMARKET_VER=0.9.6
ARG FULCRUM_VER=1.7.0


###############################################
# Install dependencies
###############################################
FROM ubuntu:${OS_VER} as os-base

ENV DEBIAN_FRONTEND noninteractive
ENV DEBCONF_NOWARNINGS="yes"
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
	    ca-certificates \
		curl \
		git \
		python3-pip \
		python3 \
		vim
RUN ln -s /usr/bin/python3 /usr/bin/python


###############################################
# Install Bitcoin Core binaries and libraries
###############################################
ARG BITCOIND_VER

RUN cd /tmp && \
	curl -# -sLO https://bitcoincore.org/bin/bitcoin-core-${BITCOIND_VER}/bitcoin-${BITCOIND_VER}-x86_64-linux-gnu.tar.gz && \
	tar -zxf bitcoin-${BITCOIND_VER}-x86_64-linux-gnu.tar.gz && \
	cd bitcoin-${BITCOIND_VER} && \
	install -vD bin/* /usr/bin && \
	install -vD lib/* /usr/lib && \
	cd /tmp && \
	rm bitcoin-${BITCOIND_VER}-x86_64-linux-gnu.tar.gz && \
	rm -rf bitcoin-${BITCOIND_VER}


###############################################
# Install JoinMarket
###############################################
ARG JOINMARKET_VER

# Checkout the git repo
RUN mkdir -p /jm
RUN cd /tmp \
	&& git clone https://github.com/JoinMarket-Org/joinmarket-clientserver.git \
	&& cd joinmarket-clientserver \
	&& git checkout v${JOINMARKET_VER} \
	&& mv /tmp/joinmarket-clientserver/ /jm/clientserver

# Install JoinMarket and its dependencies
RUN cd /jm/clientserver \
	&& ./install.sh --docker-install --without-qt


###############################################
# Install Fulcrum
###############################################
ARG FULCRUM_VER

RUN mkdir -p /jm
RUN cd /tmp \
	&& curl -# -sLO https://github.com/cculianu/Fulcrum/releases/download/v${FULCRUM_VER}/Fulcrum-${FULCRUM_VER}-x86_64-linux.tar.gz \
	&& tar -zxf Fulcrum-${FULCRUM_VER}-x86_64-linux.tar.gz \
	&& mv Fulcrum-${FULCRUM_VER}-x86_64-linux /opt/Fulcrum \
	&& rm Fulcrum-${FULCRUM_VER}-x86_64-linux.tar.gz


###############################################
# Copy resources
###############################################
# Copy bitcoind configuration directory
COPY resources/bitcoind /bitcoind
RUN ln -s /bitcoind /root/.

# Copy other configs
COPY resources/bashrc /root/.bashrc
RUN mkdir -p /root/.joinmarket/wallets
COPY resources/regtest_joinmarket.cfg /root/.joinmarket/joinmarket.cfg

# Copy the JoinMarket test wallet
COPY resources/wallet.jmdat /root/.joinmarket/wallets/wallet.jmdat

# Copy entrypoint and cmd scripts
COPY server-entrypoint.sh /usr/local/bin
RUN chmod +x /usr/local/bin/server-entrypoint.sh
COPY start-server.sh /usr/local/bin
RUN chmod +x /usr/local/bin/start-server.sh


###############################################
# Start the container
###############################################
# bitcoind regtest RPC
EXPOSE 18443/tcp
# Fulcrum RPC
EXPOSE 50001/tcp

WORKDIR /jm/clientserver/scripts
ENTRYPOINT ["/usr/local/bin/server-entrypoint.sh"]
CMD ["/usr/local/bin/start-server.sh"]
