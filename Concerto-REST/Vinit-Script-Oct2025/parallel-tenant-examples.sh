#!/bin/bash

# Parallel Tenant Creation Examples for rest-Oct2025.py
# Make sure the script is executable: chmod +x rest-Oct2025.py

echo "=== Parallel Tenant Creation Examples ==="
echo ""

echo "1. Create tenants with a range of Global IDs (50-55):"
echo "   python3 rest-Oct2025.py --action create_tenant --global-ids '50-55' --max-workers 3"
echo ""

echo "2. Create tenants with specific Global IDs (list):"
echo "   python3 rest-Oct2025.py --action create_tenant --global-ids '50,52,54,58' --max-workers 2"
echo ""

echo "3. Create tenants with mixed ranges and lists:"
echo "   python3 rest-Oct2025.py --action create_tenant --global-ids '50-52,55,60-62' --max-workers 4"
echo ""

echo "4. Create tenants with colon-separated range:"
echo "   python3 rest-Oct2025.py --action create_tenant --global-ids '50:55' --max-workers 3"
echo ""

echo "5. Single tenant (backward compatible):"
echo "   python3 rest-Oct2025.py --action create_tenant --global-id 50"
echo ""

echo "6. Parallel with custom ECP settings:"
echo "   python3 rest-Oct2025.py -ip 10.73.70.70 -user Script1 -password 'scr1@Versa123' \\"
echo "     --action create_tenant --global-ids '100-105' --max-workers 5 \\"
echo "     --bandwidth 2000 --license-year 2024"
echo ""

echo "7. Using static JSON mode (parallel):"
echo "   python3 rest-Oct2025.py --action create_tenant --global-ids '50-52' \\"
echo "     --use-static-json --payload StaticTenant.json --max-workers 2"
echo ""

echo "TIPS:"
echo "- Use --max-workers to control parallel execution (default: 5)"
echo "- Each tenant gets auto-generated name: Script-Tenant-{ID}"
echo "- Monitor logs for detailed per-tenant progress"
echo "- Failed tenants will be reported in the summary"
echo "- Script exits with error code if any tenant fails"
