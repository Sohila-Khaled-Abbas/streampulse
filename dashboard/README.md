# 🎬 StreamPulse: Native Netflix Web-App in Power BI

This directory guides you through deploying the **Native Netflix-Style Web Application inside Power BI Desktop & Power BI Service**.

---

## 🌟 What Makes This Power BI Dashboard Look Like a Streaming Web Platform?

Instead of standard generic corporate visuals, this semantic model and report design leverage:
1. **Embedded HTML5 & CSS3 Components** (via the HTML Content visual):
   - **Netflix Top Navigation Bar**: Sticky header with brand logo, active page indicator pills, and live DirectQuery status pulse.
   - **Hero Featured Trailer Card**: Dynamic movie hero banner with age rating, 4K Ultra HD badges, 5.1 Audio badges, and Bayesian match score.
   - **Movie Poster Carousel Cards**: Interactive cards with animated glowing red hover borders (`#E50914`) and completion progress bars.
   - **Interactive Modal Detail Tooltip**: Pop-up window for deep title drilldown.
2. **Dynamic SVG Vector Measures** (`Data Category: Image URL`):
   - Dynamic gradient completion bars (`#00D2D2` to `#E50914`).
   - Smooth multi-point viewership sparkline curves.
   - Golden IMDb/TMDb rating star badges.
   - Financial ROI radial bullet meters with 2.5x break-even line.
3. **Kimball Galaxy Star Schema**:
   - 3 Fact tables (`Fact_Streaming_Performance`, `Fact_Catalog_Ratings`, `Fact_Financial_ROI`).
   - 5 Conformed Dimensions (`Dim_Titles`, `Dim_Date`, `Dim_Genres`, `Dim_Territory`, `Dim_Talent_Crew`).
   - 2 Many-to-Many Bridge tables (`Bridge_Title_Genre`, `Bridge_Title_Talent`).
4. **45+ Advanced DAX Measures & Calculation Groups**:
   - Organized in 7 clean display folders.
   - Includes Bayesian Quality Rating ($m=25,000$, $C=7.0$), Pareto 80/20 Concentration, Cost Per View Hour (CPVH), and Time Intelligence Matrix.

---

## 🚀 Quick Setup Instructions

1. Read the full step-by-step masterclass in [docs/powerbi_analytics_engineering_guide.md](file:///d:/courses/Data%20Science/Data%20Engineering/Projects/streampulse/docs/powerbi_analytics_engineering_guide.md).
2. Open **Power BI Desktop**.
3. Import the theme file `netflix_cinematic_dark.json` (from Section 7 of the guide) via **View > Themes > Browse for Themes**.
4. In **Power Query**, copy and paste the 10 M queries from Section 2 of the guide.
5. In **Model View**, establish the single-direction relationships defined in the Galaxy Relationship Matrix.
6. Create the `_Measures` table and paste the 45+ DAX measures and HTML/SVG visual measures.
7. Add the **HTML Content** custom visual from AppSource and bind the `[HTML_Netflix_Navbar]` and `[HTML_Netflix_Hero_Card]` measures!
