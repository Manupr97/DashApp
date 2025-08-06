from ctypes import alignment
from flask import Flask, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from config import Config
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import unicodedata
from utils.pdf_report import (
    generar_pdf_postpartido,
    get_stats_partido,
    crear_radar_png,
    crear_barras_png,
    get_radar_path,
    get_barras_path,
    limpiar_tmp  
)
from utils.lesiones_data import load_lesiones
from layouts.lesiones_layout import layout as lesiones_layout
from callbacks.lesiones_callbacks import register_lesiones_callbacks

# Flask server y configuración
server = Flask(__name__)
server.config.from_object(Config)

# Leer los datos solo una vez
matches = pd.read_csv('data\La Liga Full Match List 24-25.csv')
stats = pd.read_csv('data\La Liga 24-25.csv')
df_lesiones = load_lesiones()


def tabla_metricas_generales(local, visitante, stats_local, stats_visitante):
    # Métricas a mostrar
    metricas = [
        ("xG", "xG"),
        ("Posesión", "Possession"),
        ("Field Tilt", "Field Tilt"),
        ("Pass in Opp. Half", "Passes in Opposition Half"),
        ("PPDA", "PPDA"),
        ("High Recovery", "High Recoveries"),
        ("Crosses", "Crosses"),
        ("Corners", "Corners"),
        ("Fouls", "Fouls"),
    ]
    # Construir la tabla
    header = html.Tr([
        html.Th("Métrica", style={"fontWeight": "bold"}),
        html.Th(local, style={"fontWeight": "bold"}),
        html.Th(visitante, style={"fontWeight": "bold"})
    ])
    rows = []
    for nombre, col in metricas:
        val_local = stats_local[col]
        val_visitante = stats_visitante[col]
        # Formato especial para porcentajes
        if "Possession" in col or "Field Tilt" in col:
            val_local = f"{val_local}%"
            val_visitante = f"{val_visitante}%"
        rows.append(
            html.Tr([
                html.Td(nombre, style={"fontWeight": "bold"}),
                html.Td(val_local),
                html.Td(val_visitante)
            ])
        )
    return dbc.Table(
        [html.Thead(header), html.Tbody(rows)],
        bordered=True,
        style={
            "background": "transparent",
            "color": "#fff",
            "fontSize": "1.1rem",
            "borderColor": "#2ecc71",  # Cambia por el color que prefieras
            "borderWidth": "2px"
        }
    )

def ranking_mini_tabla(local, visitante, stats, fecha):
    metricas = [
        ("Goles", "Goals"),
        ("xG", "xG"),
        ("xA", "xA") if "xA" in stats.columns else None,
        ("Asistencias", "Assists") if "Assists" in stats.columns else None,
        ("Recuperaciones", "High Recoveries"),
        ("Faltas", "Fouls"),
        ("Corners", "Corners"),
    ]
    metricas = [m for m in metricas if m is not None]
    header = html.Tr([
        html.Th("Métrica", style={"fontWeight": "bold"}),
        html.Th(local, style={"fontWeight": "bold"}),
        html.Th(visitante, style={"fontWeight": "bold"})
    ])
    rows = []
    for nombre, col in metricas:
        partidos = stats[stats['Date'] == fecha]
        ranking = partidos.sort_values(by=col, ascending=False).reset_index(drop=True)
        pos_local = ranking[ranking['Team'] == local].index[0] + 1
        pos_visitante = ranking[ranking['Team'] == visitante].index[0] + 1
        rows.append(
            html.Tr([
                html.Td(nombre, style={"fontWeight": "bold"}),
                html.Td(f"{pos_local}º"),
                html.Td(f"{pos_visitante}º")
            ])
        )
    return dbc.Table([html.Thead(header), html.Tbody(rows)],
                     bordered=True,
                     style={
                         "background": "transparent",
                         "color": "#fff",
                         "fontSize": "1.1rem",
                         "borderColor": "#2ecc71",
                         "borderWidth": "2px"
                     })

