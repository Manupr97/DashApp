from dash import Input, Output
from utils.lesiones_data import load_lesiones

def register_lesiones_callbacks(app):
    @app.callback(
        Output('grafico-tipos-lesion', 'figure'),
        Output('grafico-zonas-corporales', 'figure'),
        Output('tabla-lesiones', 'data'),
        Input('filtro-jugador', 'value'),
        Input('filtro-tipo-lesion', 'value')
    )
    def actualizar_dashboard(jugador, tipo_lesion):
        try:
            df = load_lesiones()
            
            if jugador:
                df = df[df['Jugador'] == jugador]
            if tipo_lesion:
                df = df[df['TipoLesion'] == tipo_lesion]
            
            fig_tipos = {
                'data': [{
                    'x': df['TipoLesion'].value_counts().index,
                    'y': df['TipoLesion'].value_counts().values,
                    'type': 'bar',
                    'marker': {'color': '#2ecc71'}
                }],
                'layout': {
                    'title': 'Número de lesiones por tipo',
                    'plot_bgcolor': 'rgba(0,0,0,0)',
                    'paper_bgcolor': 'rgba(0,0,0,0)',
                    'font': {'color': '#2ecc71'},
                    'xaxis': {'tickangle': -45},
                    'yaxis': {'gridcolor': 'rgba(255,255,255,0.1)'}
                }
            }
            
            colores_pie = ['#2ecc71', '#007bff', '#27ae60', '#2980b9', '#16a085', '#3498db', '#1abc9c', '#2980b9']
            fig_zonas = {
                'data': [{
                    'labels': df['ZonaCorporal'].value_counts().index,
                    'values': df['ZonaCorporal'].value_counts().values,
                    'type': 'pie',
                    'marker': {'colors': colores_pie},
                    'textinfo': 'percent+label',
                    'textfont': {'color': 'white'}
                }],
                'layout': {
                    'title': 'Distribución de zonas corporales afectadas',
                    'plot_bgcolor': 'rgba(0,0,0,0)',
                    'paper_bgcolor': 'rgba(0,0,0,0)',
                    'font': {'color': '#2ecc71'}
                }
            }
            
            data_tabla = df.to_dict('records')
            
            return fig_tipos, fig_zonas, data_tabla
        
        except Exception as e:
            print(f"Error en callback lesiones: {e}")
            # Devolver gráficos vacíos y tabla vacía para no romper la app
            empty_fig = {
                'data': [],
                'layout': {
                    'plot_bgcolor': 'rgba(0,0,0,0)',
                    'paper_bgcolor': 'rgba(0,0,0,0)',
                    'font': {'color': '#2ecc71'},
                    'xaxis': {'visible': False},
                    'yaxis': {'visible': False}
                }
            }
            return empty_fig, empty_fig, []