from pathlib import Path
import importlib.util, sys
repo = Path(__file__).resolve().parents[1]
bridge_path = repo / 'shared/umbrel_control/bridge.py'
spec = importlib.util.spec_from_file_location('sbp024_bridge', bridge_path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
assert module._state_matches_action('restart', 'ready')
assert module._state_matches_action('start', 'running')
assert module._state_matches_action('stop', 'stopped')
assert not module._state_matches_action('restart', 'stopped')
text = bridge_path.read_text()
assert '"reconciled": True' in text
assert 'Post-operation state reconciliation failed' in text
print('SBP-024 lifecycle post-state reconciliation verification: PASS')
print('SBP-024 lifecycle import-time verification: PASS')