def crear_grafico_barras(local, visitante, valores_local, valores_visitante, metricas):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=metricas,
        x=valores_local,
        name=local,
        orientation='h',
        marker=dict(color='#2ecc71'),
        text=valores_local,
        textposition='auto'
    ))
    fig.add_trace(go.Bar(
        y=metricas,
        x=valores_visitante,
        name=visitante,
        orientation='h',
        marker=dict(color='#3498db'),
        text=valores_visitante,
        textposition='auto'
    ))
    fig.update_layout(
        barmode='group',
        plot_bgcolor='#24282a',
        paper_bgcolor='#24282a',
        font=dict(color='#fff'),
        legend=dict(font=dict(color='#fff')),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False)
    )
    return fig

def get_escudo_path(equipo):
    # Quita tildes y pasa a minúsculas
    nombre = unicodedata.normalize('NFKD', equipo).encode('ascii', 'ignore').decode('utf-8')
    nombre = nombre.replace(" ", "_").lower()
    return f"/assets/Escudos/{nombre}.png"

@server.route('/descargar_pdf/<partido>')
def descargar_pdf(partido):
    partido_row = matches[matches['Match'] == partido].iloc[0]
    local = partido_row['Home']
    visitante = partido_row['Away']

    stats_local, stats_visitante = get_stats_partido(stats, partido, local, visitante)

    radar_path = get_radar_path(partido)
    barras_path = get_barras_path(partido)
    crear_radar_png(local, visitante, stats_local, stats_visitante, partido, radar_path)
    crear_barras_png(local, visitante, stats_local, stats_visitante, barras_path)

    buffer = generar_pdf_postpartido(partido_row, stats)
    buffer.seek(0)

    limpiar_tmp(radar_path, barras_path)

    return send_file(buffer, as_attachment=True, download_name=f"{partido_row['Match']}.pdf", mimetype='application/pdf')

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/"

# Usuario simple
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = str(id)  # ¡OJO! El id debe ser string
        self.username = username
        self.password = password

# Diccionario de usuarios de prueba
USERS = {
    "admin": User(id=1, username="admin", password="admin"),
    "analista": User(id=2, username="analista", password="futbol123"),
}

@login_manager.user_loader
def load_user(user_id):
    print(f"load_user: buscando user_id={user_id}")
    for user in USERS.values():
        if user.id == str(user_id):
            print(f"load_user: encontrado {user.username}")
            return user
    print("load_user: no encontrado")
    return None

# Dash app
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Registrar callbacks de lesiones
register_lesiones_callbacks(app)

# Layouts mínimos
login_layout = dbc.Container([
    html.H2("Login"),
    dbc.Input(id="username", type="text", placeholder="Usuario"),
    dbc.Input(id="password", type="password", placeholder="Contraseña"),
    dbc.Button("Entrar", id="login-button", n_clicks=0),
    html.Div(id="login-output")
], className="custom-page")

# Layouts de cada página
home_layout = html.Div(
    [
        html.Div([
            html.Img(src="/assets/identidad_MPR_2.png", height="80px", style={"marginBottom": "1rem"}),
            html.H1("Dashboard Post-Partido LaLiga", style={"color": "#2ecc71"}),
            html.P(
                "Explora informes post-partido con estadísticas avanzadas de LaLiga 24/25. "
                "Selecciona un partido, analiza el rendimiento de ambos equipos y descarga el reporte en PDF.",
                style={"fontSize": "1.2rem", "color": "#fff"}
            ),
            dbc.Button(
                "Ir al análisis post-partido",
                href="/performance",
                color="primary",
                size="lg",
                style={"marginTop": "2rem", "marginRight": "1rem", "display": "inline-block"}
            ),

            dbc.Button(
                "Ir al área médica",
                href="/medico",  
                color="primary",
                size="lg",
                style={"marginTop": "2rem", "display": "inline-block"}
            ),
        ], style={
            "textAlign": "center",
            "background": "rgba(36,40,42,0.95)",
            "borderRadius": "16px",
            "padding": "3rem",
            "boxShadow": "0 4px 24px rgba(0,0,0,0.2)",
            "maxWidth": "600px",
            "margin": "4rem auto"
        }),
    ],
    style={
        "minHeight": "100vh",
        "background": "linear-gradient(120deg, #24282a 60%, #007bff 100%)"
    })

# Obtén los valores únicos para los dropdowns
equipos_unicos = sorted(set(matches['Home']).union(set(matches['Away'])))
jornadas_unicas = sorted(matches['Round'].unique())

