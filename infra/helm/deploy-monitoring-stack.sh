#!/bin/bash
# This script safely deploys the monitoring stack by staging external configs.

# --- Configuration ---
RELEASE_NAME="grafana-prometheus-test"
NAMESPACE="monitoring"
CHART_DIR="./monitoring-stack"
# Path to the parent infra directory.
INFRA_DIR_PATH="../"

# Exit immediately if a command exits with a non-zero status.
set -e

# This trap ensures that the cleanup function is ALWAYS called when the script exits,
# whether it succeeds, fails, or is interrupted.
function cleanup {
  echo "--- Executing cleanup ---"
  rm -rf "${CHART_DIR}/grafana"
  rm -rf "${CHART_DIR}/prometheus"
  echo "Temporary config directories removed."
}
trap cleanup EXIT

# Copy the external config files into the chart directory
echo "--- Preparing monitoring deployment ---"
cp -r "${INFRA_DIR_PATH}/grafana" "${CHART_DIR}/grafana"
cp -r "${INFRA_DIR_PATH}/prometheus" "${CHART_DIR}/prometheus"

# 3. Deploy: Run Helm deployment 
echo "--- Deploying Helm chart to '$NAMESPACE' namespace ---"
helm upgrade --install "$RELEASE_NAME" "$CHART_DIR" \
  --namespace "$NAMESPACE"

echo "--- Helm deployment command succeeded ---"