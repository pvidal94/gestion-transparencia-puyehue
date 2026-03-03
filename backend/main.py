import os
import io
import pandas as pd
import numpy as np
from datetime import datetime
from fastapi import FastAPI, Body, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil

app = FastAPI()

# --- CONFIGURACIÓN INICIAL ---
UPLOAD_DIR = "adjuntos_transparencia"
if not os.path.exists(UPLOAD_DIR): os.makedirs(UPLOAD_DIR)
app.mount("/descargas", StaticFiles(directory=UPLOAD_DIR), name="descargas")

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

DATA_DIR = "data_storage"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
DB_PATH = os.path.join(DATA_DIR, "db_gestion_puyehue.csv")

RESPONSABLES_LISTA = [
    "Juan Soto", "Bety Mora", "Marta Ovando", "Jorge Pacheco", "Byron Oyarzun", 
    "Guido Vidal", "Eladio Acum", "Nefi Linco", "Soledad Villalobos", 
    "Javier Lopez", "Raúl Navarrete", "Daniela Silva", "Felipe Post", 
    "Robinson Rosales", "Daniella Muñoz", "Cristian Figueroa", "Graciela Copilai",
    "Karin Fuentes", "Juan Pablo Mardondes", "Pablo Hernandez"
]

USUARIOS_PRO = { "admin": "puyehue2026" }
for nombre in RESPONSABLES_LISTA:
    USUARIOS_PRO[nombre] = "puyehue123"

FERIADOS_CHILE = [
    '2026-01-01', '2026-04-03', '2026-04-04', '2026-05-01', '2026-05-21', 
    '2026-06-21', '2026-06-29', '2026-07-16', '2026-08-15', '2026-09-18', 
    '2026-09-19', '2026-10-12', '2026-10-31', '2026-11-01', '2026-12-08', 
    '2026-12-25'
]

# --- FUNCIONES DE FORMATEO ---

def normalizar_fecha_estricta(fecha_val):
    """Convierte cualquier entrada de fecha a objeto datetime de forma segura"""
    if not fecha_val or str(fecha_val).lower() in ["nan", "none", ""]:
        return None
    
    f_str = str(fecha_val).strip()
    
    # Intentar formato ISO (AAAA-MM-DD)
    try:
        return datetime.strptime(f_str, '%Y-%m-%d')
    except:
        pass
        
    # Intentar formato Chileno (DD-MM-AAAA)
    try:
        return datetime.strptime(f_str, '%d-%m-%Y')
    except:
        pass
        
    return None

def normalizar_df(df):
    df.columns = df.columns.str.strip().str.replace(' ', '_')
    columnas_base = [
        'Código', 'Fecha_Ingreso', 'Fecha_Caducidad', 'Responsable', 
        'Dependencia', 'Fecha_E_Portal', 'Prorroga', 'Dias_Habiles',
        'Adjunto_Solicitud', 'Adjunto_Respuesta'
    ]
    for col in columnas_base:
        if col not in df.columns:
            df[col] = ""
    return df.fillna("")

def procesar_informacion(df):
    df = normalizar_df(df)
    
    detalles = []
    meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    stats = {mes: 0 for mes in meses_nombres}
    conteo_deptos = {}

    for _, row in df.iterrows():
        cod = str(row['Código']).strip()
        if not cod or cod in ["", "nan"]: continue
        
        # --- LÓGICA DE CONTEO POR FECHA DE INGRESO ---
        dt_ingreso = normalizar_fecha_estricta(row['Fecha_Ingreso'])
        
        if dt_ingreso:
            nombre_mes = meses_nombres[dt_ingreso.month - 1]
            stats[nombre_mes] += 1

        # Resto de la data para la tabla
        depto = str(row['Dependencia']).strip()
        if depto and depto != "nan":
            conteo_deptos[depto] = conteo_deptos.get(depto, 0) + 1

        detalles.append({
            "Codigo": cod,
            "Ingreso": dt_ingreso.strftime('%d-%m-%Y') if dt_ingreso else str(row['Fecha_Ingreso']),
            "Responsable": str(row['Responsable']),
            "Dependencia": depto,
            "Prorroga": str(row['Prorroga']) in ['1', 'SÍ', 'Sí', 'True', True],
            "Caducidad": str(row['Fecha_Caducidad']),
            "FechaEfectiva": str(row['Fecha_E_Portal']) if str(row['Fecha_E_Portal']) != "nan" else "",
            "Estado": "RESPUESTA ENTREGADA" if str(row['Fecha_E_Portal']).strip() not in ["", "nan"] else "EN ANÁLISIS",
            "SLA": "normal", # Simplificado para estabilidad
            "Adjunto_Solicitud": str(row.get('Adjunto_Solicitud', '')),
            "Adjunto_Respuesta": str(row.get('Adjunto_Respuesta', ''))
        })

    return {
        "detalles": detalles, 
        "stats": stats, 
        "chartData": [{"name": k, "cantidad": v} for k, v in conteo_deptos.items()]
    }

