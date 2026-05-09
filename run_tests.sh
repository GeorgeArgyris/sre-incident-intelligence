#!/bin/bash

# Exit immediately if any command fails
set -e 

echo "================================================"
echo "    SRE Incident Intelligence - Test Suite"
echo "================================================"

echo -e "\n▶ Running API Tests..."
cd api
source venv/bin/activate
pytest tests/ -v
deactivate
cd ..

echo -e "\n▶ Running Enrichment Worker Tests..."
cd enrichment-worker
# Support either virtual env naming convention
source .venv/bin/activate || source venv/bin/activate
pytest tests/ -v
deactivate
cd ..

echo -e "\n▶ Running Producer Tests..."
cd producer
source .venv/bin/activate || source venv/bin/activate
pytest tests/ -v
deactivate
cd ..

echo -e "\n✅ All Python Backend Tests Passed Successfully!"
