FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       libatomic1 \
       libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY staged/monerod /usr/local/bin/monerod

RUN chmod 0755 /usr/local/bin/monerod \
    && /usr/local/bin/monerod --version

RUN useradd --system --uid 1000 --create-home monero \
    && mkdir -p /data \
    && chown -R monero:monero /data

VOLUME ["/data"]

EXPOSE 18080 18081

USER monero

ENTRYPOINT ["/usr/local/bin/monerod"]
