# 📊 Power BI Analytics Engineering & Multi-Source Kimball Galaxy Masterclass

Welcome to the **StreamPulse 2026 Enterprise Analytics Engineering Guide**. This document is a comprehensive, click-by-click training masterclass that guides you through:
1. Ingesting **5 distinct unmerged raw sources** (PostgreSQL Live Staging, 5,800+ Historical Catalog CSV, External IMDb Ratings CSV, Wide Parquet Telemetry, and Production Budget JSON) into Power BI.
2. Solving **real-world data quality and cleaning challenges** in Power Query using the **M Language**.
3. Building a **Kimball Galaxy Star Schema** that unifies live 2026 releases and the historical catalog archive with multi-fact tables and many-to-many bridge dimensions.
4. Writing **25+ Enterprise DAX Measures** for streaming velocity, Bayesian quality scoring, budget ROI, and Pareto concentration.
5. Configuring **PostgreSQL DirectQuery** with 5-minute live automatic visual refresh.

---

## 🎯 High-Level Architecture & Galaxy Schema ERD

<div align="center">
  <img src="assets/streampulse_data_model.svg" alt="StreamPulse Kimball Galaxy Star Schema ERD" width="100%" />
</div>

```
[Dim_Titles] 1 <-------- * [Fact_Catalog_Ratings]        (Active, 1-to-Many, Single Direction)
[Dim_Titles] 1 <-------- * [Fact_Streaming_Performance]  (Active, 1-to-Many, Single Direction)
[Dim_Date]   1 <-------- * [Fact_Catalog_Ratings]        (Active, 1-to-Many, Single Direction)
[Dim_Date]   1 <-------- * [Fact_Streaming_Performance]  (Active, 1-to-Many, Single Direction)
[Dim_Date]   1 <-------- * [Dim_Titles] (Release_Date)   (Inactive, 1-to-Many, for USERELATIONSHIP)
[Dim_Genres] 1 <-------- * [Bridge_Title_Genre]          (Active, 1-to-Many)
[Dim_Titles] 1 <-------- * [Bridge_Title_Genre]          (Active, 1-to-Many, Both Direction)
```

---

## 📂 Step 1: Importing the 5 Distinct Sources into Power BI

Open **Power BI Desktop** $\to$ click **Get Data** for each of the following 5 independent sources (**do not merge them in python or pre-combine them**):

| # | Source Name | Connector Type | Location / Connection String | Purpose & Data Volume |
| :- | :--- | :--- | :--- | :--- |
| **1** | `stg_netflix_titles` | **PostgreSQL Database** | Server: `localhost:5432`<br>Database: `streampulse`<br>Table: `staging.stg_netflix_titles` | Live 2026/2025 scraped releases & daily Airbyte sync |
| **2** | `Raw_Historical_Archive` | **Text/CSV** | Path: `data/raw/netflix_enriched_historical.csv` | Historical benchmark catalog (5,800+ titles, 1945–2024) |
| **3** | `Raw_IMDb_Ratings` | **Text/CSV** | Path: `data/raw/imdb_external_ratings.csv` | Live periodic audience ratings snapshot |
| **4** | `Raw_Viewership_Parquet` | **Parquet** | Path: `data/raw/streaming_viewership_wide.parquet` | Granular telemetry & viewership metrics lakehouse |
| **5** | `Raw_Budget_JSON` | **JSON** | Path: `data/raw/boxoffice_budget_feed.json` | Production budget, box office, and talent feeds |

Click **Transform Data** on any source to open the **Power Query Editor**.

---

## 🧪 Step 2: Data Cleaning in Power Query (M Language)

Here is the exact M code to transform the 5 dirty sources into the **6 clean Kimball Galaxy Tables**:

---

### Table 1: `Dim_Titles` (Unified Conformed Title Dimension)
*Appends Live 2026/2025 titles (`stg_netflix_titles`) with 5,800+ historical records from `Raw_Historical_Archive`, cleans text whitespace, non-breaking spaces `\xa0`, parses heterogeneous dates, standardizes runtime minutes, and adds surrogate key `title_key`.*

