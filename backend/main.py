import os
import io
import pandas as pd
import numpy as np
from fastapi import FastAPI, Body, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuración de CORS para que el Frontend pueda comunicarse
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

DATA_DIR = "data_storage"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
DB_PATH = os.path.join(DATA_DIR, "db_gestion_puyehue.csv")

# Feriados Chile 2026 (Para descuento en días hábiles)
FERIADOS_CHILE = [
    '2026-01-01', '2026-04-03', '2026-04-04', '2026-05-01', '2026-05-21', 
    '2026-06-21', '2026-06-29', '2026-07-16', '2026-08-15', '2026-09-18', 
    '2026-09-19', '2026-10-12', '2026-10-31', '2026-11-01', '2026-12-08', 
    '2026-12-25'
]

def normalizar_df(df):
    """Limpia nombres de columnas y asegura que existan las necesarias"""
    df.columns = df.columns.str.strip().str.replace(' ', '_')
    columnas_base = [
        'Código', 'Fecha_Ingreso', 'Fecha_Caducidad', 'Responsable', 
        'Dependencia', 'Fecha_Efectiva_Portal', 'Prorroga', 'Dias_Habiles'
    ]
    for col in columnas_base:
        if col not in df.columns:
            df[col] = ""
    return df.fillna("")

def calcular_dias_habiles(inicio_raw, fin_raw):
    """Calcula días hábiles descontando fines de semana y feriados"""
    if pd.isnull(inicio_raw) or pd.isnull(fin_raw):
        return ""
    try:
        inicio = inicio_raw.date()
        fin = fin_raw.date()
        if inicio > fin: return 0
        
        holidays = [np.datetime64(f) for f in FERIADOS_CHILE]
        # Offset para empezar a contar desde el día siguiente al ingreso
        dia_inicio = np.busday_offset(inicio, 1, roll='forward', holidays=holidays)
        # Cuenta días hasta la fecha de respuesta inclusive
        count = int(np.busday_count(dia_inicio, fin, holidays=holidays) + 1)
        return count if count >= 0 else 0
    except:
        return ""

def procesar_informacion(df):
    """Lógica principal: Calcula stats y formatea datos para la tabla"""
    df = normalizar_df(df)
    
    # Convertir a fecha real (Día primero como en Chile)
    df['FI_DT'] = pd.to_datetime(df['Fecha_Ingreso'], dayfirst=True, errors='coerce')
    df['FP_DT'] = pd.to_datetime(df['Fecha_Efectiva_Portal'], dayfirst=True, errors='coerce')
    
    detalles = []
    stats = {"Enero": 0, "Febrero": 0, "Marzo": 0}

    for _, row in df.iterrows():
        if not row['Código'] or str(row['Código']).strip() == "": continue
        
        # Estadísticas de ingresos 2026
        if pd.notnull(row['FI_DT']) and row['FI_DT'].year == 2026:
            m = row['FI_DT'].month
            if m == 1: stats["Enero"] += 1
            elif m == 2: stats["Febrero"] += 1
            elif m == 3: stats["Marzo"] += 1

        # Lógica de Días Hábiles
        valor_manual = str(row.get('Dias_Habiles', '')).strip()
        if valor_manual != "" and valor_manual != "nan":
            # Si escribiste algo a mano, se queda ese valor
            habiles = valor_manual
        else:
            # Si está vacío, calcula entre Ingreso y Portal
            habiles = calcular_dias_habiles(row['FI_DT'], row['FP_DT'])

        estado = "RESPUESTA ENTREGADA" if str(row['Fecha_Efectiva_Portal']).strip() not in ["", "nan"] else "EN ÁNALISIS"

        detalles.append({
            "Codigo": str(row['Código']),
            "Ingreso": row['FI_DT'].strftime('%d-%m-%Y') if pd.notnull(row['FI_DT']) else str(row['Fecha_Ingreso']),
            "Responsable": str(row['Responsable']),
            "Dependencia": str(row['Dependencia']),
            "Prorroga": str(row['Prorroga']) in ['1', 'SÍ', 'Sí', '1.0', 'True'],
            "Caducidad": str(row['Fecha_Caducidad']),
            "FechaEfectiva": str(row['Fecha_Efectiva_Portal']),
            "DiasHabiles": habiles,
            "Estado": estado
        })
    return {"detalles": detalles, "stats": stats}

