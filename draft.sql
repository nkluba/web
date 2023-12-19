SELECT trip_id
FROM trips
WHERE trip_long_name = 'Narva - Sillamäe - Jõhvi - Keskhaigla';

SELECT stop_sequence
FROM stop_times
WHERE trip_id = 1573009
  AND stop_id = 32371;

SELECT s.*
FROM stops s
JOIN stop_times st ON s.stop_id = st.stop_id
WHERE st.trip_id = 	1573009
ORDER BY s.stop_lat, s.stop_lon;

-- CREATE EXTENSION postgis;

-- Enable PostGIS for a specific database
-- CREATE EXTENSION postgis_topology;

-- ALTER TABLE stops ADD COLUMN geom geometry(Point, 4326);

-- Update the geometry column with the lat and lon values
-- UPDATE stops SET geom = ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326);

-- CREATE INDEX stops_geom_idx ON stops USING GIST (geom);

-- SELECT stop_name, stop_id, stop_lat, stop_lon
-- FROM stops
-- ORDER BY geom <-> ST_SetSRID(ST_MakePoint(stop_lon, stop_lat), 4326);


SELECT s.*
FROM stops s
JOIN stop_times st ON s.stop_id = st.stop_id
WHERE st.trip_id = 	1573009
ORDER BY geom <-> ST_SetSRID(ST_MakePoint(s.stop_lon, s.stop_lat), 4326);