FROM debian:bookworm-slim

ARG TARGETARCH

COPY staged/${TARGETARCH}/bitcoind /usr/local/bin/bitcoind
COPY staged/${TARGETARCH}/bitcoin-cli /usr/local/bin/bitcoin-cli

RUN chmod 0755 \
      /usr/local/bin/bitcoind \
      /usr/local/bin/bitcoin-cli \
    && /usr/local/bin/bitcoind --version | head -1

EXPOSE 8332 8333 28332 28333

ENTRYPOINT ["/usr/local/bin/bitcoind"]
