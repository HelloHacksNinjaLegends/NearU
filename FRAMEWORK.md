# Student Housing & Cost-of-Living Platform

**Hackathon Blueprint — MVP scope, research plan, team ownership, and build structure**

---

## 1. Executive Summary

Build a student-first housing decision tool that compares homes by the cost and time students actually experience, not rent alone. A student chooses a campus, budget, household preferences, and commute limit; the platform returns listings on an interactive map with estimated monthly cost, travel time, nearby amenities, and a clear trade-off between rent paid and time saved.

**Hackathon thesis:** students currently have to stitch together listing sites, maps, transit planners, and budgeting tools. This product turns that fragmented work into one explainable comparison.

---

## 2. Problem, User, and Value Proposition

**Primary user:** a student looking for a room, apartment, or shared unit near a selected campus.
**Secondary users:** roommates comparing options and university off-campus housing teams.

- **Pain point:** advertised rent hides utilities, internet, parking, transit, gas, and the time cost of a long commute.
- **Pain point:** a cheap listing can look affordable but be a poor fit once commute and day-to-day access are considered.
- **Value proposition:** compare true monthly cost, commute, amenities, and student preferences in one decision surface.
- **Differentiator:** explain the trade-off as cost per hour of commute time saved, instead of merely sorting by rent.

---

## 3. MVP: What We Will Demonstrate

The MVP should be intentionally narrow: one city, one or more nearby campuses, seeded or partner-approved listings, and transparent estimates. Accuracy and explainability matter more than having a large inventory.

### Core user journey

1. Select a school/campus, monthly rent budget, household size, and maximum commute time.
2. Browse map pins and a synchronized listing list.
3. Open a listing to see rent, included utilities, room/property details, commute by travel mode, nearby amenities, and estimated monthly total.
4. Compare up to three listings side by side.
5. See the cheaper-versus-closer calculation: extra monthly spend, commute time saved, and cost per hour saved.
6. Save or share a shortlist if time permits.

### MVP acceptance criteria

- A user can filter seeded listings by price, bedroom/roommate count, property type, and commute threshold.
- Each listing visibly separates confirmed information from estimated costs.
- The map displays a campus destination, listings, and selected amenity categories.
- The comparison view calculates total monthly cost and time-versus-cost results consistently.
- The demo works with preloaded data and does not depend on a live external API response.

### Explicitly out of scope for the hackathon

- Nationwide live inventory aggregation or unlicensed marketplace scraping.
- Lease signing, payments, identity verification, or roommate matching.
- Forecasts presented as guarantees, precise safety scoring, or personalized financial approval.
- 3D buildings, simulated window views, and floor-level visualization.

---

## 4. Data and External Services

**Listings:** use a small, realistic seeded data set or a university/property-manager feed with permission. Store source URL, last verified date, exact-versus-approximate location, and a confidence flag. Do not scrape rental sites whose terms prohibit it.

### Recommended service choices

- **Map:** MapLibre GL JS is the primary interactive map; Leaflet is the simpler fallback. Use an OSM-compatible tile provider and display listings, campuses, and cached amenity layers.
- **Amenities:** import grocery stores, gyms, hospitals, restaurants, gas stations, transit stops, and schools from OpenStreetMap through the Overpass API; store and serve the normalized results from PostGIS.
- **Commute routing:** run OpenTripPlanner with TransLink GTFS plus OpenStreetMap for transit, walking, cycling, and driving. Google Routes API remains an optional paid fallback only if self-hosting becomes risky.
- **Market benchmarks:** CMHC rental market data for Canadian city-level average rent and vacancy context, not live listing inventory.
- **Vancouver extension:** City of Vancouver open data can identify non-market-housing projects as a separately labelled affordability layer.

**Compliance and reliability:** the Python pipeline imports and caches external data on a schedule; the web app never calls public Overpass or Nominatim services per user interaction. Keep provider attribution, freshness timestamps, and legal source records.

