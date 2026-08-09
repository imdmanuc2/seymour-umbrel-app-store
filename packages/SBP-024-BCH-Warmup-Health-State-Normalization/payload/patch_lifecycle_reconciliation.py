from pathlib import Path

path = Path('shared/umbrel_control/bridge.py')
text = path.read_text()
old = '''        except Exception as exc:
            operation.executed = True
            operation.success = False
            operation.error = str(exc)
'''
new = '''        except Exception as exc:
            operation.executed = True
            if app_id is not None and action in {"start", "restart", "stop"}:
                try:
                    state_payload = self._invoke("state", app_id)
                    state = state_payload.get("result", state_payload) if isinstance(state_payload, dict) else state_payload
                    current_state = state.get("state") if isinstance(state, dict) else state
                    if _state_matches_action(action, current_state):
                        operation.success = True
                        operation.error = None
                        operation.result = {
                            "reconciled": True,
                            "state": current_state,
                            "nativeError": str(exc),
                            "statePayload": state_payload,
                        }
                    else:
                        operation.success = False
                        operation.error = _native_result_error(state_payload) or str(exc)
                except Exception as state_exc:
                    operation.success = False
                    operation.error = str(exc) + " Post-operation state reconciliation failed: " + str(state_exc)
            else:
                operation.success = False
                operation.error = str(exc)
'''
if old not in text:
    raise SystemExit('Could not locate lifecycle execute exception block.')
path.write_text(text.replace(old, new, 1))
print('Umbrel lifecycle post-state reconciliation wired.')
