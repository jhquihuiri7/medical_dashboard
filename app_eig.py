import dash
from dash import dcc, html, Input, Output

import pandas as pd
from datetime import datetime as dt
import pathlib
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
############# Elements
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


# Path
BASE_PATH = pathlib.Path(__file__).parent.resolve()
DATA_PATH = BASE_PATH.joinpath("data").resolve()

# Leer los datos y limpiarlos
df = pd.read_csv(DATA_PATH.joinpath("clinical_analytics.csv.gz"))

# realizar preprocesamiento de fecha
df = preprocesamiento(df)


nombres_clinicas = sorted(df["Clinic Name"].unique())
admit_source = sorted(df["Admit Source"].unique())


#####################################################
# Estructura App
external_scripts = [{"src": "https://cdn.tailwindcss.com"}]
def set_config(img_name):
    return {
             "displaylogo": False,
             "modeBarButtonsToRemove": [
                 "zoom",
                 "pan",
                 "zoom"
                 "autoScale",
                 "resetScale",
             ],
             "toImageButtonOptions": {
                 "format": "png",
                 "filename": img_name,
                 "height": 700,
                 "width": 1300,
                 "scale": 1,
             },
         }
app = dash.Dash(
    __name__,
    external_scripts=external_scripts,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "Dashboard Análisis Clínico"
app._favicon = "favicon.ico"
app.layout = html.Div(
    className="flex flex-col justify-around bg-white p-6 sm:flex-row",
    children=[
        html.Div(
            children=[
                html.H1(
                    "Análisis Clínico", className="text-[#2c8cff] text-4xl font-bold"
                ),
                html.H2(
                    "Bienvenidos al Dashboard Análisis Clínico",
                    className="text-5xl font-bold py-8",
                ),
                html.P(
                    "Explora el volumen de pacientes en la clínica según la hora del día, el tiempo de espera y la puntuación de atención. Haz clic en el mapa de calor para visualizar la experiencia del paciente en diferentes momentos.",
                    className="text-justify pb-8",
                ),
                html.Label("Seleccionar Clínica", className="font-bold pb-5"),
                dcc.Dropdown(
                    nombres_clinicas,
                    nombres_clinicas[2],
                    id="clinic-dropdown",
                    className="pb-8",
                ),
                html.Label("Seleccionar Hora de Registro", className="font-bold pb-5"),
                dcc.DatePickerRange(
                    id="date-picker-range",
                    className="pb-8",
                    min_date_allowed=df["Check-In Time"].dt.date.min(),
                    max_date_allowed=df["Check-In Time"].dt.date.max(),
                    initial_visible_month=df["Check-In Time"].dt.date.min(),
                    start_date=df["Check-In Time"].dt.date.min(),
                    end_date=df["Check-In Time"].dt.date.max(),
                ),
                html.Label("Seleccionar Fuente de Admisión", className="font-bold pb-5"),
                dcc.Dropdown(
                    admit_source,
                    admit_source,
                    multi=True,
                    id="admit-dropdown",
                    className="",
                ),
            ],
            className="flex-initial w-[100%] sm:w-[28%]",
        ),
        html.Div(
            children=[
                html.H3("Volumen de Pacientes", className="font-bold text-center text-3xl py-8"),
                html.Hr(),
                dcc.Graph(
                    className="hidden sm:flex",
                    id="heat_map",
                    config= set_config('VolumenPacientes'),
                ),
                dcc.Graph(
                    className="flex sm:hidden",
                    id="heat_map_vertical",
                    config=set_config('VolumenPacientes'),
                ),
                html.H3("Distribución de tiempo de espera por departamento", className="font-bold text-center text-3xl py-8"),
                html.Hr(),
                dcc.Graph(
                    id="boxplot-waiting_time",
                    className="",
                    config=set_config('TiempoEspera')
                ),
                html.H3("Distribución de puntajes de calificación por departamento", className="font-bold text-center text-3xl py-8"),
                html.Hr(),
                dcc.Graph(
                    id="boxplot-score",
                    className="",
                    config=set_config('Calificacion')
                ),
            ],
            className="flex-initial w-[100%] sm:w-[70%]",
        ),
    ],
)


@app.callback(
    [Output("heat_map", "figure"),Output("heat_map_vertical", "figure"),Output('boxplot-waiting_time', 'figure'),Output('boxplot-score', 'figure')],
    Input("clinic-dropdown", "value"),
    Input("date-picker-range", "start_date"),
    Input("date-picker-range", "end_date"),
    Input("admit-dropdown", "value"),
)
def plots(clinic, start_date, end_date, admit):
    filter_data = data(df, clinic, start_date, end_date, admit)
    heatmap_data = get_heatmap_data(filter_data)
    departments = ['General Surgery', 'Orthopedics', 'Neurosurgery', 'Plastic Surgery', 'Urology']
    fig1 = draw_heatmap(heatmap_data.values, heatmap_data.columns, heatmap_data.index)
    fig2 = draw_heatmap(heatmap_data.values.T, heatmap_data.index, heatmap_data.columns)

    filter_departments = filter_data[filter_data['Department'].isin(departments)]

    fig3 = draw_boxplot(departments, filter_departments,'Wait Time Min')
    fig4 = draw_boxplot(departments, filter_departments, 'Care Score')

    return fig1, fig2, fig3, fig4

def data(df, clinic, start_date, end_date, admit):
    new_df = df[
        (df["Clinic Name"] == clinic)
        & (df["Check-In Time"] >= start_date)
        & (df["Check-In Time"] <= end_date)
        & (df["Admit Source"].isin(admit))
        ]
    return new_df

def get_heatmap_data(filter):
    date_filtered = filter
    grouped = date_filtered.groupby(
        ["Days of Wk", "Weekday Number", "Check-In Hour", "Hour", "Time"]
    ).agg({"Number of Records": "sum"})
    grouped = grouped.reset_index()
    grouped.sort_values(by=['Weekday Number', 'Hour', 'Time'], inplace=True)
    grouped_AM = grouped[grouped["Time"] == "AM"]
    grouped_PM = grouped[grouped["Time"] == "PM"]
    final = pd.concat([grouped_AM, grouped_PM], ignore_index=True)
    original_row_order = final[
        "Days of Wk"
    ].unique()
    original_col_order = final["Check-In Hour"].unique()
    heatmap_data = final.pivot_table(
        index="Days of Wk",
        columns="Check-In Hour",
        values="Number of Records",
        fill_value=0,
    )
    return heatmap_data.reindex(
        index=original_row_order, columns=original_col_order, fill_value=0
    )

def draw_heatmap(z,x,y):
    hover = [[f"{round(val)} Patients records" for val in row] for row in z]
    return go.Figure(
        go.Heatmap(
            z=z,
            x=x,
            y=y,
            text=z,
            texttemplate="%{text}",
            textfont={"size": 12},
            showscale=False,
            hovertext=hover,
            hoverinfo="text",
        ),
        layout=go.Layout(
            xaxis=dict(side="top", tickangle=-90, fixedrange=True),
            yaxis=dict(fixedrange=True),  # Place x-axis labels at the top
            margin=go.layout.Margin(
                l=0,  # left margin
                r=0,  # right margin
                b=0,  # bottom margin
            ),
        ),
    )

def draw_boxplot(departments, filter_departments, column):
    fig = go.Figure(
        layout=go.Layout(
            template='plotly_white',
            xaxis=dict(fixedrange=True),
            yaxis=dict(fixedrange=True),  # Place x-axis labels at the top
            margin=go.layout.Margin(
                t=10,
                l=0,  # left margin
                r=0,  # right margin
                b=0,  # bottom margin
            ),
        )
    )
    for department in departments:
        fig.add_trace(
            go.Box(y=filter_departments[filter_departments['Department'] == department][column],
                   name=department),
        )

    return fig

if __name__ == "__main__":
    app.run_server(debug=False)
