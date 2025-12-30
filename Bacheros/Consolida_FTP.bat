@echo off
REM ============================================
REM  Ir al directorio del proyecto
REM ============================================

cd /d "D:\MASTER PROYECTOS\LOGISTICA\Python_Villa"

REM ============================================
REM  Activar entorno virtual
REM ============================================

call .venv\Scripts\activate

REM ============================================
REM  Ejecutar el script Consolida_FTP
REM  Guardar logs en carpeta: Log/Error
REM ============================================

python -m Scripts.Consolida_FTP > "Log\Error\Error_Consolida_FTP.log" 2>&1

pause



