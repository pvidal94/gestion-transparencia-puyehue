import React, { useState, useEffect } from 'react';
import axios from 'axios';

const RESPONSABLES_BASE = ["Juan Soto", "Bety Mora", "Marta Ovando", "Jorge Pacheco", "Byron Oyarzun", "Guido Vidal", "Eladio Acum", "Nefi Linco", "Soledad Villalobos", "Javier Lopez", "Raúl Navarrete", "Daniela Silva", "Felipe Post", "Robinson Rosales", "Daniella Muñoz"];

const DEPARTAMENTOS = ["Administrador Municipal", "Oficina de Transparencia Municipal", "Oficina de Gestión de Riesgos y Desastres", "Oficina de Transformación Digital", "Oficina de Prevención de Riesgos", "Secretaría Municipal", "Oficina O.I.R.S", "Oficina de Partes", "Oficina de Seguridad Pública e Inspección Municipal", "Oficina de Control Vehicular", "Oficina de Comunicaciones", "Oficina de Informática", "Dirección de Control", "Secretaría Comunal de Planificación", "Dirección de Obras Municipales", "Unidad de Aseo y Ornato", "Oficina de Caminos Vecinales", "Oficina de Cementerio", "Oficina de Alumbrado Público", "Dirección de Administración y Finanzas", "Oficina de Contabilidad", "Oficina de Tesorería", "Oficina de Rentas y Patentes", "Oficina de Adquisiciones", "Oficina de Inventario", "Oficina de Personal", "Dirección de Desarrollo Comunitario", "Departamento Social", "Departamento de Organizaciones Comunitarias", "Oficina de Programas Sociales", "Oficina de Deportes", "Oficina de Pueblos Originarios", "Departamento de Desarrollo Rural", "Departamento de Turismo", "Oficina PRODESAL / PDTI / PRODER", "Oficina de Cultura / Biblioteca Municipal", "Oficina de Medio Ambiente", "Oficina de Fomento Productivo", "Oficina de Tránsito", "Oficina de Licencias de Conducir", "Oficina de Permisos de Circulación", "Departamento de Educación Municipal", "Departamento de Salud Municipal"];

const THEME = {
  navy: '#0f172a',
  accent: '#2563eb',
  success: '#059669',
  danger: '#e11d48',
  bg: '#f8fafc',
  border: '#e2e8f0',
  white: '#ffffff'
};

