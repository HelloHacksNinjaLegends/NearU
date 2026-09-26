# Member 3 Backend Starter Data

This package is a demo-safe handoff from Member 3 to Member 4 for the Student Housing & Cost-of-Living Platform.

## Source decision

Use **Rentals.ca** as the single *simulated source taxonomy* for the hackathon fixtures. It is a Canadian apartment-rental marketplace, so its listing fields are a useful shape for the product. Every listing in this package is synthetic. No page, photo, address, price, or listing content was copied or scraped from Rentals.ca.

Do not implement a Rentals.ca scraper. Its Terms of Use prohibit automated data extraction unless it has been explicitly authorized in writing. For production, use a written partnership or feed agreement, direct property-manager feeds, university-approved listings, or user-submitted and moderated listings.

## Files

| File | Owner | Purpose |
| --- | --- | --- |
| `listings_mock.csv` | Member 3 | Demo-safe rental records used to seed `listings`. |
| `amenities_mock.csv` | Member 3 | Demo-safe nearby places used to seed `amenities`. |
| `campuses_mock.csv` | Shared | Campus destination used by filters and route jobs. |
| `commute_jobs_mock.csv` | Member 3 -> Member 4 | Requests for OpenTripPlanner or a deterministic mock-route provider. |
| `cost_assumptions_mock.json` | Member 3 -> Member 4 | Default values for the monthly-cost calculation. |
| `listing_api_fixture.json` | Member 3 -> Member 2/4 | Ready-to-serve FastAPI response shape. |
| `schema.sql` | Member 1/3 | PostgreSQL + PostGIS schema and indexes. |
| `member4_handoff.md` | Member 3/4 | Ownership boundary and payload contract. |

## Data rules

- Currency values are CAD and represent monthly amounts unless the column says otherwise.
- Coordinates are approximate demo coordinates. `location_precision` is intentionally set to `neighbourhood` or `approximate`.
- `is_mock=true` must remain present in all fixture records and API responses.
- `source_name` is always `Rentals.ca (synthetic fixture)` in the listing data. It is not evidence of a live listing.
- Member 4 can replace `provider=mock` route results with OpenTripPlanner output without changing a listing ID.

## Seed order

1. Run `schema.sql` in Supabase.
2. Load `campuses_mock.csv`, then `listings_mock.csv`, then `amenities_mock.csv`.
3. Member 4 uses `commute_jobs_mock.csv` to generate `commute_results`.
4. Member 4 combines listings, cost assumptions, and commute results into `listing_cost_estimates`.

## Raw-file to database mapping

- Map `source_name` to `sources.source_id` (`Rentals.ca (synthetic fixture)` maps to `rentals_ca_synthetic`).
- Convert `latitude` and `longitude` into PostGIS geometry with `ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)`.
- Split the pipe-delimited `utilities_included` value into a JSON array before inserting it into `listings.utilities_included`.
- Leave `source_listing_url` null for these fixtures: the records use made-up references and must never imply a live Rentals.ca listing.
