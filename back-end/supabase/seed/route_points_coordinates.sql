-- Fill in lat / lng for each stop (replace null), then paste into the Supabase SQL editor.
-- Rows left as null are skipped, so you can fill and run this in batches.
-- Format: latitude first, then longitude, e.g. 14.64012, 121.10563

update route_points rp
set latitude = v.lat::double precision,
    longitude = v.lng::double precision,
    updated_at = now()
from (values
  -- Marikina - SSS Village
  ('Marikina - SSS Village', 'Barangka',                    null, null),
  ('Marikina - SSS Village', 'Riverbanks',                  null, null),
  ('Marikina - SSS Village', 'Sto. Nino',                   null, null),
  ('Marikina - SSS Village', 'Savemore',                    null, null),
  ('Marikina - SSS Village', '2nd Street',                  null, null),
  ('Marikina - SSS Village', 'Conception',                  null, null),
  ('Marikina - SSS Village', 'Puregold - Conception',       null, null),
  ('Marikina - SSS Village', 'Meralco',                     null, null),
  ('Marikina - SSS Village', 'OLOPSC',                      null, null),
  ('Marikina - SSS Village', 'Puregold - Katipunan Street', null, null),
  ('Marikina - SSS Village', 'PLMAR - Rainbow',             null, null),
  ('Marikina - SSS Village', 'Rancho Village',              null, null),

  -- Marikina - Parang (Philstress)
  ('Marikina - Parang (Philstress)', 'Bayan',                null, null),
  ('Marikina - Parang (Philstress)', 'Sto. Nino',            null, null),
  ('Marikina - Parang (Philstress)', 'Conception - Simbahan', null, null),
  ('Marikina - Parang (Philstress)', 'Paliparan',            null, null),
  ('Marikina - Parang (Philstress)', 'NGI',                  null, null),
  ('Marikina - Parang (Philstress)', 'Fortune - Caltex',     null, null),
  ('Marikina - Parang (Philstress)', 'Fugoso - Boystown',    null, null),
  ('Marikina - Parang (Philstress)', 'Bonanza',              null, null),
  ('Marikina - Parang (Philstress)', 'Tower - Ikot',         null, null),

  -- Marikina - Parang (Tulay Ikot/Lamuan)
  ('Marikina - Parang (Tulay Ikot/Lamuan)', 'FEU Roosevelt',          null, null),
  ('Marikina - Parang (Tulay Ikot/Lamuan)', 'Malanday',               null, null),
  ('Marikina - Parang (Tulay Ikot/Lamuan)', 'CIS',                    null, null),
  ('Marikina - Parang (Tulay Ikot/Lamuan)', 'Tumana',                 null, null),
  ('Marikina - Parang (Tulay Ikot/Lamuan)', 'H. Bautista',            null, null),
  ('Marikina - Parang (Tulay Ikot/Lamuan)', 'Luyong',                 null, null),
  ('Marikina - Parang (Tulay Ikot/Lamuan)', 'Conception - Petron',    null, null),
  ('Marikina - Parang (Tulay Ikot/Lamuan)', 'Sta. Elena High School', null, null),
  ('Marikina - Parang (Tulay Ikot/Lamuan)', 'Calumpang',              null, null)
) as v(route_name, point_name, lat, lng)
join routes r on r.route_name = v.route_name
where rp.route_id = r.id
  and rp.point_name = v.point_name
  and v.lat is not null
  and v.lng is not null;

-- Check: stops still on the placeholder coordinates
-- select r.route_name, rp.stop_sequence, rp.point_name
-- from route_points rp join routes r on r.id = rp.route_id
-- where rp.latitude = 14.6507 and rp.longitude = 121.1029
-- order by 1, 2;
