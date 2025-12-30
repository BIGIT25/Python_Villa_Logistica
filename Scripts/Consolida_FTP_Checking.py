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
        df = pd.read_csv(
            archivo,
            encoding="latin-1",
            sep=",",
            dtype=str
        )
    elif sufijo == ".xlsx":
        df = pd.read_excel(
            archivo,
            dtype=str,
            engine="openpyxl"
        )
    else:
        raise ValueError(f"Formato no soportado: {archivo.name}")

    # Limpieza básica
    df = df.apply(lambda col: col.astype(str).str.strip())
    return df


# =============================================================
# NORMALIZAR PARTES (AMBOS ESQUEMAS)
# =============================================================
def normalizar_partes(df: pd.DataFrame, archivo_origen: str) -> pd.DataFrame:
    df.columns = df.columns.str.strip()

    mapa = {
        "Fecha": "Fecha",

        "Movimiento": "Movimiento",
        "Mov. Almacén": "Movimiento",

        "Nro. Pedido": "Nro_Pedido",
        "Nro Pedido": "Nro_Pedido",

        "Estado": "Estado",

        "CÃ³digo Producto": "Codigo",
        "Código": "Codigo",
        "Codigo": "Codigo",

        "Producto": "Producto",

        "Bultos Totales": "Bultos_Totales",
        "Ingresos": "Ingresos",
        "Salidas": "Salidas",

        "Nro. Orden": "Nro_Orden",
        "Nro Orden": "Nro_Orden",

        "Empresa": "Empresa"
    }

    # Renombrar columnas detectadas
    df = df.rename(columns={c: mapa[c] for c in df.columns if c in mapa})

    # Agregar archivo origen
    df["Archivo_Origen"] = archivo_origen

    columnas_finales = [
        "Fecha",
        "Movimiento",
        "Nro_Pedido",
        "Estado",
        "Codigo",
        "Producto",
        "Bultos_Totales",
        "Ingresos",
        "Salidas",
        "Nro_Orden",
        "Empresa",
        "Archivo_Origen"
    ]

    # Crear columnas faltantes
    for col in columnas_finales:
        if col not in df.columns:
            df[col] = None

    df = df[columnas_finales]

    # Normalizar fecha (robusto, sin dayfirst)
    df["Fecha"] = pd.to_datetime(
        df["Fecha"],
        errors="coerce"
    )

    return df


# =============================================================
# PROCESO PRINCIPAL – PARTES
# =============================================================
def Ejecutar_Consolidado_Partes():

    Archivo = Path(__file__).stem
    configurar_logging(Archivo)
    logging.info("🚀 Iniciando consolidado FTP – ANALISIS PARTES")

    ruta_ftp = Path(os.getenv("RUTA_FTP_FLEXY"))
    ruta_output = Path(os.getenv("RUTA_OUTPUT"))

    if not ruta_ftp or not ruta_output:
        raise ValueError("❌ Revisar variables de entorno")

    ruta_output.mkdir(parents=True, exist_ok=True)
    ruta_procesado = ruta_ftp / "Procesado"
    ruta_procesado.mkdir(exist_ok=True)

    df_partes = []
    archivos_procesados = []

    extensiones = [".csv", ".txt", ".xlsx"]

    # =========================
    # LECTURA ARCHIVOS
    # =========================
    for archivo in ruta_ftp.iterdir():

        if archivo.is_dir() or archivo.suffix.lower() not in extensiones:
            continue

        nombre = archivo.name.upper()

        if nombre.startswith("PROD_ANALISIS_PARTES"):
            logging.info(f"✓ PARTES: {archivo.name}")

            df = leer_archivo_generico(archivo)
            df = normalizar_partes(df, archivo.name)

            df_partes.append(df)
            archivos_procesados.append(archivo)

    if not df_partes:
        logging.warning("⚠ No se encontraron archivos PARTES")
        return

    # =========================
    # CONSOLIDAR
    # =========================
    df_final = pd.concat(df_partes, ignore_index=True)

    # =========================
    # NORMALIZAR TIPOS (CRÍTICO)
    # =========================
    for col in ["Bultos_Totales", "Ingresos", "Salidas"]:
        df_final[col] = (
            pd.to_numeric(df_final[col], errors="coerce")
            .fillna(0)
        )

    for col in ["Movimiento", "Estado", "Producto", "Empresa"]:
        df_final[col] = (
            df_final[col]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    # =========================
    # DEDUPLICAR POR CLAVE DE NEGOCIO
    # =========================
    clave_unica = [
        "Fecha",
        "Movimiento",
        "Nro_Pedido",
        "Estado",
        "Codigo",
        "Producto",
        "Bultos_Totales",
        "Ingresos",
        "Salidas",
        "Nro_Orden",
        "Empresa"
    ]

    df_final = df_final.drop_duplicates(subset=clave_unica)

    # =========================
    # EXPORTAR CONSOLIDADO
    # =========================
    salida = ruta_output / "PROD_ANALISIS_PARTES_CONSOLIDADO.csv"

    df_final.to_csv(
        salida,
        index=False,
        sep="|",
        encoding="utf-8"
    )

    logging.info(
        f"✅ Consolidado PARTES generado | Filas: {len(df_final)} | "
        f"Ingresos: {df_final['Ingresos'].sum()} | "
        f"Salidas: {df_final['Salidas'].sum()}"
    )

    # =========================
    # MOVER ARCHIVOS A PROCESADO
    # + FORZAR FECHA MODIFICACIÓN
    # =========================
    for archivo in archivos_procesados:
        destino = ruta_procesado / archivo.name

        try:
            if destino.exists():
                destino.unlink()

            archivo.rename(destino)

            # 🔧 Forzar actualización de fecha de modificación
            now = time.time()
            os.utime(destino, (now, now))

            logging.info(
                f"📦 Archivo movido a Procesado (reemplazado y actualizado): {archivo.name}"
            )

        except Exception as e:
            logging.error(f"❌ Error moviendo archivo {archivo.name}: {e}")

    logging.info("🏁 Proceso PARTES finalizado correctamente")


# =============================================================
# MAIN
# =============================================================
if __name__ == "__main__":
    Ejecutar_Consolidado_Partes()