---

## 5. Calculation Engine

### True monthly cost

```
monthly_total = rent + utilities_not_included + internet + renter_insurance
              + parking + monthly_transit_cost + monthly_car_cost
              + groceries_delta + recurring_building_fees
```

For a shared unit:

```
student_share = rent_share + (shared_utilities / roommate_count) + individual_expenses
```

Every result should label amounts as **confirmed**, **estimated**, **user-provided**, or **unavailable**.

### Transportation cost

**Transit:**

```
monthly_transit_cost = min(monthly_pass_price, trips_per_month × single_trip_fare)
                     + zone_or_supplement_fees
```

**Driving:**

```
monthly_car_cost = (round_trip_distance_km × commute_days) × fuel_litres_per_km × fuel_price_per_litre
                 + parking + tolls + optional_wear_cost_per_km
```

### Time versus cost

```
monthly_time_saved_hours = (commute_minutes_cheaper − commute_minutes_pricier) × commute_days_per_month / 60

cost_per_hour_saved = (monthly_total_pricier − monthly_total_cheaper) / monthly_time_saved_hours
```

**Guardrail:** if a listing is both more expensive and slower, show it as **dominated** rather than calculating a misleading time-saved value.

### Fair-rent signal

For the demo:

```
expected_rent = local_median_rent × bedroom_adjustment × property_type_adjustment
              × furnished_adjustment × utilities_adjustment × location_adjustment

listing_variance_pct = (asking_rent − expected_rent) / expected_rent × 100
```

Present a range:

| Variance | Label |
|---|---|
| ≤ −10% | Potentially below market |
| −10% to +10% | Near expected |
| ≥ +10% | Potentially above market |
| n/a | Insufficient comparable data |

A future version can use a hedonic regression with bedrooms, bathrooms, floor area, furnishing, utilities, property type, neighbourhood, and time effects.

### Financial planning

```
annual_housing_cost = monthly_total × 12
degree_housing_cost = annual_housing_cost × years_in_program   (adjusted by optional annual rent-growth scenarios)
months_to_goal      = (goal − starting_savings) / monthly_contribution   (down-payment goal, no investment return)
```

Keep home-buying estimates educational. They are not mortgage approval or financial advice.

---

## 6. Product and Technical Design

### Selected hackathon stack

- **Frontend:** Next.js + React + TypeScript + Tailwind CSS.
- **Map:** MapLibre GL JS (primary) or Leaflet for a simpler fallback; use an OSM-compatible tile provider.
- **Backend:** FastAPI (Python), keeping the API, calculations, routing integration, and data pipeline in Python.
- **Database:** PostgreSQL + PostGIS through Supabase for spatial filters such as "gyms within 1 km."
- **Data pipeline:** Python with pandas and requests, run as scripts or scheduled jobs to ingest, clean, normalize, and cache external data.
- **Caching:** start with PostgreSQL/Supabase cache tables for routes and amenities; introduce Redis only if the demo needs it.
- **Hosting:** Vercel for the Next.js frontend, Railway or Render for the FastAPI API, and Supabase for PostgreSQL/PostGIS.

### Core data model

- **Listing:** id, title, rent, currency, coordinates, address_display, bedrooms, bathrooms, property_type, furnished, utilities, roommate_count, parking, source, source_url, verified_at, confidence.
- **Campus:** id, name, coordinates, school_id, active.
- **Commute:** listing_id, campus_id, mode, departure_bucket, duration_minutes, distance_km, estimated_cost, provider, calculated_at.
- **Amenity:** id, type, name, coordinates, provider, updated_at.
- **ListingCostEstimate:** listing_id, user_profile_inputs, rent, utilities, internet, transit, driving, parking, insurance, total, assumption_version.

### FastAPI route surface

