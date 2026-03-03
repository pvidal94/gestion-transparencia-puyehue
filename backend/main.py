import os
import io
import pandas as pd
import numpy as np
import re
from datetime import datetime
from fastapi import FastAPI, Body, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil

app = FastAPI()

# --- CONFIGURACIÓN DE DIRECTORIOS ---
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

# --- SEGURIDAD ---
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

# --- FUNCIONES AUXILIARES ---

def normalizar_fecha_estricta(fecha_val):
    if not fecha_val or str(fecha_val).lower() in ["nan", "none", ""]:
        return None
    f_str = str(fecha_val).strip()
    for fmt in ('%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(f_str, fmt)
        except ValueError:
            continue
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

def calcular_fecha_vencimiento(fecha_ingreso_str, con_prorroga):
    try:
        dt_inicio = normalizar_fecha_estricta(fecha_ingreso_str)
        if not dt_inicio: return ""
        inicio = dt_inicio.date()
        dias_a_sumar = 30 if con_prorroga else 20
        holidays = [np.datetime64(f) for f in FERIADOS_CHILE]
        vencimiento = np.busday_offset(inicio, dias_a_sumar, roll='forward', holidays=holidays)
        return pd.to_datetime(vencimiento).strftime('%d-%m-%Y')
    except:
        return ""

def procesar_informacion(df):
    df = normalizar_df(df)
    detalles = []
    meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    stats = {mes: 0 for mes in meses_nombres}
    conteo_deptos = {}

    for _, row in df.iterrows():
        cod = str(row['Código']).strip()
        if not cod or cod in ["", "nan"]: continue
        
        dt_ingreso = normalizar_fecha_estricta(row['Fecha_Ingreso'])
        if dt_ingreso:
            stats[meses_nombres[dt_ingreso.month - 1]] += 1

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
            "SLA": "normal",
            "Adjunto_Solicitud": str(row.get('Adjunto_Solicitud', '')),
            "Adjunto_Respuesta": str(row.get('Adjunto_Respuesta', ''))
        })
    return {"detalles": detalles, "stats": stats, "chartData": [{"name": k, "cantidad": v} for k, v in conteo_deptos.items()]}

# --- RUTAS API ---

@app.get("/get-stored-data")
async def get_data():
    if os.path.exists(DB_PATH):
        df = pd.read_csv(DB_PATH).astype(str)
        return procesar_informacion(df)
    return {"detalles": [], "stats": {m: 0 for m in ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]}, "chartData": []}

@app.post("/login")
async def login(payload: dict = Body(...)):
    user, pwd = payload.get("username"), payload.get("password")
    if user in USUARIOS_PRO and USUARIOS_PRO[user] == pwd:
        return {"status": "success", "user": user}
    raise HTTPException(status_code=401, detail="Error")

@app.post("/add-manual")
async def add_manual(payload: dict = Body(...)):
    new_row = {
        'Código': str(payload.get('Codigo')),
        'Fecha_Ingreso': str(payload.get('Ingreso')),
        'Fecha_Caducidad': str(payload.get('Caducidad')),
        'Responsable': '', 'Dependencia': '', 'Fecha_E_Portal': '', 'Prorroga': '0', 'Dias_Habiles': '', 'Adjunto_Solicitud': '', 'Adjunto_Respuesta': ''
    }
    df = pd.read_csv(DB_PATH).astype(str) if os.path.exists(DB_PATH) else pd.DataFrame(columns=new_row.keys())
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DB_PATH, index=False)
    return procesar_informacion(df)

@app.post("/update-row")
async def update(payload: dict = Body(...)):
    df = pd.read_csv(DB_PATH).astype(str)
    df = normalizar_df(df)
    idx = df[df['Código'] == str(payload['Codigo'])].index
    if not idx.empty:
        campo_final = {'FechaEfectiva': 'Fecha_E_Portal'}.get(payload['Campo'], payload['Campo'])
        valor_nuevo = str(payload['Valor'])
        if campo_final == 'Prorroga':
            estado_prorroga = valor_nuevo.lower() == 'true'
            df.at[idx[0], 'Prorroga'] = '1' if estado_prorroga else '0'
            df.at[idx[0], 'Fecha_Caducidad'] = calcular_fecha_vencimiento(df.at[idx[0], 'Fecha_Ingreso'], estado_prorroga)
        else:
            df.at[idx[0], campo_final] = valor_nuevo
        df.to_csv(DB_PATH, index=False)
        return procesar_informacion(df)
    raise HTTPException(status_code=404, detail="No encontrado")

@app.post("/delete-row")
async def delete_row(payload: dict = Body(...)):
    df = pd.read_csv(DB_PATH).astype(str)
    df = df[df['Código'] != str(payload['Codigo'])]
    df.to_csv(DB_PATH, index=False)
    return procesar_informacion(df)

@app.get("/get-next-codigo")
async def get_next_codigo():
    if not os.path.exists(DB_PATH): return {"next_codigo": "MU245T0001427"}
    df = pd.read_csv(DB_PATH).astype(str)
    if df.empty: return {"next_codigo": "MU245T0001427"}
    ultimo_codigo = df['Código'].iloc[-1]
    match = re.search(r'(\d+)$', ultimo_codigo)
    if match:
        num_str = match.group(1)
        next_codigo = f"{ultimo_codigo[:match.start()]}{str(int(num_str)+1).zfill(len(num_str))}"
        return {"next_codigo": next_codigo}
    return {"next_codigo": "MU245T0001"}

@app.post("/calcular-vencimiento-inicial")
async def api_calcular_vencimiento(payload: dict = Body(...)):
    fecha_venc = calcular_fecha_vencimiento(payload.get('Ingreso'), False)
    if fecha_venc:
        return {"Caducidad": datetime.strptime(fecha_venc, '%d-%m-%Y').strftime('%Y-%m-%d')}
    return {"Caducidad": ""}

@app.get("/export-excel")
async def export():
    df = pd.read_csv(DB_PATH).astype(str)
    res = procesar_informacion(df)
    df_export = pd.DataFrame(res['detalles'])
    mapeo = {"Codigo": "CÓDIGO", "Ingreso": "FECHA INGRESO", "Responsable": "RESPONSABLE", "Dependencia": "DEPENDENCIA", "Caducidad": "CADUCIDAD", "FechaEfectiva": "FECHA PORTAL", "Estado": "ESTADO"}
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export[mapeo.keys()].rename(columns=mapeo).to_excel(writer, index=False)
    output.seek(0)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=Reporte_Puyehue.xlsx"})

@app.get("/download-backup")
async def download_backup():
    return StreamingResponse(open(DB_PATH, "rb"), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=backup.csv"})

@app.post("/subir-adjunto/{codigo}/{tipo}")
async def subir_adjunto(codigo: str, tipo: str, file: UploadFile = File(...)):
    nombre_archivo = f"{tipo}_{codigo}.{file.filename.split('.')[-1]}"
    with open(os.path.join(UPLOAD_DIR, nombre_archivo), "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    df = pd.read_csv(DB_PATH).astype(str)
    idx = df[df['Código'] == codigo].index
    if not idx.empty:
        df.at[idx[0], 'Adjunto_Solicitud' if tipo == 'solicitud' else 'Adjunto_Respuesta'] = nombre_archivo
        df.to_csv(DB_PATH, index=False)
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)