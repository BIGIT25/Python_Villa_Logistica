import os
import pandas as pd
import logging
from pathlib import Path
from dotenv import load_dotenv
from src.log.logging import configurar_logging

# ============================
# Cargar variables de entorno
# ============================
load_dotenv(".env")


def Ejecutar_Consolidado_Historico():

    Archivo = Path(__file__).stem
    configurar_logging(Archivo)
    logging.info("Iniciando consolidado de HISTÓRICOS (CHECKING / PICKING)")

    try:
        # =============================================================
        # 1️⃣ Leer rutas del .env
        # =============================================================
        ruta_historico = Path(os.getenv("RUTA_HISTORICO"))
        ruta_output = Path(os.getenv("RUTA_OUTPUT_HISTORICO"))

        if not ruta_historico:
            raise ValueError("❌ Falta RUTA_HISTORICO en .env")

        if not ruta_output:
            raise ValueError("❌ Falta RUTA_OUTPUT_HISTORICO en .env")

        ruta_output.mkdir(parents=True, exist_ok=True)

        # Archivos de salida
        archivo_checking = ruta_output / "Checking_Historico_Consolidado.csv"
        archivo_picking = ruta_output / "Picking_Historico_Consolidado.csv"

        df_checking = []
        df_picking = []

        # =============================================================
        # 2️⃣ Recorrer archivos históricos
        # =============================================================
        logging.info(f"Buscando archivos en: {ruta_historico}")

        for archivo in ruta_historico.iterdir():
            nombre = archivo.name.upper()

            # ------------ CHECKING ------------
            if nombre.startswith("CHECKING_") and archivo.suffix.lower() in [".xlsx", ".xls", ".csv"]:
                logging.info(f"✓ Archivo CHECKING detectado: {archivo.name}")

                df = pd.read_excel(archivo, dtype=str) if archivo.suffix.lower() in [".xlsx", ".xls"] else \
                     pd.read_csv(archivo, dtype=str)

                df = df.apply(lambda col: col.astype(str).str.strip())
                df["Archivo_Origen"] = archivo.name
                df_checking.append(df)

            # ------------ PICKING ------------
            elif nombre.startswith("PICKING_") and archivo.suffix.lower() in [".xlsx", ".xls", ".csv"]:
                logging.info(f"✓ Archivo PICKING detectado: {archivo.name}")

                df = pd.read_excel(archivo, dtype=str) if archivo.suffix.lower() in [".xlsx", ".xls"] else \
                     pd.read_csv(archivo, dtype=str)

                df = df.apply(lambda col: col.astype(str).str.strip())
                df["Archivo_Origen"] = archivo.name
                df_picking.append(df)

        # =============================================================
        # 3️⃣ CONSOLIDAR + QUITAR DUPLICADOS + EXPORTAR
        # =============================================================

        # ========== CHECKING ==========
        if df_checking:
            df_final_checking = pd.concat(df_checking, ignore_index=True)

            # Quitar duplicados de TODO
            df_final_checking = df_final_checking.drop_duplicates()

            df_final_checking.to_csv(archivo_checking, index=False, sep="|", encoding="utf-8")
            logging.info(f"✅ Consolidado CHECKING generado: {archivo_checking}  Filas: {len(df_final_checking)}")
        else:
            logging.warning("⚠ No se encontraron archivos CHECKING_ en el histórico")

        # ========== PICKING ==========
        if df_picking:
            df_final_picking = pd.concat(df_picking, ignore_index=True)

            df_final_picking = df_final_picking.drop_duplicates()

            df_final_picking.to_csv(archivo_picking, index=False, sep="|", encoding="utf-8")
            logging.info(f"✅ Consolidado PICKING generado: {archivo_picking}  Filas: {len(df_final_picking)}")
        else:
            logging.warning("⚠ No se encontraron archivos PICKING_ en el histórico")

    except Exception as e:
        logging.error(f"❌ Error general en consolidado HISTÓRICO: {e}")
        raise


if __name__ == "__main__":
    Ejecutar_Consolidado_Historico()
