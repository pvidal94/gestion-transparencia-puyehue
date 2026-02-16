import pandas as pd
import os

ARCHIVO_SUBIDO = "Listado Solicitudes por estado.csv"
DB_PATH = "data_storage/db_gestion_puyehue.csv"

if not os.path.exists(ARCHIVO_SUBIDO):
    print(f"❌ No se encuentra el archivo {ARCHIVO_SUBIDO}")
else:
    try:
        # Leer el archivo con la codificación correcta
        df_nuevo = pd.read_csv(ARCHIVO_SUBIDO, sep=';', encoding='latin-1')
        df_nuevo.columns = df_nuevo.columns.str.strip()

        # Mapeo exacto para que main.py lo reconozca
        df_final = pd.DataFrame()
        df_final['Código'] = df_nuevo['Código']
        df_final['Fecha_Ingreso'] = df_nuevo['Fecha ingreso']
        df_final['Fecha_Caducidad'] = df_nuevo['Fecha vencimiento']
        df_final['Prorroga'] = df_nuevo['Prorroga'].apply(lambda x: "1" if str(x).lower() == 'si' else "0")
        
        # Datos adicionales que vienen en tu CSV
        df_final['Responsable'] = ""
        df_final['Dependencia'] = ""
        
        # Si el estado es "RESPUESTA ENTREGADA", inventamos una fecha efectiva para que no salga "EN ANALISIS"
        # O la dejamos vacía si prefieres llenarla tú en la App
        df_final['Fecha_Efectiva_Portal'] = "" 
        
        if not os.path.exists("data_storage"): os.makedirs("data_storage")

        # Guardar limpio
        df_final.to_csv(DB_PATH, index=False)
        print(f"✅ EXITO: {len(df_final)} solicitudes cargadas en la base de datos.")

    except Exception as e:
        print(f"❌ Error: {e}")