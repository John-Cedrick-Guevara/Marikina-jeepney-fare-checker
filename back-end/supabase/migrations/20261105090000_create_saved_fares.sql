-- Fare search results already computed by /fair/routes, keyed by the selected stop names
-- (direction matters). A hit skips the route search and fare computation.
create table saved_fares (
    start_point_name text not null,
    end_point_name text not null,

    -- The /fair/routes response: matching routes with their points, distance and fares
    routes jsonb not null,

    created_at timestamp default now(),

    primary key (start_point_name, end_point_name)
);

-- Saved results go stale whenever routes, stops, distances or fares change, so any write
-- to those tables clears them all. Done in the database so dashboard edits, migrations
-- and scripts/fill_segment_distances.py invalidate too, not only API writes.
-- ponytail: clears every saved fare on any change; scope it per route if edits become frequent
create function clear_saved_fares() returns trigger
language plpgsql as $$
begin
    delete from saved_fares;
    return null;
end;
$$;

create trigger clear_saved_fares after insert or update or delete or truncate on routes
    for each statement execute function clear_saved_fares();
create trigger clear_saved_fares after insert or update or delete or truncate on route_points
    for each statement execute function clear_saved_fares();
create trigger clear_saved_fares after insert or update or delete or truncate on fare_matrix
    for each statement execute function clear_saved_fares();

-- Back-end only; it connects as postgres and bypasses RLS
alter table saved_fares enable row level security;
