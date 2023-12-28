import psycopg2
from datetime import datetime, timedelta

db_connection_string = "postgresql://lubandust:J9fF3NPzVeXW@ep-holy-cake-07968363.eu-central-1.aws.neon.tech/peatus?sslmode=require"


# Define the input parameters
service_ids = [224289, 224290] 
arrival_times = ['06:07:00', '14:33:00'] 
departure_times = ['06:20:00', '14:33:00']

# Connect to the database
conn = psycopg2.connect(db_connection_string)
cursor = conn.cursor()

try:
    current_user_time = datetime.now().strftime('%H:%M:%S')
    print(current_user_time)
    current_user_date = datetime.now().strftime('%Y%m%d')

    calendar_query = """
    SELECT service_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday
    FROM calendar
    WHERE service_id IN %s
    """
    cursor.execute(calendar_query, (tuple(service_ids),))
    calendar_data = cursor.fetchall()

    closest_arrivals = []

    current_day_of_week = datetime.now().weekday()

    for service_id, _, _, _, _, _, _, _ in calendar_data:
        service_index = service_ids.index(service_id)
        arrival_time = arrival_times[service_index]
        departure_time = departure_times[service_index]

        if calendar_data[service_ids.index(service_id)][current_day_of_week + 1] == 1:
            if arrival_time >= current_user_time:
                closest_arrivals.append((service_id, arrival_time, "Today"))
        if calendar_data[service_ids.index(service_id)][(current_day_of_week + 1) % 7 + 1] == 1:
            closest_arrivals.append((service_id, arrival_time, "Tomorrow"))

    closest_arrivals.sort(key=lambda x: (0 if x[2] == 'Today' else 1, x[1]))
    closest_arrivals = closest_arrivals[:5]

    print("Service ID\tArrival Time\tDay")
    for arrival in closest_arrivals:
        print(f"{arrival[0]}\t\t{arrival[1]}\t\t{arrival[2]}")

finally:
    cursor.close()
    conn.close()