```powerquery
let
    // -------------------------------------------------------------
    // Part A: Extract & Clean Live 2026/2025 Scraped Releases
    // -------------------------------------------------------------
    SourceLive = PostgreSQL.Database("localhost:5432", "streampulse"),
    stg_data = SourceLive{[Schema="staging", Item="stg_netflix_titles"]}[Data],

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
            txt = Text.Lower(Text.From([runtime_seconds])),
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
            if mins <= 0 then 90 else mins,
        Int64.Type
    ),

    CleanRatingLive = Table.TransformColumns(AddCleanRuntimeLive, {
        {"maturity_rating", each Text.Upper(Text.Trim(Text.Replace(Text.From(_), " ", "-"))), type text}
    }),

    SelectLiveCols = Table.SelectColumns(CleanRatingLive, {
        "netflix_id", "title", "title_type", "release_year", "netflix_date_added_clean", "runtime_minutes_clean", "maturity_rating"
    }),

    // -------------------------------------------------------------
    // Part B: Extract & Clean 5,800+ Historical Benchmark Records
    // -------------------------------------------------------------
    SourceHist = Csv.Document(File.Contents("D:\courses\Data Science\Data Engineering\Projects\streampulse\data\raw\netflix_enriched_historical.csv"), [Delimiter=",", Columns=15, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHeadersHist = Table.PromoteHeaders(SourceHist, [PromoteAllScalars=true]),

    ScrubHist = Table.TransformColumns(PromotedHeadersHist, {
        {"id", each Text.Trim(Text.From(_)), type text},
        {"title", each Text.Proper(Text.Trim(Text.Replace(Text.From(_), Character.FromNumber(160), " "))), type text},
        {"type", each if Text.Upper(Text.From(_)) = "MOVIE" then "Movie" else "TV Show", type text},
        {"release_year", each try Number.FromText(Text.From(_)) otherwise 2020, Int64.Type},
        {"runtime", each try Number.FromText(Text.From(_)) otherwise 90, Int64.Type},
        {"age_certification", each if _ = null or _ = "" then "TV-MA" else Text.Upper(Text.Trim(Text.From(_))), type text}
    }),

    AddCleanDateHist = Table.AddColumn(ScrubHist, "netflix_date_added_clean", each #date([release_year], 1, 1), type date),

    RenameHist = Table.RenameColumns(AddCleanDateHist, {
        {"id", "netflix_id"},
        {"type", "title_type"},
        {"runtime", "runtime_minutes_clean"},
        {"age_certification", "maturity_rating"}
    }),

    SelectHistCols = Table.SelectColumns(RenameHist, {
        "netflix_id", "title", "title_type", "release_year", "netflix_date_added_clean", "runtime_minutes_clean", "maturity_rating"
    }),

    // -------------------------------------------------------------
    // Part C: Combine Live 2026/2025 & Historical Catalog Records
    // -------------------------------------------------------------
    Combined = Table.Combine({SelectLiveCols, SelectHistCols}),
    Deduplicated = Table.Distinct(Combined, {"netflix_id"}),

    // Add Surrogate Title Key
    AddTitleKey = Table.AddIndexColumn(Deduplicated, "title_key", 1, 1, Int64.Type),

    // Add Era Segmentation
    AddEra = Table.AddColumn(AddTitleKey, "catalog_era", each
        if [release_year] = 2026 then "2026 Live Releases"
        else if [release_year] >= 2024 then "2024-2025 Modern"
        else "Historical Archive (<2024)",
        type text
    )
in
    AddEra
```

---

