import os
import time
import pandas as pd
import logging
from pathlib import Path
from dotenv import load_dotenv
from src.log.logging import configurar_logging

# =============================================================
# ENV
# =============================================================
load_dotenv(".env")


# =============================================================
# LECTOR GENÉRICO (CSV / XLSX)
# =============================================================
def leer_archivo_generico(archivo: Path) -> pd.DataFrame:
    sufijo = archivo.suffix.lower()

    if sufijo in [".csv", ".txt"]:
        df = pd.read_csv(archivo, encoding="latin-1", sep=",", dtype=str)
    elif sufijo == ".xlsx":
        df = pd.read_excel(archivo, dtype=str, engine="openpyxl")
    else:
        raise ValueError(f"Formato no soportado: {archivo.name}")

    df = df.apply(lambda col: col.astype(str).str.strip())
    return df


# =============================================================
# NORMALIZAR PICKING (AMBOS ESQUEMAS)
# =============================================================
def normalizar_picking(df: pd.DataFrame, archivo_origen: str) -> pd.DataFrame:
    df.columns = df.columns.str.strip()

    mapa = {
        # Fecha creación
        "Fecha Creacion Gestion": "Fecha_Creacion_Gestion",
        "Fecha Creación Gestion": "Fecha_Creacion_Gestion",

        # Gestión
        "Nro. Gestion": "Nro_Gestion",
        "Nro Gestión": "Nro_Gestion",

        "Estado Gestion": "Est_Gestion",
        "Estado Gestión": "Est_Gestion",

        # OP / Orden
        "Nro. OP": "Nro_OP",
        "Nro OP": "Nro_OP",

        "Nro. Orden": "Nro_Orden",
        "Nro Orden": "Nro_Orden",

        "Estado OP": "Est_OP",

        # Documento
        "Nro. Documento": "Nro_Documento",
        "Nro Documento": "Nro_Documento",

        # Tipo
        "Tipo Gestion": "Tipo_Gestion",
        "Tipo Gestión": "Tipo_Gestion",

        # Picker
        "Picker": "Picker",

        # Fechas picker
        "Fecha Inicio Picker": "Fecha_Inicio_Picker",
        "Fecha Cierre Picker": "Fecha_Cierre_Picker",

        # Tiempos
        "Tiempo Recorrido Picker": "Tiempo_Recorrido_Picker",
        "Tiempo Promedio Movimiento Picker": "Tiempo_Mov_Prom_Picker",
        "Tiempo Movimiento Prom. Picker": "Tiempo_Mov_Prom_Picker",

        # Cantidades / conteos
        "Nro. Productos": "Nro_Codigos",
        "Nro Códigos": "Nro_Codigos",

        "Nro. Ubicaciones": "Nro_Ubicaciones",
        "Nro Ubicaciones": "Nro_Ubicaciones",

        "Cantidad Solicitada": "Cantidad_Solicitada",
        "Cantidad Picking": "Cantidad_Picking",

        # Otros
        "Glosa": "Glosa",
        "Empresa": "Empresa"
    }

    df = df.rename(columns={c: mapa[c] for c in df.columns if c in mapa})

    df["Archivo_Origen"] = archivo_origen

    columnas_finales = [
        "Nro_Gestion",
        "Glosa",
        "Est_Gestion",
        "Nro_OP",
        "Nro_Orden",
        "Est_OP",
        "Nro_Documento",
        "Tipo_Gestion",
        "Picker",
        "Fecha_Inicio_Picker",
        "Fecha_Cierre_Picker",
        "Tiempo_Recorrido_Picker",
        "Tiempo_Mov_Prom_Picker",
        "Nro_Codigos",
        "Nro_Ubicaciones",
        "Cantidad_Solicitada",
        "Cantidad_Picking",
        "Fecha_Creacion_Gestion",
        "Archivo_Origen",
        "Empresa"
    ]

    for col in columnas_finales:
        if col not in df.columns:
            df[col] = None

    df = df[columnas_finales]

    # Fecha robusta (sin dayfirst)
    df["Fecha_Creacion_Gestion"] = pd.to_datetime(
        df["Fecha_Creacion_Gestion"],
        errors="coerce"
    )

    return df


# =============================================================
# PROCESO PRINCIPAL – PICKING
# =============================================================
def Ejecutar_Consolidado_Picking():

    Archivo = Path(__file__).stem
    configurar_logging(Archivo)
    logging.info("🚀 Iniciando consolidado FTP – PICKING")

    ruta_ftp = Path(os.getenv("RUTA_FTP_FLEXY"))
    ruta_output = Path(os.getenv("RUTA_OUTPUT"))

    if not ruta_ftp or not ruta_output:
        raise ValueError("❌ Revisar variables de entorno")

    ruta_output.mkdir(parents=True, exist_ok=True)
    ruta_procesado = ruta_ftp / "Procesado"
    ruta_procesado.mkdir(exist_ok=True)

    df_picking = []
    archivos_procesados = []

    extensiones = [".csv", ".txt", ".xlsx"]

    # =========================
    # LECTURA ARCHIVOS
    # =========================
    for archivo in ruta_ftp.iterdir():

        if archivo.is_dir() or archivo.suffix.lower() not in extensiones:
            continue

        nombre = archivo.name.upper()

        if nombre.startswith("PROD_ANALISIS_PICKING"):
            logging.info(f"✓ PICKING: {archivo.name}")

            df = leer_archivo_generico(archivo)
            df = normalizar_picking(df, archivo.name)

            df_picking.append(df)
            archivos_procesados.append(archivo)

    if not df_picking:
        logging.warning("⚠ No se encontraron archivos PICKING")
        return

    # =========================
    # CONSOLIDAR
    # =========================
    df_final = (
        pd.concat(df_picking, ignore_index=True)
        .drop_duplicates()
    )

    # =========================
    # EXPORTAR CONSOLIDADO
    # =========================
    salida = ruta_output / "PROD_ANALISIS_PICKING_CONSOLIDADO.csv"

    df_final.to_csv(
        salida,
        index=False,
        sep="|",
        encoding="utf-8"
    )

    logging.info(f"✅ Consolidado PICKING generado | Filas: {len(df_final)}")

    # =========================
    # MOVER A PROCESADO (REEMPLAZO + TIMESTAMP)
    # =========================
    for archivo in archivos_procesados:
        destino = ruta_procesado / archivo.name

        try:
            if destino.exists():
                destino.unlink()

            archivo.rename(destino)

            # 🔧 Forzar actualización de fecha modificación
            now = time.time()
            os.utime(destino, (now, now))

            logging.info(
                f"📦 Archivo movido a Procesado (reemplazado y actualizado): {archivo.name}"
            )

        except Exception as e:
            logging.error(f"❌ Error moviendo archivo {archivo.name}: {e}")

    logging.info("🏁 Proceso PICKING finalizado correctamente")


# =============================================================
# MAIN
# =============================================================
if __name__ == "__main__":
    Ejecutar_Consolidado_Picking()