performance_layout = html.Div([
    html.Div([
        dcc.Dropdown(
            id='selector-equipo',
            options=[{'label': eq, 'value': eq} for eq in equipos_unicos],
            placeholder="Filtrar por equipo",
            style={'width': '60%', 'display': 'inline-block', 'marginRight': '2rem'}
        ),
        dcc.Dropdown(
            id='selector-jornada',
            options=[{'label': f"Jornada {j}", 'value': j} for j in jornadas_unicas],
            placeholder="Filtrar por jornada",
            style={'width': '60%', 'display': 'inline-block', 'marginRight': '2rem'}
        ),
        dcc.Dropdown(
            id='selector-partido',
            options=[],  # Se rellenará dinámicamente
            placeholder="Selecciona un partido",
            style={'width': '75%', 'display': 'inline-block', 'marginRight': '2rem'}
        ),
    ], style={'width': '60%', 'margin': '0 auto', 'marginBottom': '2rem', 'textAlign': 'center'}),
    html.Div(id="cabecera-partido", style={"textAlign": "center", "marginBottom": "2rem"}),
    dbc.Row([
        dbc.Col(
            html.Div([
                html.H4("Estadísticas Generales", style={
                    "color": "#2ecc71",
                    "marginBottom": "1rem",
                    "textAlign": "center"
                }),
                html.Div(id="tabla-metricas")
            ]),
            width=6,
            style={"paddingRight": "3rem"}
        ),
        dbc.Col(
            html.Div([
                html.H4("Radar de Métricas Avanzadas", style={
                    "color": "#3498db",
                    "marginBottom": "1rem",
                    "textAlign": "center"
                }),
                dcc.Graph(id="radar-metricas", config={"displayModeBar": False})
            ]),
            width=6,
            style={"paddingLeft": "3rem"}
        )
    ], style={"marginBottom": "2.5rem", "alignItems": "center"}),
    dbc.Row([
        dbc.Col(
            html.Div([
                html.H4("Barras de Métricas Extra", style={
                    "color": "#2ecc71",
                    "marginBottom": "1rem",
                    "textAlign": "center"
                }),
                dcc.Graph(id="barras-extra", config={"displayModeBar": False})
            ]),
            width=7,
            style={"paddingRight": "2rem", "border": "2px solid #2ecc71", "borderRadius": "12px", "background": "rgba(36,40,42,0.7)"}
        ),
        dbc.Col(
            html.Div([
                html.H4("Ranking en la Jornada", style={
                    "color": "#2ecc71",
                    "marginBottom": "1rem",
                    "textAlign": "center"
                }),
                html.Div(id="mini-ranking")
            ]),
            width=5,
            style={"paddingLeft": "2rem"}
        ),
    ], style={"marginBottom": "2.5rem", "alignItems": "center"}),
    html.Div([
        html.A(
            dbc.Button("Descargar informe PDF", id="descargar-pdf-btn", color="primary", size="lg"),
            id="descargar-pdf-link",
            href="#",  # Se actualizará dinámicamente
            target="_blank",
            style={"textDecoration": "none"}
        )
    ], style={"textAlign": "center", "marginBottom": "2rem"}),
    html.Div([
        html.Img(src="/assets/identidad_MPR_2.png", height="60px"),
        html.P("Dashboard Deportivo - Powered by MPR", style={"color": "#aaa"})
    ], style={"textAlign": "center", "marginTop": "2rem"})
], style={"maxWidth": "1200px", "margin": "0 auto", "padding": "2rem"}) 

# Layout de lesiones (área médica)
lesiones_layout_page = html.Div([
    html.Div([
        html.Img(src="/assets/identidad_MPR_2.png", height="60px", style={"marginBottom": "1rem"}),
        html.H1("Área Médica - Dashboard de Lesiones", style={"color": "#e74c3c", "textAlign": "center"}),
    ], style={"marginBottom": "2rem"}),
    
    lesiones_layout,  # <-- Aquí usas el layout importado
    
    html.Div([
        html.Img(src="/assets/identidad_MPR_2.png", height="60px"),
        html.P("Dashboard Deportivo - Powered by MPR", style={"color": "#aaa"})
    ], style={"textAlign": "center", "marginTop": "2rem"})
], style={"maxWidth": "1200px", "margin": "0 auto", "padding": "2rem"})

