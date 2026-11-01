#!/usr/bin/env python3
"""Make lookup tables for the airport and airline codes in the flight data.

Writes:
  Lookups/airports.csv  every airport in OriginalData (345), with its name,
                        city, state, latitude/longitude, UTC offset, flight
                        count (departures + arrivals over all the original
                        files), rank, and whether it is in the reduced data
                        (the top 105; see reduce_to_reduced.py)
  Lookups/carriers.csv  every carrier code in OriginalData, with its name and
                        flight count

Both come from Bureau of Transportation Statistics tables, the same source as
the flight data. The raw downloads are kept in OriginalData/lookups/:
  T_MASTER_CORD.csv       "Aviation Support Tables: Master Coordinate"
                          https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FLL
                          (all fields; downloaded through the web form)
  L_UNIQUE_CARRIERS.csv   carrier lookup table
                          https://www.transtats.bts.gov/Download_Lookup.asp?Y11x72=Y_haVdhR_PNeeVRef
The Master Coordinate table keeps history (an airport code can have several
rows over time); we use the row that was valid for all of 2024.

Usage:
  python3 scripts/make_lookups.py              build from the saved downloads
  python3 scripts/make_lookups.py --download   download them again first

Written by Claude Code, as prompted by Michael Gleicher, November 2026
(one of the "2026 fixes").
"""
import argparse
import io
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from http.cookiejar import CookieJar
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from reduce_to_reduced import top_airports  # noqa: E402  (same ranking as the reduction)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "OriginalData" / "lookups"
OUT = ROOT / "Lookups"
TOP_K = 105
MASTER_URL = "https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FLL&QO_fu146_anzr=N8vn6v10%20f722146%20gnoyr5"
CARRIER_URL = "https://www.transtats.bts.gov/Download_Lookup.asp?Y11x72=Y_haVdhR_PNeeVRef"
PERIOD = ("2024-01-01", "2024-10-31")   # the months in OriginalData


def download():
    """fetch the two BTS tables into OriginalData/lookups/."""
    RAW.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(CARRIER_URL, RAW / "L_UNIQUE_CARRIERS.csv")

    # the Master Coordinate table is a web form: load it, tick every field, submit
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
    html = opener.open(MASTER_URL, timeout=60).read().decode("utf-8", "replace")
    form = dict(re.findall(r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"', html))
    form.update({c: "on" for c in re.findall(r'<input[^>]*type="checkbox"[^>]*name="([A-Z_0-9]+)"', html)})
    form["btnDownload"] = "Download"
    req = urllib.request.Request(MASTER_URL, data=urllib.parse.urlencode(form).encode(),
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    data = opener.open(req, timeout=180).read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        (RAW / "T_MASTER_CORD.csv").write_bytes(z.read("T_MASTER_CORD.csv"))
    print("downloaded into", RAW)


def airports(counts):
    m = pd.read_csv(RAW / "T_MASTER_CORD.csv", dtype=str)
    for c in ("AIRPORT_START_DATE", "AIRPORT_THRU_DATE"):
        m[c] = pd.to_datetime(m[c], format="%m/%d/%Y %I:%M:%S %p")
    valid = (m.AIRPORT_START_DATE <= PERIOD[0]) & (m.AIRPORT_THRU_DATE.isna() | (m.AIRPORT_THRU_DATE >= PERIOD[1]))
    m = m[valid & m.AIRPORT.isin(counts.index)].set_index("AIRPORT")
    missing = set(counts.index) - set(m.index)
    assert not missing and m.index.is_unique, f"no unique 2024 row for {missing or m.index[m.index.duplicated()]}"

    a = pd.DataFrame({
        "code": counts.index,
        "name": m.DISPLAY_AIRPORT_NAME.reindex(counts.index).values,
        "city": m.DISPLAY_AIRPORT_CITY_NAME_FULL.reindex(counts.index).str.rsplit(",", n=1).str[0].values,
        "state": m.AIRPORT_STATE_CODE.reindex(counts.index).values,
        "latitude": m.LATITUDE.reindex(counts.index).astype(float).values,
        "longitude": m.LONGITUDE.reindex(counts.index).astype(float).values,
        "utc_offset_standard": m.UTC_LOCAL_TIME_VARIATION.reindex(counts.index).values,
        "flights": counts.values,
        "rank": range(1, len(counts) + 1),
    })
    a["in_reduced_data"] = a["rank"] <= TOP_K
    return a


def carriers(flights):
    c = pd.read_csv(RAW / "L_UNIQUE_CARRIERS.csv").set_index("Code").Description
    n = flights.OP_UNIQUE_CARRIER.value_counts()
    assert n.index.isin(c.index).all(), set(n.index) - set(c.index)
    return pd.DataFrame({"code": n.index, "name": c.reindex(n.index).values, "flights": n.values})


def main(argv):
    parser = argparse.ArgumentParser(description="Make airport and carrier lookup tables")
    parser.add_argument("--download", action="store_true", help="download the BTS tables again first")
    args = parser.parse_args(argv[1:])
    if args.download or not (RAW / "T_MASTER_CORD.csv").exists():
        download()

    files = sorted((ROOT / "OriginalData").glob("*.csv"))
    flights = pd.concat([pd.read_csv(f, usecols=["ORIGIN", "DEST", "OP_UNIQUE_CARRIER"]) for f in files])
    counts, _ = top_airports([flights], TOP_K)

    OUT.mkdir(exist_ok=True)
    a = airports(counts)
    a.to_csv(OUT / "airports.csv", index=False)
    c = carriers(flights)
    c.to_csv(OUT / "carriers.csv", index=False)
    print(f"wrote {OUT / 'airports.csv'} ({len(a)} airports, {a.in_reduced_data.sum()} in the reduced data)")
    print(f"wrote {OUT / 'carriers.csv'} ({len(c)} carriers)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
