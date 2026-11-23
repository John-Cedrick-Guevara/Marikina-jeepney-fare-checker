create table route_points (
    id uuid primary key default gen_random_uuid(),

    route_id uuid not null references routes(id) on delete cascade,
    point_name text not null,

    stop_sequence integer not null,

    latitude double precision not null,
    longitude double precision not null,
    
    created_at timestamp default now(),
    updated_at timestamp default now()
);

create index idx_route_points_route_id on route_points(route_id);
create index idx_route_points_point_name on route_points(point_name);

CREATE POLICY "Allow all" ON route_points FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);