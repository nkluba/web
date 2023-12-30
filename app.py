from flask import Flask, render_template, request, jsonify
import psycopg2
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta
import os


app = Flask(__name__)

db_password = os.environ.get("DB_PASSWORD")
db_connection_string = f"postgresql://lubandust:{db_password}@ep-holy-cake-07968363.eu-central-1.aws.neon.tech/peatus?sslmode=require"

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


# get stops of selected region
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


# select values for further timetable build and for its display
# stop_sequence condition is user to setermine if bus goes from stop1 to stop2 or in other turn
# to avoid cases with directions mismatch
# + it's assumed that stops with the same name are located close to each other
# for example both stops in Narva in both directions are called 'Tempo'

@app.route('/get_buses', methods=['GET'])
def get_buses_for_stop():
    selected_stop = request.args.get('stop')
    selected_region = request.args.get('region')
    closest_stop = request.args.get('closest_stop')

    try:
        connection = psycopg2.connect(db_connection_string)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT DISTINCT t.service_id, t.trip_long_name, r.route_short_name, st1.arrival_time AS b_departure, st2.arrival_time AS b_arrival
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
            'service_id': row[0],
            'trip_long_name': row[1],
            'route_short_name': row[2],
            'b_departure': row[3],
            'b_arrival': row[4],
            'closest_stop' : closest_stop,
        } for row in cursor.fetchall()]

        connection.close()

        return jsonify({'buses': buses})

    except Exception as e:
        print("Error fetching bus data from the database:", str(e))
        return jsonify({'buses': []})


# count distance between stops to get closest
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
    

# get closest stop with same stop_sequence condition
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
    

# return closest stop for frontend
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


# build timetable from given buses basing on timetable of service_id
# consisting of days of week + trips at that time per day
# also build it for tomorrow day (will be cut if today's date and time after user time)
# have five or more trips
    
@app.route('/get_timetable', methods=['GET'])
def get_timetable():
    service_ids = list(map(int, request.args.get('service_id').split(',')))
    departure_times = list(map(str, request.args.get('bDeparture').split(',')))
    arrival_times = list(map(str, request.args.get('bArrival').split(',')))
    conn = psycopg2.connect(db_connection_string)
    cursor = conn.cursor()

    try:
        current_user_time = datetime.now().strftime('%H:%M:%S')

        calendar_query = """
        SELECT service_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday
        FROM calendar
        WHERE service_id IN %s
        """
        cursor.execute(calendar_query, (tuple(service_ids),))
        calendar_data = cursor.fetchall()
        cursor.close()
        conn.close()

        closest_arrivals = []

        current_day_of_week = datetime.now().weekday()

        for service_id, _, _, _, _, _, _, _ in calendar_data:
            service_index = service_ids.index(service_id)
            arrival_time = arrival_times[service_index]
            departure_time = departure_times[service_index]

            # if bus departure happens after user time and today, write it and save with 'Today' mark

            if calendar_data[service_ids.index(service_id)][current_day_of_week + 1] == 1:
                if departure_time >= current_user_time:
                    closest_arrivals.append((service_id, arrival_time, departure_time, "Today"))
            if calendar_data[service_ids.index(service_id)][(current_day_of_week + 1) % 7 + 1] == 1:
                closest_arrivals.append((service_id, arrival_time, departure_time, "Tomorrow"))

        # sort
                
        closest_arrivals.sort(key=lambda x: (0 if x[3] == 'Today' else 1, x[1]))
        closest_arrivals = [(x[1], x[2], x[3]) for x in closest_arrivals]
        unique_arrivals = []

        # get unique ones so trips happening at the same time are not displayed twice
        
        seen = set()
        for arrival in closest_arrivals:
            if arrival not in seen:
                unique_arrivals.append(arrival)
                seen.add(arrival)

        unique_arrivals = unique_arrivals[:5]

        result_data = []
        for arrival in unique_arrivals:
            result_data.append({
                'bArrival': arrival[0],
                'bDeparture': arrival[1],
                'day': arrival[2]
            })

        return jsonify(result_data)

    except Exception as e:
        print("Error fetching timetable:", str(e))
        return jsonify({'status': 'error', 'message': 'Error fetching timetable'})
        


if __name__ == '__main__':
    app.run(debug=True)