export default function App() {
  const [data, setData] = useState(null);
  const [stats, setStats] = useState({ Enero: 0, Febrero: 0, Marzo: 0 });
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualRow, setManualRow] = useState({ Codigo: '', Ingreso: '', Caducidad: '' });

  useEffect(() => { cargarDatos(); }, []);

  const cargarDatos = async () => {
    try {
      const res = await axios.get('http://localhost:8000/get-stored-data');
      if (res.data.detalles) { setData(res.data); setStats(res.data.stats); }
    } catch (e) { console.error(e); }
  };

  // FUNCIÓN PARA FORMATEAR FECHA DE YYYY-MM-DD A DD-MM-YYYY
  const formatearFechaChile = (fechaStr) => {
    if (!fechaStr || fechaStr === 'nan' || fechaStr === '') return '—';
    if (fechaStr.includes('-')) {
        const partes = fechaStr.split('-');
        if (partes[0].length === 4) { // Es formato YYYY-MM-DD
            return `${partes[2]}-${partes[1]}-${partes[0]}`;
        }
    }
    return fechaStr;
  };

  const editar = async (codigo, campo, valor) => {
    try { 
      const cB = campo === 'FechaEfectiva' ? 'Fecha_Efectiva_Portal' : campo;
      await axios.post('http://localhost:8000/update-row', { 
        Codigo: codigo, Campo: cB, Valor: campo === 'Prorroga' ? (valor ? "1" : "0") : valor 
      }); 
      cargarDatos();
    } catch (e) { console.error(e); }
  };

  const agregarManual = async () => {
    if (!manualRow.Codigo || !manualRow.Ingreso || !manualRow.Caducidad) {
        return alert("Por favor, complete todos los campos requeridos.");
    }
    try { 
      await axios.post('http://localhost:8000/add-manual', manualRow); 
      cargarDatos();
      setShowManualForm(false); 
      setManualRow({ Codigo: '', Ingreso: '', Caducidad: '' }); 
    } catch (e) { console.error(e); }
  };

  const eliminarFila = async (codigo) => {
    if (!window.confirm(`¿Está seguro de eliminar la solicitud ${codigo}?`)) return;
    try { 
      await axios.post('http://localhost:8000/delete-row', { Codigo: codigo }); 
      cargarDatos();
    } catch (e) { console.error("Error al eliminar:", e); }
  };

  return (
    <div style={{ padding: '40px', backgroundColor: THEME.bg, minHeight: '100vh', fontFamily: 'Inter, system-ui, sans-serif' }}>
      
      {/* HEADER */}
      <div style={{ maxWidth: '1400px', margin: '0 auto 40px auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ 
            background: THEME.white, padding: '10px', borderRadius: '16px', 
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)', display: 'flex', alignItems: 'center'
          }}>
             <img src="/logo_puyehue.png" alt="Logo" style={{ height: '60px', width: 'auto' }} />
          </div>
          <div>
            <h1 style={{ margin: 0, color: THEME.navy, fontSize: '26px', fontWeight: '800' }}>Gestión de Transparencia</h1>
            <p style={{ margin: 0, color: '#64748b', fontSize: '15px' }}>Ilustre Municipalidad de Puyehue</p>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '15px' }}>
            <button onClick={() => setShowManualForm(!showManualForm)} style={{ padding: '12px 24px', backgroundColor: showManualForm ? THEME.danger : THEME.accent, color: 'white', border: 'none', borderRadius: '12px', fontWeight: '600', cursor: 'pointer', transition: '0.3s' }}>
                {showManualForm ? '✖ Cancelar' : '＋ Nueva Solicitud'}
            </button>
            <button onClick={() => window.open('http://localhost:8000/export-excel', '_blank')} style={{ padding: '12px 24px', backgroundColor: THEME.navy, color: THEME.white, border: 'none', borderRadius: '12px', fontWeight: '600', cursor: 'pointer' }}>
                📊 Reporte Excel
            </button>
        </div>
      </div>

      {/* FORMULARIO */}
      {showManualForm && (
        <div style={{ maxWidth: '1400px', margin: '0 auto 30px auto', backgroundColor: THEME.white, padding: '30px', borderRadius: '24px', boxShadow: '0 10px 25px rgba(0,0,0,0.05)', border: `1px solid ${THEME.border}` }}>
            <h3 style={{ margin: '0 0 20px 0', color: THEME.navy, fontSize: '18px' }}>Ingreso Manual de Solicitud</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '8px', color: '#475569' }}>CÓDIGO SIGT</label>
                  <input placeholder="Ej: MU245P..." value={manualRow.Codigo} onChange={e => setManualRow({...manualRow, Codigo: e.target.value})} style={{ width: '100%', padding: '12px', borderRadius: '10px', border: `1px solid ${THEME.border}`, boxSizing: 'border-box' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '8px', color: '#475569' }}>FECHA DE INGRESO</label>
                  <input type="date" value={manualRow.Ingreso} onChange={e => setManualRow({...manualRow, Ingreso: e.target.value})} style={{ width: '100%', padding: '12px', borderRadius: '10px', border: `1px solid ${THEME.border}`, boxSizing: 'border-box' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '8px', color: '#475569' }}>FECHA MÁXIMA DE ENTREGA</label>
                  <input type="date" value={manualRow.Caducidad} onChange={e => setManualRow({...manualRow, Caducidad: e.target.value})} style={{ width: '100%', padding: '12px', borderRadius: '10px', border: `1px solid ${THEME.border}`, boxSizing: 'border-box' }} />
                </div>
            </div>
            <div style={{ textAlign: 'right', marginTop: '20px' }}>
              <button onClick={agregarManual} style={{ padding: '12px 40px', backgroundColor: THEME.success, color: 'white', border: 'none', borderRadius: '10px', fontWeight: '700', cursor: 'pointer' }}>
                Confirmar Ingreso
              </button>
            </div>
        </div>
      )}

      {/* TABLA */}
      <div style={{ maxWidth: '1400px', margin: '0 auto', backgroundColor: THEME.white, borderRadius: '24px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.05)', overflow: 'hidden', border: `1px solid ${THEME.border}` }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead style={{ backgroundColor: '#f1f5f9', borderBottom: `2px solid ${THEME.border}` }}>
            <tr>
              <th style={{ padding: '20px', color: '#475569', fontWeight: '800' }}>IDENTIFICACIÓN</th>
              <th style={{ padding: '20px', color: '#475569', fontWeight: '800' }}>UNIDAD / RESPONSABLE</th>
              <th style={{ padding: '20px', color: '#475569', fontWeight: '800', textAlign: 'center' }}>PRÓRROGA</th>
              <th style={{ padding: '20px', color: '#475569', fontWeight: '800' }}>PLAZOS</th>
              <th style={{ padding: '20px', color: '#475569', fontWeight: '800', textAlign: 'center' }}>DÍAS</th>
              <th style={{ padding: '20px', color: '#475569', fontWeight: '800' }}>ESTADO</th>
              <th style={{ padding: '20px' }}></th>
            </tr>
          </thead>
          <tbody>
            {data?.detalles.map((item, i) => {
              const isLocked = item.Estado === "RESPUESTA ENTREGADA";
              return (
                <tr key={i} style={{ borderBottom: `1px solid ${THEME.border}`, backgroundColor: isLocked ? '#f8fafc' : THEME.white }}>
                  <td style={{ padding: '20px' }}>
                    <div style={{ fontWeight: '800', color: THEME.navy, fontSize: '14px' }}>{item.Codigo}</div>
                    <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                        Ingreso: {formatearFechaChile(item.Ingreso)}
                    </div>
                  </td>
                  <td style={{ padding: '20px' }}>
                    <select value={item.Dependencia} onChange={(e) => editar(item.Codigo, 'Dependencia', e.target.value)} disabled={isLocked} style={{ width: '100%', padding: '8px', borderRadius: '8px', border: `1px solid ${THEME.border}`, marginBottom: '5px' }}>
                      <option value="">-- Unidad --</option>
                      {DEPARTAMENTOS.map(d => <option key={d} value={d}>{d}</option>)}
                    </select>
                    <select value={item.Responsable} onChange={(e) => editar(item.Codigo, 'Responsable', e.target.value)} disabled={isLocked} style={{ width: '100%', padding: '8px', borderRadius: '8px', border: `1px solid ${THEME.border}` }}>
                      <option value="">-- Responsable --</option>
                      {RESPONSABLES_BASE.map(r => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </td>
                  <td style={{ padding: '20px', textAlign: 'center' }}>
                    <button onClick={() => !isLocked && editar(item.Codigo, 'Prorroga', !item.Prorroga)} style={{ padding: '6px 12px', borderRadius: '20px', border: 'none', cursor: isLocked ? 'default' : 'pointer', fontWeight: '700', fontSize: '10px', backgroundColor: item.Prorroga ? '#fee2e2' : '#f1f5f9', color: item.Prorroga ? THEME.danger : '#64748b' }}>
                        {item.Prorroga ? 'CON PRÓRROGA' : 'SIN PRÓRROGA'}
                    </button>
                  </td>
                  <td style={{ padding: '20px' }}>
                    <div style={{ color: THEME.danger, fontWeight: '700', fontSize: '11px' }}>Vence: {formatearFechaChile(item.Caducidad)}</div>
                    <input type="date" value={item.FechaEfectiva || ""} onChange={(e) => editar(item.Codigo, 'FechaEfectiva', e.target.value)} disabled={isLocked} style={{ marginTop: '8px', padding: '6px', borderRadius: '6px', border: `1px solid ${THEME.border}`, fontSize: '11px', width: '100%' }} />
                  </td>
                  <td style={{ padding: '20px', textAlign: 'center' }}>
                    <div style={{ background: '#f1f5f9', padding: '10px', borderRadius: '12px', fontWeight: '900', color: THEME.navy }}>{item.DiasHabiles || '—'}</div>
                  </td>
                  <td style={{ padding: '20px' }}>
                    <div style={{ padding: '6px 12px', borderRadius: '8px', fontSize: '11px', fontWeight: '700', textAlign: 'center', backgroundColor: isLocked ? '#dcfce7' : '#fef3c7', color: isLocked ? '#166534' : '#92400e' }}>
                        {item.Estado}
                    </div>
                  </td>
                  <td style={{ padding: '20px', textAlign: 'center' }}>
                    {!isLocked && (
                        <button 
                            onClick={() => eliminarFila(item.Codigo)} 
                            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '18px', opacity: 0.6 }}
                            onMouseEnter={(e) => e.target.style.opacity = "1"}
                            onMouseLeave={(e) => e.target.style.opacity = "0.6"}
                        >
                            🗑️
                        </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}