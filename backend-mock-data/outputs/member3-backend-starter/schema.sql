create extension if not exists postgis;

create table if not exists sources (
  source_id text primary key,
  name text not null,
  homepage_url text,
  access_mode text not null check (access_mode in ('synthetic_fixture', 'partner_feed', 'user_submission', 'approved_api')),
  scraping_authorized boolean not null default false,
  terms_checked_at timestamptz,
  notes text
);

create table if not exists campuses (
  campus_id text primary key,
  school_id text not null,
  name text not null,
  address_display text,
  location geometry(Point, 4326) not null,
  active boolean not null default true,
  is_mock boolean not null default false
);

create table if not exists listings (
  listing_id text primary key,
  source_id text not null references sources(source_id),
  source_listing_ref text not null,
  source_listing_url text,
  is_mock boolean not null default false,
  title text not null,
  address_display text,
  neighbourhood text,
  location geometry(Point, 4326) not null,
  location_precision text not null check (location_precision in ('exact', 'approximate', 'neighbourhood')),
  monthly_rent_cad numeric(10,2) not null check (monthly_rent_cad >= 0),
  bedrooms numeric(3,1) not null check (bedrooms >= 0),
  bathrooms numeric(3,1) not null check (bathrooms >= 0),
  square_feet integer,
  property_type text not null,
  furnished boolean not null default false,
  utilities_included jsonb not null default '[]'::jsonb,
  internet_included boolean not null default false,
  parking_monthly_cad numeric(10,2) not null default 0,
  roommate_count integer not null default 0,
  pets_allowed boolean,
  laundry_in_unit boolean,
  floor_number integer,
  available_date date,
  listing_status text not null default 'available',
  data_confidence text not null check (data_confidence in ('fixture', 'confirmed', 'estimated', 'unavailable')),
  last_verified_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (source_id, source_listing_ref)
);

create table if not exists amenities (
  amenity_id text primary key,
  name text not null,
  category text not null check (category in ('grocery', 'restaurant', 'gym', 'hospital', 'gas_station', 'school', 'transit_stop')),
  location geometry(Point, 4326) not null,
  source_id text references sources(source_id),
  source_ref text,
  is_mock boolean not null default false,
  updated_at timestamptz not null default now()
);

create table if not exists commute_jobs (
  job_id text primary key,
  listing_id text not null references listings(listing_id),
  campus_id text not null references campuses(campus_id),
  travel_mode text not null check (travel_mode in ('TRANSIT', 'DRIVE', 'BICYCLE', 'WALK')),
  departure_time timestamptz not null,
  request_status text not null default 'pending' check (request_status in ('pending', 'complete', 'unavailable', 'failed')),
  is_mock boolean not null default false,
  unique (listing_id, campus_id, travel_mode, departure_time)
);

create table if not exists commute_results (
  commute_result_id bigserial primary key,
  job_id text not null unique references commute_jobs(job_id),
  duration_minutes numeric(8,2),
  distance_km numeric(8,2),
  estimated_transport_cost_cad numeric(10,2),
  provider text not null,
  provider_response jsonb,
  calculated_at timestamptz not null default now(),
  status text not null check (status in ('complete', 'unavailable', 'failed')),
  is_mock boolean not null default false
);

create table if not exists cost_assumptions (
  assumption_version text primary key,
  currency text not null default 'CAD',
  values jsonb not null,
  is_mock boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists listing_cost_estimates (
  listing_cost_estimate_id bigserial primary key,
  listing_id text not null references listings(listing_id),
  campus_id text references campuses(campus_id),
  assumption_version text not null references cost_assumptions(assumption_version),
  rent_cad numeric(10,2) not null,
  utilities_cad numeric(10,2) not null default 0,
  internet_cad numeric(10,2) not null default 0,
  transit_cad numeric(10,2) not null default 0,
  driving_cad numeric(10,2) not null default 0,
  parking_cad numeric(10,2) not null default 0,
  insurance_cad numeric(10,2) not null default 0,
  groceries_delta_cad numeric(10,2) not null default 0,
  recurring_building_fees_cad numeric(10,2) not null default 0,
  monthly_total_cad numeric(10,2) not null,
  calculated_at timestamptz not null default now(),
  is_mock boolean not null default false
);

create index if not exists listings_location_gix on listings using gist (location);
create index if not exists amenities_location_gix on amenities using gist (location);
create index if not exists listings_filter_idx on listings (monthly_rent_cad, bedrooms, property_type, listing_status);
create index if not exists commute_jobs_lookup_idx on commute_jobs (listing_id, campus_id, travel_mode, departure_time);

insert into sources (source_id, name, homepage_url, access_mode, scraping_authorized, terms_checked_at, notes)
values (
  'rentals_ca_synthetic',
  'Rentals.ca (synthetic fixture)',
  'https://rentals.ca/',
  'synthetic_fixture',
  false,
  '2026-09-26T00:00:00Z',
  'Fixture schema only. Do not scrape. Obtain written authorization before any live ingestion.'
), (
  'overpass_synthetic',
  'OpenStreetMap Overpass synthetic fixture',
  'https://wiki.openstreetmap.org/wiki/Overpass_API',
  'synthetic_fixture',
  false,
  '2026-09-26T00:00:00Z',
  'Synthetic amenity fixtures. Production pipeline must respect provider policy and cache results.'
)
on conflict (source_id) do nothing;
