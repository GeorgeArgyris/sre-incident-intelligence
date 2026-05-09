#!/bin/bash

# Exit immediately if any command fails
set -e 

echo "================================================"
echo "    SRE Incident Intelligence - Test Suite"
echo "================================================"

function run_test() {
  local dir=$1
  echo -e "\n▶ Running $dir Tests..."
  cd $dir
  
  # Automatically create the virtualenv if it doesn't exist (like inside GitHub Actions)
  if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "Constructing missing virtual environment for $dir..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    # Grab testing packages explicitly since they might not be inside prod requirements
    pip install pytest pytest-mock pytest-asyncio httpx
  else
    source .venv/bin/activate 2>/dev/null || source venv/bin/activate
  fi
  
  pytest tests/ -v
  deactivate
  cd ..
}

run_test "api"
run_test "enrichment-worker"
run_test "producer"

echo -e "\n✅ All Python Backend Tests Passed Successfully!"
