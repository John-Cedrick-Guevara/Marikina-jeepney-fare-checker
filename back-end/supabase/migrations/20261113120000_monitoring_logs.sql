-- KPI monitoring and audit trail. Neither table stores IP addresses or anything that identifies
-- a commuter (data minimization); only the API's database role reads or writes them.

-- One row per fare estimate a commuter requested
create table fare_lookups (
    id bigint generated always as identity primary key,
    origin_stop_id uuid not null references stops (id) on delete cascade,
    destination_stop_id uuid not null references stops (id) on delete cascade,
    puv_type text not null references puv_types (code),
    route_count integer not null,       -- 0 = no route connects the stops (unsupported trip)
    has_fare boolean not null,          -- at least one route came back with a fare
    duration_ms integer not null,
    created_at timestamptz not null default now()
);

create index fare_lookups_created_at on fare_lookups (created_at);

-- One row per admin change (create, update, delete, publish, upload), for accountability
create table admin_audit_log (
    id bigint generated always as identity primary key,
    admin_user_id uuid not null,
    admin_email text not null,
    method text not null,
    path text not null,
    status_code integer not null,
    created_at timestamptz not null default now()
);

create index admin_audit_log_created_at on admin_audit_log (created_at);

-- RLS on with no policies: the anon / authenticated keys can't read or write these at all
alter table fare_lookups enable row level security;
alter table admin_audit_log enable row level security;

-- Keep lookups 1 year, the audit log 2 years
select cron.schedule(
    'monitoring-retention',
    '15 16 * * *',
    $$ delete from fare_lookups where created_at < now() - interval '1 year';
       delete from admin_audit_log where created_at < now() - interval '2 years'; $$
);
