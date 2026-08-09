from pathlib import Path

path = Path('seymour-bch-node/docker-compose.yml')
text = path.read_text()
start = text.find('    healthcheck:\n')
end = text.find('\n    volumes:\n', start)
if start == -1 or end == -1:
    raise SystemExit('Could not locate BCH node healthcheck block.')
replacement = '''    healthcheck:
      test:
        - CMD-SHELL
        - >-
          output="$$(bitcoin-cli
          -conf=$${BCH_CONFIG_DIR:-/generated}/bitcoin.conf
          -datadir=$${BCH_DATA_DIR:-/data}
          -rpcconnect=127.0.0.1
          -rpcport=$${BCH_RPC_PORT:-8332}
          -rpcwait
          -rpcwaittimeout=5
          uptime 2>&1)";
          rc=$$?;
          if [ "$$rc" -eq 0 ]; then exit 0; fi;
          echo "$$output" | grep -qi "server in warmup" && exit 0;
          echo "$$output" >&2;
          exit "$$rc"
      interval: 30s
      timeout: 10s
      start_period: 90s
      retries: 5
'''
path.write_text(text[:start] + replacement + text[end:])
print('BCH Docker warmup health normalization added.')
