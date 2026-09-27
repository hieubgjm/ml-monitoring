#!/bin/bash

# ============================================
# TEST GRAFANA DRIFT DASHBOARD
# ============================================

echo "🎨 Testing Grafana Drift Dashboard..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

GRAFANA_URL="http://localhost:3000"
PROMETHEUS_URL="http://localhost:9090"

# ============================================
# Test 1: Check Grafana is Running
# ============================================
echo -e "${BLUE}Test 1: Grafana Service${NC}"
response=$(curl -s -o /dev/null -w "%{http_code}" "$GRAFANA_URL/api/health")
if [ "$response" == "200" ]; then
    echo -e "${GREEN}✓ Grafana is running${NC}"
else
    echo -e "${RED}✗ Grafana not accessible (HTTP $response)${NC}"
    echo "   Start with: docker-compose up -d grafana"
    exit 1
fi
echo ""

# ============================================
# Test 2: Check Dashboard File Exists
# ============================================
echo -e "${BLUE}Test 2: Dashboard File${NC}"
if [ -f "config/grafana/dashboards/evidently-drift-monitoring.json" ]; then
    size=$(du -h config/grafana/dashboards/evidently-drift-monitoring.json | cut -f1)
    echo -e "${GREEN}✓ Dashboard file exists ($size)${NC}"
else
    echo -e "${RED}✗ Dashboard file not found${NC}"
    exit 1
fi
echo ""

# ============================================
# Test 3: Check Prometheus is Running
# ============================================
echo -e "${BLUE}Test 3: Prometheus Service${NC}"
response=$(curl -s -o /dev/null -w "%{http_code}" "$PROMETHEUS_URL/-/healthy")
if [ "$response" == "200" ]; then
    echo -e "${GREEN}✓ Prometheus is running${NC}"
else
    echo -e "${RED}✗ Prometheus not accessible${NC}"
    echo "   Start with: docker-compose up -d prometheus"
    exit 1
fi
echo ""

# ============================================
# Test 4: Check Evidently Metrics
# ============================================
echo -e "${BLUE}Test 4: Evidently Metrics${NC}"
metrics=$(curl -s "http://localhost:8001/metrics" | grep "evidently_" | wc -l)
if [ "$metrics" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $metrics Evidently metrics${NC}"
else
    echo -e "${YELLOW}⚠ No Evidently metrics found${NC}"
    echo "   Run: ./test_evidently.sh to generate data"
fi
echo ""

# ============================================
# Test 5: Check Prometheus Target
# ============================================
echo -e "${BLUE}Test 5: Prometheus Target${NC}"
target_up=$(curl -s "$PROMETHEUS_URL/api/v1/targets" | grep -o '"job":"evidently"' | wc -l)
if [ "$target_up" -gt 0 ]; then
    echo -e "${GREEN}✓ Evidently target configured in Prometheus${NC}"
else
    echo -e "${RED}✗ Evidently target not found${NC}"
    echo "   Check config/prometheus.yml"
fi
echo ""

# ============================================
# Test 6: Check Alert Rules
# ============================================
echo -e "${BLUE}Test 6: Prometheus Alert Rules${NC}"
if [ -f "config/prometheus/evidently_alerts.yml" ]; then
    alert_count=$(grep -c "alert:" config/prometheus/evidently_alerts.yml)
    echo -e "${GREEN}✓ Alert rules file exists ($alert_count alerts)${NC}"
    
    # Check if loaded in Prometheus
    rules_loaded=$(curl -s "$PROMETHEUS_URL/api/v1/rules" | grep -o "evidently" | wc -l)
    if [ "$rules_loaded" -gt 0 ]; then
        echo -e "${GREEN}✓ Alert rules loaded in Prometheus${NC}"
    else
        echo -e "${YELLOW}⚠ Alert rules not loaded yet${NC}"
        echo "   Restart: docker-compose restart prometheus"
    fi
else
    echo -e "${RED}✗ Alert rules file not found${NC}"
fi
echo ""

# ============================================
# Test 7: Generate Sample Data
# ============================================
echo -e "${BLUE}Test 7: Generate Sample Drift Data${NC}"
echo "   Running mini test..."

# Upload reference data
curl -s -X POST "http://localhost:8001/reference" \
    -H "Content-Type: application/json" \
    -d '{
        "data": [
            {"f1": 1.0, "f2": 2.0, "f3": 3.0},
            {"f1": 1.1, "f2": 2.1, "f3": 3.1},
            {"f1": 0.9, "f2": 1.9, "f3": 2.9}
        ],
        "feature_names": ["f1", "f2", "f3"],
        "description": "Test reference data"
    }' > /dev/null

