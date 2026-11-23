-- Road distance (km) from the previous stop on the same route, filled by scripts/fill_segment_distances.py.
-- null = not fetched yet (first stop of a route stays null).
alter table route_points
    add column distance_from_previous_km numeric(7, 3) check (distance_from_previous_km >= 0);
