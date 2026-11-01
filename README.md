# Flight Data for CS765

This repository contains flight delay data for use in CS765 assignments
for the Fall 2025 class.

See [the course web flight data page](https://pages.graphics.cs.wisc.edu/765-25/posts/flight-data) for an explanation.

The repository has both the original, downloaded data for each of the 4 months
(January, April, July and October 2024), and the "simplified" data for each
month, and the combination of all 4 months.

The simplified (reduced) data, made by `scripts/reduce_to_reduced.py`, keeps:

- only the even-numbered days 2 through 28 of each month (14 days, 2 of each
  day of the week), to keep the files small
- only flights where both the origin and destination are among the 105
  busiest airports (picked separately for each file, so a few seasonal
  airports appear in some months but not others)

Because of the day filter, monthly counts are about half the real numbers,
and a day-by-day series has every other day missing.
