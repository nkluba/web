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
        print("Regions:", regions)
        connection.close()
        return regions

    except Exception as e:
        print("Error fetching data from the database:", str(e))
        return []


def get_stops_for_region(region):
    try:
        connection = psycopg2.connect(db_connection_string)
        cursor = connection.cursor()

        cursor.execute("SELECT DISTINCT stop_name FROM stops WHERE stop_area = %s", (region,))
        stops = [row[0] for row in cursor.fetchall()]
        print("Stops for region {}: {}".format(region, stops))
        connection.close()
        return stops

    except Exception as e:
        print("Error fetching stops from the database:", str(e))
        return []


@app.route('/')
def index():
    regions = get_regions_from_database()
    return render_template('index.html', regions=regions)


@app.route('/get_stops', methods=['GET'])
def get_stops():
    region = request.args.get('region')
    stops = get_stops_for_region(region)
    return jsonify(stops=stops)


if __name__ == '__main__':
    app.run(debug=True)