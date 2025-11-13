## Safety Outcomes of Autonomous Vehicles Relative to Human Drivers in Urban North America (2018–2025)

### Executive Summary
Autonomous vehicles (AVs), particularly those operating at SAE Level 3 or higher in driverless mode, have demonstrated lower per-vehicle-mile crash rates compared to human-driven vehicles in urban settings across the United States, with limited comparable data from Canada, from January 1, 2018, to September 30, 2025 [1][2]. This analysis focuses on quantifiable safety metrics, variations by location and operating conditions, dominant incident types, and regulatory reporting limitations. Data primarily draws from major deployments in cities like Phoenix, San Francisco, Los Angeles, and Austin, with limited comparable information from Canadian urban areas such as Toronto [1][10][18][22]. While AVs show reductions in injury and serious crashes, uncertainties arise from low cumulative AV mileage (e.g., approximately 96 million driverless miles for leading operators), inconsistent reporting thresholds, and operational design domain (ODD) constraints that limit AV exposure to safer conditions [1][3][12]. Overall, AVs appear safer on a per-mile basis where data is available, but direct comparability is challenged by these factors [1][2].

### Quantified Comparative Safety Outcomes
Normalized safety rates for AVs versus human-driven vehicles reveal a pattern of reduced incidents per vehicle-mile traveled (VMT), particularly for injury-related crashes [1][2]. These comparisons are most robust for leading AV operators in U.S. urban deployments, where large-scale public data exists [1][2]. Rates are expressed as incidents per million vehicle-miles traveled (IPMM), a standard normalization to account for exposure differences [1][2]. For context, national human-driven benchmarks from federal data show approximately 0.75 injured persons per million VMT and 0.0126 fatalities per million VMT in 2023, though these are person-level and not directly event-based [11].

