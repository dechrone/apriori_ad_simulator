#!/bin/bash
# E2E: Ad simulation n=1, target "age 20-40 in tier1 city", local folder ads_ohsou
# Requires: API server running with APRIORI_SKIP_AUTH=1

set -e
cd "$(dirname "$0")"

echo "=== HTTP request (curl) ==="
echo ""
echo 'curl -X POST http://127.0.0.1:8000/api/v1/simulations/run \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '\''{
  "n": 1,
  "target_group": "age 20-40 in tier1 city",
  "simulation_type": 0,
  "local_ads_dir": "ads_ohsou",
  "product_category": "general"
}'\'''
echo ""
echo "=== Sending request (timeout 300s) ==="
curl -s -X POST http://127.0.0.1:8000/api/v1/simulations/run \
  -H "Content-Type: application/json" \
  -d @e2e_simulation_request.json \
  -w "\n\nHTTP status: %{http_code}\n" \
  --max-time 300 \
  -o e2e_response.json

echo ""
echo "=== Response (first 120 lines) ==="
head -120 e2e_response.json
echo ""
if [ -s e2e_response.json ]; then
  echo "Full response saved to e2e_response.json"
fi
