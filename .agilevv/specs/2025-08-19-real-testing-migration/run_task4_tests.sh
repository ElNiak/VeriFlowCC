#!/bin/bash
# Task 4: V-Model Workflow Integration Tests Execution Script
# This script runs the sequential V-Model workflow tests with proper configuration

set -e  # Exit on any error

echo "======================================"
echo "Task 4: V-Model Workflow Integration Tests"
echo "======================================"

# Check for required environment variables
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY environment variable is required for real SDK tests"
    echo "Please set your API key: export ANTHROPIC_API_KEY=\"your-key-here\""
    exit 1
fi

echo "✓ API key configured"

# Create test results directory
mkdir -p test-results

echo "Starting sequential V-Model workflow tests..."
echo "Tests will run one after another to capture proper agent handoff patterns"
echo ""

# Set environment for testing
export PYTHONPATH=".:$PYTHONPATH"
export TEST_ENV=sequential
export VERIFFLOWCC_MOCK_MODE=false

# Run sequential tests with custom configuration
echo "Running Task 4 V-Model workflow handoff tests..."
uv run pytest -c pytest-sequential.ini \
    tests/integration/test_e2e_vmodel_workflow_handoffs.py \
    --verbose \
    --tb=long \
    --durations=0 \
    --log-cli-level=INFO \
    --capture=no \
    --timeout=1800 \
    || echo "Some tests may have failed - check results for details"

echo ""
echo "======================================"
echo "Test Execution Summary"
echo "======================================"

# Check if test results were generated
if [ -f "test-results/sequential-junit.xml" ]; then
    echo "✓ JUnit results: test-results/sequential-junit.xml"
fi

if [ -f "test-results/sequential-report.json" ]; then
    echo "✓ JSON report: test-results/sequential-report.json"
fi

if [ -f "test-results/sequential-test.log" ]; then
    echo "✓ Detailed logs: test-results/sequential-test.log"
fi

# Check for handoff metrics
if ls test-results/handoff_metrics_*.json 1> /dev/null 2>&1; then
    echo "✓ Handoff metrics generated:"
    ls -1 test-results/handoff_metrics_*.json | sed 's/^/  /'
fi

# Check for comprehensive report
if [ -f "test-results/complete_vmodel_cycle_report.json" ]; then
    echo "✓ Complete V-Model cycle report: test-results/complete_vmodel_cycle_report.json"
fi

echo ""
echo "To view detailed handoff analysis, check the generated JSON reports."
echo "To run specific handoff tests individually:"
echo "  uv run pytest tests/integration/test_e2e_vmodel_workflow_handoffs.py::TestVModelWorkflowHandoffs::test_real_requirements_to_design_handoff -v"
echo ""

echo "Task 4 test execution completed!"