AV rates are derived from driverless operations (e.g., Waymo's rider-only mode), which accumulated around 96 million miles through mid-2025 across multiple cities [1]. Human benchmarks are location-matched surface-street rates from police reports in the same geographies [1][2]. Key findings include substantial reductions in any-injury crashes (up to 80% lower for AVs) and serious-injury-or-worse events (over 90% lower) [1][2]. Fatalities in AV operations are rare, with zero reported in the largest datasets, though high-profile testing incidents (e.g., a 2018 pedestrian fatality) highlight early risks [1][2][6]. Uncertainty is moderate for injury rates due to sufficient sample sizes but high for fatalities given low event counts; confidence intervals for AV rates are typically ±20-30% based on published analyses [1][2].

#### Definitions of Rate Denominators
- **Vehicle-Miles Traveled (VMT)**: The total distance traveled by AVs or human-driven vehicles, measured via GPS, odometer, or telemetry systems. For AVs, this excludes human-driven test miles where possible, focusing on driverless (autonomous) operations [1][3].
- **Incidents per Million Vehicle-Miles Traveled (IPMM)**: Calculated as (number of incidents / total VMT) × 1,000,000. Incidents are categorized by severity: property-damage-only (PDO, no injuries), any-injury-reported (at least one injury noted in reports), serious-injury-or-worse (hospitalization or fatality), and fatalities (death within 30 days) [1][2]. Denominators for human benchmarks use city-specific VMT estimates from traffic data, adjusted for surface streets to match AV ODDs [1][2].

| Metric/Severity                  | AV Rate (IPMM) | Human Rate (IPMM) | Key Cities/Period          | Notes/Uncertainty |
|----------------------------------|----------------|-------------------|----------------------------|-------------------|
| Any-Injury-Reported Crashes     | 0.41–0.80     | 2.80–3.96        | Phoenix, SF, LA, Austin (2018–June 2025) | AV reductions ~80%; CI ±25% due to 7–96M AV miles; not statistically significant in low-exposure cities like Austin [1][2]. |
| Serious-Injury-or-Worse Crashes | 0.02          | 0.23             | Multi-city (2018–June 2025) | Over 90% reduction; low AV counts yield wide CIs (±50%) [1]. |
| Airbag-Deployment Crashes       | 0.35          | 1.65             | Multi-city (2018–June 2025) | Proxy for reportable impact; AV ~79% lower [1]. |
| Police-Reportable Crashes       | 2.10          | 4.68             | Multi-city (up to Oct 2023) | AV ~55% lower; based on 7M AV miles [2]. |
| Fatalities                      | 0.00          | 0.0126 (national)| Multi-city (2018–Sep 2025) | Zero in driverless ops; excludes rare testing fatalities; high uncertainty from small samples [1][2][11]. |

Data gaps include limited AV exposure in Canada (e.g., Toronto: <1M driverless miles publicly reported, insufficient for robust rates) and underreporting in human benchmarks due to voluntary police filings [10][17][22]. Rates for other operators (e.g., Cruise) are less reliable due to smaller disclosures and enforcement-noted incompleteness [6][7][15].

### Variations by City and Operating Domain
Safety outcomes vary significantly by urban location and environmental conditions, reflecting differences in traffic density, infrastructure, and AV operational limits [18]. In Phoenix, AVs benefit from expansive, less congested roads, yielding the lowest injury rates (0.63 IPMM any-injury vs. 2.06 human benchmark) [1]. San Francisco shows higher AV rates (0.90 IPMM any-injury vs. 7.93 human) due to denser, pedestrian-heavy environments, though still a ~89% reduction [1]. Los Angeles and Austin exhibit low serious-crash rates (0.00 IPMM in LA), but Austin's small AV mileage (~1M miles) limits statistical confidence [1]. Toronto lacks sufficient driverless VMT for city-specific rates; municipal pilots focus on low-speed shuttles with no large-scale crash data comparable to U.S. robotaxi fleets [10][22].

By operating domain, AV incidents cluster in low-risk conditions aligned with ODDs: ~65% on roads with speed limits ≤25 mph, 93% on dry pavement, and 60% in daylight [18]. Nighttime (dark conditions) accounts for ~36% of reports, but without VMT stratified by lighting, per-mile risks cannot be quantified—proportions suggest AVs avoid unlit operations [18]. Weather variations are minimal (7% wet roads, <1% snow), as AVs curtail services in adverse conditions, potentially biasing rates lower [18]. Speed bands show higher human crash rates above 50 mph, but AVs rarely operate there, creating a comparability gap [18][20]. Uncertainty is high for domain-specific rates (±40-60%) due to absent exposure breakdowns; patterns indicate AVs excel in low-speed urban cores but lack data for highways or inclement weather [1][18].

### Primary Incident Categories and Contributing Factors
AV incidents in urban North America predominantly involve low-severity events, often with the AV as the struck party [5][6]. The top categories, based on analyses of over 2,000 reported events, include [3]:

- **Rear-Ended While Stationary (~40-50% of reports)**: AVs stopped at lights or yielding are hit from behind by human drivers. This dominates due to AVs' conservative behaviors (e.g., full stops). Contributing factor: Human error in tailgating; AVs rarely at fault [5][6].
  
- **AV-Initiated Rear-Ends (~20-30%)**: AVs collide with leading vehicles during acceleration or in stop-and-go traffic. Factors include perception delays in dense flows or overly cautious gap maintenance, leading to late responses [4][5].

- **Intersection/Turning Conflicts (~15-20%)**: Collisions during turns, yields, or cut-ins, elevated at dawn/dusk (5x higher odds vs. humans). Factors: Complex signal prediction and VRU (vulnerable road user) detection failures [3][5].

- **VRU Incidents (~10-15%)**: Pedestrian or cyclist strikes/near-misses, including sensor misses (e.g., a 2023 dragging event). Factors: Occlusion in urban clutter or classification errors; ~2x higher odds during turns [3][6][7][8].

- **Sideswipes/Merges (~5-10%)** and **Fixed-Object Strikes (~5%)**: Lane-change rubs or curb/barrier contacts from path-planning edge cases [4][5].

- **Disengagement-Adjacent (~5%)**: Crashes during human intervention, often in edge scenarios like construction [5][6].

Compared to humans, AVs show 50-90% fewer incidents per mile overall, but higher relative risk in turns and low-light (2-5x odds in matched studies) [1][2][3]. Factors like ODD limits (e.g., no highways) and telematics enhance detection but inflate minor reports [1][20]. Uncertainty stems from redactions (~30% of narratives obscured) and small samples for rare events (e.g., VRU: <100 cases) [3][5][6].

### Regulatory Reporting Gaps Affecting Comparability
Regulatory frameworks differ across jurisdictions, leading to biases in AV-human comparisons. Federal U.S. rules (NHTSA Standing General Order) mandate reporting crashes with injury/fatality or airbag deployment for AVs/ADAS, but states like California require AV manufacturers to report all disengagements (human takeovers, even non-crash) and collisions causing >$1,000 damage [12]. Arizona and Texas focus on testing permits with voluntary incident logs, while Ontario's pilot program requires safety reports but lacks standardized crash thresholds [NHTSA Standing General Order (SGO) crash reporting page; Arizona DOT autonomous vehicle testing pages; Texas DOT CAV Task Force pages; Ontario Automated Vehicle Pilot regulation and program pages]. These inconsistencies mean AVs over-report minor events (e.g., California's ~5 disengagements per 1,000 miles vs. NHTSA's ~0.04 crashes per 1,000 miles for similar exposure), potentially inflating AV incident counts by 5-10x relative to human data, where only severe crashes are systematically captured [13][NHTSA ADAS Level 2 Summary Report (June 2022); California DMV disengagement pages, CSVs and 2023 news release (9,068,861 miles)].

Key gaps include:
- **Inconsistent Definitions**: "Disengagement" (CA: any safety-critical takeover) vs. "reportable crash" (NHTSA: injury/airbag threshold); this captures non-events for AVs, biasing counts upward by ~20-30% in state data [13][NHTSA Automated Vehicles Report to Congress (2023); California DMV disengagement pages].
- **Exposure Undercount**: AV VMT often limited to testing/public ops (~10-20M total across operators), vs. billions for humans; low samples widen CIs (±50% for rare events) [1][13][14].
- **Voluntary/Redacted Reporting**: ~40% of state logs redacted; human crashes underreported (only 50-60% police-filed), while AV telematics ensures near-100% capture [6][5][NHTSA crash-data systems page].
- **Geographic Fragmentation**: No unified Canada-wide system; Toronto pilots underreport vs. U.S. states [22][Ontario Automated Vehicle Pilot regulation and program pages].

#### Rubric for Comparability Limits
1. **Threshold Mismatch (High Impact)**: AVs report minor disengagements/crashes absent in human data, overestimating AV risk by 5x for low-severity events; adjust via severity filtering [RAND report "Measuring Automated Vehicle Safety: Forging a Framework" (RR2662); NHTSA ADAS Level 2 Summary Report (June 2022)].
2. **Exposure Bias (Medium-High Impact)**: AV ODDs exclude high-risk domains (e.g., rain, >50 mph), understating human-AV differences; normalize only within shared conditions [20][1].
3. **Data Completeness (Medium Impact)**: Redactions/underreporting affect ~30-40% of AV logs and >50% of human minor crashes; cross-verify via multiple sources [6][5][NHTSA crash-data systems page].
4. **Sample Size (Variable Impact)**: AV miles <0.01% of human totals; prioritize operators with >10M miles (e.g., Waymo) and quantify uncertainty via CIs [1][2][CRS insight IN11749].

This rubric highlights that while AVs show promising safety gains, unaddressed gaps prevent definitive policy conclusions without standardized reporting by late 2025 [Brookings "state of self-driving car laws" (2018); RAND report "Measuring Automated Vehicle Safety: Forging a Framework" (RR2662)].

### Sources
[1] Waymo Safety Impact Hub - https://waymo.com/safety/impact/  
[2] Kusano et al., Traffic Injury Prevention (2024) - https://www.tandfonline.com/doi/full/10.1080/15389588.2024.2380786  
[3] Nature Communications matched case-control (2024) - https://www.nature.com/articles/s41467-024-48526-4  
[4] Latent class analysis, Journal of Safety Research (2025) - https://www.sciencedirect.com/science/article/pii/S0022437524001634  
[5] NHTSA SGO ADS Incident Reports CSV - https://static.nhtsa.gov/odi/ffdd/sgo-2021-01/SGO-2021-01_Incident_Reports_ADS.csv  
[6] CA DMV Autonomous Vehicle Collision Reports - https://www.dmv.ca.gov/portal/vehicle-industry-services/autonomous-vehicles/autonomous-vehicle-collision-reports/  
[7] NHTSA Cruise Consent Order (2024) - https://www.nhtsa.gov/sites/nhtsa.gov/files/2024-09/cruise-consent-order-2024-web.pdf  
[8] DOJ Press Release Cruise DPA - https://www.justice.gov/usao-ndca/pr/cruise-admits-submitting-false-report-influence-federal-investigation-and-agrees-pay  
[9] Waymo Swiss Re Study (2024) - https://waymo.com/blog/2024/12/new-swiss-re-study-waymo  
[10] Waymo Research Paper Kusano et al. - https://waymo.com/research/comparison-of-waymo-rider-only-crash-data-to-human/  
[11] NHTSA National Statistics PDF - https://cdan.nhtsa.gov/tsftables/National%20Statistics.pdf  
[12] NHTSA Standing General Order Crash Reporting Page - https://www.nhtsa.gov/laws-regulations/standing-general-order-crash-reporting  
[13] CA DMV Disengagement Reports - https://www.dmv.ca.gov/portal/vehicle-industry-services/autonomous-vehicles/disengagement-reports/  
[14] CA DMV News Release 9M Test Miles (2024) - https://www.dmv.ca.gov/portal/news-and-media/news-releases/autonomous-vehicle-permit-holders-report-a-record-9-million-test-miles-in-california-in-12-months/  
[15] NHTSA Consent Order Cruise Press Release - https://www.nhtsa.gov/press-releases/consent-order-cruise-crash-reporting  
[16] NHTSA SGO ADAS Incident Reports CSV - https://static.nhtsa.gov/odi/ffdd/sgo-2021-01/SGO-2021-01_Incident_Reports_ADAS.csv  
[17] Toronto PTC Collision Rates Background - https://www.toronto.ca/legdocs/mmis/2024/ex/bgrd/backgroundfile-251488.pdf  
[18] NHTSA AV Crash Data Summary (2024) - https://archive.legmt.gov/content/Committees/Interim/2023-2024/Transportation/Meetings/241007-July-10-2024/03.020-nhtsa-av-crash-data-summary-2024-posting2.pdf  
[19] Waymo Safety Data Hub Blog (2024) - https://waymo.com/blog/2024/09/safety-data-hub/  
[20] IIHS Self-Driving Vehicles News (2020) - https://www.iihs.org/news/detail/self-driving-vehicles-could-struggle-to-eliminate-most-crashes  
[21] Cruise Third-Party Findings Blog (2024) - https://getcruise.com/news/blog/2024/cruise-releases-third-party-findings-regarding-october-2/  
[22] Toronto AV Pilot Background (2025) - https://www.toronto.ca/legdocs/mmis/2025/ie/bgrd/backgroundfile-254933.pdf  
NHTSA Standing General Order (SGO) Third-Amended PDF (2025)  
NHTSA ADAS Level 2 Summary Report (June 2022)  
NHTSA Automated Vehicles Report to Congress (2023)  
NHTSA Crash-Data Systems Page  
California DMV Disengagement Pages, CSVs and 2023 News Release (9,068,861 miles)  
Ontario Automated Vehicle Pilot Regulation and Program Pages  
Arizona DOT Autonomous Vehicle Testing Pages  
Texas DOT CAV Task Force Pages  
RAND Report "Measuring Automated Vehicle Safety: Forging a Framework" (RR2662)  
Brookings "State of Self-Driving Car Laws" (2018)  
CRS Insight IN11749