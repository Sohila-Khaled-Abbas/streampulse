# 📊 Power BI Analytics Engineering & Multi-Source Kimball Galaxy Masterclass

Welcome to the **StreamPulse 2026 Enterprise Analytics Engineering Guide**. This document is a comprehensive, click-by-click training masterclass that guides you through:
1. Ingesting **4 distinct unmerged raw sources** (PostgreSQL, CSV, Parquet, JSON) into Power BI.
2. Solving **real-world data quality and cleaning challenges** in Power Query using the **M Language**.
3. Building a **Kimball Galaxy Star Schema** with multi-fact tables and many-to-many bridge dimensions.
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

## 📂 Step 1: Importing the 4 Distinct Sources into Power BI

Open **Power BI Desktop** $\to$ click **Get Data** for each of the following 4 independent sources (**do not merge them in python or pre-combine them**):

### Source 1: PostgreSQL Live Staging
1. Click **Get Data** $\to$ **PostgreSQL database** $\to$ **Connect**.
2. **Server**: `localhost:5432` | **Database**: `streampulse`.
3. **Data Connectivity mode**: Choose **Import** (or **DirectQuery** if testing real-time SQL execution).
4. Navigator: Select `staging.stg_netflix_titles` $\to$ click **Transform Data** (opens Power Query Editor).

---

### Source 2: External IMDb Ratings Flat File
1. In Power Query Editor $\to$ Click **New Source** $\to$ **Text/CSV**.
2. Browse to: `D:\courses\Data Science\Data Engineering\Projects\streampulse\data\raw\imdb_external_ratings.csv`.
3. Click **OK** $\to$ Rename query in left sidebar to: `Raw_IMDb_Ratings`.

---

### Source 3: Wide Parquet Telemetry Lakehouse
1. In Power Query Editor $\to$ Click **New Source** $\to$ **Parquet**.
2. Browse to: `D:\courses\Data Science\Data Engineering\Projects\streampulse\data\raw\streaming_viewership_wide.parquet`.
3. Click **OK** $\to$ Rename query in left sidebar to: `Raw_Viewership_Parquet`.

---

### Source 4: Production Budget & Box Office JSON Feed
1. In Power Query Editor $\to$ Click **New Source** $\to$ **JSON**.
2. Browse to: `D:\courses\Data Science\Data Engineering\Projects\streampulse\data\raw\boxoffice_budget_feed.json`.
3. Click **OK** $\to$ Rename query in left sidebar to: `Raw_Budget_JSON`.

---

## 🧪 Step 2: Data Cleaning in Power Query (M Language)

Here is the exact M code to transform the 4 dirty sources into the **6 clean Kimball Galaxy Tables**:

---

### Table 1: `Dim_Titles` (Conformed Title Dimension)
*Extracted and cleaned from `stg_netflix_titles` + `Raw_Budget_JSON`.*

