from pathlib import Path
p=Path("seymour-blockchain-manager/docker-compose.yml");t=p.read_text();a='      ADOPTION_PLAN_DIRECTORY: /evidence/adoption-plans\n';b=a+'      OPERATIONS_EVIDENCE_PATH: /evidence/operations.jsonl\n      HEALTH_HISTORY_PATH: /evidence/health-history.jsonl\n      BCH_BACKUP_ROOT: /evidence/backups\n      BCH_NODE_CONTAINER: seymour-bch-node_node_1\n'
if "OPERATIONS_EVIDENCE_PATH" not in t:
 if a not in t: raise SystemExit("Expected adoption environment anchor not found.")
 t=t.replace(a,b,1)
p.write_text(t);print("Blockchain Operations Center environment added.")
