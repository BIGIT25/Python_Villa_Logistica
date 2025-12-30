import os
import subprocess
from pathlib import Path


def crear_archivo(ruta, contenido=""):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)


def crear_venv(ruta_proyecto):
    print("⚙️ Creando entorno virtual .venv ...")
    subprocess.run(["python", "-m", "venv", ".venv"], cwd=ruta_proyecto)
    print("✔ Entorno virtual creado")


def instalar_requisitos(ruta_proyecto):
    print("📦 Instalando librerías desde requirements.txt...")
    subprocess.run(
        [f"{ruta_proyecto}/.venv/Scripts/pip", "install", "-r", "requirements.txt"],
        cwd=ruta_proyecto,
        shell=True
    )
    print("✔ Librerías instaladas")


def crear_estructura(nombre_proyecto):
    base = Path(nombre_proyecto)
    base.mkdir(exist_ok=True)

    carpetas = [
        "Scripts",
        "src/log",
        "src/Conexion_Monday",
        "src/Database",
        "Adjuntos",
        "Output_Data_csv",
        "Bacheros",
        "Sql",
        "Log/Archivos_Log",
        "Log/Error"
    ]

    for carpeta in carpetas:
        (base / carpeta).mkdir(parents=True, exist_ok=True)

    # =========================
    # Crear archivos base
    # =========================
    crear_archivo(base / ".env",
                  "ARCHIVO_EMPLEADOS=\n"
                  "SALIDA_TXT_EMPLEADOS=\n"
                  "STRING_CONEXION_SQL=\n"
                  "TOKEN_MONDAY=\n"
                  )

    crear_archivo(base / "requirements.txt",
                  "pandas\npython-dotenv\nopenpyxl\nrequests\npyodbc\n")

    crear_archivo(base / "main.py",
                  '''import os
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    print("🚀 Proyecto iniciado correctamente")
''')

    crear_archivo(base / "Scripts" / "__init__.py", "")

    crear_archivo(base / "Scripts" / "plantilla_procesamiento.py",
                  '''import os
import pandas as pd
import logging
from dotenv import load_dotenv
from pathlib import Path
from src.log.logging import configurar_logging

def ejecutar():
    Archivo = Path(__file__).stem
    configurar_logging(Archivo)
    logging.info("Iniciando ejecución...")

    try:
        load_dotenv()
        # Lógica de procesamiento aquí

        logging.info("Finalizado correctamente")

    except Exception as e:
        logging.error(f"Error general: {e}")
        raise
''')

    crear_archivo(base / "src" / "log" / "logging.py",
                  '''import logging
from pathlib import Path

def configurar_logging(nombre_script):
    ruta_log = Path("./Log/Archivos_Log") / f"{nombre_script}.log"
    logging.basicConfig(
        filename=ruta_log,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
''')

    crear_archivo(base / "src" / "Database" / "conexion_sql.py",
                  '''import pyodbc
import os

def obtener_conexion():
    cadena = os.getenv("STRING_CONEXION_SQL")
    return pyodbc.connect(cadena)
''')

    crear_archivo(base / ".gitignore",
                  '''
# Python
__pycache__/
*.pyc

# Virtual environment
.venv/

# Logs
Log/Archivos_Log/*.log
Log/Error/*.log

# Output
Output_Data_csv/

# Adjuntos
Adjuntos/

# Env file
.env
'''
                  )

    print("\n📁 Estructura creada correctamente.")

    # =====================
    # ENTORNO VIRTUAL
    # =====================
    crear_venv(base)

    # =====================
    # INSTALAR REQUIREMENTS
    # =====================
    instalar_requisitos(base)

    print("\n🎉 Proyecto completamente configurado y listo para programar")
    print(f"📂 Ubicación: {base.resolve()}")
    print("👉 Activa tu entorno con:")
    print(f"\n   {base.resolve()}/.venv/Scripts/activate\n")


# ========== EJECUCIÓN ==========
if __name__ == "__main__":
    nombre = input("Python_Villa")
    crear_estructura(nombre)