### Table 2: `Dim_Genres` (Standardized Genre Dimension)
```powerquery
let
    GenreList = {
        [genre_key = 1, tmdb_genre_id = 28, genre_name = "Action", genre_category = "Mainstream"],
        [genre_key = 2, tmdb_genre_id = 12, genre_name = "Adventure", genre_category = "Mainstream"],
        [genre_key = 3, tmdb_genre_id = 16, genre_name = "Animation", genre_category = "Family & Youth"],
        [genre_key = 4, tmdb_genre_id = 35, genre_name = "Comedy", genre_category = "Mainstream"],
        [genre_key = 5, tmdb_genre_id = 80, genre_name = "Crime", genre_category = "Prestige Drama"],
        [genre_key = 6, tmdb_genre_id = 99, genre_name = "Documentary", genre_category = "Prestige & Non-Fiction"],
        [genre_key = 7, tmdb_genre_id = 18, genre_name = "Drama", genre_category = "Prestige Drama"],
        [genre_key = 8, tmdb_genre_id = 10751, genre_name = "Family", genre_category = "Family & Youth"],
        [genre_key = 9, tmdb_genre_id = 14, genre_name = "Fantasy", genre_category = "Genre & Sci-Fi"],
        [genre_key = 10, tmdb_genre_id = 27, genre_name = "Horror", genre_category = "Genre & Sci-Fi"],
        [genre_key = 11, tmdb_genre_id = 878, genre_name = "Science Fiction", genre_category = "Genre & Sci-Fi"],
        [genre_key = 12, tmdb_genre_id = 53, genre_name = "Thriller", genre_category = "Prestige Drama"],
        [genre_key = 13, tmdb_genre_id = 10749, genre_name = "Romance", genre_category = "Mainstream"]
    },
    TableFromRecords = Table.FromRecords(GenreList),
    TypedTable = Table.TransformColumnTypes(TableFromRecords, {
        {"genre_key", Int64.Type}, {"tmdb_genre_id", Int64.Type}, {"genre_name", type text}, {"genre_category", type text}
    })
in
    TypedTable
```

---

### Table 3: `Bridge_Title_Genre` (Many-to-Many Multi-Genre Bridge)
*Maps multiple genres per title from both `Raw_Budget_JSON` and `Raw_Historical_Archive`.*

```powerquery
let
    // 1. JSON Source Genres
    SourceJSON = Json.Document(File.Contents("D:\courses\Data Science\Data Engineering\Projects\streampulse\data\raw\boxoffice_budget_feed.json")),
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
    CleanGenreNameJSON = Table.TransformColumns(ExpandedRowsJSON, {
        {"Genre_List", each Text.Trim(Text.From(_)), type text}
    }),
    SelectJSONBridge = Table.SelectColumns(CleanGenreNameJSON, {"netflix_id", "Genre_List"}),

    // 2. Historical CSV Source Genres
    SourceHist = Csv.Document(File.Contents("D:\courses\Data Science\Data Engineering\Projects\streampulse\data\raw\netflix_enriched_historical.csv"), [Delimiter=",", Columns=15, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHist = Table.PromoteHeaders(SourceHist, [PromoteAllScalars=true]),
    CleanHistGenres = Table.AddColumn(PromotedHist, "Genre_List", each
        let
            raw = Text.Replace(Text.Replace(Text.Replace(Text.From([genres]), "[", ""), "]", ""), "'", ""),
            items = Text.Split(raw, ",")
        in
            List.Transform(items, each Text.Proper(Text.Trim(_))),
        type list
    ),
    ExpandedHistRows = Table.ExpandListColumn(CleanHistGenres, "Genre_List"),
    RenameHistBridge = Table.RenameColumns(ExpandedHistRows, {{"id", "netflix_id"}}),
    SelectHistBridge = Table.SelectColumns(RenameHistBridge, {"netflix_id", "Genre_List"}),

    // 3. Combine Bridges
    CombinedBridges = Table.Combine({SelectJSONBridge, SelectHistBridge}),
    FilteredEmpty = Table.SelectRows(CombinedBridges, each [Genre_List] <> "" and [Genre_List] <> null),

    // 4. Map surrogate keys
    MergedTitles = Table.NestedJoin(FilteredEmpty, {"netflix_id"}, Dim_Titles, {"netflix_id"}, "Dim_Titles", JoinKind.Inner),
    ExpandedTitleKey = Table.ExpandTableColumn(MergedTitles, "Dim_Titles", {"title_key"}, {"title_key"}),

    MergedGenres = Table.NestedJoin(ExpandedTitleKey, {"Genre_List"}, Dim_Genres, {"genre_name"}, "Dim_Genres", JoinKind.Inner),
    ExpandedGenreKey = Table.ExpandTableColumn(MergedGenres, "Dim_Genres", {"genre_key"}, {"genre_key"}),

    SelectFinal = Table.SelectColumns(ExpandedGenreKey, {"title_key", "genre_key"}),
    AddWeight = Table.AddColumn(SelectFinal, "genre_weight", each 1.0, type number),
    Deduplicated = Table.Distinct(AddWeight)
in
    Deduplicated
```

