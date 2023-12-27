from flask import Flask, render_template, request, jsonify
import psycopg2
from math import radians, sin, cos, sqrt, atan2
import datetime


app = Flask(__name__)

db_connection_string = "postgresql://lubandust:J9fF3NPzVeXW@ep-holy-cake-07968363.eu-central-1.aws.neon.tech/peatus?sslmode=require"


def get_regions_from_database():
    try:
        connection = psycopg2.connect(db_connection_string)
        cursor = connection.cursor()

        cursor.execute("SELECT DISTINCT stop_area FROM stops")
        regions = [row[0] for row in cursor.fetchall()]
        connection.close()
        return regions

    except Exception as e:
        print("Error fetching data from the database:", str(e))
        return []


def get_stops_for_region(region):
    try:
        connection = psycopg2.connect(db_connection_string)
        cursor = connection.cursor()
        cursor.execute("SELECT stop_name FROM stops WHERE stop_area = %s", (region,))
        stops = [row[0] for row in cursor.fetchall()]
        connection.close()
        return stops

    except Exception as e:
        print("Error fetching data from the database:", str(e))
        return []


@app.route('/')
def index():
    regions = get_regions_from_database()
    stops = get_stops_for_region(regions[0] if regions else "")
    return render_template('index.html', regions=regions, stops=stops)


@app.route('/get_stops', methods=['GET'])
def get_stops():
    input_region = request.args.get('region')
    input_stop = request.args.get('stop')

    stops = get_stops_for_region_and_stop(input_region, input_stop)
    return jsonify({'stops': stops})

def get_stops_for_region_and_stop(region, stop):
    try:
        connection = psycopg2.connect(db_connection_string)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT DISTINCT stop_name
            FROM stops
            WHERE stop_area = %s AND stop_name ILIKE %s
        """, (region, f"%{stop}%"))

        stops = [{'stop_name': row[0]} for row in cursor.fetchall()]

        connection.close()
        return stops
    except Exception as e:
        print("Error fetching data from the database:", str(e))
        return []

def get_regions_from_database_autocomplete(input_text):
    try:
        connection = psycopg2.connect(db_connection_string)
        cursor = connection.cursor()

        cursor.execute("SELECT DISTINCT stop_area FROM stops WHERE stop_area ILIKE %s", ('%' + input_text + '%',))
        regions = [row[0] for row in cursor.fetchall()]
        connection.close()
        return regions

    except Exception as e:
        print("Error fetching data from the database:", str(e))
        return []


@app.route('/get_regions_autocomplete', methods=['GET'])
def get_regions_autocomplete():
    input_text = request.args.get('input')
    regions = get_regions_from_database_autocomplete(input_text)

    return jsonify({'regions': regions})

@app.route('/get_buses', methods=['GET'])
def get_buses_for_stop():
    selected_stop = request.args.get('stop')
    selected_region = request.args.get('region')
    closest_stop = request.args.get('closest_stop')
    print(closest_stop)
    print(selected_stop)
    try:
        connection = psycopg2.connect(db_connection_string)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT DISTINCT t.trip_long_name, r.route_short_name, st1.arrival_time AS b_departure, st2.arrival_time AS b_arrival
            FROM stop_times st1
            JOIN stops s1 ON st1.stop_id = s1.stop_id
            JOIN stop_times st2 ON st1.trip_id = st2.trip_id
            JOIN stops s2 ON st2.stop_id = s2.stop_id
            JOIN trips t ON st1.trip_id = t.trip_id
            JOIN routes r ON t.route_id = r.route_id
            WHERE s1.stop_name = %s
                AND s2.stop_name = %s
                AND s1.stop_area = %s
                AND s2.stop_area = %s
                AND st1.stop_sequence < st2.stop_sequence
            ORDER BY b_departure;
        """, (closest_stop, selected_stop, selected_region, selected_region))

        buses = [{
            'trip_long_name': row[0],
            'b_departure': row[1],
            'b_arrival': row[2]
        } for row in cursor.fetchall()]

        print(buses)

        connection.close()

        return jsonify({'buses': buses})

    except Exception as e:
        print("Error fetching bus data from the database:", str(e))
        return jsonify({'buses': []})



