#!/bin/bash
# This script uninstalls the niche-explorer application and the monitoring stack.

set -e

echo "--- Checking and uninstalling main application from 'niche-explorer' namespace ---"
if helm list -n niche-explorer --short | grep -q '^niche-application$'; then
  helm uninstall -n niche-explorer niche-application
  echo "Helm 'niche-application' release uninstalled successfully."
else
  echo "Helm 'niche-application' release not found in niche-explorer namespace. Skipping uninstallation."
fi


echo ""
echo "--- Checking and uninstalling monitoring stack from 'monitoring' namespace ---"
if helm list -n monitoring --short | grep -q '^niche-monitoring$'; then
  helm uninstall -n monitoring niche-monitoring
  echo "Helm 'niche-monitoring' release uninstalled successfully."
else
  echo "Helm 'niche-monitoring' release not found in monitoring namespace. Skipping uninstallation."
fi


echo ""
echo "Undeployment complete."