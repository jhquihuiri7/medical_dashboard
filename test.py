
import dash
from dash import dcc, html, Input, Output
import numpy as np
import pandas as pd
import datetime
from datetime import datetime as dt
import pathlib
import plotly.graph_objects as go
import plotly.io as pio

BASE_PATH = pathlib.Path(__file__).parent.resolve()
DATA_PATH = BASE_PATH.joinpath("data").resolve()
def preprocesamiento(df):
    # Llenar las categorias vacias con 'No Identificado'
    df["Admit Source"] = df["Admit Source"].fillna("Not Identified")
    # Date
    # Formateo "checkin Time"
    df["Check-In Time"] = df["Check-In Time"].apply(
        lambda x: dt.strptime(x, "%Y-%m-%d %I:%M:%S %p")
    )  # String -> Datetime

    # Insertar día de la semana y hora del "Checking time"
    df["Days of Wk"] = df["Check-In Hour"] = df["Check-In Time"]
    df["Days of Wk"] = df["Days of Wk"].apply(
        lambda x: dt.strftime(x, "%A")
    )  # Datetime -> weekday string
    df["Weekday Number"] = df["Check-In Time"].dt.dayofweek
    df["Check-In Hour"] = df["Check-In Hour"].apply(
        lambda x: dt.strftime(x, "%I %p")
    )  # Datetime -> int(hour) + AM/PM
    df["Hour"] = df["Check-In Hour"].str[:3]
    df["Time"] = df["Check-In Hour"].str[3:]

    return df
# Leer los datos y limpiarlos
df = pd.read_csv(DATA_PATH.joinpath("clinical_analytics.csv.gz"))
# realizar preprocesamiento de fecha
df = preprocesamiento(df)

