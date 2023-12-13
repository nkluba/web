from flask import Flask, render_template
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


@app.route('/')
def index():
    regions = get_regions_from_database()
    return render_template('index.html', regions=regions)


if __name__ == '__main__':
    app.run(debug=True)