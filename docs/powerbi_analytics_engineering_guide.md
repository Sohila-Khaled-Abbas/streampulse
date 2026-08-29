# 🎬 StreamPulse: Power BI Native Netflix Web-App & Kimball Galaxy Masterclass

Welcome to the **StreamPulse 2026 Enterprise Power BI Analytics Engineering Guide**. This masterclass provides a complete, click-by-click blueprint to build a **fully native Netflix-style streaming web application inside Power BI Desktop & Service**. 

It combines **Kimball Galaxy Multi-Fact Star Schema Architecture**, **Advanced M Language (Power Query) ETL Pipelines**, **45+ Business-Critical DAX Measures**, **Calculation Groups**, **Dynamic SVG Visual Measures**, and **Native HTML5 & CSS3 Embedded Visual Components** (via the HTML Content visual and SVG Image URL measures) to turn Power BI into an interactive, cinematic data platform.

---

## 📑 Masterclass Table of Contents
1. [Enterprise Architecture: The Kimball Galaxy Constellation](#1-enterprise-architecture-the-kimball-galaxy-constellation)
2. [Multi-Source Ingestion & Advanced M Language (Power Query) Scripts](#2-multi-source-ingestion--advanced-m-language-power-query-scripts)
   - [Conformed Dimension Queries (Dim_Titles, Dim_Date, Dim_Genres, Dim_Territory, Dim_Talent_Crew)](#conformed-dimension-queries)
   - [Many-to-Many Bridge Queries (Bridge_Title_Genre, Bridge_Title_Talent)](#many-to-many-bridge-queries)
   - [Multi-Grain Fact Queries (Fact_Streaming_Performance, Fact_Catalog_Ratings, Fact_Financial_ROI)](#multi-grain-fact-queries)
3. [Netflix Web-App UI Components in Power BI (HTML, CSS & SVG)](#3-netflix-web-app-ui-components-in-power-bi-html-css--svg)
   - [HTML/CSS Web Component 1: Netflix Top Navigation Header](#htmlcss-web-component-1-netflix-top-navigation-header)
   - [HTML/CSS Web Component 2: Netflix Featured Hero Player & Metadata Card](#htmlcss-web-component-2-netflix-featured-hero-player--metadata-card)
   - [HTML/CSS Web Component 3: Netflix Movie Poster Card Carousel with Hover Glow](#htmlcss-web-component-3-netflix-movie-poster-card-carousel-with-hover-glow)
   - [HTML/CSS Web Component 4: Interactive Glassmorphic KPI Scorecard](#htmlcss-web-component-4-interactive-glassmorphic-kpi-scorecard)
   - [HTML/CSS Web Component 5: Netflix "More Info" Modal Detail Pop-up (Tooltip Page)](#htmlcss-web-component-5-netflix-more-info-modal-detail-pop-up-tooltip-page)
4. [Dynamic SVG Vector Visual Measures (Data Category: Image URL)](#4-dynamic-svg-vector-visual-measures-data-category-image-url)
   - [SVG 1: Dynamic Gradient Completion Progress Bar](#svg-1-dynamic-gradient-completion-progress-bar)
   - [SVG 2: Multi-Point Smooth Viewership Sparkline](#svg-2-multi-point-smooth-viewership-sparkline)
   - [SVG 3: Golden Rating Star Badge](#svg-3-golden-rating-star-badge)
   - [SVG 4: Financial ROI Radial Meter & Break-Even Marker](#svg-4-financial-roi-radial-meter--break-even-marker)
   - [SVG 5: Global Top 10 Red Number Rank Visual](#svg-5-global-top-10-red-number-rank-visual)
5. [Enterprise DAX Measure Library (45+ Measures & 7 Display Folders)](#5-enterprise-dax-measure-library-45-measures--7-display-folders)
   - [Folder 01: Core Streaming & Catalog KPIs](#folder-01-core-streaming--catalog-kpis)
   - [Folder 02: Time Intelligence (YoY, MoM, YTD, Rolling Velocity)](#folder-02-time-intelligence)
   - [Folder 03: Advanced Analytics & Pareto 80/20 Concentration](#folder-03-advanced-analytics--pareto-8020-concentration)
   - [Folder 04: Bayesian Rating & Quality Scoring](#folder-04-bayesian-rating--quality-scoring)
   - [Folder 05: Financial ROI & Unit Economics](#folder-05-financial-roi--unit-economics)
   - [Folder 06: Dynamic SVG Visual Measures](#folder-06-dynamic-svg-visual-measures)
   - [Folder 07: HTML/CSS Web-App Components](#folder-07-htmlcss-web-app-components)
6. [Calculation Groups: Time Intelligence & Unit Currency Switcher](#6-calculation-groups-time-intelligence--unit-currency-switcher)
7. [Netflix Cinematic Dark JSON Theme File](#7-netflix-cinematic-dark-json-theme-file)
8. [5-Page Native Web-App Layout & Navigation Architecture](#8-5-page-native-web-app-layout--navigation-architecture)
9. [DirectQuery Performance Tuning & Production Best Practices](#9-directquery-performance-tuning--production-best-practices)

---

## 1. Enterprise Architecture: The Kimball Galaxy Constellation

The StreamPulse Semantic Model is built on a **Kimball Galaxy Star Schema** (Constellation Schema). It unites three distinct business processes (Streaming Telemetry, Catalog Quality, and Box Office ROI) around shared **Conformed Dimensions**.

```
                                    +-----------------------+
                                    |     Dim_Territory     |
                                    +-----------------------+
                                                | 1
                                                | *
+--------------------+ 1            * +---------------------------+ *            1 +-------------------+
|     Dim_Genres     | <------------- |     Bridge_Title_Genre    | -------------> |     Dim_Titles    |
+--------------------+                +---------------------------+                +-------------------+
                                                                                     | 1   | 1       | 1
       +-----------------------------------------------------------------------------+     |         +------------------+
       | *                                                                                 | *                          | *
+-----------------------------+               +--------------------------+  1            * |                   +--------------------+
| Fact_Streaming_Performance  |               |      Dim_Talent_Crew     | <---------------+                   | Fact_Financial_ROI |
+-----------------------------+               +--------------------------+                                     +--------------------+
       | *                                                 | 1                                                          | *
       |                                                   | *                                                          |
       |                              +---------------------------+                                                     |
       |                              |    Bridge_Title_Talent    |                                                     |
       |                              +---------------------------+                                                     |
       | *                                                                                                              | *
+--------------------+ 1                                                                                                |
|      Dim_Date      | <------------------------------------------------------------------------------------------------+
+--------------------+ 1
       |
       | *
+-----------------------------+
|    Fact_Catalog_Ratings     |
+-----------------------------+
```

### Relationship Design Rules
1. **Single-Direction Filtering (`1:*`)**: Relationships flow exclusively from Dimensions to Fact tables. This prevents ambiguous filter propagation and enables maximum VertiPaq engine cache utilization.
2. **Bridge Tables with Uniform Weights**: Many-to-many relationships between `Dim_Titles` and `Dim_Genres` / `Dim_Talent_Crew` use bridge tables with an explicit `weight` attribute (`1.0`), preventing duplicate row inflation during cross-genre aggregations.
3. **No Direct Fact-to-Fact Relationships**: Metrics crossing business domains (e.g., *View Hours per $1M Budget*) are calculated dynamically in DAX via the shared `Dim_Titles[title_key]` conformed dimension.

---

## 2. Multi-Source Ingestion & Advanced M Language (Power Query) Scripts

To create these tables in Power BI Desktop:
1. Open **Power BI Desktop** $\to$ click **Transform Data** (Power Query Editor).
2. Create a Parameter named `File_Path` (Type: Text) pointing to your local raw directory:
   ```powerquery
   "D:\courses\Data Science\Data Engineering\Projects\streampulse\data\raw\" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]
   ```
3. Create a **Blank Query** for each of the tables below and paste the code into the **Advanced Editor**.

---

### Conformed Dimension Queries

#### Table 1: `Dim_Titles` (Conformed Title Dimension)
```powerquery
let
    // Part A: Extract & Clean Live 2026 Scraped Releases
    SourceLive = try PostgreSQL.Database("localhost:5432", "streampulse") otherwise null,
    stg_data = if SourceLive <> null then SourceLive{[Schema="staging", Item="stg_netflix_titles"]}[Data] else #table({"netflix_id","title","title_type","release_year","date_added","runtime_seconds","maturity_rating"}, {}),

    ScrubLive = Table.TransformColumns(stg_data, {
        {"title", each Text.Proper(Text.Trim(Text.Replace(Text.From(_), Character.FromNumber(160), " "))), type text},
        {"netflix_id", each Text.Trim(Text.From(_)), type text}
    }),

    AddCleanDateLive = Table.AddColumn(ScrubLive, "netflix_date_added_clean", each
        try Date.From(DateTimeZone.From([date_added]))
        otherwise try Date.FromText([date_added], "en-US")
        otherwise try Date.FromText([date_added], "en-GB")
        otherwise #date(2026, 1, 1),
        type date
    ),

    AddCleanRuntimeLive = Table.AddColumn(AddCleanDateLive, "runtime_minutes_clean", each
        let
            txt = if [runtime_seconds] = null then "" else Text.Lower(Text.From([runtime_seconds])),
            mins = if Text.Contains(txt, "mins") or Text.Contains(txt, "min") then
                       Number.From(Text.Select(txt, {"0".."9"}))
                   else if Text.Contains(txt, "h") then
                       let
                           parts = Text.Split(txt, "h"),
                           hours = Number.From(Text.Select(parts{0}, {"0".."9"})),
                           rem_mins = Number.From(Text.Select(parts{1}, {"0".."9"}))
                       in
                           (hours * 60) + rem_mins
                   else if try Number.FromText(txt) > 500 otherwise false then
                       Number.Round(Number.FromText(txt) / 60)
                   else
                       try Number.FromText(txt) otherwise 90
        in
            if mins = null or mins <= 0 then 90 else mins,
        Int64.Type
    ),

    CleanRatingLive = Table.TransformColumns(AddCleanRuntimeLive, {
        {"maturity_rating", each if _ = null then "TV-MA" else Text.Upper(Text.Trim(Text.Replace(Text.From(_), " ", "-"))), type text}
    }),

    SelectLiveCols = Table.SelectColumns(CleanRatingLive, {
        "netflix_id", "title", "title_type", "release_year", "netflix_date_added_clean", "runtime_minutes_clean", "maturity_rating"
    }),

    // Part B: Extract & Clean 7,786 Historical Kaggle Benchmark Records
    SourceHist = Csv.Document(File.Contents(File_Path & "netflix_enriched_historical.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeadersHist = Table.PromoteHeaders(SourceHist, [PromoteAllScalars=true]),

    ScrubHist = Table.TransformColumns(PromotedHeadersHist, {
        {"id", each Text.Trim(Text.From(_)), type text},
        {"title", each Text.Proper(Text.Trim(Text.Replace(Text.From(_), Character.FromNumber(160), " "))), type text},
        {"type", each if _ = null then "Movie" else if Text.Upper(Text.From(_)) = "MOVIE" then "Movie" else "TV Show", type text},
        {"release_year", each try Number.FromText(Text.From(_)) otherwise 2020, Int64.Type},
        {"runtime", each try Number.FromText(Text.From(_)) otherwise 90, Int64.Type},
        {"age_certification", each if _ = null or Text.From(_) = "" then "TV-MA" else Text.Upper(Text.Trim(Text.From(_))), type text}
    }),

    AddCleanDateHist = Table.AddColumn(ScrubHist, "netflix_date_added_clean", each
        let
            y = try Int64.From([release_year]) otherwise 2020,
            valid_y = if y = null or y < 1900 or y > 2100 then 2020 else y
        in
            #date(valid_y, 1, 1),
        type date
    ),

    RenameHist = Table.RenameColumns(AddCleanDateHist, {
        {"id", "netflix_id"},
        {"type", "title_type"},
        {"runtime", "runtime_minutes_clean"},
        {"age_certification", "maturity_rating"}
    }),

    SelectHistCols = Table.SelectColumns(RenameHist, {
        "netflix_id", "title", "title_type", "release_year", "netflix_date_added_clean", "runtime_minutes_clean", "maturity_rating"
    }),

    // Part C: Combine & Enrich Conformed Title Attributes (100% Null-Safe)
    Combined = Table.Combine({SelectLiveCols, SelectHistCols}),
    Deduplicated = Table.Distinct(Combined, {"netflix_id"}),
    AddTitleKey = Table.AddIndexColumn(Deduplicated, "title_key", 1, 1, Int64.Type),

    AddEra = Table.AddColumn(AddTitleKey, "catalog_era", each
        let
            y = if [release_year] = null then 2020 else [release_year]
        in
            if y = 2026 then "2026 Live Releases"
            else if y >= 2024 then "2024-2025 Modern"
            else if y >= 2015 then "2015-2023 Streaming Boom"
            else "Historical Archive (<2015)",
        type text
    ),

    AddRuntimeTier = Table.AddColumn(AddEra, "runtime_tier", each
        let
            t = if [title_type] = null then "Movie" else Text.Proper(Text.Trim(Text.From([title_type]))),
            mins = if [runtime_minutes_clean] = null then 90 else [runtime_minutes_clean]
        in
            if t = "TV Show" then "Episodic Series"
            else if mins < 45 then "Short Feature (<45m)"
            else if mins <= 100 then "Standard Feature (45-100m)"
            else if mins <= 140 then "Extended Feature (101-140m)"
            else "Blockbuster Epic (>140m)",
        type text
    ),

    AddMaturityCategory = Table.AddColumn(AddRuntimeTier, "maturity_category", each
        let
            r = if [maturity_rating] = null then "TV-MA" else Text.Upper(Text.Trim(Text.From([maturity_rating])))
        in
            if r = "TV-MA" or r = "R" or r = "NC-17" then "Adult / Mature (18+)"
            else if r = "TV-14" or r = "PG-13" then "Teens & Young Adults (13+)"
            else if r = "PG" or r = "TV-PG" then "Parental Guidance (PG)"
            else "Kids & Family (G / TV-Y)",
        type text
    )
in
    AddMaturityCategory
```

---

#### Table 2: `Dim_Date` (Dynamic Calendar Dimension)
```powerquery
let
    DatasetDates = List.RemoveNulls(Dim_Titles[netflix_date_added_clean]),
    MinDateRaw = if List.IsEmpty(DatasetDates) then #date(2015, 1, 1) else List.Min(DatasetDates),
    MaxDateRaw = if List.IsEmpty(DatasetDates) then #date(2026, 12, 31) else List.Max(DatasetDates),
    CurrentDate = DateTime.Date(DateTime.LocalNow()),

    StartYear = Date.Year(MinDateRaw),
    EndYear = Date.Year(List.Max({MaxDateRaw, CurrentDate})),
    StartDate = #date(StartYear, 1, 1),
    EndDate = #date(EndYear, 12, 31),

    NumberOfDays = Duration.Days(EndDate - StartDate) + 1,
    DateList = List.Dates(StartDate, NumberOfDays, #duration(1, 0, 0, 0)),
    DateTable = Table.FromList(DateList, Splitter.SplitByNothing(), {"full_date"}, null, ExtraValues.Error),
    TypedDate = Table.TransformColumnTypes(DateTable, {{"full_date", type date}}),

    AddDateKey = Table.AddColumn(TypedDate, "date_key", each Date.Year([full_date]) * 10000 + Date.Month([full_date]) * 100 + Date.Day([full_date]), Int64.Type),
    AddYear = Table.AddColumn(AddDateKey, "year", each Date.Year([full_date]), Int64.Type),
    AddQuarter = Table.AddColumn(AddYear, "quarter", each Date.QuarterOfYear([full_date]), Int64.Type),
    AddQuarterName = Table.AddColumn(AddQuarter, "quarter_name", each "Q" & Text.From([quarter]) & " " & Text.From([year]), type text),
    AddMonthNum = Table.AddColumn(AddQuarterName, "month_number", each Date.Month([full_date]), Int64.Type),
    AddMonthName = Table.AddColumn(AddMonthNum, "month_name", each Date.MonthName([full_date]), type text),
    AddMonthShort = Table.AddColumn(AddMonthName, "month_short", each Text.Start([month_name], 3), type text),
    AddDayOfWeek = Table.AddColumn(AddMonthShort, "day_of_week", each Date.DayOfWeek([full_date], Day.Monday) + 1, Int64.Type),
    AddDayName = Table.AddColumn(AddDayOfWeek, "day_name", each Date.DayOfWeekName([full_date]), type text),
    AddIsWeekend = Table.AddColumn(AddDayName, "is_weekend", each if [day_of_week] <> null and [day_of_week] >= 6 then true else false, type logical),
    AddFiscalPeriod = Table.AddColumn(AddIsWeekend, "fiscal_period", each "FY" & Text.From(try [year] otherwise 2026) & "-Q" & Text.From(try [quarter] otherwise 1), type text),
    AddIsCurrentYear = Table.AddColumn(AddFiscalPeriod, "is_current_year", each if [full_date] <> null then Date.Year([full_date]) = Date.Year(CurrentDate) else false, type logical),
    AddIsPastOrCurrent = Table.AddColumn(AddIsCurrentYear, "is_past_or_current", each if [full_date] <> null then [full_date] <= CurrentDate else false, type logical),
    AddYearOffset = Table.AddColumn(AddIsPastOrCurrent, "relative_year_offset", each if [full_date] <> null then Date.Year([full_date]) - Date.Year(CurrentDate) else 0, Int64.Type),
    AddMonthOffset = Table.AddColumn(AddYearOffset, "relative_month_offset", each 
        if [full_date] <> null then
            ((Date.Year([full_date]) - Date.Year(CurrentDate)) * 12) + (Date.Month([full_date]) - Date.Month(CurrentDate))
        else 0,
        Int64.Type
    ),
    AddNetflixQuarterEnd = Table.AddColumn(AddMonthOffset, "is_netflix_quarter_end", each 
        if [full_date] <> null then
            (Date.Month([full_date]) = 3 and Date.Day([full_date]) = 31) or
            (Date.Month([full_date]) = 6 and Date.Day([full_date]) = 30) or
            (Date.Month([full_date]) = 9 and Date.Day([full_date]) = 30) or
            (Date.Month([full_date]) = 12 and Date.Day([full_date]) = 31)
        else false,
        type logical
    )
in
    AddNetflixQuarterEnd
```

---

#### Table 3: `Dim_Genres` (Standardized Genre Dimension)
```powerquery
let
    GenreRecords = {
        [genre_key = 1, tmdb_genre_id = 28, genre_name = "Action", genre_category = "Mainstream Commercial", sort_order = 1],
        [genre_key = 2, tmdb_genre_id = 12, genre_name = "Adventure", genre_category = "Mainstream Commercial", sort_order = 2],
        [genre_key = 3, tmdb_genre_id = 16, genre_name = "Animation", genre_category = "Family & Youth", sort_order = 3],
        [genre_key = 4, tmdb_genre_id = 35, genre_name = "Comedy", genre_category = "Mainstream Commercial", sort_order = 4],
        [genre_key = 5, tmdb_genre_id = 80, genre_name = "Crime", genre_category = "Prestige & Thriller", sort_order = 5],
        [genre_key = 6, tmdb_genre_id = 99, genre_name = "Documentary", genre_category = "Prestige & Non-Fiction", sort_order = 6],
        [genre_key = 7, tmdb_genre_id = 18, genre_name = "Drama", genre_category = "Prestige & Thriller", sort_order = 7],
        [genre_key = 8, tmdb_genre_id = 10751, genre_name = "Family", genre_category = "Family & Youth", sort_order = 8],
        [genre_key = 9, tmdb_genre_id = 14, genre_name = "Fantasy", genre_category = "Sci-Fi & Genre", sort_order = 9],
        [genre_key = 10, tmdb_genre_id = 27, genre_name = "Horror", genre_category = "Sci-Fi & Genre", sort_order = 10],
        [genre_key = 11, tmdb_genre_id = 878, genre_name = "Science Fiction", genre_category = "Sci-Fi & Genre", sort_order = 11],
        [genre_key = 12, tmdb_genre_id = 53, genre_name = "Thriller", genre_category = "Prestige & Thriller", sort_order = 12],
        [genre_key = 13, tmdb_genre_id = 10749, genre_name = "Romance", genre_category = "Mainstream Commercial", sort_order = 13]
    },
    TableFromRecords = Table.FromRecords(GenreRecords),
    TypedTable = Table.TransformColumnTypes(TableFromRecords, {
        {"genre_key", Int64.Type}, {"tmdb_genre_id", Int64.Type}, {"genre_name", type text}, {"genre_category", type text}, {"sort_order", Int64.Type}
    })
in
    TypedTable
```

---

#### Table 4: `Dim_Territory` (Global Geography Dimension)
```powerquery
let
    TerritoryRecords = {
        [territory_key = 1, territory_code = "US", territory_name = "United States", region_group = "North America", currency_code = "USD", market_maturity = "Mature Hub", streaming_penetration_pct = 0.85],
        [territory_key = 2, territory_code = "GB", territory_name = "United Kingdom", region_group = "EMEA", currency_code = "GBP", market_maturity = "Mature Hub", streaming_penetration_pct = 0.78],
        [territory_key = 3, territory_code = "KR", territory_name = "South Korea", region_group = "APAC", currency_code = "KRW", market_maturity = "High Growth", streaming_penetration_pct = 0.72],
        [territory_key = 4, territory_code = "JP", territory_name = "Japan", region_group = "APAC", currency_code = "JPY", market_maturity = "Mature Hub", streaming_penetration_pct = 0.65],
        [territory_key = 5, territory_code = "GL", territory_name = "Global / Rest of World", region_group = "Worldwide", currency_code = "USD", market_maturity = "Emerging Markets", streaming_penetration_pct = 0.45]
    },
    TableFromRecords = Table.FromRecords(TerritoryRecords),
    TypedTable = Table.TransformColumnTypes(TableFromRecords, {
        {"territory_key", Int64.Type}, {"territory_code", type text}, {"territory_name", type text},
        {"region_group", type text}, {"currency_code", type text}, {"market_maturity", type text}, {"streaming_penetration_pct", type number}
    })
in
    TypedTable
```

---

#### Table 5: `Dim_Talent_Crew` (Creative Talent Dimension)
```powerquery
let
    SourceHist = Csv.Document(File.Contents(File_Path & "netflix_enriched_historical.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHist = Table.PromoteHeaders(SourceHist, [PromoteAllScalars=true]),
    
    DirectorsList = Table.SelectColumns(PromotedHist, {"director"}),
    SplitDirectors = Table.ExpandListColumn(Table.AddColumn(DirectorsList, "name_split", each Text.Split(Text.From([director]), ",")), "name_split"),
    CleanDirectors = Table.TransformColumns(SplitDirectors, {{"name_split", each Text.Proper(Text.Trim(_)), type text}}),
    FilteredDirectors = Table.SelectRows(CleanDirectors, each [name_split] <> "" and [name_split] <> null and [name_split] <> "None"),
    DirectorsTable = Table.Distinct(Table.SelectColumns(FilteredDirectors, {"name_split"})),
    AddDirectorRole = Table.AddColumn(DirectorsTable, "primary_role", each "Director", type text),

    SourceJSON = Json.Document(File.Contents(File_Path & "boxoffice_budget_feed.json")),
    DataJSON = SourceJSON[data],
    TableJSON = Table.FromList(DataJSON, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    ExpandedJSON = Table.ExpandRecordColumn(TableJSON, "Column1", {"production_info"}, {"production_info"}),
    ExpandedProd = Table.ExpandRecordColumn(ExpandedJSON, "production_info", {"producer"}, {"producer"}),
    CleanProducers = Table.TransformColumns(ExpandedProd, {{"producer", each Text.Proper(Text.Trim(Text.From(_))), type text}}),
    FilteredProducers = Table.SelectRows(CleanProducers, each [producer] <> "" and [producer] <> null),
    ProducersTable = Table.RenameColumns(Table.Distinct(FilteredProducers), {{"producer", "name_split"}}),
    AddProducerRole = Table.AddColumn(ProducersTable, "primary_role", each "Producer", type text),

    CombinedTalent = Table.Combine({AddDirectorRole, AddProducerRole}),
    DeduplicatedTalent = Table.Distinct(CombinedTalent, {"name_split"}),
    AddCrewKey = Table.AddIndexColumn(DeduplicatedTalent, "crew_key", 1, 1, Int64.Type),
    RenameTalent = Table.RenameColumns(AddCrewKey, {{"name_split", "person_name"}}),
    
    AddTalentTier = Table.AddColumn(RenameTalent, "star_power_tier", each
        if [person_name] = "Christopher Nolan" or [person_name] = "James Cameron" or [person_name] = "Jerry Bruckheimer" then "Tier 1 - Global A-List"
        else if [person_name] = "Kathleen Kennedy" or [person_name] = "David Fincher" or [person_name] = "Martin Scorsese" then "Tier 1 - Global A-List"
        else "Tier 2 - Established Talent",
        type text
    )
in
    AddTalentTier
```

---

### Many-to-Many Bridge Queries

#### Table 6: `Bridge_Title_Genre` (Title <-> Genre Bridge)
```powerquery
let
    SourceJSON = Json.Document(File.Contents(File_Path & "boxoffice_budget_feed.json")),
    DataJSON = SourceJSON[data],
    TableJSON = Table.FromList(DataJSON, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    ExpandedJSON = Table.ExpandRecordColumn(TableJSON, "Column1", {"stream_id", "categorization"}, {"netflix_id", "categorization"}),
    ExpandedCat = Table.ExpandRecordColumn(ExpandedJSON, "categorization", {"genres"}, {"genres_raw"}),

    AddListJSON = Table.AddColumn(ExpandedCat, "Genre_List", each
        if Value.Is([genres_raw], type list) then [genres_raw]
        else Text.Split(Text.From([genres_raw]), "|"),
        type list
    ),
    ExpandedRowsJSON = Table.ExpandListColumn(AddListJSON, "Genre_List"),
    CleanGenreNameJSON = Table.TransformColumns(ExpandedRowsJSON, {{"Genre_List", each Text.Trim(Text.From(_)), type text}}),
    SelectJSONBridge = Table.SelectColumns(CleanGenreNameJSON, {"netflix_id", "Genre_List"}),

    SourceHist = Csv.Document(File.Contents(File_Path & "netflix_enriched_historical.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHist = Table.PromoteHeaders(SourceHist, [PromoteAllScalars=true]),
    CleanHistGenres = Table.AddColumn(PromotedHist, "Genre_List", each
        let
            raw = Text.Replace(Text.Replace(Text.Replace(Text.From([genres]), "[", ""), "]", ""), "'", ""),
            items = Text.Split(raw, ";")
        in
            List.Transform(items, each Text.Proper(Text.Trim(_))),
        type list
    ),
    ExpandedHistRows = Table.ExpandListColumn(CleanHistGenres, "Genre_List"),
    RenameHistBridge = Table.RenameColumns(ExpandedHistRows, {{"id", "netflix_id"}}),
    SelectHistBridge = Table.SelectColumns(RenameHistBridge, {"netflix_id", "Genre_List"}),

    CombinedBridges = Table.Combine({SelectJSONBridge, SelectHistBridge}),
    FilteredEmpty = Table.SelectRows(CombinedBridges, each [Genre_List] <> "" and [Genre_List] <> null),

    StandardizedGenreName = Table.AddColumn(FilteredEmpty, "genre_name_clean", each
        let g = if [Genre_List] = null then "" else Text.Proper(Text.From([Genre_List])) in
        if Text.Contains(g, "Action") then "Action"
        else if Text.Contains(g, "Adventure") then "Adventure"
        else if Text.Contains(g, "Animation") or Text.Contains(g, "Anime") then "Animation"
        else if Text.Contains(g, "Comedy") or Text.Contains(g, "Comedies") then "Comedy"
        else if Text.Contains(g, "Crime") then "Crime"
        else if Text.Contains(g, "Docu") then "Documentary"
        else if Text.Contains(g, "Drama") then "Drama"
        else if Text.Contains(g, "Family") or Text.Contains(g, "Children") then "Family"
        else if Text.Contains(g, "Fantasy") then "Fantasy"
        else if Text.Contains(g, "Horror") then "Horror"
        else if Text.Contains(g, "Sci") then "Science Fiction"
        else if Text.Contains(g, "Thrill") then "Thriller"
        else if Text.Contains(g, "Romance") or Text.Contains(g, "Romantic") then "Romance"
        else "Drama",
        type text
    ),

    MergedTitles = Table.NestedJoin(StandardizedGenreName, {"netflix_id"}, Dim_Titles, {"netflix_id"}, "Dim_Titles", JoinKind.Inner),
    ExpandedTitleKey = Table.ExpandTableColumn(MergedTitles, "Dim_Titles", {"title_key"}, {"title_key"}),

    MergedGenres = Table.NestedJoin(ExpandedTitleKey, {"genre_name_clean"}, Dim_Genres, {"genre_name"}, "Dim_Genres", JoinKind.Inner),
    ExpandedGenreKey = Table.ExpandTableColumn(MergedGenres, "Dim_Genres", {"genre_key"}, {"genre_key"}),

    SelectFinal = Table.SelectColumns(ExpandedGenreKey, {"title_key", "genre_key"}),
    AddWeight = Table.AddColumn(SelectFinal, "genre_weight", each 1.0, type number),
    Deduplicated = Table.Distinct(AddWeight)
in
    Deduplicated
```

---

#### Table 7: `Bridge_Title_Talent` (Title <-> Talent Bridge)
```powerquery
let
    SourceHist = Csv.Document(File.Contents(File_Path & "netflix_enriched_historical.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHist = Table.PromoteHeaders(SourceHist, [PromoteAllScalars=true]),
    SelectCols = Table.SelectColumns(PromotedHist, {"id", "director"}),
    RenameId = Table.RenameColumns(SelectCols, {{"id", "netflix_id"}}),
    ExpandDirectors = Table.ExpandListColumn(Table.AddColumn(RenameId, "person_name", each Text.Split(Text.From([director]), ",")), "person_name"),
    CleanName = Table.TransformColumns(ExpandDirectors, {{"person_name", each Text.Proper(Text.Trim(_)), type text}}),
    Filtered = Table.SelectRows(CleanName, each [person_name] <> "" and [person_name] <> null and [person_name] <> "None"),

    MergedTitles = Table.NestedJoin(Filtered, {"netflix_id"}, Dim_Titles, {"netflix_id"}, "Dim_Titles", JoinKind.Inner),
    ExpandedTitle = Table.ExpandTableColumn(MergedTitles, "Dim_Titles", {"title_key"}, {"title_key"}),

    MergedTalent = Table.NestedJoin(ExpandedTitle, {"person_name"}, Dim_Talent_Crew, {"person_name"}, "Dim_Talent", JoinKind.Inner),
    ExpandedTalent = Table.ExpandTableColumn(MergedTalent, "Dim_Talent", {"crew_key"}, {"crew_key"}),

    SelectFinal = Table.SelectColumns(ExpandedTalent, {"title_key", "crew_key"}),
    AddBillingOrder = Table.AddColumn(SelectFinal, "billing_order", each 1, Int64.Type),
    Deduplicated = Table.Distinct(AddBillingOrder)
in
    Deduplicated
```

---

### Multi-Grain Fact Queries

#### Table 8: `Fact_Streaming_Performance` (Granular Telemetry Fact)
```powerquery
let
    Source = Parquet.Document(File.Contents(File_Path & "streaming_viewership_wide.parquet")),

    Unpivoted = Table.Unpivot(Source, {"Hours_2026_01", "Hours_2026_02", "Hours_2026_03"}, "Month_Col", "global_view_hours_millions"),
    CleanHours = Table.TransformColumns(Unpivoted, {{"global_view_hours_millions", each if _ = null then 0.0 else if _ < 0 then 0.0 else _, type number}}),

    AddDateKey = Table.AddColumn(CleanHours, "date_key", each
        let
            m_str = Text.AfterDelimiter([Month_Col], "Hours_"),
            y = Number.FromText(Text.Start(m_str, 4)),
            m = Number.FromText(Text.End(m_str, 2))
        in
            y * 10000 + m * 100 + 1,
        Int64.Type
    ),

    AddTerritoryKey = Table.AddColumn(AddDateKey, "territory_key", each
        let c = Text.Upper(Text.Trim(Text.From([territory_region]))) in
        if c = "USA" or c = "US" or c = "UNITED STATES" then 1
        else if c = "UK" or c = "GBR" or c = "GREAT BRITAIN" then 2
        else if c = "KOR" or c = "SOUTH KOREA" then 3
        else if c = "JPN" or c = "JAPAN" then 4
        else 5,
        Int64.Type
    ),

    MergedTitles = Table.NestedJoin(AddTerritoryKey, {"catalog_ref_id"}, Dim_Titles, {"netflix_id"}, "Dim_Titles", JoinKind.Inner),
    ExpandedTitleKey = Table.ExpandTableColumn(MergedTitles, "Dim_Titles", {"title_key"}, {"title_key"}),

    SelectFact = Table.SelectColumns(ExpandedTitleKey, {
        "title_key", "date_key", "territory_key", "device_category",
        "global_view_hours_millions", "avg_completion_pct", "subscribers_reached_thousands"
    }),
#### Table 9: `Fact_Catalog_Ratings` (Periodic Rating Snapshot Fact)
```powerquery
let
    // Part A: Live Snapshot Ratings (from Raw_IMDb_Ratings CSV)
    SourceLive = Csv.Document(File.Contents(File_Path & "imdb_external_ratings.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedLive = Table.PromoteHeaders(SourceLive, [PromoteAllScalars=true]),

    ParseLiveVotes = Table.AddColumn(PromotedLive, "vote_count_clean", each
        let
            v = if [vote_count_raw] = null then "" else Text.Upper(Text.Trim(Text.From([vote_count_raw]))),
            num = if v = "" or v = "NULL" or v = "N/A" then
                      1000
                  else if Text.EndsWith(v, "M") then
                      (try Number.FromText(Text.Remove(v, "M")) otherwise 1.0) * 1000000
                  else if Text.EndsWith(v, "K") then
                      (try Number.FromText(Text.Remove(v, "K")) otherwise 1.0) * 1000
                  else
                      try Number.FromText(Text.Replace(v, ",", "")) otherwise 1000
        in
            Int64.From(if num = null or num < 0 then 1000 else num),
        Int64.Type
    ),

    ParseLiveScore = Table.AddColumn(ParseLiveVotes, "vote_average_clean", each
        let
            raw = if [user_score] = null then "" else Text.Upper(Text.Trim(Text.From([user_score]))),
            score = if raw = "" or raw = "NULL" or raw = "N/A" then
                        7.0
                    else if Text.Contains(raw, "/10") then
                        try Number.FromText(Text.BeforeDelimiter(raw, "/10")) otherwise 7.0
                    else if Text.EndsWith(raw, "%") then
                        (try Number.FromText(Text.Remove(raw, "%")) otherwise 70.0) / 10.0
                    else
                        try Number.FromText(raw) otherwise 7.0,
            valid_score = if score = null then 7.0 else score
        in
            if valid_score > 10.0 then 10.0 else if valid_score < 0.0 then 0.0 else Number.Round(valid_score, 1),
        type number
    ),

    SortedLive = Table.Sort(ParseLiveScore, {{"title_id", Order.Ascending}, {"snapshot_timestamp", Order.Descending}}),
    DeduplicatedLive = Table.Distinct(SortedLive, {"title_id"}),

    AddLiveDateKey = Table.AddColumn(DeduplicatedLive, "date_key", each
        let d = try Date.From(DateTimeZone.From([snapshot_timestamp])) otherwise #date(2026, 2, 1) in
        Date.Year(d) * 10000 + Date.Month(d) * 100 + Date.Day(d),
        Int64.Type
    ),

    RenameLiveFact = Table.RenameColumns(AddLiveDateKey, {
        {"title_id", "netflix_id"},
        {"vote_average_clean", "vote_average"},
        {"vote_count_clean", "vote_count"},
        {"critic_metascore", "critic_score"}
    }),

    SelectLiveFact = Table.SelectColumns(RenameLiveFact, {
        "netflix_id", "date_key", "vote_average", "vote_count", "critic_score"
    }),

    // Part B: Historical Kaggle Ratings (7,786 records)
    SourceHist = Csv.Document(File.Contents(File_Path & "netflix_enriched_historical.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHist = Table.PromoteHeaders(SourceHist, [PromoteAllScalars=true]),

    AddHistDateKey = Table.AddColumn(PromotedHist, "date_key", each
        let y = try Number.FromText(Text.From([release_year])) otherwise 2020 in
        (if y = null or y < 1900 or y > 2100 then 2020 else y) * 10000 + 101,
        Int64.Type
    ),

    CleanHistRatings = Table.AddColumn(AddHistDateKey, "vote_average", each
        let
            s = try Number.FromText(Text.From([imdb_score])) otherwise 7.0,
            valid_s = if s = null then 7.0 else s
        in
            if valid_s > 10.0 then 10.0 else if valid_s <= 0.0 then 7.0 else Number.Round(valid_s, 1),
        type number
    ),
    CleanHistVotes = Table.AddColumn(CleanHistRatings, "vote_count", each
        let
            v = try Int64.From(Number.FromText(Text.From([imdb_votes]))) otherwise 1000
        in
            if v = null or v <= 0 then 1000 else v,
        Int64.Type
    ),
    CleanHistMetascore = Table.AddColumn(CleanHistVotes, "critic_score", each
        let
            m = try Number.FromText(Text.From([tmdb_score])) * 10 otherwise 70.0,
            valid_m = if m = null then 70.0 else m
        in
            if valid_m > 100.0 then 100.0 else if valid_m <= 0.0 then 70.0 else Number.Round(valid_m, 1),
        type number
    ),
    RenameHistFact = Table.RenameColumns(CleanHistMetascore, {{"id", "netflix_id"}}),
    SelectHistFact = Table.SelectColumns(RenameHistFact, {
        "netflix_id", "date_key", "vote_average", "vote_count", "critic_score"
    }),

    // Part C: Combine & Map Surrogate Title Key
    CombinedFacts = Table.Combine({SelectLiveFact, SelectHistFact}),
    MergedTitles = Table.NestedJoin(CombinedFacts, {"netflix_id"}, Dim_Titles, {"netflix_id"}, "Dim_Titles", JoinKind.Inner),
    ExpandedTitleKey = Table.ExpandTableColumn(MergedTitles, "Dim_Titles", {"title_key"}, {"title_key"}),

    FinalFact = Table.SelectColumns(ExpandedTitleKey, {
        "title_key", "date_key", "vote_average", "vote_count", "critic_score"
    }),
    AddRatingFactKey = Table.AddIndexColumn(FinalFact, "fact_rating_key", 1, 1, Int64.Type)
in
    AddRatingFactKey
```

---

#### Table 10: `Fact_Financial_ROI` (Production Budget & Unit Economics Fact)
```powerquery
let
    SourceJSON = Json.Document(File.Contents(File_Path & "boxoffice_budget_feed.json")),
    DataJSON = SourceJSON[data],
    TableJSON = Table.FromList(DataJSON, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    ExpandedData = Table.ExpandRecordColumn(TableJSON, "Column1", {"stream_id", "production_info", "financial_roi_tier"}, {"netflix_id", "production_info", "financial_roi_tier"}),
    ExpandedProd = Table.ExpandRecordColumn(ExpandedData, "production_info", {"production_budget_raw", "worldwide_gross_raw"}, {"budget_raw", "gross_raw"}),

    ParseBudgetUSD = Table.AddColumn(ExpandedProd, "production_budget_usd", each
        let
            txt = if [budget_raw] = null then "" else Text.Upper(Text.Trim(Text.From([budget_raw]))),
            num = if txt = "" or txt = "NULL" or txt = "N/A" or Text.Contains(txt, "DIRECT TO SVOD") or Text.Contains(txt, "TBD") then
                      25000000.0
                  else if Text.Contains(txt, "M") then
                      (try Number.FromText(Text.Select(Text.BeforeDelimiter(txt, "M"), {"0".."9", "."})) otherwise 50.0) * 1000000
                  else if Text.Contains(txt, "MILLION") then
                      (try Number.FromText(Text.Select(Text.BeforeDelimiter(txt, "MILLION"), {"0".."9", "."})) otherwise 45.0) * 1000000 * 1.08
                  else
                      try Number.FromText(Text.Select(txt, {"0".."9"})) otherwise 25000000.0
        in
            if num = null or num <= 0 then 25000000.0 else num,
        type number
    ),

    ParseGrossUSD = Table.AddColumn(ParseBudgetUSD, "worldwide_gross_usd", each
        let
            txt = if [gross_raw] = null then "" else Text.Upper(Text.Trim(Text.From([gross_raw]))),
            num = if txt = "" or txt = "NULL" or txt = "N/A" or Text.Contains(txt, "DIRECT TO SVOD") or Text.Contains(txt, "TBD") then
                      0.0
                  else if Text.Contains(txt, "M") then
                      (try Number.FromText(Text.Select(Text.BeforeDelimiter(txt, "M"), {"0".."9", "."})) otherwise 0.0) * 1000000
                  else
                      try Number.FromText(Text.Select(txt, {"0".."9"})) otherwise 0.0
        in
            if num = null or num < 0 then 0.0 else num,
        type number
    ),

    MergedTitles = Table.NestedJoin(ParseGrossUSD, {"netflix_id"}, Dim_Titles, {"netflix_id"}, "Dim_Titles", JoinKind.Inner),
    ExpandedTitleKey = Table.ExpandTableColumn(MergedTitles, "Dim_Titles", {"title_key"}, {"title_key"}),

    AddDateKey = Table.AddColumn(ExpandedTitleKey, "date_key", each 20260101, Int64.Type),

    SelectFact = Table.SelectColumns(AddDateKey, {
        "title_key", "date_key", "production_budget_usd", "worldwide_gross_usd", "financial_roi_tier"
    }),
    AddFinancialKey = Table.AddIndexColumn(SelectFact, "financial_key", 1, 1, Int64.Type)
in
    AddFinancialKey
```

---

---

## 3. Netflix Web-App UI Components in Power BI (4K UHD Optimized HTML, CSS & SVG)

To give Power BI the exact look and feel of a **modern streaming platform website & command center** running natively on **4K UHD (3840 x 2160)** displays, use these DAX measures in conjunction with the **HTML Content visual (AppSource)** or the native **New Card Visual** (with Data Category set to `Image URL`).

---

### HTML/CSS Web Component 0.1: Netflix Home Page Hero Command Banner (4K UHD)
*Add this measure to an HTML Content visual on **Page 0 (Home Page)** with 4K dimensions ($X: 60, Y: 150, W: 3720, H: 340$).*

```dax
HTML_Home_Hero_Banner = 
VAR _Hour = HOUR(NOW())
VAR _Greeting = 
    SWITCH(
        TRUE(),
        _Hour < 12, "Good Morning",
        _Hour < 18, "Good Afternoon",
        "Good Evening"
    )
VAR _TotalTitles = FORMAT(COUNTROWS(Dim_Titles), "#,##0")
VAR _TotalHours = [Total_View_Hours_Formatted]
VAR _AvgQuality = FORMAT([Bayesian_Weighted_Score], "0.0") & " / 10.0"
RETURN
"<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; }
  @keyframes pulseGlow {
    0% { box-shadow: 0 0 0 0 rgba(229, 9, 20, 0.8); }
    70% { box-shadow: 0 0 0 20px rgba(229, 9, 20, 0); }
    100% { box-shadow: 0 0 0 0 rgba(229, 9, 20, 0); }
  }
  .hero-home-wrap {
    width: 100%; height: 320px; border-radius: 20px;
    background: linear-gradient(135deg, rgba(20, 20, 20, 0.96) 0%, rgba(10, 10, 10, 0.98) 60%, rgba(229, 9, 20, 0.22) 100%);
    border: 1.5px solid rgba(255, 255, 255, 0.1); padding: 40px 60px;
    display: flex; align-items: center; justify-content: space-between;
    box-shadow: 0 20px 48px rgba(0, 0, 0, 0.85);
  }
  .left-hero { display: flex; flex-direction: column; gap: 14px; max-width: 2000px; }
  .greeting-tag { display: flex; align-items: center; gap: 14px; font-size: 18px; font-weight: 800; color: #E50914; letter-spacing: 2px; text-transform: uppercase; }
  .pulse-dot { width: 12px; height: 12px; background: #E50914; border-radius: 50%; animation: pulseGlow 1.8s infinite; }
  .hero-title {
    font-size: 48px; font-weight: 900; letter-spacing: -1px; line-height: 1.15;
    background: linear-gradient(90deg, #FFFFFF 0%, #EAEAEA 50%, #E50914 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  .hero-subtitle { color: #A3A3A3; font-size: 20px; font-weight: 400; line-height: 1.5; }
  .hero-metrics-pill {
    display: flex; align-items: center; gap: 32px; background: rgba(30, 30, 30, 0.7);
    backdrop-filter: blur(16px); border: 1.5px solid rgba(255, 255, 255, 0.08);
    padding: 22px 42px; border-radius: 16px;
  }
  .pill-item { display: flex; flex-direction: column; }
  .pill-label { color: #888888; font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; }
  .pill-val { color: #FFFFFF; font-size: 32px; font-weight: 900; margin-top: 4px; }
  .pill-val.gold { color: #F5C518; }
  .pill-val.teal { color: #00D2D2; }
  .pill-divider { width: 1.5px; height: 48px; background: rgba(255, 255, 255, 0.12); }
</style>
</head>
<body>
  <div class='hero-home-wrap'>
    <div class='left-hero'>
      <div class='greeting-tag'>
        <div class='pulse-dot'></div>
        <span>" & _Greeting & " • StreamPulse 2026 Enterprise Platform Portal</span>
      </div>
      <div class='hero-title'>Streaming Intelligence &amp; Analytics Command Center</div>
      <div class='hero-subtitle'>Unified Kimball Galaxy Warehouse • 3-Tier Medallion Architecture • Live DirectQuery Telemetry</div>
    </div>
    <div class='hero-metrics-pill'>
      <div class='pill-item'>
        <span class='pill-label'>Total Catalog</span>
        <span class='pill-val'>" & _TotalTitles & "</span>
      </div>
      <div class='pill-divider'></div>
      <div class='pill-item'>
        <span class='pill-label'>Global Streamed</span>
        <span class='pill-val teal'>" & _TotalHours & "</span>
      </div>
      <div class='pill-divider'></div>
      <div class='pill-item'>
        <span class='pill-label'>Bayesian Quality</span>
        <span class='pill-val gold'>★ " & _AvgQuality & "</span>
      </div>
    </div>
  </div>
</body>
</html>"
```

---

### HTML/CSS Web Component 0.2: Interactive 5-Module Navigation Portal Hub (4K UHD)
*Add this measure to an HTML Content visual on **Page 0 (Home Page)** with 4K dimensions ($X: 60, Y: 610, W: 3720, H: 460$).*

```dax
HTML_Home_Navigation_Hub = 
"<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; }
  .nav-grid {
    display: grid; grid-template-columns: repeat(5, 1fr); gap: 24px; width: 100%; height: 430px;
  }
  .module-card {
    background: #141414; border: 1.5px solid #242424; border-radius: 18px; padding: 32px 28px;
    display: flex; flex-direction: column; justify-content: space-between;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); cursor: pointer; position: relative; overflow: hidden;
  }
  .module-card::before {
    content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 4px;
    background: transparent; transition: background 0.3s ease;
  }
  .module-card:hover {
    transform: translateY(-8px); background: #1A1A1A;
    border-color: #E50914; box-shadow: 0 16px 36px rgba(229, 9, 20, 0.3);
  }
  .module-card:hover::before { background: #E50914; }
  .mod-header { display: flex; align-items: center; justify-content: space-between; }
  .mod-badge {
    width: 58px; height: 58px; border-radius: 14px; background: rgba(229, 9, 20, 0.12);
    border: 1.5px solid rgba(229, 9, 20, 0.35); display: flex; align-items: center; justify-content: center;
    font-size: 28px; color: #E50914;
  }
  .mod-num { color: #666666; font-size: 16px; font-weight: 800; }
  .mod-title { color: #FFFFFF; font-size: 24px; font-weight: 800; margin-top: 20px; line-height: 1.25; }
  .mod-desc { color: #999999; font-size: 16px; font-weight: 400; line-height: 1.5; margin-top: 10px; }
  .mod-cta {
    display: flex; align-items: center; gap: 8px; color: #E50914; font-size: 16px;
    font-weight: 800; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 22px;
  }
  .mod-cta-arrow { transition: transform 0.2s ease; }
  .module-card:hover .mod-cta-arrow { transform: translateX(6px); }
</style>
</head>
<body>
  <div class='nav-grid'>
    <!-- Card 1 -->
    <div class='module-card'>
      <div>
        <div class='mod-header'>
          <div class='mod-badge'>🎬</div>
          <span class='mod-num'>PAGE 01</span>
        </div>
        <div class='mod-title'>Executive Pulse</div>
        <div class='mod-desc'>Global Top 10 rankings, live scraper drops, featured hero player, and high-level KPIs.</div>
      </div>
      <div class='mod-cta'>Launch View <span class='mod-cta-arrow'>→</span></div>
    </div>

    <!-- Card 2 -->
    <div class='module-card'>
      <div>
        <div class='mod-header'>
          <div class='mod-badge'>🌌</div>
          <span class='mod-num'>PAGE 02</span>
        </div>
        <div class='mod-title'>Catalog Galaxy</div>
        <div class='mod-desc'>7,786 conformed titles, multi-genre bridge matrix, era segmentation &amp; maturity ratings.</div>
      </div>
      <div class='mod-cta'>Launch View <span class='mod-cta-arrow'>→</span></div>
    </div>

    <!-- Card 3 -->
    <div class='module-card'>
      <div>
        <div class='mod-header'>
          <div class='mod-badge'>📊</div>
          <span class='mod-num'>PAGE 03</span>
        </div>
        <div class='mod-title'>Viewership Telemetry</div>
        <div class='mod-desc'>Monthly stream hours, completion rate %, subscriber reach &amp; regional device mix.</div>
      </div>
      <div class='mod-cta'>Launch View <span class='mod-cta-arrow'>→</span></div>
    </div>

    <!-- Card 4 -->
    <div class='module-card'>
      <div>
        <div class='mod-header'>
          <div class='mod-badge'>💰</div>
          <span class='mod-num'>PAGE 04</span>
        </div>
        <div class='mod-title'>Financial ROI Hub</div>
        <div class='mod-desc'>Production budget vs. worldwide gross, 2.5x break-even indicator &amp; Cost Per View Hour.</div>
      </div>
      <div class='mod-cta'>Launch View <span class='mod-cta-arrow'>→</span></div>
    </div>

    <!-- Card 5 -->
    <div class='module-card'>
      <div>
        <div class='mod-header'>
          <div class='mod-badge'>🎭</div>
          <span class='mod-num'>PAGE 05</span>
        </div>
        <div class='mod-title'>Creative Talent Hub</div>
        <div class='mod-desc'>Director &amp; producer credits, billing order hierarchy, star power tiers &amp; filmographies.</div>
      </div>
      <div class='mod-cta'>Launch View <span class='mod-cta-arrow'>→</span></div>
    </div>
  </div>
</body>
</html>"
```

---

### HTML/CSS Web Component 0.3: Live Real-Time Marquee Ticker (4K UHD)
*Add this measure to an HTML Content visual on **Page 0 (Home Page)** with 4K dimensions ($X: 60, Y: 510, W: 3720, H: 80$).*

```dax
HTML_Home_Marquee_Ticker = 
"<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', -apple-system, sans-serif; }
  @keyframes marquee {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
  }
  .ticker-wrap {
    width: 100%; height: 70px; background: rgba(18, 18, 18, 0.95);
    border: 1.5px solid rgba(255, 255, 255, 0.08); border-radius: 12px;
    display: flex; align-items: center; overflow: hidden; padding: 0 20px;
  }
  .ticker-badge {
    background: #E50914; color: #FFFFFF; font-size: 16px; font-weight: 900;
    padding: 6px 16px; border-radius: 6px; letter-spacing: 1.5px; text-transform: uppercase;
    white-space: nowrap; margin-right: 25px; z-index: 2; box-shadow: 0 0 16px rgba(229, 9, 20, 0.6);
  }
  .ticker-content {
    display: inline-block; white-space: nowrap;
    animation: marquee 40s linear infinite; color: #CCCCCC; font-size: 20px; font-weight: 500;
  }
  .ticker-item { margin-right: 60px; }
  .ticker-highlight { color: #FFFFFF; font-weight: 700; }
  .ticker-green { color: #46D369; font-weight: 700; }
  .ticker-gold { color: #F5C518; font-weight: 700; }
  .ticker-teal { color: #00D2D2; font-weight: 700; }
</style>
</head>
<body>
  <div class='ticker-wrap'>
    <div class='ticker-badge'>LIVE DROPS</div>
    <div class='ticker-content'>
      <span class='ticker-item'>🔥 <span class='ticker-highlight'>Avatar: Fire and Ash</span> leads global charts with <span class='ticker-teal'>2.1B Hours</span></span>
      <span class='ticker-item'>⭐ <span class='ticker-highlight'>Stranger Things S5</span> achieves highest Bayesian Quality Score at <span class='ticker-gold'>8.8 / 10.0</span></span>
      <span class='ticker-item'>🔄 <span class='ticker-highlight'>Airbyte ELT Pipeline 0.50.36</span>: Daily sync completed with <span class='ticker-green'>100% Conformance</span></span>
      <span class='ticker-item'>💰 <span class='ticker-highlight'>Avengers: Doomsday</span> grosses <span class='ticker-green'>$1.2B Worldwide</span> (2.4x Multiplier)</span>
      <span class='ticker-item'>⚡ <span class='ticker-highlight'>DirectQuery Latency</span>: Optimized at <span class='ticker-teal'>&lt;240ms</span> response time</span>
      <span class='ticker-item'>📊 <span class='ticker-highlight'>Catalog Galaxy</span>: 10 Unified Tables conformed under Kimball Architecture</span>
    </div>
  </div>
</body>
</html>"
```

---

### HTML/CSS Web Component 0.4: Platform Architecture & Metadata Drawer (4K UHD)
*Add this measure to an HTML Content visual on **Page 0 (Home Page)** with 4K dimensions ($X: 60, Y: 1090, W: 3720, H: 540$).*

```dax
HTML_Home_Platform_Vitals = 
"<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', -apple-system, sans-serif; }
  .vitals-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; width: 100%; height: 500px;
  }
  .vital-card {
    background: #121212; border: 1.5px solid #222222; border-radius: 16px; padding: 30px;
    display: flex; flex-direction: column; justify-content: space-between;
  }
  .vital-card.primary { border-left: 6px solid #E50914; }
  .vital-card.success { border-left: 6px solid #46D369; }
  .vital-card.teal { border-left: 6px solid #00D2D2; }
  .vital-card.gold { border-left: 6px solid #F5C518; }
  .v-title { color: #888888; font-size: 16px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; }
  .v-metric { color: #FFFFFF; font-size: 34px; font-weight: 900; margin: 10px 0; }
  .v-list { list-style: none; display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
  .v-item { color: #AAAAAA; font-size: 16px; display: flex; align-items: center; justify-content: space-between; }
  .v-tag { background: #222222; padding: 4px 10px; border-radius: 4px; font-weight: 600; color: #EEE; font-size: 14px; }
  .status-pill {
    display: inline-flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 700;
    color: #46D369; background: rgba(70, 211, 105, 0.14); padding: 6px 14px; border-radius: 16px; width: fit-content;
  }
  .status-dot { width: 8px; height: 8px; background: #46D369; border-radius: 50%; }
</style>
</head>
<body>
  <div class='vitals-grid'>
    <!-- Tile 1 -->
    <div class='vital-card primary'>
      <div>
        <div class='v-title'>Lakehouse Ingestion Stack</div>
        <div class='v-metric'>Bronze Layer</div>
      </div>
      <ul class='v-list'>
        <li class='v-item'><span>Live 2026 Scraper</span> <span class='v-tag'>Wikipedia / RSS</span></li>
        <li class='v-item'><span>Historical Archive</span> <span class='v-tag'>7,786 Kaggle CSV</span></li>
        <li class='v-item'><span>Audience Ratings</span> <span class='v-tag'>IMDb / TMDb</span></li>
        <li class='v-item'><span>Streaming Telemetry</span> <span class='v-tag'>Wide Parquet</span></li>
      </ul>
    </div>

    <!-- Tile 2 -->
    <div class='vital-card success'>
      <div>
        <div class='v-title'>ELT &amp; Data Pipeline Engine</div>
        <div class='v-metric'>Airbyte 0.50.36</div>
      </div>
      <div>
        <div class='status-pill'><div class='status-dot'></div> ACTIVE &amp; SYNCED</div>
        <ul class='v-list' style='margin-top: 12px;'>
          <li class='v-item'><span>Sync Frequency</span> <span class='v-tag'>Daily Cron</span></li>
          <li class='v-item'><span>Data Profiling</span> <span class='v-tag'>100% Conformed</span></li>
          <li class='v-item'><span>Entity Match</span> <span class='v-tag'>RapidFuzz Levenshtein</span></li>
        </ul>
      </div>
    </div>

    <!-- Tile 3 -->
    <div class='vital-card teal'>
      <div>
        <div class='v-title'>Kimball Galaxy Architecture</div>
        <div class='v-metric'>10 Data Tables</div>
      </div>
      <ul class='v-list'>
        <li class='v-item'><span>Conformed Dimensions</span> <span class='v-tag'>5 Tables (1:*)</span></li>
        <li class='v-item'><span>Many-to-Many Bridges</span> <span class='v-tag'>2 Tables (Weight 1.0)</span></li>
        <li class='v-item'><span>Multi-Grain Facts</span> <span class='v-tag'>3 Tables</span></li>
        <li class='v-item'><span>DirectQuery Views</span> <span class='v-tag'>3 Views</span></li>
      </ul>
    </div>

    <!-- Tile 4 -->
    <div class='vital-card gold'>
      <div>
        <div class='v-title'>Power BI Semantic Platform</div>
        <div class='v-metric'>45+ DAX Measures</div>
      </div>
      <ul class='v-list'>
        <li class='v-item'><span>Bayesian Shrinkage</span> <span class='v-tag'>m=25K, C=7.0</span></li>
        <li class='v-item'><span>Calculation Groups</span> <span class='v-tag'>Time Intelligence</span></li>
        <li class='v-item'><span>Embedded Components</span> <span class='v-tag'>HTML5 / CSS3 / SVG</span></li>
        <li class='v-item'><span>DirectQuery Latency</span> <span class='v-tag'>&lt; 300 ms SLA</span></li>
      </ul>
    </div>
  </div>
</body>
</html>"
```

---

### Animated SVG Vector Measure 1: Pure SVG Animated Pulsing Radar Beacon (4K UHD)
*Set Data Category to **`Image URL`**. Use in tables, matrix headers, or the New Card Visual for an animated neon live status beacon.*

```dax
SVG_Animated_Pulse_Radar = 
"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 60' width='60' height='60'>
  <style>
    @keyframes pulseRing {
      0% { r: 8px; opacity: 1; stroke-width: 3px; }
      100% { r: 26px; opacity: 0; stroke-width: 0.8px; }
    }
    @keyframes centerGlow {
      0%, 100% { transform: scale(1); fill: %23E50914; }
      50% { transform: scale(1.25); fill: %23FF3333; }
    }
    .ring1 { animation: pulseRing 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite; }
    .ring2 { animation: pulseRing 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite 0.6s; }
    .dot { transform-origin: center; animation: centerGlow 1.5s ease-in-out infinite; }
  </style>
  <circle class='ring1' cx='30' cy='30' r='8' fill='none' stroke='%23E50914' />
  <circle class='ring2' cx='30' cy='30' r='8' fill='none' stroke='%23E50914' />
  <circle class='dot' cx='30' cy='30' r='7' fill='%23E50914' />
</svg>"
```

---

### Animated SVG Vector Measure 2: Real-Time Animated Quality Gauge Ring (4K UHD)
*Set Data Category to **`Image URL`**. Renders an animated SVG radial completion gauge.*

```dax
SVG_Animated_Quality_Ring = 
VAR _Score = [Avg_Completion_Rate_Pct]
VAR _Pct = IF(ISBLANK(_Score), 75, MIN(MAX(_Score, 0), 100))
VAR _DashOffset = FORMAT(283 - (283 * (_Pct / 100.0)), "0")
RETURN
"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100' width='120' height='120'>
  <style>
    .track { fill: none; stroke: %23262626; stroke-width: 9; }
    .fill-bar {
      fill: none; stroke: %2300D2D2; stroke-width: 9;
      stroke-dasharray: 283; stroke-dashoffset: " & _DashOffset & ";
      stroke-linecap: round; transform: rotate(-90deg); transform-origin: 50% 50%;
      transition: stroke-dashoffset 0.8s ease;
    }
    .score-txt { font-family: Segoe UI, sans-serif; font-size: 22px; font-weight: 900; fill: %23FFFFFF; text-anchor: middle; dominant-baseline: middle; }
    .sub-txt { font-family: Segoe UI, sans-serif; font-size: 9px; font-weight: 700; fill: %23888888; text-anchor: middle; }
  </style>
  <circle class='track' cx='50' cy='50' r='45' />
  <circle class='fill-bar' cx='50' cy='50' r='45' />
  <text class='score-txt' x='50' y='46'>" & FORMAT(_Pct, "0") & "%</text>
  <text class='sub-txt' x='50' y='64'>QUALITY</text>
</svg>"
```

---

### HTML/CSS Web Component 1: Dynamic Netflix Top Navigation Header (4K UHD)
*This measure dynamically highlights the active tab based on the selected report page or navigation context ($X: 0, Y: 0, W: 3840, H: 120$).*

```dax
HTML_Netflix_Navbar_Dynamic = 
VAR _CurrentPage = SELECTEDVALUE(Dim_Navigation[page_name], "Portal Home")
VAR _P0_Class = IF(_CurrentPage = "Portal Home" || ISBLANK(_CurrentPage), "nav-item active", "nav-item")
VAR _P1_Class = IF(_CurrentPage = "Executive Pulse", "nav-item active", "nav-item")
VAR _P2_Class = IF(_CurrentPage = "Catalog Galaxy", "nav-item active", "nav-item")
VAR _P3_Class = IF(_CurrentPage = "Viewership Telemetry", "nav-item active", "nav-item")
VAR _P4_Class = IF(_CurrentPage = "Financial ROI", "nav-item active", "nav-item")
VAR _P5_Class = IF(_CurrentPage = "Talent Creative Hub", "nav-item active", "nav-item")
RETURN
"<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', -apple-system, sans-serif; }
  .navbar {
    display: flex; align-items: center; justify-content: space-between;
    width: 100%; height: 110px; background: linear-gradient(180deg, rgba(0,0,0,0.96) 0%, rgba(18,18,18,0.85) 100%);
    backdrop-filter: blur(16px); border-bottom: 1.5px solid rgba(255,255,255,0.08); padding: 0 60px;
  }
  .left-group { display: flex; align-items: center; gap: 48px; }
  .brand-logo { color: #E50914; font-size: 38px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; cursor: pointer; }
  .nav-links { display: flex; gap: 36px; list-style: none; }
  .nav-item { color: #CCCCCC; font-size: 20px; font-weight: 600; transition: all 0.2s ease; cursor: pointer; padding-bottom: 6px; }
  .nav-item.active { color: #FFFFFF; font-weight: 800; border-bottom: 3px solid #E50914; }
  .nav-item:hover { color: #E50914; }
  .right-group { display: flex; align-items: center; gap: 28px; }
  .live-badge {
    display: flex; align-items: center; gap: 10px; background: rgba(229, 9, 20, 0.15);
    border: 1.5px solid #E50914; color: #E50914; padding: 6px 16px; border-radius: 24px; font-size: 16px; font-weight: 800;
  }
  .pulse-dot { width: 10px; height: 10px; background: #E50914; border-radius: 50%; box-shadow: 0 0 10px #E50914; }
  .user-avatar { width: 48px; height: 48px; border-radius: 6px; background: #2A2A2A; border: 1.5px solid #444; display: flex; align-items: center; justify-content: center; color: #FFF; font-size: 16px; font-weight: bold; }
</style>
</head>
<body>
  <div class='navbar'>
    <div class='left-group'>
      <div class='brand-logo'>STREAMPULSE</div>
      <ul class='nav-links'>
        <li class='" & _P0_Class & "'>Portal Home</li>
        <li class='" & _P1_Class & "'>Executive Pulse</li>
        <li class='" & _P2_Class & "'>Catalog Galaxy</li>
        <li class='" & _P3_Class & "'>Viewership Telemetry</li>
        <li class='" & _P4_Class & "'>Financial ROI</li>
        <li class='" & _P5_Class & "'>Talent Creative Hub</li>
      </ul>
    </div>
    <div class='right-group'>
      <div class='live-badge'><div class='pulse-dot'></div> DIRECTQUERY LIVE</div>
      <div class='user-avatar'>EX</div>
    </div>
  </div>
</body>
</html>"
```

#### Page-Specific Drop-In Navbar Measures:
If you prefer dedicated measures per page without a slicer table:
- **`[HTML_Navbar_Page0_Home]`**: Sets `Portal Home` as `active`.
- **`[HTML_Navbar_Page1_Executive]`**: Sets `Executive Pulse` as `active`.
- **`[HTML_Navbar_Page2_Catalog]`**: Sets `Catalog Galaxy` as `active`.
- **`[HTML_Navbar_Page3_Telemetry]`**: Sets `Viewership Telemetry` as `active`.
- **`[HTML_Navbar_Page4_Financial]`**: Sets `Financial ROI` as `active`.
- **`[HTML_Navbar_Page5_Talent]`**: Sets `Talent Creative Hub` as `active`.

---

### 🧭 Best Practice: Implementing Native Power BI Page Navigation

Because sandboxed HTML visuals cannot execute direct page routing scripts, Power BI provides the **Native Page Navigator Visual** (`Insert > Buttons > Navigator > Page navigator`).

#### Step-by-Step Styling for Native Netflix Page Navigator (4K UHD):
1. Go to top ribbon $\to$ **Insert** $\to$ **Buttons** $\to$ **Navigator** $\to$ **Page navigator**.
2. Position it inside the top header:
   - **Horizontal ($X$)**: `360 px` (next to the `STREAMPULSE` logo)
   - **Vertical ($Y$)**: `20 px`
   - **Width ($W$)**: `2400 px`
   - **Height ($H$)**: `75 px`
3. In **Format visual** $\to$ **Visual** $\to$ **Grid / Layout**:
   - **Orientation**: `Horizontal`
   - **Space between buttons**: `16 px`
4. In **Shape**:
   - **Shape**: `Rounded rectangle` $\to$ **Corner radius**: `8 px`
5. In **Style** (Configure the 3 Button States):
   - **Default State**:
     - **Text**: Font `Segoe UI Semibold` $\to$ Size: `18 px` $\to$ Color: `#AAAAAA`
     - **Fill**: `Off` (Transparent)
     - **Border**: `Off`
   - **On Hover State**:
     - **Text**: Color: `#FFFFFF`
     - **Fill**: Color: `#1C1C1C` $\to$ Transparency: `20%`
     - **Border**: Color: `#E50914` $\to$ Width: `1.5 px`
   - **Selected State (Current Active Page)**:
     - **Text**: Font `Segoe UI Bold` $\to$ Size: `18 px` $\to$ Color: `#FFFFFF`
     - **Fill**: Color: `rgba(229, 9, 20, 0.15)`
     - **Border**: Color: `#E50914` $\to$ Width: `2 px`
     - **Accent Bar**: Bottom $\to$ Color: `#E50914` $\to$ Width: `3 px`
6. Under **General > Effects**:
   - Background: `Off`
   - Border: `Off`

#### Interactive Routing for Page 0 Navigation Hub (5 Module Cards):
On **Page 0 (Home Page)**, place a transparent **Blank Button** over each of the 5 cards in the Navigation Hub:
1. **Insert** $\to$ **Buttons** $\to$ **Blank**.
2. Place it over Card 1: $(X: 60, Y: 610, W: 720, H: 460)$.
3. In **Format button** $\to$ turn **Fill**, **Border**, and **Text** `Off`.
4. In **Action**: Toggle **`On`** $\to$ **Type**: `Page navigation` $\to$ **Destination**: `Executive Pulse` (or respective page).
5. Repeat for the other 4 cards!

---

### HTML/CSS Web Component 2: Netflix Featured Hero Player & Metadata Card (4K UHD)
*Generates the signature Netflix featured hero banner with trailer mockup, rating match percentage, and audio/video badges ($X: 60, Y: 150, W: 2400, H: 520$).*

```dax
HTML_Netflix_Hero_Card = 
VAR _Title = SELECTEDVALUE(Dim_Titles[title], "Avatar: Fire and Ash")
VAR _Era = SELECTEDVALUE(Dim_Titles[catalog_era], "2026 Live Releases")
VAR _Rating = SELECTEDVALUE(Dim_Titles[maturity_rating], "TV-MA")
VAR _Runtime = FORMAT(SELECTEDVALUE(Dim_Titles[runtime_minutes_clean], 145), "0") & " min"
VAR _Hours = [Total_View_Hours_Formatted]
VAR _BayesianScore = FORMAT([Bayesian_Weighted_Score], "0.0")
VAR _MatchPct = FORMAT(MIN(MAX([Avg_Completion_Rate_Pct] + 18, 75), 99), "0") & "% Match"
RETURN
"<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', -apple-system, sans-serif; }
  .hero-container {
    position: relative; width: 100%; height: 490px; border-radius: 20px;
    background: linear-gradient(90deg, #0A0A0A 0%, rgba(18,18,18,0.88) 50%, rgba(229,9,20,0.18) 100%), #141414;
    border: 1.5px solid rgba(255,255,255,0.1); padding: 50px 60px; display: flex; flex-direction: column; justify-content: center;
    box-shadow: 0 16px 40px rgba(0,0,0,0.85);
  }
  .featured-tag { color: #E50914; font-size: 16px; font-weight: 900; letter-spacing: 2.5px; text-transform: uppercase; margin-bottom: 10px; }
  .title-text { color: #FFFFFF; font-size: 48px; font-weight: 900; letter-spacing: -0.8px; margin-bottom: 12px; }
  .badge-row { display: flex; align-items: center; gap: 18px; margin-bottom: 18px; }
  .match-badge { color: #46D369; font-weight: 800; font-size: 20px; }
  .rating-badge { border: 1.5px solid #888; color: #AAA; font-size: 15px; padding: 3px 10px; border-radius: 4px; }
  .tech-badge { background: #262626; color: #EEE; font-size: 14px; font-weight: 800; padding: 4px 8px; border-radius: 4px; }
  .metrics-summary { color: #CCC; font-size: 19px; line-height: 1.6; max-width: 1200px; }
  .btn-row { display: flex; gap: 20px; margin-top: 24px; }
  .play-btn { background: #FFFFFF; color: #000000; font-weight: 800; font-size: 18px; padding: 12px 30px; border-radius: 6px; border: none; cursor: pointer; display: flex; align-items: center; gap: 10px; }
  .info-btn { background: rgba(109, 109, 110, 0.7); color: #FFFFFF; font-weight: 800; font-size: 18px; padding: 12px 30px; border-radius: 6px; border: none; cursor: pointer; }
</style>
</head>
<body>
  <div class='hero-container'>
    <div class='featured-tag'>★ #1 STREAMING TITLE GLOBALLY</div>
    <div class='title-text'>" & _Title & "</div>
    <div class='badge-row'>
      <span class='match-badge'>" & _MatchPct & "</span>
      <span class='rating-badge'>" & _Rating & "</span>
      <span class='tech-badge'>" & _Runtime & "</span>
      <span class='tech-badge'>4K ULTRA HD</span>
      <span class='tech-badge'>DOLBY ATMOS</span>
      <span class='tech-badge'>★ " & _BayesianScore & " BAYESIAN</span>
    </div>
    <div class='metrics-summary'>
      Generated <b>" & _Hours & "</b> worldwide. Unfolds across multiple genre dimensions with top-tier viewer retention.
    </div>
    <div class='btn-row'>
      <button class='play-btn'>▶ Play Title</button>
      <button class='info-btn'>ⓘ More Info</button>
    </div>
  </div>
</body>
</html>"
```

---

### HTML/CSS Web Component 3: Netflix Movie Poster Card Carousel with Hover Glow (4K UHD)
*HTML component rendering a Netflix streaming carousel card with smooth hover transitions.*

```dax
HTML_Movie_Card_Card = 
VAR _Title = SELECTEDVALUE(Dim_Titles[title], "Avatar: Fire and Ash")
VAR _Genre = SELECTEDVALUE(Dim_Genres[genre_name], "Sci-Fi & Fantasy")
VAR _Rating = SELECTEDVALUE(Dim_Titles[maturity_rating], "TV-MA")
VAR _Score = FORMAT([Bayesian_Weighted_Score], "0.0")
VAR _Completion = FORMAT([Avg_Completion_Rate_Pct], "0") & "%"
RETURN
"<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }
  .card-wrap {
    width: 100%; height: 100%; background: #1C1C1C; border-radius: 12px; padding: 22px;
    border: 1.5px solid #2B2B2B; display: flex; flex-direction: column; justify-content: space-between;
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease; cursor: pointer;
  }
  .card-wrap:hover {
    transform: translateY(-6px) scale(1.02); border-color: #E50914;
    box-shadow: 0 12px 28px rgba(229, 9, 20, 0.35);
  }
  .card-top { display: flex; justify-content: space-between; align-items: flex-start; }
  .card-title { color: #FFFFFF; font-size: 20px; font-weight: 800; line-height: 1.25; max-width: 240px; }
  .badge-score { background: #262626; color: #F5C518; font-size: 16px; font-weight: 800; padding: 3px 8px; border-radius: 6px; }
  .card-genre { color: #888888; font-size: 16px; font-weight: 500; margin-top: 4px; }
  .progress-bg { width: 100%; height: 6px; background: #333333; border-radius: 3px; overflow: hidden; margin-top: 10px; }
  .progress-fill { height: 100%; width: " & _Completion & "; background: #E50914; border-radius: 3px; }
  .card-bot { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; }
  .stat-label { color: #AAAAAA; font-size: 14px; }
  .stat-val { color: #00D2D2; font-size: 16px; font-weight: 800; }
</style>
</head>
<body>
  <div class='card-wrap'>
    <div>
      <div class='card-top'>
        <div class='card-title'>" & _Title & "</div>
        <div class='badge-score'>★ " & _Score & "</div>
      </div>
      <div class='card-genre'>" & _Genre & " • " & _Rating & "</div>
    </div>
    <div>
      <div class='progress-bg'><div class='progress-fill'></div></div>
      <div class='card-bot'>
        <span class='stat-label'>Avg Completion</span>
        <span class='stat-val'>" & _Completion & "</span>
      </div>
    </div>
  </div>
</body>
</html>"
```

---

### HTML/CSS Web Component 4: Interactive Glassmorphic KPI Scorecard (4K UHD)
```dax
HTML_Glass_KPI_Scorecard = 
VAR _Hours = [Total_View_Hours_Formatted]
VAR _Growth = [View_Hours_YoY_Pct]
VAR _Subtitle = 
    IF(
        NOT ISBLANK(_Growth),
        IF(_Growth >= 0, "<span style='color:#46D369;'>▲ +" & FORMAT(_Growth, "0.0%") & "</span> vs prior year", "<span style='color:#E50914;'>▼ " & FORMAT(_Growth, "0.0%") & "</span> vs prior year"),
        "Stable baseline"
    )
RETURN
"<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }
  .kpi-box {
    width: 100%; height: 180px; background: rgba(22, 22, 22, 0.85); backdrop-filter: blur(16px);
    border: 1.5px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 26px 32px;
    display: flex; flex-direction: column; justify-content: space-between; border-left: 6px solid #E50914;
  }
  .kpi-title { color: #9E9E9E; font-size: 16px; font-weight: 800; text-transform: uppercase; letter-spacing: 1.2px; }
  .kpi-val { color: #FFFFFF; font-size: 42px; font-weight: 900; letter-spacing: -0.8px; }
  .kpi-sub { color: #888888; font-size: 16px; font-weight: 600; }
</style>
</head>
<body>
  <div class='kpi-box'>
    <div class='kpi-title'>GLOBAL VIEWERSHIP HOURS</div>
    <div class='kpi-val'>" & _Hours & "</div>
    <div class='kpi-sub'>" & _Subtitle & "</div>
  </div>
</body>
</html>"
```

---

### HTML/CSS Web Component 5: Netflix "More Info" Modal Detail Pop-up (4K UHD Tooltip Page)
*Design a Tooltip report page (480px x 360px) and embed this measure for a detailed Netflix movie synopsis popup.*

```dax
HTML_Modal_Detail_Tooltip = 
VAR _Title = SELECTEDVALUE(Dim_Titles[title], "Title Details")
VAR _Genre = SELECTEDVALUE(Dim_Genres[genre_name], "General")
VAR _Rating = SELECTEDVALUE(Dim_Titles[maturity_rating], "TV-MA")
VAR _Era = SELECTEDVALUE(Dim_Titles[catalog_era], "2026 Live")
VAR _Runtime = FORMAT(SELECTEDVALUE(Dim_Titles[runtime_minutes_clean], 90), "0") & "m"
VAR _Bayesian = FORMAT([Bayesian_Weighted_Score], "0.0")
VAR _Audience = FORMAT([Avg_IMDb_Rating], "0.0")
VAR _Critic = FORMAT([Avg_Critic_Score], "0")
VAR _Budget = IF(NOT ISBLANK([Total_Production_Budget_M]), "$" & FORMAT([Total_Production_Budget_M], "#,##0") & "M", "Direct SVOD")
VAR _Gross = IF(NOT ISBLANK([Total_Worldwide_Gross_M]), "$" & FORMAT([Total_Worldwide_Gross_M], "#,##0") & "M", "Streaming Only")
RETURN
"<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }
  .modal-card {
    width: 480px; height: 360px; background: #141414; border: 1.5px solid #333333; border-radius: 12px;
    padding: 24px; display: flex; flex-direction: column; justify-content: space-between;
    box-shadow: 0 16px 36px rgba(0,0,0,0.9);
  }
  .modal-header { border-bottom: 1.5px solid #262626; padding-bottom: 12px; margin-bottom: 12px; }
  .m-title { color: #FFFFFF; font-size: 24px; font-weight: 800; }
  .m-meta { color: #888888; font-size: 16px; margin-top: 4px; }
  .grid-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .stat-cell { background: #1C1C1C; padding: 10px 14px; border-radius: 6px; border-left: 3px solid #E50914; }
  .s-label { color: #888; font-size: 13px; text-transform: uppercase; font-weight: 700; }
  .s-val { color: #FFF; font-size: 18px; font-weight: 800; margin-top: 4px; }
  .score-cell { color: #F5C518; }
</style>
</head>
<body>
  <div class='modal-card'>
    <div class='modal-header'>
      <div class='m-title'>" & _Title & "</div>
      <div class='m-meta'>" & _Era & " • " & _Genre & " • " & _Rating & " • " & _Runtime & "</div>
    </div>
    <div class='grid-stats'>
      <div class='stat-cell'><div class='s-label'>Bayesian Score</div><div class='s-val score-cell'>★ " & _Bayesian & " / 10</div></div>
      <div class='stat-cell'><div class='s-label'>IMDb / Metascore</div><div class='s-val'>" & _Audience & " / " & _Critic & "</div></div>
      <div class='stat-cell'><div class='s-label'>Production Budget</div><div class='s-val'>" & _Budget & "</div></div>
      <div class='stat-cell'><div class='s-label'>Worldwide Gross</div><div class='s-val'>" & _Gross & "</div></div>
    </div>
    <div style='color:#555; font-size:12px; text-align:right;'>StreamPulse Semantic Galaxy Layer</div>
  </div>
</body>
</html>"
```
      <div class='stat-cell'><div class='s-label'>Bayesian Score</div><div class='s-val score-cell'>★ " & _Bayesian & " / 10</div></div>
      <div class='stat-cell'><div class='s-label'>IMDb / Metascore</div><div class='s-val'>" & _Audience & " / " & _Critic & "</div></div>
      <div class='stat-cell'><div class='s-label'>Production Budget</div><div class='s-val'>" & _Budget & "</div></div>
      <div class='stat-cell'><div class='s-label'>Worldwide Gross</div><div class='s-val'>" & _Gross & "</div></div>
    </div>
    <div style='color:#555; font-size:9px; text-align:right;'>StreamPulse Semantic Galaxy Layer</div>
  </div>
</body>
</html>"
```

---

## 4. Dynamic SVG Vector Visual Measures (4K UHD Optimized, Data Category: Image URL)

> [!IMPORTANT]
> **Data Category Setup**: In Power BI Desktop Model View, select each measure $\to$ in the **Properties pane** set **Data Category** to **`Image URL`**. Use these inside **Table**, **Matrix**, and **New Card** visuals.

### SVG 1: Dynamic Gradient Completion Progress Bar (4K UHD)
```dax
SVG_Completion_ProgressBar = 
VAR _Pct = [Avg_Completion_Rate_Pct]
VAR _ClampedPct = MIN(MAX(_Pct, 0), 100)
VAR _BarWidth = INT(_ClampedPct * 1.8)
VAR _Color = 
    SWITCH(
        TRUE(),
        _ClampedPct >= 80, "#00D2D2",
        _ClampedPct >= 60, "#E50914",
        "#888888"
    )
RETURN
    "data:image/svg+xml;utf8," &
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='30' viewBox='0 0 240 30'>" &
    "<rect x='0' y='7' width='180' height='16' rx='8' fill='#242424'/>" &
    "<rect x='0' y='7' width='" & _BarWidth & "' height='16' rx='8' fill='" & _Color & "'/>" &
    "<text x='192' y='20' font-family='Segoe UI, sans-serif' font-size='14' font-weight='bold' fill='#FFFFFF'>" & 
    FORMAT(_ClampedPct, "0") & "%</text>" &
    "</svg>"
```

### SVG 2: Multi-Point Smooth Viewership Sparkline (4K UHD)
```dax
SVG_Viewership_Sparkline = 
VAR _Hours = [Total_View_Hours_M]
VAR _P2 = INT(32 - MIN(MAX(_Hours * 0.15, 4), 26))
VAR _P3 = INT(32 - MIN(MAX(_Hours * 0.32, 6), 28))
RETURN
    "data:image/svg+xml;utf8," &
    "<svg xmlns='http://www.w3.org/2000/svg' width='160' height='38' viewBox='0 0 160 38'>" &
    "<path d='M 6 30 Q 55 " & _P2 & ", 110 " & _P3 & " T 154 6' fill='none' stroke='#E50914' stroke-width='3.5' stroke-linecap='round'/>" &
    "<circle cx='154' cy='6' r='4.5' fill='#E50914'/>" &
    "</svg>"
```

### SVG 3: Golden Rating Star Badge (4K UHD)
```dax
SVG_Rating_Star_Badge = 
VAR _Score = [Bayesian_Weighted_Score]
VAR _FormattedScore = FORMAT(_Score, "0.0")
RETURN
    "data:image/svg+xml;utf8," &
    "<svg xmlns='http://www.w3.org/2000/svg' width='100' height='30' viewBox='0 0 100 30'>" &
    "<rect x='0' y='0' width='100' height='30' rx='6' fill='#1F1F1F' stroke='#333333' stroke-width='1.5'/>" &
    "<path d='M14 6l2.4 4.8 5.3.8-3.8 3.7.9 5.3-4.8-2.5-4.8 2.5.9-5.3-3.8-3.7 5.3-.8z' fill='#F5C518'/>" &
    "<text x='32' y='21' font-family='Segoe UI, sans-serif' font-size='15' font-weight='bold' fill='#FFFFFF'>" & _FormattedScore & "</text>" &
    "</svg>"
```

### SVG 4: Financial ROI Radial Meter & Break-Even Marker (4K UHD)
```dax
SVG_ROI_Bullet_Meter = 
VAR _ROI = [Financial_ROI_Multiplier]
VAR _Width = INT(MIN(MAX(_ROI * 36, 0), 160))
VAR _FillColor = IF(_ROI >= 2.5, "#00D2D2", IF(_ROI >= 1.0, "#E50914", "#E5A914"))
RETURN
    "data:image/svg+xml;utf8," &
    "<svg xmlns='http://www.w3.org/2000/svg' width='190' height='28' viewBox='0 0 190 28'>" &
    "<rect x='0' y='6' width='160' height='16' rx='4' fill='#2A2A2A'/>" &
    "<rect x='0' y='6' width='" & _Width & "' height='16' rx='4' fill='" & _FillColor & "'/>" &
    "<line x1='90' y1='2' x2='90' y2='26' stroke='#FFFFFF' stroke-width='2.5'/>" &
    "</svg>"
```

### SVG 5: Global Top 10 Red Number Rank Visual (4K UHD)
```dax
SVG_Top10_Rank_Badge = 
VAR _Rank = SELECTEDVALUE(Fact_Streaming_Performance[performance_key], 1)
RETURN
    "data:image/svg+xml;utf8," &
    "<svg xmlns='http://www.w3.org/2000/svg' width='60' height='60' viewBox='0 0 60 60'>" &
    "<text x='30' y='48' font-family='Segoe UI, Impact, sans-serif' font-size='50' font-weight='900' text-anchor='middle' fill='#141414' stroke='#E50914' stroke-width='2.5'>" & 
    _Rank & "</text>" &
    "</svg>"
```

---

## 5. Enterprise DAX Measure Library (45+ Measures & 7 Display Folders)

Create a dedicated disconnected table named `_Measures` and organize the following formulas into their respective display folders:

---

### Folder 01: Core Streaming & Catalog KPIs
```dax
Total_Catalog_Titles = DISTINCTCOUNT(Dim_Titles[title_key])

Total_Movies = CALCULATE([Total_Catalog_Titles], Dim_Titles[title_type] = "Movie")

Total_TV_Shows = CALCULATE([Total_Catalog_Titles], Dim_Titles[title_type] = "TV Show")

Total_View_Hours_M = SUM(Fact_Streaming_Performance[global_view_hours_millions])

Total_View_Hours_Formatted = 
VAR _Hours = [Total_View_Hours_M]
RETURN
    SWITCH(
        TRUE(),
        _Hours >= 1000, FORMAT(_Hours / 1000, "#,##0.0") & " Billion Hrs",
        _Hours >= 1, FORMAT(_Hours, "#,##0.0") & " Million Hrs",
        FORMAT(_Hours * 1000, "#,##0") & " Thousand Hrs"
    )

Avg_Completion_Rate_Pct = AVERAGE(Fact_Streaming_Performance[avg_completion_pct])

Total_Subscribers_Reached_K = SUM(Fact_Streaming_Performance[subscribers_reached_thousands])

Avg_Runtime_Minutes = AVERAGE(Dim_Titles[runtime_minutes_clean])
```

---

### Folder 02: Time Intelligence
```dax
View_Hours_YTD = CALCULATE([Total_View_Hours_M], DATESYTD(Dim_Date[full_date]))

View_Hours_PY = CALCULATE([Total_View_Hours_M], SAMEPERIODLASTYEAR(Dim_Date[full_date]))

View_Hours_YoY_Growth = 
VAR _Current = [Total_View_Hours_M]
VAR _Prior = [View_Hours_PY]
RETURN IF(NOT ISBLANK(_Prior), _Current - _Prior, BLANK())

View_Hours_YoY_Pct = DIVIDE([View_Hours_YoY_Growth], [View_Hours_PY], BLANK())

View_Hours_PM = CALCULATE([Total_View_Hours_M], PREVIOUSMONTH(Dim_Date[full_date]))

View_Hours_MoM_Pct = DIVIDE([Total_View_Hours_M] - [View_Hours_PM], [View_Hours_PM], BLANK())

Rolling_28D_View_Hours = 
CALCULATE([Total_View_Hours_M], DATESINPERIOD(Dim_Date[full_date], MAX(Dim_Date[full_date]), -28, DAY))

Rolling_90D_View_Hours = 
CALCULATE([Total_View_Hours_M], DATESINPERIOD(Dim_Date[full_date], MAX(Dim_Date[full_date]), -90, DAY))
```

---

### Folder 03: Advanced Analytics & Pareto 80/20 Concentration
```dax
Pareto_Cumulative_View_Hours = 
VAR _CurrentHours = [Total_View_Hours_M]
VAR _AllTitles = ALLSELECTED(Dim_Titles[title_key], Dim_Titles[title])
RETURN
    IF(
        NOT ISBLANK(_CurrentHours),
        SUMX(FILTER(_AllTitles, [Total_View_Hours_M] >= _CurrentHours), [Total_View_Hours_M])
    )

Pareto_Cumulative_Pct = 
DIVIDE([Pareto_Cumulative_View_Hours], CALCULATE([Total_View_Hours_M], ALLSELECTED(Dim_Titles)), BLANK())

Pareto_Catalog_Tier = 
VAR _CumPct = [Pareto_Cumulative_Pct]
RETURN
    SWITCH(
        TRUE(),
        ISBLANK(_CumPct), BLANK(),
        _CumPct <= 0.80, "Tier A (Top 80% Engine)",
        _CumPct <= 0.95, "Tier B (Mid 15% Sustainer)",
        "Tier C (Long-Tail 5%)"
    )

Top_10_Concentration_Share_Pct = 
VAR _Top10Hours = CALCULATE([Total_View_Hours_M], TOPN(10, ALLSELECTED(Dim_Titles), [Total_View_Hours_M], DESC))
VAR _TotalHours = CALCULATE([Total_View_Hours_M], ALLSELECTED(Dim_Titles))
RETURN DIVIDE(_Top10Hours, _TotalHours, BLANK())
```

---

### Folder 04: Bayesian Rating & Quality Scoring
```dax
Avg_IMDb_Rating = AVERAGE(Fact_Catalog_Ratings[vote_average])

Total_Vote_Count = SUM(Fact_Catalog_Ratings[vote_count])

Bayesian_Weighted_Score = 
VAR _R = [Avg_IMDb_Rating]
VAR _v = [Total_Vote_Count]
VAR _m = 25000.0
VAR _C = 7.0
RETURN
    IF(NOT ISBLANK(_R) && _v > 0, DIVIDE(_v * _R + _m * _C, _v + _m, BLANK()), _C)

Avg_Critic_Score = AVERAGE(Fact_Catalog_Ratings[critic_score])

Critic_Audience_Gap = 
VAR _AudienceScaled = [Avg_IMDb_Rating] * 10.0
VAR _Critic = [Avg_Critic_Score]
RETURN IF(NOT ISBLANK(_Critic) && NOT ISBLANK(_AudienceScaled), _AudienceScaled - _Critic, BLANK())

Quality_Tier_Classification = 
VAR _Score = [Bayesian_Weighted_Score]
RETURN
    SWITCH(
        TRUE(),
        _Score >= 8.3, "🏆 Masterpiece (Top Tier)",
        _Score >= 7.5, "⭐ Certified Hit",
        _Score >= 6.5, "👍 Solid Performer",
        "⚠️ Mixed / Polarizing"
    )
```

---

### Folder 05: Financial ROI & Unit Economics
```dax
Total_Production_Budget_M = DIVIDE(SUM(Fact_Financial_ROI[production_budget_usd]), 1000000, BLANK())

Total_Worldwide_Gross_M = DIVIDE(SUM(Fact_Financial_ROI[worldwide_gross_usd]), 1000000, BLANK())

Net_Box_Office_Profit_M = 
VAR _Gross = [Total_Worldwide_Gross_M]
VAR _Budget = [Total_Production_Budget_M]
RETURN IF(NOT ISBLANK(_Gross) && _Gross > 0, _Gross - _Budget, BLANK())

Financial_ROI_Multiplier = DIVIDE([Total_Worldwide_Gross_M], [Total_Production_Budget_M], BLANK())

Cost_Per_View_Hour_USD = 
VAR _TotalBudgetUSD = SUM(Fact_Financial_ROI[production_budget_usd])
VAR _TotalViewHours = [Total_View_Hours_M] * 1000000
RETURN DIVIDE(_TotalBudgetUSD, _TotalViewHours, BLANK())

Budget_Efficiency_Index = DIVIDE([Total_View_Hours_M], [Total_Production_Budget_M], BLANK())
```

---

## 6. Calculation Groups: Time Intelligence & Unit Currency Switcher

Create the **Time Intelligence Calculation Group** using Tabular Editor:

### Table: `Time_Intelligence_Matrix`
- **Item 1: `Current Value`** $\to$ `SELECTEDMEASURE()`
- **Item 2: `YTD`** $\to$ `CALCULATE(SELECTEDMEASURE(), DATESYTD(Dim_Date[full_date]))`
- **Item 3: `YoY Growth`** $\to$ `SELECTEDMEASURE() - CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR(Dim_Date[full_date]))`
- **Item 4: `YoY %`** $\to$ `DIVIDE(SELECTEDMEASURE() - CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR(Dim_Date[full_date])), CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR(Dim_Date[full_date])), BLANK())`
- **Item 5: `Rolling 28D`** $\to$ `CALCULATE(SELECTEDMEASURE(), DATESINPERIOD(Dim_Date[full_date], MAX(Dim_Date[full_date]), -28, DAY))`

---

## 7. Netflix Cinematic Dark JSON Theme File

Save the following clean, schema-compliant JSON as [`dashboard/netflix_cinematic_dark.json`](file:///d:/courses/Data%20Science/Data%20Engineering/Projects/streampulse/dashboard/netflix_cinematic_dark.json) and import it into Power BI Desktop via **View > Themes > Browse for Themes**:

```json
{
  "name": "StreamPulse Netflix Cinematic Dark",
  "dataColors": [
    "#E50914",
    "#00D2D2",
    "#F5C518",
    "#46D369",
    "#B81D24",
    "#7C3AED",
    "#F97316",
    "#38BDF8",
    "#FFFFFF",
    "#888888"
  ],
  "background": "#0B0B0B",
  "foreground": "#141414",
  "tableAccent": "#E50914",
  "good": "#46D369",
  "neutral": "#F5C518",
  "bad": "#E50914",
  "minimum": "#1A1A1A",
  "center": "#F5C518",
  "maximum": "#46D369",
  "textClasses": {
    "callout": {
      "fontSize": 28,
      "fontFace": "Segoe UI",
      "color": "#FFFFFF"
    },
    "title": {
      "fontSize": 14,
      "fontFace": "Segoe UI Semibold",
      "color": "#FFFFFF"
    },
    "header": {
      "fontSize": 12,
      "fontFace": "Segoe UI Semibold",
      "color": "#E5E5E5"
    },
    "label": {
      "fontSize": 11,
      "fontFace": "Segoe UI",
      "color": "#CCCCCC"
    }
  },
  "visualStyles": {
    "page": {
      "*": {
        "background": [
          {
            "color": { "solid": { "color": "#0B0B0B" } },
            "transparency": 0
          }
        ],
        "outspace": [
          {
            "color": { "solid": { "color": "#050505" } },
            "transparency": 0
          }
        ]
      }
    },
    "*": {
      "*": {
        "background": [
          {
            "color": { "solid": { "color": "#141414" } },
            "transparency": 0
          }
        ],
        "border": [
          {
            "show": true,
            "color": { "solid": { "color": "#282828" } }
          }
        ],
        "dropShadow": [
          {
            "show": true,
            "color": { "solid": { "color": "#000000" } }
          }
        ],
        "title": [
          {
            "show": true,
            "fontColor": { "solid": { "color": "#FFFFFF" } },
            "fontFamily": "Segoe UI Semibold",
            "fontSize": 13
          }
        ]
      }
    }
  }
}
```

---

## 8. 4K UHD (3840 x 2160) 6-Page Native Web-App Construction Guide

To achieve an ultra-crisp, broadcast-grade streaming web platform experience in Power BI:

### 🖥️ 4K Canvas Setup Instructions
1. In Power BI Desktop, go to **Format Page** (brush icon) $\to$ expand **Canvas settings**.
2. Set **Type** to **`Custom`**.
3. Set **Width** to **`3840 px`** and **Height** to **`2160 px`** (16:9 Ultra HD).
4. Go to the top ribbon $\to$ **View** tab $\to$ set **Page View** to **`Fit to page`** while editing on standard monitors.
5. Apply the `dashboard/netflix_cinematic_dark.json` theme.
6. Place the `[HTML_Netflix_Navbar]` measure at $(X=0, Y=0, W=3840, H=120)$ on every page.

---

### 🌐 Page 0: Streaming Platform Command Center & Home Portal (4K UHD Layout)

| Visual # | Visual Type | Position & Size (4K) | Primary Fields / DAX Measures | Purpose & Visual Styling |
|---|---|---|---|---|
| **V0.1** | `HTML Content` | $X: 0, Y: 0, W: 3840, H: 120$ | `[HTML_Netflix_Navbar]` | Fixed top navigation bar with active "Portal Home" tab and live DirectQuery beacon. |
| **V0.2** | `HTML Content` | $X: 60, Y: 150, W: 3720, H: 340$ | `[HTML_Home_Hero_Banner]` | Dynamic time-based greeting, live platform telemetry, total catalog count & Bayesian quality. |
| **V0.3** | `HTML Content` | $X: 60, Y: 510, W: 3720, H: 80$ | `[HTML_Home_Marquee_Ticker]` | Animated CSS `@keyframes marquee` continuous streaming news and data pipeline ticker. |
| **V0.4** | `HTML Content` | $X: 60, Y: 610, W: 3720, H: 460$ | `[HTML_Home_Navigation_Hub]` | 5 interactive module route cards with glowing red hover borders and launch bookmarks. |
| **V0.5** | `HTML Content` | $X: 60, Y: 1090, W: 3720, H: 540$ | `[HTML_Home_Platform_Vitals]` | 4-column architecture drawer (Bronze Ingestion, Airbyte 0.50.36, Galaxy Star, Power BI SLA). |
| **V0.6** | `New Card` | $X: 60, Y: 1650, W: 1840, H: 450$ | `[Total_Titles_Ingested]`, `[Total_View_Hours_Formatted]`, `[Avg_Completion_Rate_Pct]`, `[Bayesian_Weighted_Score]` | High-impact callout numbers with glowing borders and SVG progress bars. |
| **V0.7** | `Table` | $X: 1940, Y: 1650, W: 1840, H: 450$ | `Dim_Titles[catalog_era]`, `[Total_Titles_Ingested]`, `[Total_View_Hours_M]`, `[Avg_IMDb_Rating]`, `[SVG_Completion_ProgressBar]` | Data warehouse conformed summary table across streaming eras. |

---

### 🎬 Page 1: Executive Pulse & Live Radar (4K UHD Layout)

| Visual # | Visual Type | Position & Size (4K) | Primary Fields / DAX Measures | Purpose & Visual Styling |
|---|---|---|---|---|
| **V1.1** | `HTML Content` | $X: 0, Y: 0, W: 3840, H: 120$ | `[HTML_Netflix_Navbar]` | Top navigation bar with active "Executive Pulse" tab. |
| **V1.2** | `HTML Content` | $X: 60, Y: 150, W: 2400, H: 520$ | `[HTML_Netflix_Hero_Card]` | Signature Netflix hero banner with trailer mockup, match %, audio/video badges, and action buttons. |
| **V1.3** | `Table / Matrix` | $X: 2500, Y: 150, W: 1280, H: 960$ | `[SVG_Top10_Rank_Badge]`, `Dim_Titles[title]`, `Dim_Titles[maturity_rating]`, `[Total_View_Hours_M]`, `[Bayesian_Weighted_Score]` | Global Top 10 streaming chart sorted descending by `[Total_View_Hours_M]`. |
| **V1.4** | `HTML Content` | $X: 60, Y: 690, W: 2400, H: 220$ | `[HTML_Glass_KPI_Scorecard]` | 4 glassmorphic KPI scorecards (Total Hours, Bayesian Score, Avg Completion %, Active Subscribers). |
| **V1.5** | `Area Chart` | $X: 60, Y: 930, W: 2400, H: 680$ | **X**: `Dim_Date[month_name]`, **Y**: `[Total_View_Hours_M]`, **Legend**: `Dim_Titles[catalog_era]` | Real-time viewership trajectory curve with neon cyan gradient fill. |
| **V1.6** | `Matrix` | $X: 60, Y: 1630, W: 2400, H: 470$ | **Rows**: `Dim_Genres[genre_name]`, **Values**: `[Total_Titles_Ingested]`, `[Total_View_Hours_M]`, `[Avg_Completion_Rate_Pct]`, `[SVG_Completion_ProgressBar]` | Multi-genre performance matrix with inline SVG progress bars. |
| **V1.7** | `Donut Chart` | $X: 2500, Y: 1130, W: 1280, H: 470$ | **Legend**: `Dim_Territory[region_group]`, **Values**: `[Total_View_Hours_M]` | Global regional market share distribution (North America, EMEA, APAC, Worldwide). |
| **V1.8** | `Table` | $X: 2500, Y: 1620, W: 1280, H: 480$ | `Dim_Titles[title]`, `Dim_Titles[release_year]`, `[Avg_IMDb_Rating]`, `[SVG_Rating_Star_Badge]` | DirectQuery live scraped releases with golden star badges. |

---

### 🌌 Page 2: Kimball Galaxy Catalog Explorer (4K UHD Layout)

| Visual # | Visual Type | Position & Size (4K) | Primary Fields / DAX Measures | Purpose & Visual Styling |
|---|---|---|---|---|
| **V2.1** | `HTML Content` | $X: 0, Y: 0, W: 3840, H: 120$ | `[HTML_Netflix_Navbar]` | Top navigation bar with active "Catalog Galaxy" tab. |
| **V2.2** | `Slicers Bar` | $X: 60, Y: 140, W: 3720, H: 100$ | `Dim_Titles[catalog_era]`, `Dim_Titles[maturity_category]`, `Dim_Genres[genre_category]`, `Dim_Titles[runtime_tier]` | Horizontal dark badge slicers for multi-dimensional catalog filtering. |
| **V2.3** | `Clustered Bar` | $X: 60, Y: 260, W: 1800, H: 650$ | **Y**: `Dim_Titles[catalog_era]`, **X**: `[Total_Titles_Ingested]`, **Legend**: `Dim_Titles[title_type]` | Era distribution comparing Movies vs. TV Shows across the 7,786 conformed records. |
| **V2.4** | `Column Chart` | $X: 1900, Y: 260, W: 1880, H: 650$ | **X**: `Fact_Catalog_Ratings[vote_average]`, **Y**: `[Total_Titles_Ingested]`, **Line**: `[Bayesian_Weighted_Score]` | Bayesian shrinkage quality score distribution curve against raw audience ratings. |
| **V2.5** | `Matrix` | $X: 60, Y: 930, W: 2400, H: 1170$ | **Rows**: `Dim_Titles[title]`, `Dim_Genres[genre_name]`, **Values**: `Dim_Titles[release_year]`, `Dim_Titles[maturity_rating]`, `Dim_Titles[runtime_minutes_clean]`, `[Bayesian_Weighted_Score]`, `[Pareto_Catalog_Tier]`, `[SVG_Rating_Star_Badge]` | Detailed conformed title explorer with Pareto Tier A/B/C classification and hover synopsis tooltips (`[HTML_Modal_Detail_Tooltip]`). |
| **V2.6** | `Donut Chart` | $X: 2500, Y: 930, W: 1280, H: 560$ | **Legend**: `[Pareto_Catalog_Tier]`, **Values**: `[Total_View_Hours_M]` | 80/20 Pareto rule visualization demonstrating core viewership concentration. |
| **V2.7** | `HTML Content` | $X: 2500, Y: 1510, W: 1280, H: 590$ | `[HTML_Movie_Card_Card]` | Dynamic Netflix glowing card preview of selected catalog title. |

---

### 📊 Page 3: Viewership & Engagement Telemetry (4K UHD Layout)

| Visual # | Visual Type | Position & Size (4K) | Primary Fields / DAX Measures | Purpose & Visual Styling |
|---|---|---|---|---|
| **V3.1** | `HTML Content` | $X: 0, Y: 0, W: 3840, H: 120$ | `[HTML_Netflix_Navbar]` | Top navigation bar with active "Viewership Telemetry" tab. |
| **V3.2** | `Line Chart` | $X: 60, Y: 150, W: 2500, H: 800$ | **X**: `Dim_Date[month_name]`, **Y**: `[Total_View_Hours_M]`, **Small Multiples**: `Fact_Streaming_Performance[device_category]` | Unpivoted Lakehouse telemetry monthly trends broken down by Connected TV, Mobile, Desktop, and Tablet. |
| **V3.3** | `New Card` | $X: 2600, Y: 150, W: 1180, H: 800$ | `[Total_View_Hours_M]`, `[View_Hours_MoM_Growth_M]`, `[View_Hours_MoM_Pct]`, `[Rolling_28D_View_Hours_M]`, `[SVG_Animated_Quality_Ring]` | Real-time viewership telemetry and velocity cards with animated circular SVG completion ring. |
| **V3.4** | `Scatter Plot` | $X: 60, Y: 980, W: 2500, H: 1120$ | **X**: `[Avg_Completion_Rate_Pct]`, **Y**: `[Total_View_Hours_M]`, **Size**: `[Active_Subscribers_Reached_K]`, **Play Axis**: `Dim_Date[month_name]` | Quadrant analysis mapping engagement quality vs. global volume with playback animation. |
| **V3.5** | `Matrix` | $X: 2600, Y: 980, W: 1180, H: 1120$ | **Rows**: `Dim_Territory[territory_name]`, **Columns**: `Fact_Streaming_Performance[device_category]`, **Values**: `[Total_View_Hours_M]`, `[SVG_Completion_ProgressBar]` | Territory vs. Device cross-tabulation with heatmap color bars. |

---

### 💰 Page 4: Financial ROI & Unit Economics (4K UHD Layout)

| Visual # | Visual Type | Position & Size (4K) | Primary Fields / DAX Measures | Purpose & Visual Styling |
|---|---|---|---|---|
| **V4.1** | `HTML Content` | $X: 0, Y: 0, W: 3840, H: 120$ | `[HTML_Netflix_Navbar]` | Top navigation bar with active "Financial ROI" tab. |
| **V4.2** | `Scatter Plot` | $X: 60, Y: 150, W: 2500, H: 900$ | **X**: `[Total_Production_Budget_M]`, **Y**: `[Total_Worldwide_Gross_M]`, **Details**: `Dim_Titles[title]`, **Color**: `Fact_Financial_ROI[financial_roi_tier]` | Budget vs. Worldwide Gross scatter plot with fixed **$Y = 2.5X$ Theatrical Break-Even Reference Line**. |
| **V4.3** | `Matrix` | $X: 2600, Y: 150, W: 1180, H: 900$ | `[Total_Production_Budget_M]`, `[Total_Worldwide_Gross_M]`, `[Net_Box_Office_Profit_M]`, `[Financial_ROI_Multiplier]`, `[SVG_ROI_Bullet_Meter]` | Financial unit economics scorecard with dynamic SVG bullet meters. |
| **V4.4** | `Clustered Column` | $X: 60, Y: 1080, W: 2500, H: 1020$ | **X**: `Dim_Titles[title]`, **Y**: `[Cost_Per_View_Hour_USD]`, **Line**: `[Budget_Efficiency_Index]` | Unit economics ranking showing Cost Per View Hour (CPVH) and viewership ROI efficiency. |
| **V4.5** | `Waterfall Chart` | $X: 2600, Y: 1080, W: 1180, H: 1020$ | **Category**: `Dim_Titles[catalog_era]`, **Y**: `[Net_Box_Office_Profit_M]` | Net profit contribution waterfall by release era. |

---

### 🎭 Page 5: Creative Talent & Star Power Hub (4K UHD Layout)

| Visual # | Visual Type | Position & Size (4K) | Primary Fields / DAX Measures | Purpose & Visual Styling |
|---|---|---|---|---|
| **V5.1** | `HTML Content` | $X: 0, Y: 0, W: 3840, H: 120$ | `[HTML_Netflix_Navbar]` | Top navigation bar with active "Talent Creative Hub" tab. |
| **V5.2** | `Clustered Bar` | $X: 60, Y: 150, W: 1800, H: 850$ | **Y**: `Dim_Talent_Crew[person_name]`, **X**: `[Total_View_Hours_M]`, **Legend**: `Dim_Talent_Crew[star_power_tier]` | Top 15 creative directors and producers ranked by aggregate global streaming hours. |
| **V5.3** | `Matrix` | $X: 1900, Y: 150, W: 1880, H: 850$ | **Rows**: `Dim_Talent_Crew[person_name]`, `Dim_Talent_Crew[primary_role]`, **Values**: `[Total_Titles_Ingested]`, `[Total_View_Hours_M]`, `[Bayesian_Weighted_Score]`, `[SVG_Rating_Star_Badge]` | Talent creative scorecard with star power tier ratings and golden star badges. |
| **V5.4** | `Matrix Table` | $X: 60, Y: 1030, W: 3720, H: 1070$ | **Rows**: `Dim_Talent_Crew[person_name]`, `Dim_Titles[title]`, **Values**: `Dim_Titles[release_year]`, `Dim_Genres[genre_name]`, `[Total_View_Hours_M]`, `[Avg_Completion_Rate_Pct]`, `[SVG_Completion_ProgressBar]`, `[Total_Worldwide_Gross_M]`, `[SVG_Viewership_Sparkline]` | Complete creative filmography browser with inline SVG completion progress bars and sparkline trajectories. |

---

## 9. DirectQuery Performance Tuning & Production Best Practices

1. **Enable Referential Integrity**: On all 1-to-many relationships from dimensions to fact tables, check **Assume Referential Integrity** in Power BI to ensure the engine issues fast `INNER JOIN` queries instead of `OUTER JOIN`.
2. **Push Down Transformations to PostgreSQL Reporting Views**: Utilize `reporting.vw_powerbi_catalog_pulse` and `reporting.vw_powerbi_performance_matrix` to pre-aggregate heavy joins.
3. **Avoid Row-Level Calculated Columns**: Implement all calculations as DAX measures or M columns during initial data loading.
4. **Data Category for SVGs**: Always set the Data Category of SVG measures to `Image URL` in the Model view.

---

*Authored for the StreamPulse Enterprise Analytics Platform 2026.*