| Route | Purpose |
|---|---|
| `GET /api/listings` | Filters: campus, budget, bedrooms, roommates, type, maxCommute, amenities |
| `GET /api/listings/:id` | Listing detail, monthly-cost breakdown, commute results, nearby amenities |
| `POST /api/compare` | Up to three listing IDs plus user assumptions; returns normalized comparison |
| `POST /api/commute` | Computes or reads cached travel-mode results |
| `GET /api/campuses` | Map layers and filter metadata |
| `GET /api/amenities` | Map layers and filter metadata |

---

## 7. Four-Person Team Plan

### Chatgpt — Technical Lead and Integration Owner

Own the FastAPI service, PostgreSQL/PostGIS schema, API contract, Supabase configuration, Railway/Render deployment, environment setup, and final integration. This person protects the demo path and resolves merge conflicts.

### Member 2 — Frontend and Map Experience Owner

Own the Next.js/React interface, MapLibre GL JS map (or Leaflet fallback), map/list synchronization, listing cards, detail drawer, responsive layout, and visual polish. Build against fixture data first.

### Member 3 — Data Pipeline and Amenities Owner

Own the Python pandas/requests pipeline, listing normalization, Overpass amenity imports, and demo fixtures. Publish clean, versioned Listing and Amenity payloads to Supabase/PostGIS so the frontend and routing work can proceed independently.

### Member 4 — Routing, Calculations, QA, and Pitch Owner

Own TransLink GTFS/OpenTripPlanner integration, commute payloads, cost-calculation functions, and the fair-rent range. In parallel, own acceptance testing, demo script, pitch content, screenshots/video fallback, and the judge-facing narrative.

### Working agreements

- Member 1 owns the main branch and deployment; use small pull requests or coordinated commits.
- Member 2 can proceed against fixtures; Member 1 publishes the FastAPI contract early. Member 3 and Member 4 work simultaneously after agreeing on two small contracts: Listing/Amenity payloads and Commute/Cost payloads.
- Member 4 maintains the demo data/story and logs defects with reproducible steps.
- Every member protects one demo-critical feature and one fallback screenshot or video.
- Freeze new features before the final hour; prioritize a reliable end-to-end flow.

---

## 8. Suggested Hackathon Timeline

- **Hour 0–1:** agree on the campus, seeded listings, tech stack, visual direction, and exact demo storyline.
- **Hour 1–3:** Member 1 scaffolds FastAPI/Supabase; Member 2 builds the Next.js MapLibre/Leaflet shell; Member 3 builds the Python pipeline and Overpass amenity fixtures; Member 4 builds OpenTripPlanner/GTFS routing and calculation fixtures while starting the pitch and test plan.
- **Hour 3–6:** Member 3 loads clean listings/amenities while Member 4 supplies commute/cost results; integrate both in filters, listing details, and the comparison view.
- **Hour 6–8:** wire real APIs only where safe; otherwise retain reliable fixtures and provider-labelled mock results.
- **Final 2 hours:** test complete demo, improve empty/error states, record fallback video, rehearse the pitch, and deploy.

---

## 9. Repository and Documentation Structure

Use this structure so each person has a clear place to work and judges can quickly understand the project:

```
student-housing-platform/
  README.md                         # setup, architecture, demo link, data limitations
  docs/
    product-brief.md                # user, scope, non-goals, acceptance criteria
    research-and-sources.md         # data sources, terms, formulas, assumptions
    api-contract.md                 # FastAPI endpoints and request/response examples
    demo-script.md                  # 90-second and 3-minute demo scripts
    decisions.md                    # concise architecture and scope decisions
  frontend/
    app/                            # Next.js routes and pages
    components/                     # MapLibre/Leaflet map, filters, cards, comparison
    lib/                            # FastAPI client and shared UI helpers
  backend/
    app/main.py                     # FastAPI entry point
    app/api/                        # listings, commute, comparison, amenities routers
    app/services/                   # PostGIS, routing, cost-calculation services
    app/models/                     # Pydantic request/response models
    requirements.txt                # FastAPI, SQLAlchemy, GeoAlchemy, Python deps
  pipeline/
    ingest_listings.py              # pandas-based cleaning and seed generation
    fetch_amenities.py              # scheduled/cached Overpass imports
    refresh_gtfs.py                 # TransLink GTFS refresh for OpenTripPlanner
    requirements.txt                # pandas, requests and ingestion dependencies
  data/
    listings.seed.json              # legal, demo-safe listing data
    campuses.seed.json
    amenities.seed.json
  supabase/
    migrations/                     # PostgreSQL/PostGIS schema and spatial indexes
  tests/
    backend/                        # FastAPI routes and calculation edge cases
    frontend/                       # key UI and comparison-flow tests
```