@app.callback(
    Output("descargar-pdf-link", "href"),
    Input("selector-partido", "value")
)
def actualizar_link_descarga(partido):
    if not partido:
        return "#"
    return f"/descargar_pdf/{partido}"

# Navbar
navbar = dbc.Navbar(
    dbc.Container([
        html.A(
            dbc.Row([
                dbc.Col(html.Img(src="/assets/identidad_MPR_2.png", height="40px")),
                dbc.Col(dbc.NavbarBrand("Dashboard Deportivo", className="ms-2")),
            ], align="center", className="g-0"),
            href="/",
            style={"textDecoration": "none"},
        ),
        dbc.NavbarToggler(id="navbar-toggler"),
        dbc.Collapse(
            dbc.Nav([
                dbc.NavItem(dbc.NavLink("Home", href="/")),
                dbc.NavItem(dbc.NavLink("Performance", href="/performance")),
                dbc.NavItem(dbc.NavLink("Médico", href="/medico")),
                dbc.Button("Logout", id="logout-button", color="danger", className="ms-2", n_clicks=0)
            ], className="ms-auto", navbar=True),
            id="navbar-collapse",
            navbar=True,
        ),
    ]),
    color="primary",
    dark=True,
    sticky="top",
)

main_layout = dbc.Container([
    navbar,
    html.Div(id="page-content-inner", style={"marginTop": "2rem"}),
    html.Div(id="logout-output")  # <- Este div debe estar aquí
], fluid=True)

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id="page-content")
])

# Callback de login
@app.callback(
    Output("login-output", "children"),
    Input("login-button", "n_clicks"),
    State("username", "value"),
    State("password", "value"),
    prevent_initial_call=True
)
def login(n_clicks, username, password):
    print(f"Intento de login: usuario={username}, password={password}")
    user = next((u for u in USERS.values() if u.username == username and u.password == password), None)
    if user:
        login_user(user)
        print(f"Login correcto para usuario: {user.username}")
        print(f"current_user.is_authenticated tras login: {current_user.is_authenticated}")
        return dcc.Location(href="/", id="redirect")
    else:
        print("Login fallido: usuario o contraseña incorrectos")
        return dbc.Alert("Usuario o contraseña incorrectos", color="danger")

# Callback para mostrar la página según autenticación
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if not current_user.is_authenticated:
        return login_layout
    return main_layout

@app.callback(
    Output("page-content-inner", "children"),
    Input("url", "pathname")
)
def render_inner_page(pathname):
    if not current_user.is_authenticated:
        return html.Div("Acceso denegado")
    if pathname == "/performance":
        return performance_layout
    elif pathname == "/medico": 
        return lesiones_layout_page  
    else:
        return home_layout

@app.callback(
    Output('selector-partido', 'options'),
    [Input('selector-equipo', 'value'),
     Input('selector-jornada', 'value')]
)
def filtrar_partidos(equipo, jornada):
    df = matches.copy()
    if equipo:
        df = df[(df['Home'] == equipo) | (df['Away'] == equipo)]
    if jornada:
        df = df[df['Round'] == jornada]
    return [
        {'label': f"{row['Match']} ({row['Date']})", 'value': row['Match']}
        for _, row in df.iterrows()
    ]

@app.callback(
    Output('selector-partido', 'value'),
    [Input('selector-partido', 'options')],
    [State('selector-partido', 'value')]
)
def seleccionar_primero(options, current_value):
    if not options:
        return None
    values = [opt['value'] for opt in options]
    if current_value in values:
        return current_value
    return values[0]