```powerquery
let
    Source = PostgreSQL.Database("localhost:5432", "streampulse"),
    stg_data = Source{[Schema="staging", Item="stg_netflix_titles"]}[Data],

    // 1. Text scrubbing: Strip leading/trailing whitespace & non-breaking spaces (\xa0)
    ScrubText = Table.TransformColumns(stg_data, {
        {"title", each Text.Proper(Text.Trim(Text.Replace(Text.From(_), Character.FromNumber(160), " "))), type text},
        {"netflix_id", each Text.Trim(Text.From(_)), type text}
    }),

    // 2. Parse heterogeneous date strings with resilient try/otherwise ladder
    AddCleanDate = Table.AddColumn(ScrubText, "netflix_date_added_clean", each
        try Date.From(DateTimeZone.From([date_added]))
        otherwise try Date.FromText([date_added], "en-US")
        otherwise try Date.FromText([date_added], "en-GB")
        otherwise #date(2026, 1, 1),
        type date
    ),

    // 3. Normalize runtime string text into clean integer minutes
    AddCleanRuntime = Table.AddColumn(AddCleanDate, "runtime_minutes_clean", each
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

    // 4. Standardize Maturity Rating
    CleanRating = Table.TransformColumns(AddCleanRuntime, {
        {"maturity_rating", each Text.Upper(Text.Trim(Text.Replace(Text.From(_), " ", "-"))), type text}
    }),

    // 5. Add Surrogate Title Key
    AddTitleKey = Table.AddIndexColumn(CleanRating, "title_key", 1, 1, Int64.Type),

    // 6. Add Catalog Era Segmentation
    AddEra = Table.AddColumn(AddTitleKey, "catalog_era", each
        if [release_year] = 2026 then "2026 Live Releases"
        else if [release_year] >= 2024 then "2024-2025 Modern"
        else "Historical Archive (<2024)",
        type text
    ),

    // 7. Select & Reorder Final Dimension Columns
    SelectCols = Table.SelectColumns(AddEra, {
        "title_key", "netflix_id", "title", "title_type", "release_year",
        "netflix_date_added_clean", "runtime_minutes_clean", "maturity_rating", "catalog_era"
    })
in
    SelectCols
```

---