### README requirements

- One-sentence problem statement and two-sentence solution.
- Screenshots or a short demo video/GIF.
- Local setup instructions and environment variables without secrets.
- Data-source and licensing disclosure.
- Formula assumptions and the distinction between estimates and confirmed listing facts.
- Known limitations and planned next steps.

---

## 10. Demo Script and Judging Narrative

Open with a concrete decision: *"A student has a $1,600 rent ceiling and needs to reach campus in 35 minutes."* Show the search, map, and two comparable listings. Explain that the cheaper listing is not necessarily cheaper once transit, utilities, and 13 hours of monthly commute time are included. End with the cost-per-hour-saved insight and the vision: a trustworthy decision layer for every student housing search.

- **Problem:** fragmented information creates expensive, stressful housing decisions.
- **Solution:** one student-specific comparison tool for true cost, commute, and access.
- **Proof:** demonstrate the complete filtering-to-comparison flow with transparent assumptions.
- **Why now:** mapping, transit, and cost data exist but are not combined for this decision.
- **Next:** verified listings, university partnerships, GTFS-real-time routing, saved searches, and personalized ranking.

---

## 11. Risks and Fallbacks

| Risk | Fallback |
|---|---|
| Live API or rate-limit failure | Use cached route/amenity responses and label the data's timestamp. |
| Insufficient legal inventory | Use clearly marked demo fixtures or partner-approved listings. |
| Map integration fails | Show synchronized card/list view plus static screenshot or recorded video. |
| Routing precision varies by departure time | Show the selected mode and time window; do not imply a guarantee. |
| Fair-rent model lacks comparable data | Show "insufficient data" instead of an unsupported score. |
| Team integration delays | Keep each module usable with stable mock contracts. |

---

## 12. Source Notes

Use these sources in the README and pitch deck. Recheck terms, pricing, coverage, and local transit availability before any production launch.

- [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/)
- [TransLink GTFS Data](https://www.translink.ca/about-us/doing-business-with-translink/app-developer-resources/gtfs/gtfs-data)
- [OpenStreetMap Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)
- [Google Routes API](https://developers.google.com/maps/documentation/routes)
- [Google Places API](https://developers.google.com/maps/documentation/places/web-service/op-overview)
- [GTFS Schedule Reference](https://gtfs.org/documentation/schedule/reference/)
- [OpenTripPlanner Data Sources](https://opentripplanner.readthedocs.io/en/latest/Interfaces-Data-Sources/)
- [CMHC Rental Market Data](https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-data/data-tables/rental-market)
- [Statistics Canada CPI FAQ](https://www.statcan.gc.ca/en/subjects-start/prices_and_price_indexes/consumer_price_indexes/faq)
- [Nominatim Usage Policy](https://operations.osmfoundation.org/policies/nominatim/)
- [Zumper Terms of Use](https://www.zumper.com/terms-and-conditions)
- [Office for National Statistics Rental Index Methodology](https://www.ons.gov.uk/peoplepopulationandcommunity/housing/methodologies/priceindexofprivaterentsqmi)

---

*Prepared as a hackathon planning document. Replace Member 1–4 with names, select the launch campus, and confirm the event's deadline before implementation.*
