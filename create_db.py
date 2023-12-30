import os
import pandas as pd
from sqlalchemy import create_engine

db_password = os.environ.get("DB_PASSWORD")
db_connection_string = f"postgresql://lubandust:{db_password}@ep-holy-cake-07968363.eu-central-1.aws.neon.tech/peatus?sslmode=require"

engine = create_engine(db_url)

def create_table_from_file(file_path):
    table_name = os.path.splitext(os.path.basename(file_path))[0]
    df = pd.read_csv(file_path)
    df.to_sql(table_name, engine, if_exists='replace', index=False)

def insert_data_into_tables():
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.txt'):
            file_path = os.path.join(folder_path, file_name)
            create_table_from_file(file_path)

if __name__ == "__main__":
    insert_data_into_tables()