---

### Table 4: `Dim_Date` (Dynamic Dataset-Driven Calendar Dimension)
*Paste this dynamic M script into a **Blank Query** named `Dim_Date`. It automatically detects the earliest historical year (e.g. 1945) up to current/future release years (2026/2027).*

```powerquery
let
    // 1. Dynamically fetch all dates from Dim_Titles
    DatasetDates = List.RemoveNulls(Dim_Titles[netflix_date_added_clean]),

    // 2. Compute dynamic Min and Max dates with fallback defaults
    MinDateRaw = if List.IsEmpty(DatasetDates) then #date(2020, 1, 1) else List.Min(DatasetDates),
    MaxDateRaw = if List.IsEmpty(DatasetDates) then #date(2026, 12, 31) else List.Max(DatasetDates),
    CurrentDate = DateTime.Date(DateTime.LocalNow()),

    // 3. Expand boundaries to full calendar years
    StartYear = Date.Year(MinDateRaw),
    EndYear = Date.Year(List.Max({MaxDateRaw, CurrentDate})),
    StartDate = #date(StartYear, 1, 1),
    EndDate = #date(EndYear, 12, 31),

    // 4. Generate continuous daily dates list
    NumberOfDays = Duration.Days(EndDate - StartDate) + 1,
    DateList = List.Dates(StartDate, NumberOfDays, #duration(1, 0, 0, 0)),
    DateTable = Table.FromList(DateList, Splitter.SplitByNothing(), {"full_date"}, null, ExtraValues.Error),
    TypedDate = Table.TransformColumnTypes(DateTable, {{"full_date", type date}}),

    // 5. Standard Calendar Attributes
    AddDateKey = Table.AddColumn(TypedDate, "date_key", each Date.Year([full_date]) * 10000 + Date.Month([full_date]) * 100 + Date.Day([full_date]), Int64.Type),
    AddYear = Table.AddColumn(AddDateKey, "year", each Date.Year([full_date]), Int64.Type),
    AddQuarter = Table.AddColumn(AddYear, "quarter", each Date.QuarterOfYear([full_date]), Int64.Type),
    AddQuarterName = Table.AddColumn(AddQuarter, "quarter_name", each "Q" & Text.From([quarter]) & " " & Text.From([year]), type text),
    AddMonthNum = Table.AddColumn(AddQuarterName, "month_number", each Date.Month([full_date]), Int64.Type),
    AddMonthName = Table.AddColumn(AddMonthNum, "month_name", each Date.MonthName([full_date]), type text),
    AddMonthShort = Table.AddColumn(AddMonthName, "month_short", each Text.Start([month_name], 3), type text),
    AddDayOfWeek = Table.AddColumn(AddMonthShort, "day_of_week", each Date.DayOfWeek([full_date], Day.Monday) + 1, Int64.Type),
    AddDayName = Table.AddColumn(AddDayOfWeek, "day_name", each Date.DayOfWeekName([full_date]), type text),
    AddIsWeekend = Table.AddColumn(AddDayName, "is_weekend", each if [day_of_week] >= 6 then true else false, type logical),
    AddFiscalPeriod = Table.AddColumn(AddIsWeekend, "fiscal_period", each "FY" & Text.From([year]) & "-Q" & Text.From([quarter]), type text),

    // 6. Dynamic Streaming & Time-Intelligence Offsets
    AddIsCurrentYear = Table.AddColumn(AddFiscalPeriod, "is_current_year", each Date.Year([full_date]) = Date.Year(CurrentDate), type logical),
    AddIsPastOrCurrent = Table.AddColumn(AddIsCurrentYear, "is_past_or_current", each [full_date] <= CurrentDate, type logical),
    AddYearOffset = Table.AddColumn(AddIsPastOrCurrent, "relative_year_offset", each Date.Year([full_date]) - Date.Year(CurrentDate), Int64.Type),
    AddMonthOffset = Table.AddColumn(AddYearOffset, "relative_month_offset", each 
        ((Date.Year([full_date]) - Date.Year(CurrentDate)) * 12) + (Date.Month([full_date]) - Date.Month(CurrentDate)),
        Int64.Type
    ),
    AddNetflixQuarterEnd = Table.AddColumn(AddMonthOffset, "is_netflix_quarter_end", each 
        (Date.Month([full_date]) = 3 and Date.Day([full_date]) = 31) or
        (Date.Month([full_date]) = 6 and Date.Day([full_date]) = 30) or
        (Date.Month([full_date]) = 9 and Date.Day([full_date]) = 30) or
        (Date.Month([full_date]) = 12 and Date.Day([full_date]) = 31),
        type logical
    )
in
    AddNetflixQuarterEnd
```