@app.get("/get-stored-data")
async def get_data():
    if os.path.exists(DB_PATH):
        df = pd.read_csv(DB_PATH).astype(str)
        return procesar_informacion(df)
    return {"detalles": [], "stats": {"Enero": 0, "Febrero": 0, "Marzo": 0}}

@app.post("/update-row")
async def update(payload: dict = Body(...)):
    if not os.path.exists(DB_PATH): return {"status": "error"}
    df = pd.read_csv(DB_PATH).astype(str)
    df = normalizar_df(df)
    
    idx = df[df['Código'] == str(payload['Codigo'])].index
    if not idx.empty:
        campo_map = {'FechaEfectiva': 'Fecha_Efectiva_Portal', 'DiasHabiles': 'Dias_Habiles'}
        campo_final = campo_map.get(payload['Campo'], payload['Campo'])
        df.at[idx[0], campo_final] = str(payload['Valor'])
        df.to_csv(DB_PATH, index=False)
        return {"status": "success"}
    return {"status": "error"}

@app.post("/add-manual")
async def add(payload: dict = Body(...)):
    # 1. Creamos la nueva fila
    new_data = {
        'Código': payload['Codigo'], 
        'Fecha_Ingreso': payload['Ingreso'], 
        'Fecha_Caducidad': payload['Caducidad'], 
        'Responsable': '', 
        'Dependencia': '', 
        'Fecha_Efectiva_Portal': '', 
        'Prorroga': '0', 
        'Dias_Habiles': ''
    }
    
    # 2. Leemos los datos actuales
    if os.path.exists(DB_PATH):
        df_existente = pd.read_csv(DB_PATH).astype(str)
        # 3. Concatenamos: Existente PRIMERO, Nueva DESPUÉS (al final)
        df_final = pd.concat([df_existente, pd.DataFrame([new_data])], ignore_index=True)
    else:
        df_final = pd.DataFrame([new_data])
        
    # 4. Guardamos
    df_final.to_csv(DB_PATH, index=False)
    
    # 5. Retornamos la información procesada para que se vea en la App
    return procesar_informacion(df_final)

@app.post("/delete-row")
async def delete_row(payload: dict = Body(...)):
    codigo = payload.get('Codigo')
    if os.path.exists(DB_PATH):
        df = pd.read_csv(DB_PATH).astype(str)
        # Filtramos el DataFrame para excluir la fila con ese código
        df = df[df['Código'] != codigo]
        df.to_csv(DB_PATH, index=False)
        return procesar_informacion(df)
    return {"message": "Archivo no encontrado"}

@app.get("/export-excel")
async def export():
    if not os.path.exists(DB_PATH): raise HTTPException(404, "No hay datos")
    df = pd.read_csv(DB_PATH).astype(str)
    res = procesar_informacion(df)
    df_export = pd.DataFrame(res['detalles'])
    mapeo_excel = {
        "Codigo": "CÓDIGO", "Ingreso": "FECHA INGRESO", "Responsable": "RESPONSABLE",
        "Dependencia": "DEPENDENCIA", "Prorroga": "PRÓRROGA", "Caducidad": "CADUCIDAD",
        "FechaEfectiva": "FECHA PORTAL", "DiasHabiles": "DÍAS HÁBILES", "Estado": "ESTADO"
    }
    df_export = df_export[mapeo_excel.keys()].rename(columns=mapeo_excel)
    df_export['PRÓRROGA'] = df_export['PRÓRROGA'].apply(lambda x: "SÍ" if x else "NO")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Q1_2026')
    output.seek(0)
    return StreamingResponse(
        output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={"Content-Disposition": "attachment; filename=Reporte_Puyehue_2026.xlsx"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)