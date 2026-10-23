"""
Step 3a - Nearby-place features from OpenStreetMap (free), for the "WHERE" model.

Training : download all places in Chicago once (about 12 queries), count how many of each
           kind lie within 400 m of every grid cell.
Live API : the same counts for any point on Earth with one small query (get_features_live).

Output: data/processed/cell_features.parquet
Usage : python backend/ml/osm_features.py
"""
import time
from collections import defaultdict

import numpy as np
import pandas as pd
import requests
from sklearn.neighbors import BallTree

from common import (LAT_MAX, LAT_MIN, LNG_MAX, LNG_MIN, RAW, read_table, table_path,
                    write_table)

RADIUS_M = 400
MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
]
HEADERS = {
    "User-Agent": "SafeRouteAI/1.0 (+https://github.com/harishgit0/AI-Tourist-Safety-Predictor)",
    "Accept": "application/json",
}
TILES = 3  # Chicago is split into TILES x TILES squares for the bulk download

# category -> list of (osm key, allowed values or None for "any value")
CATEGORIES = {
    "bars": [("amenity", {"bar", "pub", "nightclub"})],
    "food": [("amenity", {"restaurant", "cafe", "fast_food"})],
    "rail_stations": [("railway", {"station", "subway_entrance", "tram_stop"}),
                      ("public_transport", {"station"})],
    "bus_stops": [("highway", {"bus_stop"})],
    "shops": [("shop", None)],
    "parks": [("leisure", {"park", "playground"})],
    "lodging": [("tourism", {"hotel", "hostel", "motel", "guest_house"})],
    "attractions": [("tourism", {"attraction", "museum", "gallery", "viewpoint"})],
    "police": [("amenity", {"police"})],
    "schools": [("amenity", {"school", "college", "university"})],
    "liquor": [("shop", {"alcohol"})],
    "banks_atms": [("amenity", {"bank", "atm"})],
}
DENSITY_CATS = ["bars", "food", "shops", "lodging", "attractions", "banks_atms"]
FEATURE_COLUMNS = list(CATEGORIES) + ["poi_total"]


def _live_selectors(lat, lng, radius):
    """Combine same-key filters into one selector to reduce Overpass query cost."""
    values_by_key = defaultdict(set)
    any_value_keys = set()
    for rules in CATEGORIES.values():
        for key, values in rules:
            if values is None:
                any_value_keys.add(key)
            else:
                values_by_key[key].update(values)

    selectors = []
    for key in sorted(any_value_keys | values_by_key.keys()):
        if key in any_value_keys:
            selector = f'nwr["{key}"](around:{radius},{lat},{lng});'
        else:
            selector = f'nwr{_filter(key, values_by_key[key])}(around:{radius},{lat},{lng});'
        selectors.append(selector)
    return "".join(selectors)


def _filter(key, values):
    if values is None:
        return f'["{key}"]'
    return f'["{key}"~"^({"|".join(sorted(values))})$"]'


def _matches(tags, category):
    for key, values in CATEGORIES[category]:
        if key in tags and (values is None or tags[key] in values):
            return True
    return False


def overpass(query, timeout=150, retries=4, wait_429=30):
    """POST a query to the Overpass mirrors; waits when rate-limited; prints the real errors."""
    last = None
    for attempt in range(retries):
        for url in MIRRORS:
            host = url.split("/")[2]
            try:
                r = requests.post(url, data={"data": query}, headers=HEADERS, timeout=timeout)
                if r.status_code == 429:
                    last = "429 Too Many Requests"
                    print(f"  {host}: rate-limited (429); waiting {wait_429}s")
                    time.sleep(wait_429)
                    continue
                if r.status_code != 200:
                    last = f"HTTP {r.status_code}"
                    print(f"  {host}: HTTP {r.status_code} {r.text[:100]!r}")
                    continue
                return r.json()
            except (requests.RequestException, ValueError) as e:
                last = f"{type(e).__name__}: {e}"
                print(f"  {host}: {type(e).__name__}")
        time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"Overpass unavailable (last error: {last}). Wait a few minutes and re-run; "
                       "finished tiles are cached.")


def _centre(el):
    if "lat" in el:
        return el["lat"], el["lon"]
    c = el.get("center")
    return (c["lat"], c["lon"]) if c else None


