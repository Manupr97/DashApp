import pandas as pd
import os

def load_lesiones():
    """
    Carga el dataset de lesiones desde data/lesiones.csv y devuelve un DataFrame.
    """
    ruta = os.path.join(os.path.dirname(__file__), '..', 'data', 'lesiones.csv')
    df = pd.read_csv(ruta, parse_dates=['FechaInicio', 'FechaFin'])
    return df