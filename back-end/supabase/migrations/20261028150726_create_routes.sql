create table routes (
    id uuid primary key default gen_random_uuid(),

    route_name text not null,
    
    created_at timestamp default now(),
    updated_at timestamp default now()
);

create index idx_routes_route_name on routes(route_name);

CREATE POLICY "Allow all" ON routes FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);