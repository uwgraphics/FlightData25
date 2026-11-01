# Flight Data for CS765

This repository contains flight delay data for use in CS765 assignments.
It was made for the Fall 2025 class, and fixed up for Fall 2026 (see
[Versions](#versions)).

See [the course web flight data page](https://pages.graphics.cs.wisc.edu/765-25/posts/flight-data) for an explanation.
(That page describes the 2025 version, as students used it.)

The data comes from the Bureau of Transportation Statistics
[On-Time Performance data](https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr),
which documents each field. Each row is one domestic flight.

## Files

- `OriginalData/` - the data as downloaded from BTS, one file per month:
  January, April, July and October 2024 (the first month of each quarter).
- `ReducedData/` - the "simplified" data for each month, and
  `combined-reduced.csv`, all 4 months together (about 927K flights).
- `Lookups/` - what the codes mean (new in 2026):
  - `airports.csv` - every airport in the original data (345): name, city,
    state, latitude/longitude, UTC offset, number of flights (departures +
    arrivals over the 4 original months), rank by flights, and whether it is
    in the reduced data.
  - `carriers.csv` - each airline code, its name, and its number of flights.
- `scripts/reduce_to_reduced.py` - makes `ReducedData/` from `OriginalData/`.
- `scripts/make_lookups.py` - makes `Lookups/` from BTS tables (the raw
  downloads are in `OriginalData/lookups/`; the script says where they came
  from).

## How the data was reduced

The reduced data keeps:

- **Only the even-numbered days 2 through 28 of each month** (14 days). This
  keeps the files small, and every month has the same number of days and 2
  of each day of the week.
- **Only flights between the top 105 airports** (both the origin and the
  destination must be in the list). Airports are ranked by flights
  (departures + arrivals) over all 4 months; the 105th has 6,176. We picked
  105 so that MSN (Madison) is always included - it ranks 98th. The ranks are
  in `Lookups/airports.csv`.

This removes about 60% of the flights (2.38 million down to 927K).

Consequences of the day filter:

- A "month" is 14 days, so counts (per month, per route, per airport) are
  about half the real monthly numbers.
- A day-by-day series has every other day missing. Events on odd days are
  not in the data, only their effects. For example, the CrowdStrike outage
  on Friday July 19, 2024 is missing, but the cancellations from the
  aftermath (Delta took days to recover) show up on the 20th and 22nd.

## Things to know about the columns

- **Times** (`CRS_DEP_TIME`, `DEP_TIME`, `ARR_TIME`, `WHEELS_OFF`, ...) are
  numbers in `hhmm` form (`1405` = 2:05 pm), so you can't subtract them
  directly. They are in each airport's **local time**, and midnight
  sometimes appears as `2400`. `CRS_` means scheduled ("computer reservation
  system"); the others are actual.
- **There is no date column**: build one from `YEAR`, `MONTH` and
  `DAY_OF_MONTH`. `DAY_OF_WEEK` is 1 = Monday ... 7 = Sunday.
- **Delays** are in minutes, and negative means early. Most flights are on
  time or early: the median `ARR_DELAY` is -5 minutes.
- **Delay causes** (`CARRIER_DELAY`, `WEATHER_DELAY`, `NAS_DELAY`,
  `SECURITY_DELAY`, `LATE_AIRCRAFT_DELAY`) are only filled in for flights
  that arrived 15 or more minutes late; they are empty (not zero) otherwise.
- **Cancelled and diverted flights** have no arrival time or delay.
  `CANCELLATION_CODE` is A = carrier, B = weather, C = National Air System,
  D = security.
- **Airlines and airports are codes** (`OP_UNIQUE_CARRIER` like `WN`, `9E`;
  `ORIGIN`/`DEST` like `MSN`); `Lookups/` has the names and airport
  locations. Some carriers (e.g. `9E`, `OO`, `YX`) are regional airlines that
  fly under a bigger airline's brand.
- **Time zones**: `utc_offset_standard` in `Lookups/airports.csv` is the
  offset in *standard* time (Madison is `-0600`). Daylight saving time was
  in effect for all of the April, July and October data, so add an hour
  for those months (Madison is `-0500` in July) - except in Arizona,
  Hawaii, Puerto Rico, the Virgin Islands and Guam, which don't use it.
- `DISTANCE` is in miles; elapsed times are in minutes.

## Versions

- **`v2025`** (git tag): the data as Fall 2025 students used it.
- **2026 fixes** (Fall 2026):
  - The top 105 airports were picked separately for each file, so the
    monthly files did not all have the same airports (14 seasonal airports,
    like ASE, BZN and EYW, were in some months but not others) and did not
    add up to the combined file. Now one list, from all 4 months, is used
    for every file. `combined-reduced.csv` is unchanged; each monthly file
    changed by a few hundred rows.
  - Added `Lookups/` (airport names, locations and time zones; airline
    names) and the script that makes them.
  - This README now documents the reduction (including the even-days rule,
    which the 2025 web page described as "the first 28 days") and the
    columns.
