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
        print(region)
        cursor.execute("SELECT stop_name FROM stops WHERE stop_area = %s", (region,))
        stops = [row[0] for row in cursor.fetchall()]
        print(stops)
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


@app.route('/search', methods=['GET'])
def search():
    selected_region = request.args.get('region')
    stops = get_stops_for_region(selected_region)
    return render_template('index.html', regions=get_regions_from_database(), stops=stops)


if __name__ == '__main__':
    app.run(debug=True)