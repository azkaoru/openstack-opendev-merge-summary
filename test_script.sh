#!/bin/bash
# Test script for get_merged_diffs.py

echo "=== Testing get_merged_diffs.py ==="

echo -e "\n1. Testing default configuration (dry run):"
OPENDEV_DRY_RUN=true python3 get_merged_diffs.py 2>/dev/null | jq -r '.repository, .status, .age'

echo -e "\n2. Testing custom repository:"
OPENDEV_REPO_NAME=openstack/nova OPENDEV_DRY_RUN=true python3 get_merged_diffs.py 2>/dev/null | jq -r '.repository'

echo -e "\n3. Testing custom status:"
OPENDEV_STATUS=open OPENDEV_DRY_RUN=true python3 get_merged_diffs.py 2>/dev/null | jq -r '.status'

echo -e "\n4. Testing custom age:"
OPENDEV_AGE=7d OPENDEV_DRY_RUN=true python3 get_merged_diffs.py 2>/dev/null | jq -r '.age'

echo -e "\n5. Testing all custom parameters:"
OPENDEV_REPO_NAME=openstack/keystone OPENDEV_STATUS=closed OPENDEV_AGE=30d OPENDEV_DRY_RUN=true python3 get_merged_diffs.py 2>/dev/null | jq -r '.query'

echo -e "\n6. Validating JSON structure:"
OPENDEV_DRY_RUN=true python3 get_merged_diffs.py 2>/dev/null | jq 'keys'

echo -e "\n=== All tests completed ==="