---

### Table 5: `Fact_Catalog_Ratings` (Unified Ratings Snapshot Fact)
*Combines live rating snapshots from `Raw_IMDb_Ratings` and historical ratings from `Raw_Historical_Archive`.*

```powerquery
let
    // -------------------------------------------------------------
    // Part A: Live Snapshot Ratings (from Raw_IMDb_Ratings)
    // -------------------------------------------------------------
    SourceLive = Raw_IMDb_Ratings,

    ParseLiveVotes = Table.AddColumn(SourceLive, "vote_count_clean", each
        let
            v = Text.Upper(Text.Trim(Text.From([vote_count_raw]))),
            num = if Text.EndsWith(v, "M") then
                      Number.FromText(Text.Remove(v, "M")) * 1000000
                  else if Text.EndsWith(v, "K") then
                      Number.FromText(Text.Remove(v, "K")) * 1000
                  else
                      try Number.FromText(Text.Replace(v, ",", "")) otherwise 0
        in
            Int64.From(num),
        Int64.Type
    ),

    ParseLiveScore = Table.AddColumn(ParseLiveVotes, "vote_average_clean", each
        let
            raw = Text.Trim(Text.From([user_score])),
            score = if Text.Contains(raw, "/10") then
                        Number.FromText(Text.BeforeDelimiter(raw, "/10"))
                    else if Text.EndsWith(raw, "%") then
                        Number.FromText(Text.Remove(raw, "%")) / 10.0
                    else
                        try Number.FromText(raw) otherwise 7.0
        in
            if score > 10.0 then 10.0 else if score < 0.0 then 0.0 else Number.Round(score, 1),
        type number
    ),

    SortedLive = Table.Sort(ParseLiveScore, {{"title_id", Order.Ascending}, {"snapshot_timestamp", Order.Descending}}),
    DeduplicatedLive = Table.Distinct(SortedLive, {"title_id"}),

    AddLiveDateKey = Table.AddColumn(DeduplicatedLive, "date_key", each
        let
            d = try Date.From(DateTimeZone.From([snapshot_timestamp])) otherwise #date(2026, 2, 1)
        in
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

    // -------------------------------------------------------------
    // Part B: Historical Ratings (from Raw_Historical_Archive)
    // -------------------------------------------------------------
    SourceHist = Csv.Document(File.Contents("D:\courses\Data Science\Data Engineering\Projects\streampulse\data\raw\netflix_enriched_historical.csv"), [Delimiter=",", Columns=15, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    PromotedHist = Table.PromoteHeaders(SourceHist, [PromoteAllScalars=true]),

    AddHistDateKey = Table.AddColumn(PromotedHist, "date_key", each
        let
            y = try Number.FromText(Text.From([release_year])) otherwise 2020
        in
            y * 10000 + 101,
        Int64.Type
    ),

    CleanHistRatings = Table.AddColumn(AddHistDateKey, "vote_average", each try Number.FromText(Text.From([imdb_score])) otherwise 7.0, type number),
    CleanHistVotes = Table.AddColumn(CleanHistRatings, "vote_count", each try Int64.From(Number.FromText(Text.From([imdb_votes]))) otherwise 1000, Int64.Type),
    CleanHistMetascore = Table.AddColumn(CleanHistVotes, "critic_score", each try Number.FromText(Text.From([tmdb_score])) * 10 otherwise 70, type number),

    RenameHistFact = Table.RenameColumns(CleanHistMetascore, {{"id", "netflix_id"}}),
    SelectHistFact = Table.SelectColumns(RenameHistFact, {
        "netflix_id", "date_key", "vote_average", "vote_count", "critic_score"
    }),

    // -------------------------------------------------------------
    // Part C: Combine & Map Surrogate Title Key
    // -------------------------------------------------------------
    CombinedFacts = Table.Combine({SelectLiveFact, SelectHistFact}),
    MergedTitles = Table.NestedJoin(CombinedFacts, {"netflix_id"}, Dim_Titles, {"netflix_id"}, "Dim_Titles", JoinKind.Inner),
    ExpandedTitleKey = Table.ExpandTableColumn(MergedTitles, "Dim_Titles", {"title_key"}, {"title_key"}),

    FinalFact = Table.SelectColumns(ExpandedTitleKey, {
        "title_key", "date_key", "vote_average", "vote_count", "critic_score"
    })
in
    FinalFact
```

