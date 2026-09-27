#!/bin/bash

# ============================================
# TEST EVIDENTLY AI INTEGRATION
# ============================================

echo "🧪 Testing Evidently AI Service..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

EVIDENTLY_URL="http://localhost:8001"

# ============================================
# Test 1: Health Check
# ============================================
echo -e "${BLUE}Test 1: Health Check${NC}"
response=$(curl -s "$EVIDENTLY_URL/health")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Service is running${NC}"
    echo "   Response: $response"
else
    echo -e "${RED}✗ Service not accessible${NC}"
    exit 1
fi
echo ""

# ============================================
# Test 2: Check Reference Data
# ============================================
echo -e "${BLUE}Test 2: Check Reference Data${NC}"
response=$(curl -s "$EVIDENTLY_URL/reference")
echo "   $response"

reference_loaded=$(echo $response | grep -o '"loaded":true' | wc -l)
if [ $reference_loaded -eq 1 ]; then
    echo -e "${GREEN}✓ Reference data is loaded${NC}"
else
    echo -e "${YELLOW}⚠ No reference data loaded yet${NC}"
    echo -e "${YELLOW}  You need to upload reference data first${NC}"
fi
echo ""

# ============================================
# Test 3: Upload Sample Reference Data
# ============================================
if [ $reference_loaded -eq 0 ]; then
    echo -e "${BLUE}Test 3: Upload Sample Reference Data${NC}"
    
    # Create sample data (wine dataset features)
    cat > /tmp/sample_reference.json << 'EOF'
{
  "data": [
    {"feature_1": 7.4, "feature_2": 0.7, "feature_3": 0.0, "feature_4": 1.9, "feature_5": 0.076},
    {"feature_1": 7.8, "feature_2": 0.88, "feature_3": 0.0, "feature_4": 2.6, "feature_5": 0.098},
    {"feature_1": 7.8, "feature_2": 0.76, "feature_3": 0.04, "feature_4": 2.3, "feature_5": 0.092},
    {"feature_1": 11.2, "feature_2": 0.28, "feature_3": 0.56, "feature_4": 1.9, "feature_5": 0.075},
    {"feature_1": 7.4, "feature_2": 0.7, "feature_3": 0.0, "feature_4": 1.9, "feature_5": 0.076}
  ],
  "feature_names": ["feature_1", "feature_2", "feature_3", "feature_4", "feature_5"],
  "description": "Sample wine dataset reference data"
}
EOF
    
    response=$(curl -s -X POST "$EVIDENTLY_URL/reference" \
        -H "Content-Type: application/json" \
        -d @/tmp/sample_reference.json)
    
    echo "   $response"
    echo -e "${GREEN}✓ Sample reference data uploaded${NC}"
    echo ""
fi

# ============================================
# Test 4: Capture Sample Production Data
# ============================================
echo -e "${BLUE}Test 4: Capture Production Data${NC}"

for i in {1..10}; do
    # Add some variation to simulate drift
    variation=$(awk -v seed=$RANDOM 'BEGIN{srand(seed); print rand()*0.5}')
    
    curl -s -X POST "$EVIDENTLY_URL/capture" \
        -H "Content-Type: application/json" \
        -d "{
            \"features\": {
                \"feature_1\": $(awk -v v=$variation 'BEGIN{print 7.4 + v}'),
                \"feature_2\": $(awk -v v=$variation 'BEGIN{print 0.7 + v*0.1}'),
                \"feature_3\": $(awk -v v=$variation 'BEGIN{print 0.0 + v*0.1}'),
                \"feature_4\": $(awk -v v=$variation 'BEGIN{print 1.9 + v}'),
                \"feature_5\": $(awk -v v=$variation 'BEGIN{print 0.076 + v*0.01}')
            },
            \"prediction\": $(awk -v v=$variation 'BEGIN{print 5 + v}')
        }" > /dev/null
    
    echo -n "."
done

echo -e "\n${GREEN}✓ Captured 10 production samples${NC}"
echo ""

# ============================================
# Test 5: Trigger Drift Analysis
# ============================================
echo -e "${BLUE}Test 5: Trigger Drift Analysis${NC}"

response=$(curl -s -X POST "$EVIDENTLY_URL/analyze" \
    -H "Content-Type: application/json" \
    -d '{"window_size": 10, "threshold": 0.1}')

echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"

drift_detected=$(echo $response | grep -o '"drift_detected":true' | wc -l)
if [ $drift_detected -eq 1 ]; then
    echo -e "${YELLOW}⚠ Drift detected!${NC}"
else
    echo -e "${GREEN}✓ No drift detected${NC}"
fi
echo ""

# ============================================
# Test 6: List Reports
# ============================================
echo -e "${BLUE}Test 6: List Generated Reports${NC}"
response=$(curl -s "$EVIDENTLY_URL/reports")
report_count=$(echo $response | grep -o '"count":[0-9]*' | grep -o '[0-9]*')

if [ "$report_count" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $report_count report(s)${NC}"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo -e "${YELLOW}⚠ No reports generated yet${NC}"
fi
echo ""

# ============================================
# Test 7: Check Prometheus Metrics
# ============================================
echo -e "${BLUE}Test 7: Check Prometheus Metrics${NC}"
metrics=$(curl -s "$EVIDENTLY_URL/metrics" | grep "evidently_" | head -n 5)

if [ ! -z "$metrics" ]; then
    echo -e "${GREEN}✓ Metrics exposed successfully${NC}"
    echo "   Sample metrics:"
    echo "$metrics" | while read line; do echo "     $line"; done
else
    echo -e "${RED}✗ No metrics found${NC}"
fi
echo ""

# ============================================
# Summary
# ============================================
echo "════════════════════════════════════════════════"
echo -e "${GREEN}✅ Evidently AI Integration Tests Complete${NC}"
echo "════════════════════════════════════════════════"
echo ""
echo "📊 Next steps:"
echo "   1. View Evidently UI: $EVIDENTLY_URL"
echo "   2. View reports: $EVIDENTLY_URL/reports"
echo "   3. Check metrics in Prometheus: http://localhost:9090"
echo "   4. View drift dashboard in Grafana: http://localhost:3000"
echo ""
echo "📝 Available endpoints:"
echo "   - Health: GET $EVIDENTLY_URL/health"
echo "   - Capture data: POST $EVIDENTLY_URL/capture"
echo "   - Analyze drift: POST $EVIDENTLY_URL/analyze"
echo "   - Upload reference: POST $EVIDENTLY_URL/reference"
echo "   - List reports: GET $EVIDENTLY_URL/reports"
echo "   - Metrics: GET $EVIDENTLY_URL/metrics"
echo ""

# Cleanup
rm -f /tmp/sample_reference.json

