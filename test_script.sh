#!/bin/bash
# Test script for get_merged_diffs.py

echo "=== Testing get_merged_diffs.py ==="

echo -e "\n1. Testing default configuration (dry run):"
DRY_RUN=true python3 get_merged_diffs.py 2>/dev/null | jq -r '.repository, .status, .age'

echo -e "\n2. Testing custom repository:"
REPO_NAME=openstack/nova DRY_RUN=true python3 get_merged_diffs.py 2>/dev/null | jq -r '.repository'

echo -e "\n3. Testing custom status:"
STATUS=open DRY_RUN=true python3 get_merged_diffs.py 2>/dev/null | jq -r '.status'

echo -e "\n4. Testing custom age:"
AGE=7d DRY_RUN=true python3 get_merged_diffs.py 2>/dev/null | jq -r '.age'

echo -e "\n5. Testing all custom parameters:"
REPO_NAME=openstack/keystone STATUS=closed AGE=30d DRY_RUN=true python3 get_merged_diffs.py 2>/dev/null | jq -r '.query'

echo -e "\n6. Validating JSON structure:"
DRY_RUN=true python3 get_merged_diffs.py 2>/dev/null | jq 'keys'

echo -e "\n=== All tests completed ==="