---

### Table 6: `Fact_Streaming_Performance` (Granular Telemetry Fact)
*Cleaned and unpivoted from `Raw_Viewership_Parquet`.*

```powerquery
let
    Source = Raw_Viewership_Parquet,

    // 1. Unpivot Monthly Columns to Rows
    Unpivoted = Table.Unpivot(Source, {"Hours_2026_01", "Hours_2026_02", "Hours_2026_03"}, "Month_Col", "global_view_hours_millions"),

    // 2. Replace Sentinel Negative Values (-999, -1) with 0.0
    CleanHours = Table.TransformColumns(Unpivoted, {
        {"global_view_hours_millions", each if _ < 0 then 0.0 else _, type number}
    }),

    // 3. Extract Clean Date Key (e.g. "Hours_2026_01" -> 20260101)
    AddDateKey = Table.AddColumn(CleanHours, "date_key", each
        let
            m_str = Text.AfterDelimiter([Month_Col], "Hours_"),
            y = Number.FromText(Text.Start(m_str, 4)),
            m = Number.FromText(Text.End(m_str, 2))
        in
            y * 10000 + m * 100 + 1,
        Int64.Type
    ),

    // 4. Standardize Country Names
    StandardizeCountry = Table.AddColumn(AddDateKey, "territory_standardized", each
        let
            c = Text.Upper(Text.Trim(Text.From([territory_region])))
        in
            if c = "USA" or c = "US" or c = "UNITED STATES" or c = "U.S.A." then "United States"
            else if c = "UK" or c = "GBR" or c = "GREAT BRITAIN" then "United Kingdom"
            else if c = "KOR" or c = "SOUTH KOREA" then "South Korea"
            else if c = "JPN" or c = "JAPAN" then "Japan"
            else "Global",
        type text
    ),

    // 5. Map surrogate title_key
    MergedTitles = Table.NestedJoin(StandardizeCountry, {"catalog_ref_id"}, Dim_Titles, {"netflix_id"}, "Dim_Titles", JoinKind.Inner),
    ExpandedTitleKey = Table.ExpandTableColumn(MergedTitles, "Dim_Titles", {"title_key"}, {"title_key"}),

    // 6. Select Fact Columns
    SelectFact = Table.SelectColumns(ExpandedTitleKey, {
        "title_key", "date_key", "territory_standardized", "device_category",
        "global_view_hours_millions", "avg_completion_pct", "subscribers_reached_thousands"
    }),
    AddSurrogateFactKey = Table.AddIndexColumn(SelectFact, "performance_key", 1, 1, Int64.Type)
in
    AddSurrogateFactKey
```

