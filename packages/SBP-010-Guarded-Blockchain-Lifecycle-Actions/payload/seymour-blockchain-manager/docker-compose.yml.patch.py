from pathlib import Path
p=Path.cwd()/'seymour-blockchain-manager/docker-compose.yml';s=p.read_text()
s=s.replace('      DOCKER_SOCKET: /var/run/docker.sock','      DOCKER_SOCKET: /var/run/docker.sock\n      SEYMOUR_UMBREL_CONTROL_SCRIPT: /control/seymour-umbrel-app\n      LIFECYCLE_EVIDENCE_PATH: /evidence/lifecycle.jsonl')
s=s.replace('      - /var/run/docker.sock:/var/run/docker.sock:ro','      - /var/run/docker.sock:/var/run/docker.sock:ro\n      - ${APP_DATA_DIR}/data/evidence:/evidence\n      - /home/umbrel/seymour-umbrel-app-store-git/scripts:/control:ro')
p.write_text(s);print('Lifecycle compose contract installed.')
