# Member 3 -> Member 4 Handoff

## What Member 3 supplies

- 12 synthetic listings in `listings_mock.csv`.
- 15 synthetic amenities in `amenities_mock.csv`.
- One UBC campus destination in `campuses_mock.csv`.
- 36 route jobs in `commute_jobs_mock.csv`: 12 listings x 3 travel modes.
- Cost defaults in `cost_assumptions_mock.json`.

## What Member 4 returns

For every `job_id`, write one `commute_results` record:

```json
{
  "job_id": "cjob_001",
  "listing_id": "lst_001",
  "campus_id": "campus_ubc_vancouver",
  "travel_mode": "TRANSIT",
  "duration_minutes": 32,
  "distance_km": 9.4,
  "estimated_transport_cost_cad": 5.75,
  "provider": "mock | open_trip_planner",
  "calculated_at": "2026-09-26T00:00:00Z",
  "is_mock": true
}
```

## Contract rules

- Do not change `listing_id`, `campus_id`, or `job_id`.
- Use `provider=mock` until OpenTripPlanner has a built graph and TransLink GTFS feed.
- Return a nullable duration/distance with an explicit `status=unavailable` if a mode cannot be routed.
- Treat every coordinate as approximate. Do not show an exact door location in the frontend.
- Member 4 owns computed fields. Member 3 owns source and normalized-listing fields.
