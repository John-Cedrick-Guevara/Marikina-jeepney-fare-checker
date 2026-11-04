create table fare_matrix (
    distance_km integer primary key check (distance_km > 0),

    regular_fare numeric(6, 2) not null check (regular_fare > 0),
    discounted_fare numeric(6, 2) not null check (discounted_fare > 0),

    created_at timestamp default now(),
    updated_at timestamp default now()
);

-- New jeepney fare rate; discounted_fare = student / elderly / PWD
insert into fare_matrix (distance_km, regular_fare, discounted_fare) values
    (1, 14.00, 11.25),
    (2, 14.00, 11.25),
    (3, 14.00, 11.25),
    (4, 14.00, 11.25),
    (5, 16.00, 12.75),
    (6, 18.00, 14.50),
    (7, 20.00, 16.00),
    (8, 22.00, 17.50),
    (9, 24.00, 19.25),
    (10, 26.00, 20.75),
    (11, 28.00, 22.50),
    (12, 30.00, 24.00),
    (13, 32.00, 25.50),
    (14, 34.00, 27.25),
    (15, 36.00, 28.75),
    (16, 38.00, 30.50),
    (17, 40.00, 32.00),
    (18, 42.00, 33.50),
    (19, 44.00, 35.25),
    (20, 46.00, 36.75),
    (21, 48.00, 38.50),
    (22, 50.00, 40.00),
    (23, 52.00, 41.50),
    (24, 54.00, 43.25),
    (25, 56.00, 44.75);

-- Read-only for clients; the back-end connects as postgres and bypasses RLS
alter table fare_matrix enable row level security;

CREATE POLICY "Allow read" ON fare_matrix FOR SELECT TO anon, authenticated USING (true);
