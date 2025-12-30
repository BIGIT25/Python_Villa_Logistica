import pyodbc
import os

def obtener_conexion():
    cadena = os.getenv("STRING_CONEXION_SQL")
    return pyodbc.connect(cadena)
