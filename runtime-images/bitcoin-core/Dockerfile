FROM debian:bookworm-slim

ARG BITCOIN_VERSION=29.0
ARG TARGETARCH

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl tar \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    case "${TARGETARCH}" in \
      amd64) release_arch="x86_64" ;; \
      arm64) release_arch="aarch64" ;; \
      *) echo "Unsupported TARGETARCH: ${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    base="https://bitcoincore.org/bin/bitcoin-core-${BITCOIN_VERSION}"; \
    archive="bitcoin-${BITCOIN_VERSION}-${release_arch}-linux-gnu.tar.gz"; \
    curl -fsSLO "${base}/${archive}"; \
    curl -fsSLO "${base}/SHA256SUMS"; \
    grep "  ${archive}$" SHA256SUMS > SHA256SUMS.selected; \
    sha256sum -c SHA256SUMS.selected; \
    tar -xzf "${archive}"; \
    install -m 0755 "bitcoin-${BITCOIN_VERSION}/bin/bitcoind" /usr/local/bin/bitcoind; \
    install -m 0755 "bitcoin-${BITCOIN_VERSION}/bin/bitcoin-cli" /usr/local/bin/bitcoin-cli; \
    rm -rf "bitcoin-${BITCOIN_VERSION}" "${archive}" SHA256SUMS SHA256SUMS.selected

RUN bitcoind --version | head -1

EXPOSE 8332 8333 28332 28333

ENTRYPOINT ["/usr/local/bin/bitcoind"]
