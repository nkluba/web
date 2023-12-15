from flask import Flask, render_template, request, jsonify
import psycopg2

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
        cursor.execute("SELECT stop_name FROM stops WHERE region = %s AND stop_name ILIKE %s", (region, f"%{stop}%"))
        stops = [row[0] for row in cursor.fetchall()]
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

    try:
        connection = psycopg2.connect(db_connection_string)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT DISTINCT ON (r.route_short_name)
                r.route_short_name,
                t.trip_id,
                t.trip_long_name,
                st.arrival_time,
                st.departure_time
            FROM stops s
            JOIN stop_times st ON s.stop_id = st.stop_id
            JOIN trips t ON st.trip_id = t.trip_id
            JOIN routes r ON t.route_id = r.route_id
            WHERE s.stop_name = %s
            ORDER BY r.route_short_name, st.arrival_time
        """, (selected_stop,))

        buses = [{
            'route_short_name': row[0],
            'trip_id': row[1],
            'trip_long_name': row[2],
            'arrival_time': row[3],
            'departure_time': row[4]
        } for row in cursor.fetchall()]

        connection.close()

        return jsonify({'buses': buses})

    except Exception as e:
        print("Error fetching bus data from the database:", str(e))
        return jsonify({'buses': []})

if __name__ == '__main__':
    app.run(debug=True)