# Capture production data
for i in {1..5}; do
    curl -s -X POST "http://localhost:8001/capture" \
        -H "Content-Type: application/json" \
        -d "{
            \"features\": {\"f1\": $(awk -v seed=$RANDOM 'BEGIN{srand(seed); print rand()*2}'), \"f2\": $(awk -v seed=$RANDOM 'BEGIN{srand(seed); print rand()*2}'), \"f3\": $(awk -v seed=$RANDOM 'BEGIN{srand(seed); print rand()*2}')},
            \"prediction\": $(awk -v seed=$RANDOM 'BEGIN{srand(seed); print rand()*10}')
        }" > /dev/null
done

# Analyze
result=$(curl -s -X POST "http://localhost:8001/analyze" \
    -H "Content-Type: application/json" \
    -d '{"window_size": 5}')

drift_detected=$(echo $result | grep -o '"drift_detected":true' | wc -l)
if [ $drift_detected -eq 1 ]; then
    echo -e "${YELLOW}✓ Test data generated (drift detected)${NC}"
else
    echo -e "${GREEN}✓ Test data generated (no drift)${NC}"
fi
echo ""

# ============================================
# Test 8: Wait for Prometheus Scrape
# ============================================
echo -e "${BLUE}Test 8: Wait for Metrics Update${NC}"
echo -n "   Waiting for Prometheus to scrape (30s)..."
sleep 30
echo -e " ${GREEN}✓${NC}"
echo ""

# ============================================
# Test 9: Verify Metrics in Prometheus
# ============================================
echo -e "${BLUE}Test 9: Verify Metrics in Prometheus${NC}"

metrics_to_check=(
    "evidently_data_drift_detected"
    "evidently_drift_score"
    "evidently_drifted_features_count"
    "evidently_analysis_total"
)

for metric in "${metrics_to_check[@]}"; do
    result=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$metric" | grep -o "\"value\":\[" | wc -l)
    if [ "$result" -gt 0 ]; then
        echo -e "   ${GREEN}✓${NC} $metric"
    else
        echo -e "   ${RED}✗${NC} $metric"
    fi
done
echo ""

# ============================================
# Summary & Next Steps
# ============================================
echo "════════════════════════════════════════════════"
echo -e "${GREEN}✅ Dashboard Testing Complete${NC}"
echo "════════════════════════════════════════════════"
echo ""
echo "📊 Access Dashboard:"
echo "   URL: $GRAFANA_URL/d/evidently-drift"
echo "   Login: admin / admin"
echo ""
echo "🔔 Check Alerts:"
echo "   URL: $PROMETHEUS_URL/alerts"
echo ""
echo "📈 View Metrics:"
echo "   URL: $PROMETHEUS_URL/graph"
echo "   Query: evidently_data_drift_detected"
echo ""
echo "📝 Documentation:"
echo "   Guide: GRAFANA_DRIFT_DASHBOARD.md"
echo "   Setup: GRAFANA_DASHBOARD_SETUP.md"
echo ""
echo "🎯 Next Steps:"
echo "   1. Open Grafana dashboard (link above)"
echo "   2. Verify all 11 panels show data"
echo "   3. Check Prometheus alerts are loaded"
echo "   4. Integrate with your API for auto-capture"
echo "   5. Setup alert notifications (Slack/Email)"
echo ""
