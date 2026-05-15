#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
ORCHESTRATOR_DIR="$PROJECT_DIR/mint-orchestrator"

echo "=== Mint Orchestrator Integration Tests ==="
PASS=0
FAIL=0

run_test() {
    local name="$1"
    shift
    echo -n "  [$name] ... "
    if "$@" >/dev/null 2>&1; then
        echo "OK"
        ((PASS++))
    else
        echo "FAIL"
        ((FAIL++))
    fi
}

run_test_verbose() {
    local name="$1"
    shift
    echo -n "  [$name] ... "
    output=$("$@" 2>&1) && rc=$? || rc=$?
    if [[ $rc -eq 0 ]]; then
        echo "OK"
        ((PASS++))
    else
        echo "FAIL"
        echo "$output" | head -5
        ((FAIL++))
    fi
}

echo ""
echo "Python package tests:"
run_test_verbose "orchestrator imports" python3 -c "from tollgate_mint_orchestrator.mint_registry import MintRegistry"
run_test_verbose "validator imports" python3 -c "from tollgate_mint_orchestrator.event_validator import EventValidator, SUPPORTED_UNITS"
run_test_verbose "audit imports" python3 -c "from tollgate_mint_orchestrator.audit_log import AuditLogger"
run_test_verbose "api imports" python3 -c "from tollgate_mint_orchestrator.api import OrchestratorAPI"
run_test_verbose "subscriber imports" python3 -c "from tollgate_mint_orchestrator.nostr_subscriber import NostrSubscriber"
run_test_verbose "grpc imports" python3 -c "from tollgate_mint_orchestrator.grpc_client import MintGrpcClient"
run_test_verbose "daemon imports" python3 -c "from tollgate_mint_orchestrator.daemon import run_daemon"
run_test_verbose "cli imports" python3 -c "from tollgate_mint_approve.cli import main, SUPPORTED_UNITS as CLI_UNITS"

echo ""
echo "Unit tests:"
if command -v pytest >/dev/null 2>&1; then
    export PYTHONPATH="$ORCHESTRATOR_DIR/src:$PROJECT_DIR/mint-approve/src"
    run_test_verbose "pytest registry" pytest "$ORCHESTRATOR_DIR/tests/test_mint_registry.py" -v --tb=short 2>&1
    run_test_verbose "pytest validator" pytest "$ORCHESTRATOR_DIR/tests/test_event_validator.py" -v --tb=short 2>&1
    run_test_verbose "pytest audit" pytest "$ORCHESTRATOR_DIR/tests/test_audit_log.py" -v --tb=short 2>&1
    run_test_verbose "pytest grpc" pytest "$ORCHESTRATOR_DIR/tests/test_grpc_client.py" -v --tb=short 2>&1
    run_test_verbose "pytest daemon" pytest "$ORCHESTRATOR_DIR/tests/test_daemon.py" -v --tb=short 2>&1
else
    echo "  pytest not found, skipping unit tests"
    ((FAIL++))
fi

echo ""
echo "========================================"
echo "Results: $PASS passed, $FAIL failed"
echo "========================================"

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