# Callback para actualizar la infografía
@app.callback(
    [
        Output("cabecera-partido", "children"),
        Output("tabla-metricas", "children"),
        Output("radar-metricas", "figure"),
        Output("barras-extra", "figure"),
        Output("mini-ranking", "children"),
    ],
    [Input("selector-partido", "value")]
)
def actualizar_infografia(nombre_partido):
    # 1. Filtrar datos del partido
    partido = matches[matches['Match'] == nombre_partido].iloc[0]
    local = partido['Home']
    visitante = partido['Away']
    fecha = partido['Date']
    jornada = partido['Round']

    stats_partido = stats[stats['Match'] == nombre_partido]
    stats_local = stats_partido[stats_partido['Team'] == local].iloc[0]
    stats_visitante = stats_partido[stats_partido['Team'] == visitante].iloc[0]

    # 2. Tabla de métricas generales
    tabla = tabla_metricas_generales(local, visitante, stats_local, stats_visitante)

    # 3. Ranking en formato tabla
    ranking = ranking_mini_tabla(local, visitante, stats, fecha)

    # 4. Cabecera
    cabecera = html.Div([
        html.Div([
            html.Img(src=get_escudo_path(local), height="60px", style={"marginRight": "1rem"}),
            html.H2(f"{local} {stats_local['Goals']} - {stats_visitante['Goals']} {visitante}", style={"display": "inline-block", "verticalAlign": "middle", "color": "#2ecc71"}),
            html.Img(src=get_escudo_path(visitante), height="60px", style={"marginLeft": "1rem"}),
        ], style={"display": "flex", "justifyContent": "center", "alignItems": "center"}),
        html.P(f"Jornada {jornada} - {fecha}", style={"color": "#aaa"})
    ])

    # 5. Radar chart profesional
    radar_metricas = ["xG", "Shots", "PPDA", "Field Tilt", "High Recoveries", "Corners", "Crosses"]
    local_vals = [float(stats_local[m]) for m in radar_metricas]
    visitante_vals = [float(stats_visitante[m]) for m in radar_metricas]
    maximos = [max(l, v) * 1.2 if max(l, v) > 0 else 1 for l, v in zip(local_vals, visitante_vals)]  # margen 20%

    # Normaliza los valores para que el radar sea comparable visualmente
    def normaliza(valores, maximos):
        return [v / m if m != 0 else 0 for v, m in zip(valores, maximos)]

    local_norm = normaliza(local_vals, maximos)
    visitante_norm = normaliza(visitante_vals, maximos)

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=local_norm + [local_norm[0]],
        theta=radar_metricas + [radar_metricas[0]],
        fill='toself',
        name=local,
        line=dict(color='#2ecc71', width=4),
        marker=dict(size=8),
        opacity=0.7
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=visitante_norm + [visitante_norm[0]],
        theta=radar_metricas + [radar_metricas[0]],
        fill='toself',
        name=visitante,
        line=dict(color='#3498db', width=4),
        marker=dict(size=8),
        opacity=0.7
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(
                visible=True,
                color='#aaa',
                showline=True,
                linewidth=2,
                gridcolor='#444',
                gridwidth=1,
                range=[0, 1]
            ),
            angularaxis=dict(
                color='#fff',
                linewidth=2,
                gridcolor='#444',
                gridwidth=1,
            )
        ),
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#fff'),
        margin=dict(l=80, r=80, t=80, b=80)
    )

    # 6. Barras extra
    extra_metricas = ["Corners", "Crosses", "Fouls", "On-Ball Pressure", "Off-Ball Pressure"]
    local_extra = [float(stats_local[m]) for m in extra_metricas]
    visitante_extra = [float(stats_visitante[m]) for m in extra_metricas]

    fig_barras = go.Figure()
    fig_barras.add_trace(go.Bar(
        y=extra_metricas,
        x=local_extra,
        name=local,
        orientation='h',
        marker=dict(color='#2ecc71', line=dict(color='#fff', width=2)),
        text=local_extra,
        textposition='auto'
    ))
    fig_barras.add_trace(go.Bar(
        y=extra_metricas,
        x=visitante_extra,
        name=visitante,
        orientation='h',
        marker=dict(color='#3498db', line=dict(color='#fff', width=2)),
        text=visitante_extra,
        textposition='auto'
    ))
    fig_barras.update_layout(
        barmode='group',
        plot_bgcolor='#24282a',
        paper_bgcolor='#24282a',
        font=dict(color='#fff'),
        legend=dict(font=dict(color='#fff')),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False),
        margin=dict(l=30, r=30, t=30, b=30)
    )

    return cabecera, tabla, fig_radar, fig_barras, ranking

# Callback de logout
@app.callback(
    Output("logout-output", "children"),
    Input("logout-button", "n_clicks"),
    prevent_initial_call=True
)
def logout(n_clicks):
    logout_user()
    print("Logout realizado")
    return dcc.Location(href="/", id="redirect-logout")
if __name__ == "__main__":
    app.run(debug=False)