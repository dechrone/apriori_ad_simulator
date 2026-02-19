====================================================================================================
APRIORI SIMULATION REPORTS - FILE GUIDE
====================================================================================================

This directory contains detailed reports from the Apriori simulation.

FILES:
----------------------------------------------------------------------------------------------------

1. selected_personas.json
   - Raw personas selected from the database
   - Before enrichment

2. enriched_personas.json
   - Personas after psychographic enrichment
   - Includes: purchasing power, digital literacy, device type, etc.

3. raw_reactions.json
   - All raw reactions from the simulation
   - Machine-readable format

4. detailed_reactions.json
   - Structured format with persona + ad + reaction details
   - Useful for analysis

5. readable_reactions.txt
   - Human-readable format
   - Organized by ad, showing each persona's reaction

6. persona_comparison.txt
   - Shows how EACH PERSONA reacted to ALL ADS
   - Useful for understanding persona behavior patterns

7. ad_comparison.txt
   - Shows how ALL PERSONAS reacted to EACH AD
   - Useful for understanding ad effectiveness

8. simulation_report.json
   - Final aggregated report with portfolio optimization
   - Upload this to the dashboard

9. founder_report.txt
   - ✨ FOUNDER-READY REPORT with 'oddly specific' segment insights
   - Shows which ad owns which niche and why
   - Budget allocation based on segment value

====================================================================================================
TIP: Start with 'founder_report.txt' for the strategic verdict,
     then dive into 'persona_comparison.txt' and 'ad_comparison.txt'
     for detailed analysis.
====================================================================================================
