# Apartment Finder: Tech Stack and Folder Structure

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js + React + TypeScript + Tailwind | Fast to build, easy to deploy |
| Map | MapLibre GL JS (or Leaflet for a simpler start) | Free and handles many markers well |
| Backend | FastAPI (Python) | Same language as your data pipeline |
| Database | PostgreSQL + PostGIS (Supabase gives you this free) | Spatial queries like "gyms within 1 km" |
| Data pipeline | Python (pandas, requests) run as scripts or scheduled jobs | Ingest and clean the data |
| Commute routing | OpenTripPlanner (free, uses TransLink GTFS + OpenStreetMap) or Google Routes API (paid, easier) | Transit, bike, walk, and drive times |
| Amenities data | OpenStreetMap via the Overpass API | Free gyms and grocery stores with coordinates |
| Hosting | Vercel (frontend), Railway/Render (API), Supabase (DB) | Cheap or free at this scale |

## Data sources

- **Listings:** This is the hard part. Scraping Craigslist, Kijiji, Rentals.ca, or Zumper usually violates their terms and breaks often. Safer options are a listings API or partner feed, a manually curated CSV to start, or UBC Housing and student-run listings. Design the ingestion layer so the source is swappable.
- **Gyms and groceries:** Overpass queries like `leisure=fitness_centre` and `shop=supermarket` inside a Metro Vancouver bounding box.
- **Commute time:** Precompute it per listing to UBC and cache it, so the map loads instantly.
- **Commute cost:**
  - Transit: a fare lookup table. UBC students get the U-Pass BC, so transit is effectively a flat fee already covered.
  - Driving: distance × per-km cost, plus a UBC parking estimate.
  - Bike or walk: $0.

## Folder structure (monorepo)

```
apartment-finder/
├── README.md
├── docker-compose.yml          # local Postgres/PostGIS (+ OTP optional)
├── .env.example
│
├── apps/
│   ├── web/                    # Next.js frontend
│   │   ├── app/
│   │   │   ├── page.tsx        # main split view: list + map
│   │   │   └── listing/[id]/page.tsx
│   │   ├── components/
│   │   │   ├── Map/            # MapView, ListingMarker, AmenityLayer
│   │   │   ├── ListingList/    # ListingCard, virtualized list
│   │   │   ├── Filters/        # price, beds, max commute, amenities
│   │   │   └── CommuteBadge.tsx
│   │   ├── hooks/              # useListings, useMapSync
│   │   ├── lib/                # api client, formatters
│   │   └── types/
│   │
│   └── api/                    # FastAPI backend
│       ├── main.py
│       ├── routers/            # listings.py, amenities.py, commute.py
│       ├── services/           # commute_service.py, cost_calculator.py
│       ├── models/             # SQLAlchemy models
│       ├── schemas/            # Pydantic schemas
│       └── db/                 # session, migrations (Alembic)
│
├── pipeline/                   # data ingestion (Python)
│   ├── ingest_listings.py      # CSV / API / scraper adapters
│   ├── ingest_amenities.py     # Overpass → PostGIS
│   ├── geocode.py              # addresses → lat/lng
│   ├── compute_commutes.py     # listing → UBC, all modes, cached
│   ├── sources/                # one adapter per listing source
│   └── config/                 # fare tables, UBC coordinates, bbox
│
├── data/
│   ├── raw/                    # downloaded, untouched (gitignored)
│   ├── processed/
│   └── gtfs/                   # TransLink GTFS feed
│
├── infra/                      # deploy configs, OTP setup
├── docs/                       # data model, API spec, decisions
└── tests/
```

## Core data model

- **listings:** id, title, price, beds, baths, address, `geom` (PostGIS point), source, url, scraped_at
- **amenities:** id, type (gym/grocery), name, `geom`
- **commutes:** listing_id, mode (transit/bike/walk/drive), minutes, monthly_cost_estimate

## Main flow

1. The pipeline loads listings, geocodes them, and pulls amenities.
2. `compute_commutes.py` calculates each listing's route to UBC and stores it.
3. The frontend requests `GET /listings?max_price=...&max_commute=...&bbox=...`.
4. The list and map stay in sync: hovering a card highlights its marker, and panning the map filters the list.
5. Toggling "Gyms" or "Groceries" shows amenity layers, with a "walk time to nearest grocery" stat on each card.

## Suggested build order

1. Hardcode about 30 listings in a CSV, load them into PostGIS, and show the list and map together.
2. Add commute times and costs.
3. Add amenity layers and filters.
4. Only then work on automated listing ingestion, since it's the riskiest piece.

I can scaffold the repo, write the PostGIS schema, or draft the Overpass queries for Metro Vancouver if you want to start on any of those.