# --- RUTAS ---

@app.get("/get-stored-data")
async def get_data():
    if os.path.exists(DB_PATH):
        df = pd.read_csv(DB_PATH).astype(str)
        return procesar_informacion(df)
    return {"detalles": [], "stats": {m: 0 for m in meses_nombres}, "chartData": []}

@app.post("/login")
async def login(payload: dict = Body(...)):
    user, pwd = payload.get("username"), payload.get("password")
    if user in USUARIOS_PRO and USUARIOS_PRO[user] == pwd:
        return {"status": "success", "user": user}
    raise HTTPException(status_code=401, detail="Error")

@app.get("/export-excel")
async def export():
    df = pd.read_csv(DB_PATH).astype(str)
    res = procesar_informacion(df)
    df_export = pd.DataFrame(res['detalles'])
    mapeo = {"Codigo": "CÓDIGO", "Ingreso": "FECHA INGRESO", "Responsable": "RESPONSABLE", "Dependencia": "DEPENDENCIA", "Caducidad": "CADUCIDAD", "FechaEfectiva": "FECHA PORTAL", "Estado": "ESTADO"}
    df_final = df_export[mapeo.keys()].rename(columns=mapeo)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False)
    output.seek(0)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=Reporte_Puyehue.xlsx"})

@app.get("/download-backup")
async def download_backup():
    return StreamingResponse(open(DB_PATH, "rb"), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=backup.csv"})


# --- AGREGAR ESTA FUNCIÓN PARA EL CÁLCULO ---
def calcular_fecha_vencimiento(fecha_ingreso_str, con_prorroga):
    try:
        dt_inicio = normalizar_fecha_estricta(fecha_ingreso_str)
        if not dt_inicio: return ""
        
        inicio = dt_inicio.date()
        dias_a_sumar = 30 if con_prorroga else 20
        holidays = [np.datetime64(f) for f in FERIADOS_CHILE]
        
        # Cálculo de días hábiles usando numpy
        vencimiento = np.busday_offset(inicio, dias_a_sumar, roll='forward', holidays=holidays)
        return pd.to_datetime(vencimiento).strftime('%d-%m-%Y')
    except Exception as e:
        print(f"Error calculando vencimiento: {e}")
        return ""

# --- AGREGAR/REEMPLAZAR LA RUTA DE ACTUALIZACIÓN ---
@app.post("/update-row")
async def update(payload: dict = Body(...)):
    if not os.path.exists(DB_PATH): return {"status": "error"}
    
    df = pd.read_csv(DB_PATH).astype(str)
    df = normalizar_df(df)
    
    idx = df[df['Código'] == str(payload['Codigo'])].index
    if not idx.empty:
        campo_final = {'FechaEfectiva': 'Fecha_E_Portal'}.get(payload['Campo'], payload['Campo'])
        valor_nuevo = str(payload['Valor'])
        
        # Si el campo es Prorroga, actualizamos el valor y recalculamos Caducidad
        if campo_final == 'Prorroga':
            # Convertimos el booleano de React a '1' o '0' para el CSV
            estado_prorroga = valor_nuevo.lower() == 'true'
            df.at[idx[0], 'Prorroga'] = '1' if estado_prorroga else '0'
            # Recalcular Caducidad basado en la nueva prórroga
            df.at[idx[0], 'Fecha_Caducidad'] = calcular_fecha_vencimiento(df.at[idx[0], 'Fecha_Ingreso'], estado_prorroga)
        else:
            df.at[idx[0], campo_final] = valor_nuevo
            
        df.to_csv(DB_PATH, index=False)
        return procesar_informacion(df)
    
    raise HTTPException(status_code=404, detail="No encontrado")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)