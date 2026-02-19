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