### Table 2: `Dim_Genres` (Standardized Genre Dimension)
```powerquery
let
    // Create static conformed genre dimension table
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
*Extracted from `Raw_Budget_JSON` by expanding pipe strings (`"Action|Sci-Fi"`) and nested arrays.*

```powerquery
let
    Source = Json.Document(File.Contents("D:\courses\Data Science\Data Engineering\Projects\streampulse\data\raw\boxoffice_budget_feed.json")),
    Data = Source[data],
    ConvertedToTable = Table.FromList(Data, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    ExpandedRecord = Table.ExpandRecordColumn(ConvertedToTable, "Column1", {"stream_id", "categorization"}, {"netflix_id", "categorization"}),
    ExpandedCat = Table.ExpandRecordColumn(ExpandedRecord, "categorization", {"genres"}, {"genres_raw"}),

    // 1. Convert pipe-delimited string or list into standardized list
    AddList = Table.AddColumn(ExpandedCat, "Genre_List", each
        if Value.Is([genres_raw], type list) then [genres_raw]
        else Text.Split(Text.From([genres_raw]), "|"),
        type list
    ),

    // 2. Expand list to multiple rows
    ExpandedRows = Table.ExpandListColumn(AddList, "Genre_List"),
    CleanGenreName = Table.TransformColumns(ExpandedRows, {
        {"Genre_List", each Text.Trim(Text.From(_)), type text}
    }),

    // 3. Join with Dim_Titles to retrieve surrogate title_key
    MergedTitles = Table.NestedJoin(CleanGenreName, {"netflix_id"}, Dim_Titles, {"netflix_id"}, "Dim_Titles", JoinKind.Inner),
    ExpandedTitleKey = Table.ExpandTableColumn(MergedTitles, "Dim_Titles", {"title_key"}, {"title_key"}),

    // 4. Join with Dim_Genres to retrieve surrogate genre_key
    MergedGenres = Table.NestedJoin(ExpandedTitleKey, {"Genre_List"}, Dim_Genres, {"genre_name"}, "Dim_Genres", JoinKind.Inner),
    ExpandedGenreKey = Table.ExpandTableColumn(MergedGenres, "Dim_Genres", {"genre_key"}, {"genre_key"}),

    // 5. Select Final Bridge Columns & Add Weight
    SelectBridge = Table.SelectColumns(ExpandedGenreKey, {"title_key", "genre_key"}),
    AddWeight = Table.AddColumn(SelectBridge, "genre_weight", each 1.0, type number),
    Deduplicated = Table.Distinct(AddWeight)
in
    Deduplicated
```

---

### Table 4: `Dim_Date` (Fully Dynamic Dataset-Driven Calendar Dimension)
*Paste this dynamic M script into a **Blank Query** named `Dim_Date`. It automatically reads the minimum and maximum dates from `Dim_Titles` and generates a contiguous calendar covering full fiscal years.*

```powerquery
let
    // 1. Dynamically fetch all date values from the Dim_Titles dimension
    DatasetDates = List.RemoveNulls(Dim_Titles[netflix_date_added_clean]),

    // 2. Compute dynamic Min and Max dates with fallback defaults
    MinDateRaw = if List.IsEmpty(DatasetDates) then #date(2020, 1, 1) else List.Min(DatasetDates),
    MaxDateRaw = if List.IsEmpty(DatasetDates) then #date(2026, 12, 31) else List.Max(DatasetDates),
    CurrentDate = DateTime.Date(DateTime.LocalNow()),

    // 3. Expand boundaries to full calendar years (Jan 1 of earliest year to Dec 31 of latest year / current year)
    StartYear = Date.Year(MinDateRaw),
    EndYear = Date.Year(List.Max({MaxDateRaw, CurrentDate})),
    StartDate = #date(StartYear, 1, 1),
    EndDate = #date(EndYear, 12, 31),

    // 4. Generate continuous daily dates list
    NumberOfDays = Duration.Days(EndDate - StartDate) + 1,
    DateList = List.Dates(StartDate, NumberOfDays, #duration(1, 0, 0, 0)),
    DateTable = Table.FromList(DateList, Splitter.SplitByNothing(), {"full_date"}, null, ExtraValues.Error),
    TypedDate = Table.TransformColumnTypes(DateTable, {{"full_date", type date}}),

    // 5. Build standard date attributes
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

    // 6. Dynamic streaming and relative offsets
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

### Table 5: `Fact_Catalog_Ratings` (Periodic Snapshot Ratings Fact)
*Cleaned from `Raw_IMDb_Ratings`.*

```powerquery
let
    Source = Raw_IMDb_Ratings,

    // 1. Clean shorthand votes ("1.4M" -> 1400000, "850K" -> 850000)
    ParseVotes = Table.AddColumn(Source, "vote_count_clean", each
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

    // 2. Normalize user score (0.0 - 10.0 scale)
    ParseScore = Table.AddColumn(ParseVotes, "vote_average_clean", each
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

    // 3. Deduplicate: Keep latest snapshot row per title
    Sorted = Table.Sort(ParseScore, {{"title_id", Order.Ascending}, {"snapshot_timestamp", Order.Descending}}),
    Deduplicated = Table.Distinct(Sorted, {"title_id"}),

    // 4. Join with Dim_Titles to map surrogate title_key
    MergedTitles = Table.NestedJoin(Deduplicated, {"title_id"}, Dim_Titles, {"netflix_id"}, "Dim_Titles", JoinKind.Inner),
    ExpandedTitleKey = Table.ExpandTableColumn(MergedTitles, "Dim_Titles", {"title_key"}, {"title_key"}),

    // 5. Add Date Key (Snapshot Date Key)
    AddDateKey = Table.AddColumn(ExpandedTitleKey, "date_key", each
        let
            d = try Date.From(DateTimeZone.From([snapshot_timestamp])) otherwise #date(2026, 2, 1)
        in
            Date.Year(d) * 10000 + Date.Month(d) * 100 + Date.Day(d),
        Int64.Type
    ),

    // 6. Select Fact Columns
    SelectFactCols = Table.SelectColumns(AddDateKey, {
        "title_key", "date_key", "vote_average_clean", "vote_count_clean", "critic_metascore"
    }),
    RenameCols = Table.RenameColumns(SelectFactCols, {
        {"vote_average_clean", "vote_average"},
        {"vote_count_clean", "vote_count"},
        {"critic_metascore", "critic_score"}
    })
in
    RenameCols
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

    // 3. Extract Clean Date Key (e.g., "Hours_2026_01" -> 20260101)
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

    // 5. Join with Dim_Titles to map surrogate title_key
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

## 🏛️ Step 3: Configuring Model View Relationships

Click **Close & Apply** in Power Query Editor $\to$ switch to **Model View** in Power BI Desktop. Configure the relationships exactly as listed below:

| From Table | Column | To Table | Column | Cardinality | Cross Filter | State |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `Dim_Titles` | `title_key` | `Fact_Catalog_Ratings` | `title_key` | `1 : *` (One-to-Many) | Single | **Active** |
| `Dim_Titles` | `title_key` | `Fact_Streaming_Performance` | `title_key` | `1 : *` (One-to-Many) | Single | **Active** |
| `Dim_Date` | `date_key` | `Fact_Catalog_Ratings` | `date_key` | `1 : *` (One-to-Many) | Single | **Active** |
| `Dim_Date` | `date_key` | `Fact_Streaming_Performance` | `date_key` | `1 : *` (One-to-Many) | Single | **Active** |
| `Dim_Genres` | `genre_key` | `Bridge_Title_Genre` | `genre_key` | `1 : *` (One-to-Many) | Single | **Active** |
| `Dim_Titles` | `title_key` | `Bridge_Title_Genre` | `title_key` | `1 : *` (One-to-Many) | **Both** | **Active** |
| `Dim_Date` | `full_date` | `Dim_Titles` | `netflix_date_added_clean` | `1 : *` (One-to-Many) | Single | *Inactive* (for `USERELATIONSHIP`) |

---

## 🧮 Step 4: Writing Enterprise DAX Measures

Create a dedicated `_Measures` table (Click **Enter Data** $\to$ Name table `_Measures` $\to$ Click **Load**). Add the following production measures:

### 1. Viewership & Quality Measures
```dax
// 1. Total Global View Hours (Millions)
Total Global View Hours = 
SUM(Fact_Streaming_Performance[global_view_hours_millions])

// 2. Average Audience Completion Rate %
Avg Completion Rate % = 
AVERAGE(Fact_Streaming_Performance[avg_completion_pct]) / 100

// 3. Bayesian Weighted Rating (Solves Small Sample Bias)
// Formula: (v / (v + m)) * R + (m / (v + m)) * C
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
```

---

### 2. Financial ROI & Budget Measures
```dax
// 4. Total Production Budget ($M)
Total Budget ($M) = 
COUNTROWS(Dim_Titles) * 35.0  // Default $35M baseline per original

// 5. Effective Cost Per View Hour ($/Hour)
Cost Per View Hour = 
DIVIDE(
    [Total Budget ($M)] * 1000000,
    [Total Global View Hours] * 1000000,
    0
)

// 6. Budget Efficiency Multiplier
Budget Efficiency Ratio = 
DIVIDE(
    [Total Global View Hours],
    [Total Budget ($M)],
    0
)
```

---

### 3. Pareto 80/20 & Time Intelligence Measures
```dax
// 7. Cumulative Viewership Share %
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

// 8. Pareto Driver Flag
Is Pareto Driver = 
IF([Cumulative Viewership Share %] <= 0.80, "Core Driver (Top 80% Hours)", "Long-Tail Catalog")

// 9. YTD View Hours (Time Intelligence)
YTD View Hours = 
CALCULATE(
    [Total Global View Hours],
    DATESYTD(Dim_Date[full_date])
)
```

---

## ⚡ Step 5: Power BI DirectQuery Live Auto-Refresh

If using the **PostgreSQL DirectQuery** connection mode on `reporting.vw_powerbi_catalog_pulse`:
1. Click the blank canvas area on your report page.
2. In the right-hand **Format visual** pane $\to$ Select **Page refresh**.
3. Toggle **Page refresh** to **ON**.
4. Set **Refresh interval**: `5 Minutes` (or `1 Minute`).
5. **Outcome**: Every time the daily Airbyte scraper ELT runs and inserts new 2026 streaming drops, the visuals refresh on your screen in real time!
