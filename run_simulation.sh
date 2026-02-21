#!/bin/bash

# Run Apriori simulation in foreground with full output
# This script runs the simulation in your terminal so you can see all output

cd /Users/rahul/CrediGo/Apriori/backend

echo "=========================================="
echo "APRIORI AD PORTFOLIO SIMULATOR"
echo "=========================================="
echo ""
echo "Starting simulation..."
echo "This will take 3-5 minutes"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ensure OpenRouter key and models are set for this run
export OPENROUTER_API_KEY="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"
export GEMINI_PRO_MODEL="google/gemini-2.5-pro"
export GEMINI_FLASH_MODEL="google/gemini-2.5-flash"
export MAX_CONCURRENT_REQUESTS="5"

# Run the simulation
python3 main.py

echo ""
echo "=========================================="
echo "SIMULATION COMPLETE"
echo "=========================================="
echo ""
echo "Reports saved in data/ directory:"
echo "  - persona_comparison.txt"
echo "  - ad_comparison.txt"
echo "  - readable_reactions.txt"
echo "  - simulation_report.json"
echo ""
echo "To view dashboard: streamlit run src/ui/app.py"
