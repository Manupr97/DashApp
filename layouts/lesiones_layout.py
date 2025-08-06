from dash import html, dcc, dash_table
import pandas as pd
from utils.lesiones_data import load_lesiones

df = load_lesiones()

layout = html.Div([
    html.H2("Dashboard Área Médica: Lesiones de Jugadores"),
    
    html.Div([
        html.Label("Filtrar por jugador:", style={"color": "#2ecc71", "marginRight": "0.5rem"}),
        dcc.Dropdown(
            id='filtro-jugador',
            options=[{'label': j, 'value': j} for j in sorted(df['Jugador'].unique())],
            value=None,
            placeholder="Selecciona un jugador",
            multi=False,
            style={'width': '300px', 'fontSize': '1.1rem'}
        ),
        html.Label("Filtrar por tipo de lesión:", style={"color": "#2ecc71", "marginLeft": "2rem", "marginRight": "0.5rem"}),
        dcc.Dropdown(
            id='filtro-tipo-lesion',
            options=[{'label': t, 'value': t} for t in sorted(df['TipoLesion'].unique())],
            value=None,
            placeholder="Selecciona un tipo de lesión",
            multi=False,
            style={'width': '300px', 'fontSize': '1.1rem'}
        ),
    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '2rem'}),
    
    html.Div([
        dcc.Loading(
            id="loading-grafico-tipos",
            type="circle",
            children=dcc.Graph(id='grafico-tipos-lesion', style={'width': '48%', 'display': 'inline-block'})
        ),
        dcc.Loading(
            id="loading-grafico-zonas",
            type="circle",
            children=dcc.Graph(id='grafico-zonas-corporales', style={'width': '48%', 'display': 'inline-block'})
        ),
    ]),
    
    html.H4("Tabla de lesiones", style={"color": "#2ecc71", "marginTop": "2rem"}),
    dcc.Loading(
        id="loading-tabla-lesiones",
        type="circle",
        children=dash_table.DataTable(
            id='tabla-lesiones',
            columns=[{'name': col, 'id': col} for col in df.columns],
            data=df.to_dict('records'),
            page_size=10,
            filter_action='native',
            sort_action='native',
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'backgroundColor': 'transparent',
                'color': 'white',
                'fontSize': '1rem',
                'padding': '8px',
            },
            style_header={
                'backgroundColor': 'transparent',
                'fontWeight': 'bold',
                'border': '1px solid #007bff',
                'color': '#2ecc71',
                'fontSize': '1.1rem',
            },
            style_data={
                'border': '1px solid #007bff',
            },
            style_filter={
                'backgroundColor': 'transparent',
                'color': 'white',
            }
        )
    )
], style={"backgroundColor": "transparent", "padding": "1rem"})