---

## 🏛️ Step 3: Configure Model View Relationships in Power BI

1. In Power Query Editor $\to$ Click **Close & Apply**.
2. Switch to **Model View** (the 3rd icon on the left navigation bar).
3. Connect the relationships as follows:

| From Dimension | Column | To Fact / Bridge | Column | Cardinality | Filter Direction | State |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `Dim_Titles` | `title_key` | `Fact_Catalog_Ratings` | `title_key` | `1 : *` (One-to-Many) | Single | **Active** |
| `Dim_Titles` | `title_key` | `Fact_Streaming_Performance` | `title_key` | `1 : *` (One-to-Many) | Single | **Active** |
| `Dim_Date` | `date_key` | `Fact_Catalog_Ratings` | `date_key` | `1 : *` (One-to-Many) | Single | **Active** |
| `Dim_Date` | `date_key` | `Fact_Streaming_Performance` | `date_key` | `1 : *` (One-to-Many) | Single | **Active** |
| `Dim_Genres` | `genre_key` | `Bridge_Title_Genre` | `genre_key` | `1 : *` (One-to-Many) | Single | **Active** |
| `Dim_Titles` | `title_key` | `Bridge_Title_Genre` | `title_key` | `1 : *` (One-to-Many) | **Both** | **Active** |
| `Dim_Date` | `full_date` | `Dim_Titles` | `netflix_date_added_clean` | `1 : *` (One-to-Many) | Single | *Inactive* (for `USERELATIONSHIP`) |

---

## 🧮 Step 4: Key DAX Measures to Add

Create a dedicated `_Measures` table (Click **Enter Data** $\to$ Name table `_Measures` $\to$ Click **Load**). Add these core measures:

```dax
// 1. Total Global View Hours (Millions)
Total Global View Hours = 
SUM(Fact_Streaming_Performance[global_view_hours_millions])

// 2. Average Audience Completion Rate %
Avg Completion Rate % = 
AVERAGE(Fact_Streaming_Performance[avg_completion_pct]) / 100

// 3. Bayesian Weighted Rating (Solves Small Sample Bias across 5,800+ Catalog Titles)
Bayesian Weighted Rating = 
VAR TitleVotes = SUM(Fact_Catalog_Ratings[vote_count])
VAR TitleAvg = AVERAGE(Fact_Catalog_Ratings[vote_average])
VAR CatalogAvg = CALCULATE(AVERAGE(Fact_Catalog_Ratings[vote_average]), ALL(Fact_Catalog_Ratings))
VAR M_Threshold = 500
RETURN
IF(
    TitleVotes > 0,
    DIVIDE(TitleVotes, TitleVotes + M_Threshold) * TitleAvg + 
    DIVIDE(M_Threshold, TitleVotes + M_Threshold) * CatalogAvg,
    CatalogAvg
)

// 4. Pareto 80/20 Concentration Flag
Cumulative Viewership Share % = 
VAR CurrentHours = [Total Global View Hours]
VAR AllHours = CALCULATE([Total Global View Hours], ALLSELECTED(Dim_Titles))
VAR HigherRankingHours = 
    CALCULATE(
        [Total Global View Hours],
        FILTER(
            ALLSELECTED(Dim_Titles),
            [Total Global View Hours] >= CurrentHours
        )
    )
RETURN
DIVIDE(HigherRankingHours, AllHours, 0)

Is Pareto Driver = 
IF([Cumulative Viewership Share %] <= 0.80, "Core Driver (Top 80% Hours)", "Long-Tail Catalog")
```

---

## 🔄 Step 5: Live DirectQuery Auto-Refresh Setup

If using DirectQuery against PostgreSQL:
1. Select the blank report canvas.
2. In the right-hand **Format visual** pane $\to$ Select **Page refresh**.
3. Toggle **Page refresh** to **ON** and set interval to **5 Minutes**.
4. Power BI will execute live DirectQuery SQL queries against your warehouse to stream real-time updates!