# ---------------- training: bulk download + counting ----------------
def download_all():
    """Download every relevant place in Chicago in TILES x TILES small queries (resumable)."""
    folder = RAW / "osm"
    folder.mkdir(parents=True, exist_ok=True)
    lat_edges = np.linspace(LAT_MIN, LAT_MAX, TILES + 1)
    lng_edges = np.linspace(LNG_MIN, LNG_MAX, TILES + 1)
    union = lambda bbox: "".join(f"nwr{_filter(k, v)}{bbox};"
                                 for rules in CATEGORIES.values() for k, v in rules)
    tiles = []
    for i in range(TILES):
        for j in range(TILES):
            path = folder / f"tile_{i}_{j}.csv"
            if path.exists():
                print(f"  tile {i * TILES + j + 1}/{TILES * TILES}: cached")
                tiles.append(pd.read_csv(path))
                continue
            bbox = f"({lat_edges[i]:.4f},{lng_edges[j]:.4f},{lat_edges[i + 1]:.4f},{lng_edges[j + 1]:.4f})"
            data = overpass(f"[out:json][timeout:120];({union(bbox)});out tags center;")
            recs = []
            for el in data.get("elements", []):
                c = _centre(el)
                cats = [cat for cat in CATEGORIES if _matches(el.get("tags", {}), cat)]
                if c and cats:
                    recs.append((el.get("type", ""), el.get("id", 0), c[0], c[1], "|".join(cats)))
            tile = pd.DataFrame(recs, columns=["type", "id", "lat", "lng", "cats"])
            tile.to_csv(path, index=False)
            tiles.append(tile)
            print(f"  tile {i * TILES + j + 1}/{TILES * TILES}: {len(tile):,} places")
            time.sleep(5)  # be polite to the free servers

    allp = pd.concat(tiles).drop_duplicates(["type", "id"])  # ways crossing tile borders appear twice
    allp["cats"] = allp["cats"].fillna("")
    print(f"\nTotal unique places: {len(allp):,}")
    for cat in CATEGORIES:
        sub = allp[allp["cats"].str.split("|").apply(lambda lst: cat in lst)][["lat", "lng"]]
        sub.to_csv(folder / f"{cat}.csv", index=False)
        print(f"  {cat}: {len(sub):,}")


def build_cell_features():
    labels = read_table(table_path("chicago_labels"))
    cells = labels[["cell_id", "lat", "lng"]].drop_duplicates("cell_id").reset_index(drop=True)
    coords = np.radians(cells[["lat", "lng"]].to_numpy())
    for cat in CATEGORIES:
        pts = pd.read_csv(RAW / "osm" / f"{cat}.csv")
        if len(pts) == 0:
            cells[cat] = 0
            continue
        tree = BallTree(np.radians(pts[["lat", "lng"]].to_numpy()), metric="haversine")
        cells[cat] = tree.query_radius(coords, r=RADIUS_M / 6371000.0, count_only=True)
    cells["poi_total"] = cells[DENSITY_CATS].sum(axis=1)
    path = table_path("cell_features")
    write_table(cells, path)
    print(f"\nSaved features for {len(cells):,} cells to {path}")
    print(cells[FEATURE_COLUMNS].describe().round(1).T.to_string())


# ---------------- live: any point on Earth ----------------
def get_features_live(lat, lng, radius=RADIUS_M, fast=False):
    """Count nearby places. Fast mode is intended for route comparisons."""
    parts = _live_selectors(lat, lng, radius)
    query = f"[out:json][timeout:15];({parts});out tags center;"

    if fast:
        data = None
        last_error = "No Overpass server responded"

        # Query selectors are grouped by tag key; allow multiple mirrors a little
        # more time so a slow public instance does not make both cards disappear.
        for url in MIRRORS[:3]:
            try:
                response = requests.post(
                    url,
                    data={"data": query},
                    headers=HEADERS,
                    timeout=4,
                )
                if response.status_code != 200:
                    last_error = f"HTTP {response.status_code}"
                    continue

                data = response.json()
                break
            except (requests.RequestException, ValueError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"

        if data is None:
            raise RuntimeError(
                f"Fast Overpass lookup failed: {last_error}"
            )
    else:
        data = overpass(
            query,
            timeout=8,
            retries=1,
            wait_429=0,
        )

    counts = {category: 0 for category in CATEGORIES}
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        for category in CATEGORIES:
            if _matches(tags, category):
                counts[category] += 1

    counts["poi_total"] = sum(
        counts[category] for category in DENSITY_CATS
    )
    return counts


if __name__ == "__main__":
    print("Downloading Chicago places from OpenStreetMap (first run takes a few minutes) ...")
    download_all()
    build_cell_features()
