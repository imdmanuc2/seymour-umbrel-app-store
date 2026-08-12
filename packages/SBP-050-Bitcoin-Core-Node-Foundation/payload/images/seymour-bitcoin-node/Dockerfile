FROM debian:bookworm-slim

ARG BITCOIN_VERSION=29.0
ARG TARGETARCH=amd64

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       curl \
       tar \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    case "${TARGETARCH:-amd64}" in \
      amd64) BTC_ARCH="x86_64-linux-gnu" ;; \
      arm64) BTC_ARCH="aarch64-linux-gnu" ;; \
      *) echo "Unsupported architecture: ${TARGETARCH:-unknown}"; exit 1 ;; \
    esac; \
    echo "Building Bitcoin Core ${BITCOIN_VERSION} for ${BTC_ARCH}"; \
    curl -fsSLO \
      "https://bitcoincore.org/bin/bitcoin-core-${BITCOIN_VERSION}/bitcoin-${BITCOIN_VERSION}-${BTC_ARCH}.tar.gz"; \
    curl -fsSLO \
      "https://bitcoincore.org/bin/bitcoin-core-${BITCOIN_VERSION}/SHA256SUMS"; \
    grep " bitcoin-${BITCOIN_VERSION}-${BTC_ARCH}.tar.gz$" SHA256SUMS \
      | sha256sum -c -; \
    tar -xzf "bitcoin-${BITCOIN_VERSION}-${BTC_ARCH}.tar.gz"; \
    install -m 0755 \
      "bitcoin-${BITCOIN_VERSION}/bin/bitcoind" \
      "bitcoin-${BITCOIN_VERSION}/bin/bitcoin-cli" \
      /usr/local/bin/; \
    rm -rf \
      "bitcoin-${BITCOIN_VERSION}" \
      "bitcoin-${BITCOIN_VERSION}-${BTC_ARCH}.tar.gz" \
      SHA256SUMS

RUN useradd --system --uid 1000 --create-home bitcoin \
    && mkdir -p /data /generated /state \
    && chown -R bitcoin:bitcoin /data /generated /state

VOLUME ["/data", "/generated", "/state"]

EXPOSE 8332 8333 28332 28333

USER bitcoin

ENTRYPOINT ["/usr/local/bin/bitcoind"]
