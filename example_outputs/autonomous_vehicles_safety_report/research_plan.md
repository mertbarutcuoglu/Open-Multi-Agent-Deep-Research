## Research Plan for Safety Outcomes of Autonomous Vehicles vs. Human Drivers in Urban North America (2018–2025)

### Assessment and Breakdown
- **Main Concepts**: Comparative safety metrics (collision, injury, fatality rates per vehicle-mile); variations by location (cities in US/Canada) and conditions (day/night, weather, speed limits); dominant AV incident types (e.g., rear-end collisions, disengagement-related); regulatory reporting gaps affecting data comparability.
- **Key Entities**: Autonomous vehicles (AVs, focusing on SAE Level 3+ or driverless deployments); human-driven vehicles; urban environments in US (e.g., San Francisco, Phoenix, Austin, Los Angeles) and Canada (e.g., Toronto); incidents by severity (property damage, injury, fatality).
- **Specific Facts Needed**: Normalized rates (per VMT or VHT); exposure data (miles/hours driven); incident counts by type, severity, location, domain; definitions of terms (disengagement, reportable crash); sources of bias (incomplete reporting, inconsistent definitions).
- **Temporal/Contextual Constraints**: Data from Jan 1, 2018, to Sep 30, 2025; urban North America only; current as of Nov 2025.
- **User Priorities**: Quantifiable comparisons with uncertainty quantified; clear tables and definitions; focus on policy-relevant gaps; neutral, evidence-based analysis for analysts/executives.

### Query Type
Breadth-first query. The topic divides into independent sub-topics: (1) core safety rates comparison, (2) variations by city/domain, (3) incident categories/factors, (4) reporting gaps/biases. These can be researched in parallel without heavy dependencies, enabling efficient coverage of metrics, variations, incidents, and limitations. Synthesis will aggregate into a cohesive report with table and rubric.

### Detailed Research Plan
- **Subagent Allocation** (4 subagents for medium complexity; parallel deployment to cover distinct components efficiently):
  1. **Subagent: safety_rates_agent** - Focus: Quantify collision, injury, fatality rates per vehicle-mile (VMT) for AVs vs. human vehicles. Gather exposure-normalized data by severity; include city-level where available (e.g., SF, Phoenix, Toronto). Sources: NHTSA/FARS, California DMV, Arizona DOT, Toronto TTC reports; AV company safety reports (Waymo, Cruise, Uber ATG); peer-reviewed studies (e.g., from TRB, arXiv preprints with methods disclosed). Output: Structured data table with rates, exposure definitions, sources; note uncertainties/gaps. Prioritize 2+ sources per claim; quantify via confidence intervals if available.
  2. **Subagent: variations_analysis_agent** - Focus: Variations in outcomes by city (US/Canada urban) and domain (day/night, weather, speed limits <25/25-50/>50 mph). Use same sources; extract breakdowns from reports/studies. Output: Summary of patterns (e.g., higher AV rates in rain?); data points by category; highlight data scarcity. Ensure 2+ sources; flag inconsistencies.
  3. **Subagent: incident_types_agent** - Focus: Dominant AV incident categories (e.g., rear-end while stationary, pedestrian interactions, disengagement-adjacent); contributing factors (e.g., sensor limitations, traffic density). Sources: AV incident databases (NHTSA, DMV disengagement reports), company incident logs, peer-reviewed analyses. Output: List of top categories with frequencies/examples; factors breakdown; compare to human incidents where possible. 2+ sources per type.
  4. **Subagent: reporting_gaps_agent** - Focus: Regulatory frameworks (e.g., disengagement vs. crash reporting in CA, federal NHTSA rules); definitions inconsistencies; biases (e.g., AVs over-report minor incidents). Sources: Regulatory docs (FMVSS, state AV laws), GAO/CRS reports, studies on data comparability (e.g., RAND, UC Berkeley). Output: Key gaps/limitations; rubric outline for comparability; quantify biases (e.g., % underreported human crashes). 2+ sources.

- **Evaluation of Plan Elements**:
  - **Independence**: Each subagent handles a distinct key question; minimal overlap (e.g., sources shared but analyses separate).
  - **Multiple Perspectives**: Subagents instructed to use diverse sources (official, company, academic) for verification.
  - **Expected Outputs**: Factual summaries with data, sources, uncertainties; aggregate to enable table creation, variation discussion, incident lists, gap analysis.
  - **Necessity**: Directly maps to objectives/questions; covers must-includes (rates table, definitions, rubric).
  - **Efficiency**: 4 subagents (no more than needed); parallel execution; if gaps found post-run, iterate with 1-2 more (e.g., fact-check agent).

- **Synthesis Approach**: Compile rates into a Markdown table (AV vs. human, by severity/city); define denominators (e.g., VMT = total miles driven, verified via odometer/GPS); discuss variations/incidents narratively; end with rubric on limits (e.g., AV data skewed by testing vs. full ops). Resolve conflicts via recency/consensus; quantify uncertainty (e.g., "rates based on 10M AV miles, CI ±20%"). Ensure neutral tone, no speculation.

- **Execution Strategy**: Deploy all 4 subagents in parallel immediately after plan save. Review outputs for completeness; if needed, deploy 1 serial follow-up (e.g., for specific city data). Synthesize when sufficient (diminishing returns after initial runs). No self-research beyond planning; terminate if core facts covered (e.g., key rates from 3+ cities).

This plan ensures comprehensive, evidence-based coverage for an excellent report.