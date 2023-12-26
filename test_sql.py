import psycopg2

# Connect to your PostgreSQL database
db_connection_string = "postgresql://lubandust:J9fF3NPzVeXW@ep-holy-cake-07968363.eu-central-1.aws.neon.tech/peatus?sslmode=require"

conn = psycopg2.connect(db_connection_string)

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Execute the initial query to get stop_ids
initial_query = """
    SELECT DISTINCT
        s.stop_id
    FROM
        stops s
    JOIN
        stop_times st ON s.stop_id = st.stop_id
    JOIN
        trips t ON st.trip_id = t.trip_id
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
        AND s.stop_area = 'Narva linn';
"""

cursor.execute(initial_query)
stop_ids = [row[0] for row in cursor.fetchall()]

# Create a dictionary to store stop_sequence for each stop_id
stop_sequence_dict = {}

# Iterate over each stop_id and check stop_sequence
for stop_id in stop_ids:
    # Query to get stop_sequence for the given stop_id
    sequence_query = f"""
        SELECT
            stop_sequence
        FROM
            stop_times
        WHERE
            stop_id = {stop_id}
    """
    cursor.execute(sequence_query)
    stop_sequence = cursor.fetchone()

    if stop_sequence:
        # Store stop_sequence in the dictionary
        stop_sequence_dict[stop_id] = stop_sequence[0]

# Close the cursor and connection
cursor.close()
conn.close()

# Now stop_sequence_dict contains stop_id as keys and stop_sequence as values
print(stop_sequence_dict)
