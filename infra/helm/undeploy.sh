#!/bin/bash
# This script uninstalls the niche-explorer application and the monitoring stack.

set -e

echo "--- Uninstalling main application from 'niche-explorer' namespace ---"
helm uninstall -n niche-explorer niche-application

echo "Helm 'niche-application' release uninstalled successfully."


echo ""
echo "--- Uninstalling monitoring stack from 'monitoring' namespace ---"
helm uninstall -n monitoring niche-monitoring

echo "Helm 'niche-monitoring' release uninstalled successfully."


echo ""
echo "Undeployment complete."