@app.route('/send_user_location', methods=['GET'])
def receive_user_location():
    try:
        latitude = request.args.get('latitude')
        longitude = request.args.get('longitude')
        bus_route = request.args.get('bus_route')

        print(f"User location received - Latitude: {latitude}, Longitude: {longitude}, Bus Route: {bus_route}")

        return jsonify({'status': 'success', 'message': 'User location received successfully'})

    except Exception as e:
        print(f"Error processing user location: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error processing user location'})


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

def get_trip_long_name(bus_route):
    return bus_route.split(' - ', 1)[1]

def get_stops_for_trip(trip_long_name):
    try:
        connection = psycopg2.connect(db_connection_string)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT s.stop_name, s.stop_lat, s.stop_lon
            FROM stops s
            JOIN stop_times st ON s.stop_id = st.stop_id
            JOIN trips t ON st.trip_id = t.trip_id
            WHERE t.trip_long_name = %s
        """, (trip_long_name,))

        stops = [{'stop_id': row[0], 'stop_lat': row[1], 'stop_lon': row[2]} for row in cursor.fetchall()]

        connection.close()
        return stops

    except Exception as e:
        print("Error fetching stops from the database:", str(e))
        return []
    

def get_closest_stops(selected_stop, stop_area):
    try:
        connection = psycopg2.connect(db_connection_string)
        cursor = connection.cursor()

        sql_query = """
            SELECT DISTINCT
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
                        s_inner.stop_name = %s
                )
                AND s.stop_area = %s
                AND st.stop_sequence < st_tempo.stop_sequence;
        """
        cursor.execute(sql_query, (selected_stop, stop_area))
        
        stops = [{'stop_id': row[0], 'stop_lat': row[1], 'stop_lon': row[2]} for row in cursor.fetchall()]

        connection.close()
        return stops
    
    except Exception as e:
        print("Error fetching closest stop from the database:", str(e))
        return []
    

@app.route('/get_closest_stop', methods=['GET'])
def get_closest_stop():
    try:
        user_latitude = request.args.get('latitude')
        user_longitude = request.args.get('longitude')
        selected_stop = request.args.get('selected_stop')
        stop_area = request.args.get('stop_area')

        stops = get_closest_stops(selected_stop, stop_area)

        if not stops:
            return jsonify({'status': 'error', 'message': 'No stops found for the given trip_long_name'})

        for stop in stops:
            stop['distance'] = haversine(float(user_latitude), float(user_longitude), float(stop['stop_lat']), float(stop['stop_lon']))

        closest_stop = min(stops, key=lambda x: x['distance'])
        return jsonify({'status': 'success', 'closest_stop': closest_stop})

    except Exception as e:
        print("Error processing user location:", str(e))
        return jsonify({'status': 'error', 'message': 'Error processing user location'})


@app.route('/get_closest_arrivals', methods=['GET'])
def get_closest_arrivals():
    try:
        bus_route = request.args.get('bus_route').split(' - ', 1)[1] #get Tehase - Kannuka part
        closest_stop_name = request.args.get('closest_stop')
        print(closest_stop_name)
        selected_stop_name = request.args.get('selected_stop')
        print(selected_stop_name)
        connection = psycopg2.connect(db_connection_string)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT DISTINCT t.trip_long_name, st1.arrival_time, r.route_short_name
            FROM stop_times st1
            JOIN stop_times st2 ON st1.trip_id = st2.trip_id
            JOIN stops s1 ON st1.stop_id = s1.stop_id
            JOIN stops s2 ON st2.stop_id = s2.stop_id
            JOIN trips t ON st1.trip_id = t.trip_id
            JOIN routes r ON t.route_id = r.route_id
            WHERE t.trip_long_name = %s
                AND s1.stop_name = %s
                AND s2.stop_name = %s
                AND st1.stop_sequence < st2.stop_sequence
            ORDER BY st1.arrival_time;
        """, (bus_route, closest_stop_name, selected_stop_name))
        user_time = datetime.datetime.strptime("10:00:00", "%H:%M:%S")

        arrivals = [{
            'trip_long_name': row[0],
            'arrival_time': row[1],
            'route_short_name': row[2]
        } for row in cursor.fetchall() if datetime.datetime.strptime(row[1], "%H:%M:%S") > user_time]

        return jsonify({'status': 'success', 'arrivals': arrivals, 'closest_stop_id': closest_stop_name})

    except Exception as e:
        print("Error fetching arrivals from the database:", str(e))
        return jsonify({'status': 'error', 'message': 'Error fetching arrivals'})
    

if __name__ == '__main__':
    app.run(debug=True)