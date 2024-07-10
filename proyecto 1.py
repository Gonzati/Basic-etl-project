# Importing the required libraries
import glob
import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime
from bs4 import BeautifulSoup
import requests

url = 'https://web.archive.org/web/20230902185326/https://en.wikipedia.org/wiki/List_of_countries_by_GDP_%28nominal%29'
db_name = 'World_Economies.db'
table_name = 'Countries_by_GDP'
table_attribs = ["Country", "GDP_USD_Billion"]
csv_path = './Countries_by_GDP.csv'  # cambiado para funcionar en local
log_file = "Etl_project_log.txt"
target_file = "Countries_by_GDP.csv"
df = pd.DataFrame(columns=table_attribs)

# Función de extracción
def extract(url, table_attribs):
    page = requests.get(url).text
    data = BeautifulSoup(page, 'html.parser')
    df = pd.DataFrame(columns=table_attribs)
    tables = data.find_all('tbody')
    rows = tables[2].find_all('tr')
    for row in rows:
        col = row.find_all('td')
        if len(col) != 0:
            if col[0].find('a') is not None and '—' not in col[2].text:
                data_dict = {"Country": col[0].a.contents[0],
                             "GDP_USD_millions": col[2].contents[0]}
                df1 = pd.DataFrame(data_dict, index=[0])
                df = pd.concat([df, df1], ignore_index=True)
    return df

# Función de transformación
def transform(df):
    # Guardar la columna como una lista
    gdp_millions = df['GDP_USD_millions'].tolist()
    
    # Convertir el texto de moneda a números flotantes y dividir por 1000
    gdp_billions = []
    for value in gdp_millions:
        numeric_value = float(''.join(value.split(',')))
        gdp_billions.append(np.round(numeric_value / 1000, 2))
    
    # Asignar la lista modificada de nuevo al DataFrame
    df['GDP_USD_Billion'] = gdp_billions
    
    # Eliminar la columna original
    df.drop(columns=['GDP_USD_millions'], inplace=True)
    
    return df

# Esta función guarda el df en csv
def load_data(target_file, transformed_data):
    transformed_data.to_csv(target_file, index=False)

# Esta función guarda el df en la base de datos
def load_to_db(df, sql_connection, table_name):
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)
    print("Table is ready")

# Función para ejecutar una consulta en la base de datos
def run_query(query_statement, sql_connection):
    query_output = pd.read_sql(query_statement, sql_connection)
    print(query_statement)
    print(query_output)

# Función para registrar el progreso
def log_progress(message):
    timestamp_format = '%Y-%m-%d %H:%M:%S'  # Year-Month-Day Hour:Minute:Second
    now = datetime.now()  # get current timestamp
    timestamp = now.strftime(timestamp_format)
    with open(log_file, "a") as f:
        f.write(timestamp + ',' + message + '\n')

# Visualizar avance
try:
    log_progress('Preliminaries complete. Initiating ETL process')
    df = extract(url, table_attribs)
    log_progress('Data extraction complete. Initiating Transformation process')
    df = transform(df)
    log_progress('Data transformation complete. Initiating loading process')
    load_data(csv_path, df)
    log_progress('Data saved to CSV file')
    sql_connection = sqlite3.connect(db_name)
    log_progress('SQL Connection initiated.')
    load_to_db(df, sql_connection, table_name)
    log_progress('Data loaded to Database as table. Running the query')
    query_statement = f"SELECT * from {table_name} WHERE GDP_USD_Billion >= 100"
    run_query(query_statement, sql_connection)
    log_progress('Process Complete.')
    sql_connection.close()
except Exception as e:
    log_progress(f"ETL Job Failed: {str(e)}")
