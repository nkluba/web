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
-- Riia - Pärnu - Tallinn
-- 	Tallinn - Pärnu - Riia
-- are different routes
-- direction_code take first symbol and last

-- trip_headsign - last stop
-- get direction of trip by stops, then get last stop and get trip_headsign by it

SELECT s.*
FROM stops s
JOIN stop_times st ON s.stop_id = st.stop_id
WHERE st.trip_id = 	1573009
ORDER BY geom <-> ST_SetSRID(ST_MakePoint(s.stop_lon, s.stop_lat), 4326);

-- Get stops which include both stop_1 and user_loc in routes + where direction is from user_loc to stop

SELECT 
    DISTINCT
    s.stop_name,
    s.stop_lat,
    s.stop_lon
FROM
    stops s
JOIN
    stop_times st ON s.stop_id = st.stop_id
JOIN
    trips t ON st.trip_id = t.trip_id
JOIN
    stop_times st_tempo ON t.trip_id = st_tempo.trip_id
JOIN
    stops s_tempo ON st_tempo.stop_id = s_tempo.stop_id
WHERE
    t.trip_id IN (
        SELECT
            st_inner.trip_id
        FROM
            stop_times st_inner
        JOIN
            stops s_inner ON st_inner.stop_id = s_inner.stop_id
        WHERE
            s_inner.stop_name = 'Tempo'
    )
    AND s.stop_area = 'Narva linn'
    AND st.stop_sequence < st_tempo.stop_sequence;