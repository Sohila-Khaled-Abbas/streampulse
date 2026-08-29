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

## 3. Netflix Web-App UI Components in Power BI (HTML, CSS & SVG)

To give Power BI the exact look and feel of a **modern streaming platform website & command center**, use these DAX measures in conjunction with the **HTML Content visual (AppSource)** or the native **New Card Visual** (with Data Category set to `Image URL`).

---

### HTML/CSS Web Component 0.1: Netflix Home Page Hero Command Banner
*Add this measure to an HTML Content visual across the top of **Page 0 (Home Page)** (Width: 1840px, Height: 180px).*

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
  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }
  @keyframes pulseGlow {
    0% { box-shadow: 0 0 0 0 rgba(229, 9, 20, 0.7); }
    70% { box-shadow: 0 0 0 12px rgba(229, 9, 20, 0); }
    100% { box-shadow: 0 0 0 0 rgba(229, 9, 20, 0); }
  }
  .hero-home-wrap {
    width: 100%; height: 160px; border-radius: 14px;
    background: linear-gradient(135deg, rgba(20, 20, 20, 0.95) 0%, rgba(10, 10, 10, 0.98) 60%, rgba(229, 9, 20, 0.18) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08); padding: 25px 35px;
    display: flex; align-items: center; justify-content: space-between;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.7);
  }
  .left-hero { display: flex; flex-direction: column; gap: 8px; max-width: 900px; }
  .greeting-tag { display: flex; align-items: center; gap: 10px; font-size: 12px; font-weight: 700; color: #E50914; letter-spacing: 1.2px; text-transform: uppercase; }
  .pulse-dot { width: 8px; height: 8px; background: #E50914; border-radius: 50%; animation: pulseGlow 1.8s infinite; }
  .hero-title {
    font-size: 32px; font-weight: 900; letter-spacing: -0.5px;
    background: linear-gradient(90deg, #FFFFFF 0%, #E0E0E0 50%, #E50914 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  .hero-subtitle { color: #A3A3A3; font-size: 13px; font-weight: 400; line-height: 1.4; }
  .hero-metrics-pill {
    display: flex; align-items: center; gap: 20px; background: rgba(30, 30, 30, 0.6);
    backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.06);
    padding: 12px 24px; border-radius: 10px;
  }
  .pill-item { display: flex; flex-direction: column; }
  .pill-label { color: #888888; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; }
  .pill-val { color: #FFFFFF; font-size: 18px; font-weight: 800; }
  .pill-val.gold { color: #F5C518; }
  .pill-val.teal { color: #00D2D2; }
  .pill-divider { width: 1px; height: 28px; background: rgba(255, 255, 255, 0.1); }
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

### HTML/CSS Web Component 0.2: Interactive 5-Module Navigation Portal Hub
*Add this measure to an HTML Content visual on **Page 0 (Home Page)** (Width: 1840px, Height: 240px) to render clickable module cards.*

```dax
HTML_Home_Navigation_Hub = 
"<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; }
  .nav-grid {
    display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; width: 100%; height: 220px;
  }
  .module-card {
    background: #141414; border: 1px solid #242424; border-radius: 12px; padding: 20px 18px;
    display: flex; flex-direction: column; justify-content: space-between;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); cursor: pointer; position: relative; overflow: hidden;
  }
  .module-card::before {
    content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 3px;
    background: transparent; transition: background 0.3s ease;
  }
  .module-card:hover {
    transform: translateY(-6px); background: #1C1C1C;
    border-color: #E50914; box-shadow: 0 12px 24px rgba(229, 9, 20, 0.25);
  }
  .module-card:hover::before { background: #E50914; }
  .mod-header { display: flex; align-items: center; justify-content: space-between; }
  .mod-badge {
    width: 36px; height: 36px; border-radius: 8px; background: rgba(229, 9, 20, 0.12);
    border: 1px solid rgba(229, 9, 20, 0.3); display: flex; align-items: center; justify-content: center;
    font-size: 18px; color: #E50914;
  }
  .mod-num { color: #555555; font-size: 12px; font-weight: 800; }
  .mod-title { color: #FFFFFF; font-size: 15px; font-weight: 800; margin-top: 12px; line-height: 1.2; }
  .mod-desc { color: #888888; font-size: 11px; font-weight: 400; line-height: 1.4; margin-top: 6px; }
  .mod-cta {
    display: flex; align-items: center; gap: 6px; color: #E50914; font-size: 11px;
    font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 14px;
  }
  .mod-cta-arrow { transition: transform 0.2s ease; }
  .module-card:hover .mod-cta-arrow { transform: translateX(4px); }
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

### HTML/CSS Web Component 0.3: Live Real-Time Marquee Ticker
*Add this measure to an HTML Content visual on **Page 0 (Home Page)** (Width: 1840px, Height: 44px) for a continuous news ticker.*

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
    width: 100%; height: 38px; background: rgba(18, 18, 18, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 6px;
    display: flex; align-items: center; overflow: hidden; padding: 0 10px;
  }
  .ticker-badge {
    background: #E50914; color: #FFFFFF; font-size: 10px; font-weight: 900;
    padding: 3px 8px; border-radius: 4px; letter-spacing: 1px; text-transform: uppercase;
    white-space: nowrap; margin-right: 15px; z-index: 2; box-shadow: 0 0 10px rgba(229, 9, 20, 0.5);
  }
  .ticker-content {
    display: inline-block; white-space: nowrap;
    animation: marquee 35s linear infinite; color: #CCCCCC; font-size: 12px; font-weight: 500;
  }
  .ticker-item { margin-right: 40px; }
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

### HTML/CSS Web Component 0.4: Platform Architecture & Metadata Drawer
*Add this measure to an HTML Content visual on **Page 0 (Home Page)** (Width: 1840px, Height: 280px).*

```dax
HTML_Home_Platform_Vitals = 
"<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', -apple-system, sans-serif; }
  .vitals-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; width: 100%; height: 260px;
  }
  .vital-card {
    background: #121212; border: 1px solid #222222; border-radius: 10px; padding: 18px;
    display: flex; flex-direction: column; justify-content: space-between;
  }
  .vital-card.primary { border-left: 4px solid #E50914; }
  .vital-card.success { border-left: 4px solid #46D369; }
  .vital-card.teal { border-left: 4px solid #00D2D2; }
  .vital-card.gold { border-left: 4px solid #F5C518; }
  .v-title { color: #888888; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; }
  .v-metric { color: #FFFFFF; font-size: 22px; font-weight: 800; margin: 6px 0; }
  .v-list { list-style: none; display: flex; flex-direction: column; gap: 4px; margin-top: 6px; }
  .v-item { color: #AAAAAA; font-size: 11px; display: flex; align-items: center; justify-content: space-between; }
  .v-tag { background: #222222; padding: 2px 6px; border-radius: 3px; font-weight: 600; color: #EEE; }
  .status-pill {
    display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 700;
    color: #46D369; background: rgba(70, 211, 105, 0.12); padding: 4px 8px; border-radius: 12px; width: fit-content;
  }
  .status-dot { width: 6px; height: 6px; background: #46D369; border-radius: 50%; }
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
        <ul class='v-list' style='margin-top: 8px;'>
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

### Animated SVG Vector Measure 1: Pure SVG Animated Pulsing Radar Beacon
*Set Data Category to **`Image URL`**. Use in tables, matrix headers, or the New Card Visual for an animated neon live status beacon.*

```dax
SVG_Animated_Pulse_Radar = 
"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40' width='40' height='40'>
  <style>
    @keyframes pulseRing {
      0% { r: 6px; opacity: 1; stroke-width: 2px; }
      100% { r: 18px; opacity: 0; stroke-width: 0.5px; }
    }
    @keyframes centerGlow {
      0%, 100% { transform: scale(1); fill: %23E50914; }
      50% { transform: scale(1.2); fill: %23FF3333; }
    }
    .ring1 { animation: pulseRing 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite; }
    .ring2 { animation: pulseRing 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite 0.6s; }
    .dot { transform-origin: center; animation: centerGlow 1.5s ease-in-out infinite; }
  </style>
  <circle class='ring1' cx='20' cy='20' r='6' fill='none' stroke='%23E50914' />
  <circle class='ring2' cx='20' cy='20' r='6' fill='none' stroke='%23E50914' />
  <circle class='dot' cx='20' cy='20' r='5' fill='%23E50914' />
</svg>"
```

---

### Animated SVG Vector Measure 2: Real-Time Animated Quality Gauge Ring
*Set Data Category to **`Image URL`**. Renders an animated SVG radial completion gauge.*

```dax
SVG_Animated_Quality_Ring = 
VAR _Score = [Avg_Completion_Rate_Pct]
VAR _Pct = IF(ISBLANK(_Score), 75, MIN(MAX(_Score, 0), 100))
VAR _DashOffset = FORMAT(283 - (283 * (_Pct / 100.0)), "0")
RETURN
"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100' width='80' height='80'>
  <style>
    .track { fill: none; stroke: %23262626; stroke-width: 8; }
    .fill-bar {
      fill: none; stroke: %2300D2D2; stroke-width: 8;
      stroke-dasharray: 283; stroke-dashoffset: " & _DashOffset & ";
      stroke-linecap: round; transform: rotate(-90deg); transform-origin: 50% 50%;
      transition: stroke-dashoffset 0.8s ease;
    }
    .score-txt { font-family: Segoe UI, sans-serif; font-size: 20px; font-weight: 800; fill: %23FFFFFF; text-anchor: middle; dominant-baseline: middle; }
    .sub-txt { font-family: Segoe UI, sans-serif; font-size: 8px; font-weight: 600; fill: %23888888; text-anchor: middle; }
  </style>
  <circle class='track' cx='50' cy='50' r='45' />
  <circle class='fill-bar' cx='50' cy='50' r='45' />
  <text class='score-txt' x='50' y='46'>" & FORMAT(_Pct, "0") & "%</text>
  <text class='sub-txt' x='50' y='64'>QUALITY</text>
</svg>"
```

---

### 🎨 How to Integrate Animated GIFs & Lottie in Power BI

Power BI allows you to embed animated GIFs and animated SVGs seamlessly using three distinct techniques:

#### Technique A: Direct HTML Content Visual (Recommended for Web Portals)
Pass animated GIF URLs or Base64 data URIs directly inside your DAX measures:
```dax
HTML_Animated_Hero_GIF = 
"<!DOCTYPE html>
<html>
<head>
<style>
  .gif-container {
    width: 100%; height: 100%; border-radius: 8px; overflow: hidden;
    position: relative; border: 1px solid #333333;
  }
  .gif-img { width: 100%; height: 100%; object-fit: cover; }
  .gif-overlay {
    position: absolute; bottom: 0; left: 0; width: 100%;
    background: linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.9) 100%);
    padding: 15px; color: #FFF; font-family: Segoe UI, sans-serif;
  }
</style>
</head>
<body>
  <div class='gif-container'>
    <img class='gif-img' src='https://assets.nflxext.com/ffe/siteui/acquisition/ourStory/fuji/desktop/video-tv-0819.m4v' alt='StreamPulse Pulse' />
    <div class='gif-overlay'>
      <div style='font-size:14px; font-weight:bold;'>DirectQuery Live Radar</div>
      <div style='font-size:11px; color:#AAA;'>Real-time streaming ingestion active</div>
    </div>
  </div>
</body>
</html>"
```

#### Technique B: Native New Card Visual via Animated SVG (Zero Dependencies)
Create a DAX measure returning SVG code with `@keyframes` animations (e.g. `[SVG_Animated_Pulse_Radar]`), set its **Data Category** to `Image URL`, and bind it to the Image slot of Power BI's native **New Card visual**.

#### Technique C: Local GIF Playback via Line Chart Plot Area
If you want to play a local `.gif` without external hosting:
1. Insert a blank **Line Chart** visual.
2. Go to **Format Visual > Plot Area Background > Add Image**.
3. Browse and select your `.gif` file.
4. Set **Image Fit** to `Fit` and **Transparency** to `0%`.
5. Turn off X-Axis, Y-Axis, Title, and Gridlines. Power BI will loop the GIF infinitely on canvas.

---

### HTML/CSS Web Component 1: Netflix Top Navigation Header
*Add this measure to an HTML Content visual anchored across the top of your report (Width: 1920px, Height: 70px).*

```dax
HTML_Netflix_Navbar = 
VAR _CurrentYear = YEAR(TODAY())
RETURN
"<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', -apple-system, sans-serif; }
  .navbar {
    display: flex; align-items: center; justify-content: space-between;
    width: 100%; height: 60px; background: linear-gradient(180deg, rgba(0,0,0,0.95) 0%, rgba(18,18,18,0.7) 100%);
    backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255,255,255,0.08); padding: 0 35px;
  }
  .left-group { display: flex; align-items: center; gap: 32px; }
  .brand-logo { color: #E50914; font-size: 24px; font-weight: 900; letter-spacing: 1.5px; text-transform: uppercase; cursor: pointer; }
  .nav-links { display: flex; gap: 24px; list-style: none; }
  .nav-item { color: #CCCCCC; font-size: 14px; font-weight: 500; transition: color 0.2s ease; cursor: pointer; }
  .nav-item.active { color: #FFFFFF; font-weight: 700; border-bottom: 2px solid #E50914; padding-bottom: 4px; }
  .nav-item:hover { color: #E50914; }
  .right-group { display: flex; align-items: center; gap: 20px; }
  .live-badge {
    display: flex; align-items: center; gap: 6px; background: rgba(229, 9, 20, 0.15);
    border: 1px solid #E50914; color: #E50914; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700;
  }
  .pulse-dot { width: 7px; height: 7px; background: #E50914; border-radius: 50%; box-shadow: 0 0 8px #E50914; }
  .user-avatar { width: 32px; height: 32px; border-radius: 4px; background: #2A2A2A; border: 1px solid #444; display: flex; align-items: center; justify-content: center; color: #FFF; font-size: 12px; font-weight: bold; }
</style>
</head>
<body>
  <div class='navbar'>
    <div class='left-group'>
      <div class='brand-logo'>STREAMPULSE</div>
      <ul class='nav-links'>
        <li class='nav-item'>Portal Home</li>
        <li class='nav-item active'>Executive Pulse</li>
        <li class='nav-item'>Catalog Galaxy</li>
        <li class='nav-item'>Viewership Telemetry</li>
        <li class='nav-item'>Financial ROI</li>
        <li class='nav-item'>Talent Creative Hub</li>
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

---

### HTML/CSS Web Component 2: Netflix Featured Hero Player & Metadata Card
*Generates the signature Netflix featured hero banner with trailer mockups, rating match percentage, and audio/video badges.*

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
    position: relative; width: 100%; height: 260px; border-radius: 12px;
    background: linear-gradient(90deg, #0A0A0A 0%, rgba(18,18,18,0.85) 50%, rgba(229,9,20,0.15) 100%), #141414;
    border: 1px solid rgba(255,255,255,0.1); padding: 30px 40px; display: flex; flex-direction: column; justify-content: center;
    box-shadow: 0 8px 24px rgba(0,0,0,0.8);
  }
  .featured-tag { color: #E50914; font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 6px; }
  .title-text { color: #FFFFFF; font-size: 32px; font-weight: 900; letter-spacing: -0.5px; margin-bottom: 8px; }
  .badge-row { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
  .match-badge { color: #46D369; font-weight: 700; font-size: 14px; }
  .rating-badge { border: 1px solid #888; color: #AAA; font-size: 11px; padding: 1px 6px; border-radius: 2px; }
  .tech-badge { background: #262626; color: #EEE; font-size: 10px; font-weight: 700; padding: 2px 5px; border-radius: 2px; }
  .metrics-summary { color: #CCC; font-size: 13px; line-height: 1.5; max-width: 650px; }
  .btn-row { display: flex; gap: 14px; margin-top: 16px; }
  .play-btn { background: #FFFFFF; color: #000000; font-weight: 700; font-size: 13px; padding: 8px 20px; border-radius: 4px; border: none; cursor: pointer; display: flex; align-items: center; gap: 6px; }
  .info-btn { background: rgba(109, 109, 110, 0.7); color: #FFFFFF; font-weight: 700; font-size: 13px; padding: 8px 20px; border-radius: 4px; border: none; cursor: pointer; }
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

### HTML/CSS Web Component 3: Netflix Movie Poster Card Carousel with Hover Glow
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
    width: 220px; height: 130px; background: #1C1C1C; border-radius: 8px; padding: 14px;
    border: 1px solid #2B2B2B; display: flex; flex-direction: column; justify-content: space-between;
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease; cursor: pointer;
  }
  .card-wrap:hover {
    transform: translateY(-4px) scale(1.02); border-color: #E50914;
    box-shadow: 0 8px 20px rgba(229, 9, 20, 0.35);
  }
  .card-top { display: flex; justify-content: space-between; align-items: flex-start; }
  .card-title { color: #FFFFFF; font-size: 13px; font-weight: 700; line-height: 1.2; max-width: 140px; }
  .badge-score { background: #262626; color: #F5C518; font-size: 11px; font-weight: 700; padding: 2px 5px; border-radius: 4px; }
  .card-genre { color: #888888; font-size: 11px; font-weight: 500; }
  .progress-bg { width: 100%; height: 4px; background: #333333; border-radius: 2px; overflow: hidden; margin-top: 6px; }
  .progress-fill { height: 100%; width: " & _Completion & "; background: #E50914; border-radius: 2px; }
  .card-bot { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
  .stat-label { color: #AAAAAA; font-size: 10px; }
  .stat-val { color: #00D2D2; font-size: 11px; font-weight: 700; }
</style>
</head>
<body>
  <div class='card-wrap'>
    <div class='card-top'>
      <div class='card-title'>" & _Title & "</div>
      <div class='badge-score'>★ " & _Score & "</div>
    </div>
    <div class='card-genre'>" & _Genre & " • " & _Rating & "</div>
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

### HTML/CSS Web Component 4: Interactive Glassmorphic KPI Scorecard
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
    width: 100%; height: 110px; background: rgba(22, 22, 22, 0.75); backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 16px 20px;
    display: flex; flex-direction: column; justify-content: space-between; border-left: 4px solid #E50914;
  }
  .kpi-title { color: #9E9E9E; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; }
  .kpi-val { color: #FFFFFF; font-size: 26px; font-weight: 900; letter-spacing: -0.5px; }
  .kpi-sub { color: #777777; font-size: 11px; font-weight: 500; }
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

### HTML/CSS Web Component 5: Netflix "More Info" Modal Detail Pop-up (Tooltip Page)
*Design a Tooltip report page (320px x 240px) and embed this measure for a detailed Netflix movie synopsis popup.*

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
    width: 320px; height: 240px; background: #141414; border: 1px solid #333333; border-radius: 8px;
    padding: 16px; display: flex; flex-direction: column; justify-content: space-between;
    box-shadow: 0 12px 28px rgba(0,0,0,0.9);
  }
  .modal-header { border-bottom: 1px solid #262626; padding-bottom: 8px; margin-bottom: 8px; }
  .m-title { color: #FFFFFF; font-size: 16px; font-weight: 800; }
  .m-meta { color: #888888; font-size: 11px; margin-top: 2px; }
  .grid-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .stat-cell { background: #1C1C1C; padding: 6px 8px; border-radius: 4px; border-left: 2px solid #E50914; }
  .s-label { color: #888; font-size: 9px; text-transform: uppercase; font-weight: 700; }
  .s-val { color: #FFF; font-size: 12px; font-weight: 800; margin-top: 2px; }
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
    <div style='color:#555; font-size:9px; text-align:right;'>StreamPulse Semantic Galaxy Layer</div>
  </div>
</body>
</html>"
```

---

## 4. Dynamic SVG Vector Visual Measures (Data Category: Image URL)

> [!IMPORTANT]
> **Data Category Setup**: In Power BI Desktop Model View, select each measure $\to$ in the **Properties pane** set **Data Category** to **`Image URL`**. Use these inside **Table**, **Matrix**, and **New Card** visuals.

### SVG 1: Dynamic Gradient Completion Progress Bar
```dax
SVG_Completion_ProgressBar = 
VAR _Pct = [Avg_Completion_Rate_Pct]
VAR _ClampedPct = MIN(MAX(_Pct, 0), 100)
VAR _BarWidth = INT(_ClampedPct * 1.4)
VAR _Color = 
    SWITCH(
        TRUE(),
        _ClampedPct >= 80, "#00D2D2",
        _ClampedPct >= 60, "#E50914",
        "#888888"
    )
RETURN
    "data:image/svg+xml;utf8," &
    "<svg xmlns='http://www.w3.org/2000/svg' width='180' height='22' viewBox='0 0 180 22'>" &
    "<rect x='0' y='5' width='140' height='12' rx='6' fill='#242424'/>" &
    "<rect x='0' y='5' width='" & _BarWidth & "' height='12' rx='6' fill='" & _Color & "'/>" &
    "<text x='146' y='15' font-family='Segoe UI, sans-serif' font-size='11' font-weight='bold' fill='#FFFFFF'>" & 
    FORMAT(_ClampedPct, "0") & "%</text>" &
    "</svg>"
```

### SVG 2: Multi-Point Smooth Viewership Sparkline
```dax
SVG_Viewership_Sparkline = 
VAR _Hours = [Total_View_Hours_M]
VAR _P2 = INT(24 - MIN(MAX(_Hours * 0.12, 2), 20))
VAR _P3 = INT(24 - MIN(MAX(_Hours * 0.28, 4), 22))
RETURN
    "data:image/svg+xml;utf8," &
    "<svg xmlns='http://www.w3.org/2000/svg' width='120' height='28' viewBox='0 0 120 28'>" &
    "<path d='M 5 22 Q 40 " & _P2 & ", 80 " & _P3 & " T 115 4' fill='none' stroke='#E50914' stroke-width='2.5' stroke-linecap='round'/>" &
    "<circle cx='115' cy='4' r='3.5' fill='#E50914'/>" &
    "</svg>"
```

### SVG 3: Golden Rating Star Badge
```dax
SVG_Rating_Star_Badge = 
VAR _Score = [Bayesian_Weighted_Score]
VAR _FormattedScore = FORMAT(_Score, "0.0")
RETURN
    "data:image/svg+xml;utf8," &
    "<svg xmlns='http://www.w3.org/2000/svg' width='75' height='22' viewBox='0 0 75 22'>" &
    "<rect x='0' y='0' width='75' height='22' rx='4' fill='#1F1F1F' stroke='#333333' stroke-width='1'/>" &
    "<path d='M10 4l1.8 3.6 4 .6-2.9 2.8.7 4-3.6-1.9-3.6 1.9.7-4-2.9-2.8 4-.6z' fill='#F5C518'/>" &
    "<text x='23' y='15' font-family='Segoe UI, sans-serif' font-size='11' font-weight='bold' fill='#FFFFFF'>" & _FormattedScore & "</text>" &
    "</svg>"
```

### SVG 4: Financial ROI Radial Meter & Break-Even Marker
```dax
SVG_ROI_Bullet_Meter = 
VAR _ROI = [Financial_ROI_Multiplier]
VAR _Width = INT(MIN(MAX(_ROI * 28, 0), 120))
VAR _FillColor = IF(_ROI >= 2.5, "#00D2D2", IF(_ROI >= 1.0, "#E50914", "#E5A914"))
RETURN
    "data:image/svg+xml;utf8," &
    "<svg xmlns='http://www.w3.org/2000/svg' width='140' height='20' viewBox='0 0 140 20'>" &
    "<rect x='0' y='4' width='120' height='12' rx='3' fill='#2A2A2A'/>" &
    "<rect x='0' y='4' width='" & _Width & "' height='12' rx='3' fill='" & _FillColor & "'/>" &
    "<line x1='70' y1='1' x2='70' y2='19' stroke='#FFFFFF' stroke-width='2'/>" &
    "</svg>"
```

### SVG 5: Global Top 10 Red Number Rank Visual
```dax
SVG_Top10_Rank_Badge = 
VAR _Rank = SELECTEDVALUE(Fact_Streaming_Performance[performance_key], 1)
RETURN
    "data:image/svg+xml;utf8," &
    "<svg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 40 40'>" &
    "<text x='20' y='32' font-family='Segoe UI, Impact, sans-serif' font-size='36' font-weight='900' text-anchor='middle' fill='#141414' stroke='#E50914' stroke-width='2'>" & 
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

## 8. 6-Page Native Web-App Layout & Navigation Architecture

Set your page canvas to **1920 x 1080 (16:9)**. Place the `[HTML_Netflix_Navbar]` measure at $(X=0, Y=0, W=1920, H=60)$ on all pages.

### Page 0: Streaming Platform Command Center & Home Portal (Landing Page)
```
+---------------------------------------------------------------------------------------------------------------+
| [N] STREAMPULSE  [Portal Home]   Executive Pulse   Catalog Galaxy   Viewership Telemetry   ROI   Talent [LIVE]|
+---------------------------------------------------------------------------------------------------------------+
|  +---------------------------------------------------------------------------------------------------------+  |
|  | HERO HOME COMMAND BANNER (HTML/CSS Dynamic Greeting, DirectQuery Pulse, Total Catalog Vitals)           |  |
|  | "Good Evening • StreamPulse 2026 Platform" | 7,786 Titles | 1.25B Hours Streamed | 98.4% Quality Index  |  |
|  +---------------------------------------------------------------------------------------------------------+  |
|  +---------------------------------------------------------------------------------------------------------+  |
|  | LIVE REAL-TIME MARQUEE TICKER (HTML/CSS Keyframes Continuous News Ticker)                               |  |
|  | [LIVE DROPS] 🔥 Avatar: Fire & Ash 2.1B Hrs • 🔄 Airbyte 0.50.36 Active • 💰 Avengers 4 $1.2B Worldwide|  |
|  +---------------------------------------------------------------------------------------------------------+  |
|  +---------------------------------------------------------------------------------------------------------+  |
|  | INTERACTIVE 5-MODULE NAVIGATION PORTAL HUB (Hover Glow Web Route Cards)                                 |  |
|  | [🎬 Page 1: Executive] [🌌 Page 2: Catalog] [📊 Page 3: Telemetry] [💰 Page 4: ROI] [🎭 Page 5: Talent] |  |
|  +---------------------------------------------------------------------------------------------------------+  |
|  +---------------------------------------------------------------------------------------------------------+  |
|  | PLATFORM ARCHITECTURE & METADATA VITALS DRAWER (4 Glassmorphic Architecture Cards)                      |  |
|  | 1. Lakehouse Ingestion  | 2. Airbyte ELT 0.50.36 | 3. Kimball Galaxy Star | 4. Power BI DirectQuery SLA|  |
|  +---------------------------------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------------------+
```

---

### Page 1: Executive Pulse & Live Radar
```
+---------------------------------------------------------------------------------------------------------------+
| [N] STREAMPULSE   Portal Home  [Executive Pulse]  Catalog Galaxy   Viewership Telemetry   Financial ROI [LIVE]|
+---------------------------------------------------------------------------------------------------------------+
|  +-------------------------------------------------------------------+  +------------------------------------+|
|  | HERO STREAMING FEATURED PLAYER (HTML/CSS Embedded Visual)         |  | GLOBAL TOP 10 RANKINGS MATRIX      ||
|  | Avatar: Fire and Ash | 2.1B Hours | ⭐ 8.8 Bayesian | 98% Match   |  | 1. Avatar: Fire and Ash     2.1B   ||
|  | [▶ Watch Telemetry] [ⓘ Title Metrics]                             |  | 2. Stranger Things S5       1.8B   ||
|  +-------------------------------------------------------------------+  | 3. Avengers: Doomsday       1.6B   ||
|  +-------------------+  +-------------------+  +---------------------+  | 4. Wednesday Season 2       1.2B   ||
|  | GLOBAL VIEW HOURS |  | BAYESIAN QUALITY  |  | AVG COMPLETION RATE |  | 5. Squid Game Season 2      1.1B   ||
|  | 4.8B Hours (+14%) |  | 7.84 / 10.0 ⭐    |  | 74.2% [SVG Bar]     |  | 6. Dune: Part Three         950M   ||
|  +-------------------+  +-------------------+  +---------------------+  +------------------------------------+|
|  +-------------------------------------------------------------------+  +------------------------------------+|
|  | VIEWERSHIP VELOCITY TREND (Area / Line Chart with Sparkline)      |  | REGIONAL SHARE (Donut / Matrix)    ||
|  | [ Jan 2026 ===================> Feb 2026 ====================> ]  |  | USA 42% | EMEA 28% | APAC 22%       ||
|  +-------------------------------------------------------------------+  +------------------------------------+|
+---------------------------------------------------------------------------------------------------------------+
```

---

## 9. DirectQuery Performance Tuning & Production Best Practices

1. **Enable Referential Integrity**: On all 1-to-many relationships from dimensions to fact tables, check **Assume Referential Integrity** in Power BI to ensure the engine issues fast `INNER JOIN` queries instead of `OUTER JOIN`.
2. **Push Down Transformations to PostgreSQL Reporting Views**: Utilize `reporting.vw_powerbi_catalog_pulse` and `reporting.vw_powerbi_performance_matrix` to pre-aggregate heavy joins.
3. **Avoid Row-Level Calculated Columns**: Implement all calculations as DAX measures or M columns during initial data loading.

---

*Authored for the StreamPulse Enterprise Analytics Platform 2026.*
