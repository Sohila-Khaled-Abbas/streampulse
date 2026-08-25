# StreamPulse: Power BI Analytics & Reporting

This directory contains the Power BI reporting assets (`.pbix` files, layout designs, and DAX metric measures) connected directly to the PostgreSQL `reporting` warehouse schema via DirectQuery.

---

## DirectQuery Visual Highlights

The StreamPulse Power BI dashboard exposes real-time streaming intelligence:

1. **Catalog Velocity & Ingestion Pulse**:
   - Total active titles on Netflix.
   - 7-day rolling additions vs. removals.
   - Average days from theatrical premiere to Netflix release (`days_to_streaming`).

2. **Audience Quality & TMDb Rating Distribution**:
   - Average Rating vs. TMDb Popularity Scatter Plot.
   - Top-tier titles distribution ($\ge 8.0$ rating vs. lower tiers).
   - Genre penetration matrix (Drama, Comedy, Sci-Fi, Documentaries).

3. **Entity Match Confidence Monitor**:
   - Health gauge for the Entity Resolution engine (percentage of exact matches vs. fuzzy matches vs. unresolved items).

---

## Connecting Power BI Desktop

1. Start your local database with `docker compose up -d`.
2. Open **Power BI Desktop**.
3. Choose **Home > Get Data > PostgreSQL Database**.
4. Configure connection:
   - **Server**: `localhost:5432`
   - **Database**: `streampulse`
   - **Data Connectivity Mode**: **DirectQuery**
5. Select the view: `reporting.vw_powerbi_catalog_pulse`.
6. Save your report file into this folder as `streampulse_analytics.pbix`.
