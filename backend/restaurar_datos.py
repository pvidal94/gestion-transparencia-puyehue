import pandas as pd
import os

# Ruta corregida para asegurar que llegue a la carpeta data_storage
DB_PATH = "data_storage/db_gestion_puyehue.csv"

datos = [
    ["MU245T0001368", "01-10-2025", "Daniela Silva", "Dirección de Desarrollo Comunitario", "1", "13-11-2025", "2025-11-10"],
    ["MU245T0001369", "04-10-2025", "Soledad Villalobos", "Oficina de Medio Ambiente", "0", "04-11-2025", "2025-10-21"],
    ["MU245T0001370", "05-10-2025", "Bety Mora", "Dirección de Obras Municipales", "1", "18-11-2025", "2025-11-17"],
    ["MU245T0001371", "09-10-2025", "Eladio Acum", "Oficina de Tránsito", "0", "07-11-2025", "2025-11-04"],
    ["MU245T0001372", "13-10-2025", "Eladio Acum", "Oficina de Tránsito", "0", "11-11-2025", "2025-11-10"],
    ["MU245T0001373", "13-10-2025", "Juan Soto", "Administración Municipal", "0", "11-11-2025", "2025-11-06"],
    ["MU245T0001374", "15-10-2025", "Eladio Acum", "Oficina de Tránsito", "0", "13-11-2025", "2025-11-04"],
    ["MU245T0001375", "18-10-2025", "Juan Soto", "Administración Municipal", "0", "18-11-2025", "2025-10-20"],
    ["MU245T0001376", "20-10-2025", "Juan Soto", "Administración Municipal", "0", "18-11-2025", "2025-10-21"],
    ["MU245T0001377", "20-10-2025", "Juan Soto", "Administración Municipal", "0", "18-11-2025", "2025-10-21"],
    ["MU245T0001378", "21-10-2025", "Guido Vidal", "Oficina de Tesorería", "0", "19-11-2025", "2025-11-19"],
    ["MU245T0001379", "23-10-2025", "Eladio Acum", "Oficina de Tránsito", "0", "21-11-2025", "2025-11-21"],
    ["MU245T0001380", "24-10-2025", "Eladio Acum", "Oficina de Tránsito", "0", "24-11-2025", "2025-11-05"],
    ["MU245T0001381", "29-10-2025", "Soledad Villalobos", "Oficina de Medio Ambiente", "0", "27-11-2025", "2025-11-21"],
    ["MU245T0001382", "30-10-2025", "Eladio Acum", "Oficina de Tránsito", "0", "28-11-2025", "2025-11-24"],
    ["MU245T0001383", "03-11-2025", "Byron Oyarzun", "Oficina de Contabilidad", "0", "16-01-2026", "2025-11-27"],
    ["MU245T0001384", "03-11-2025", "Soledad Villalobos", "Oficina de Medio Ambiente", "0", "01-12-2025", "2025-11-21"],
    ["MU245T0001385", "04-11-2025", "Eladio Acum", "Oficina de Tránsito", "0", "02-12-2025", "2025-12-02"],
    ["MU245T0001386", "05-11-2025", "Juan Soto", "Administración Municipal", "0", "03-12-2025", "2025-12-03"],
    ["MU245T0001387", "07-11-2025", "Bety Mora", "Dirección de Obras Municipales", "0", "05-12-2025", "2025-11-21"],
    ["MU245T0001388", "10-11-2025", "Nefi Linco", "Secretaría Comunal de Planificación", "1", "23-12-2025", "2025-12-23"],
    ["MU245T0001389", "17-11-2025", "Javier Lopez", "Oficina de Seguridad Pública e Inspección Municipal", "0", "16-12-2025", "2025-12-02"],
    ["MU245T0001390", "18-11-2025", "Jorge Pacheco", "Dirección de Administración y Finanzas", "1", "02-01-2026", ""],
    ["MU245T0001391", "23-11-2025", "Juan Soto", "Administración Municipal", "1", "08-01-2026", ""],
    ["MU245T0001392", "23-11-2025", "Nefi Linco", "Secretaría Comunal de Planificación", "1", "08-01-2026", ""],
    ["MU245T0001393", "25-11-2025", "Juan Soto", "Administración Municipal", "0", "24-12-2025", "2025-11-27"],
    ["MU245T0001394", "28-11-2025", "Soledad Villalobos", "Oficina de Medio Ambiente", "0", "30-12-2025", "2025-12-29"],
    ["MU245T0001395", "28-11-2025", "Bety Mora", "Dirección de Obras Municipales", "0", "30-12-2025", "2025-12-29"],
    ["MU245T0001396", "04-12-2025", "Juan Soto", "Administración Municipal", "0", "06-01-2026", "2025-12-11"],
    ["MU245T0001397", "11-12-2025", "Eladio Acum", "Oficina de Tránsito", "0", "12-01-2026", ""],
    ["MU245T0001398", "15-12-2025", "Nefi Linco", "Secretaría Comunal de Planificación", "0", "14-01-2026", ""],
    ["MU245T0001399", "18-12-2025", "Soledad Villalobos", "Oficina de Medio Ambiente", "0", "19-01-2026", "2025-12-31"],
    ["MU245T0001400", "23-12-2025", "Eladio Acum", "Oficina de Tránsito", "0", "22-01-2026", ""],
    ["MU245T0001401", "23-12-2025", "Soledad Villalobos", "Oficina de Medio Ambiente", "0", "22-01-2026", ""],
    ["MU245T0001402", "29-12-2025", "Felipe Post", "Oficina de Deportes", "0", "27-01-2026", ""],
    ["MU245T0001403", "30-12-2025", "Juan Soto", "Administración Municipal", "0", "28-01-2026", ""]
]

df = pd.DataFrame(datos, columns=['Código', 'Fecha_Ingreso', 'Responsable', 'Dependencia', 'Prorroga', 'Fecha_Caducidad', 'Fecha_Efectiva_Portal'])

if not os.path.exists("data_storage"):
    os.makedirs("data_storage")

df.to_csv(DB_PATH, index=False)
print("✅ DATOS RESTAURADOS EXITOSAMENTE")