import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const RESPONSABLES_BASE = ["Juan Soto", "Bety Mora", "Marta Ovando", "Jorge Pacheco", "Byron Oyarzun", "Guido Vidal", "Eladio Acum", "Nefi Linco", "Soledad Villalobos", "Javier Lopez", "Raúl Navarrete", "Daniela Silva", "Felipe Post", "Robinson Rosales", "Daniella Muñoz","Cristian Figueroa","Graciela Copilai","Karin Fuentes","Juan Pablo Mardondes","Pablo Hernandez"];

const DEPARTAMENTOS = ["Administrador Municipal", "Oficina de Transparencia Municipal", "Oficina de Gestión de Riesgos y Desastres", "Oficina de Transformación Digital", "Oficina de Prevención de Riesgos", "Secretaría Municipal", "Oficina O.I.R.S", "Oficina de Partes", "Oficina de Seguridad Pública e Inspección Municipal", "Oficina de Control Vehicular", "Oficina de Comunicaciones", "Oficina de Informática", "Dirección de Control", "Secretaría Comunal de Planificación", "Dirección de Obras Municipales", "Unidad de Aseo y Ornato", "Oficina de Caminos Vecinales", "Oficina de Cementerio", "Oficina de Alumbrado Público", "Dirección de Administración y Finanzas", "Oficina de Contabilidad", "Oficina de Tesorería", "Oficina de Rentas y Patentes", "Oficina de Adquisiciones", "Oficina de Inventario", "Oficina de Personal", "Dirección de Desarrollo Comunitario", "Departamento Social", "Departamento de Organizaciones Comunitarias", "Oficina de Programas Sociales", "Oficina de Deportes", "Oficina de Pueblos Originarios", "Departamento de Desarrollo Rural", "Departamento de Turismo", "Oficina PRODESAL / PDTI / PRODER", "Oficina de Cultura / Biblioteca Municipal", "Oficina de Medio Ambiente", "Oficina de Fomento Productivo", "Oficina de Tránsito", "Oficina de Licencias de Conducir", "Oficina de Permisos de Circulación", "Departamento de Educación Municipal", "Departamento de Salud Municipal"];

const THEME = {
  navy: '#0f172a',
  accent: '#2563eb',
  success: '#059669',
  danger: '#e11d48',
  warning: '#d97706',
  bg: '#f8fafc',
  border: '#e2e8f0',
  white: '#ffffff'
};

export default function App() {
  const [user, setUser] = useState(localStorage.getItem('user_puyehue') || null);
  const isAdmin = user === 'admin';
  const [loginData, setLoginData] = useState({ username: '', password: '' });
  const [loginError, setLoginError] = useState(false);
  const [data, setData] = useState({ detalles: [], stats: {}, chartData: [] });
  const [showManualForm, setShowManualForm] = useState(false);
  const [manualRow, setManualRow] = useState({ Codigo: '', Ingreso: '', Caducidad: '' });
  const [busqueda, setBusqueda] = useState("");

  useEffect(() => { if (user) cargarDatos(); }, [user]);

  const cargarDatos = async () => {
    try {
      const res = await axios.get('http://localhost:8000/get-stored-data');
      if (res.data) setData(res.data);
    } catch (e) { console.error("Error al cargar:", e); }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post('http://localhost:8000/login', loginData);
      if (res.data.status === 'success') {
        setUser(res.data.user);
        localStorage.setItem('user_puyehue', res.data.user);
        setLoginError(false);
      }
    } catch (err) { setLoginError(true); }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user_puyehue');
  };

  const manejarSubida = async (codigo, archivo, tipo) => {
    if (!archivo) return;
    const formData = new FormData();
    formData.append('file', archivo);
    try {
      await axios.post(`http://localhost:8000/subir-adjunto/${codigo}/${tipo}`, formData);
      cargarDatos();
      alert(`Archivo de ${tipo} guardado.`);
    } catch (e) { alert("Error al subir archivo."); }
  };

  const formatearFechaParaInput = (fechaStr) => {
    if (!fechaStr || fechaStr === 'nan' || fechaStr === '') return '';
    if (fechaStr.includes('-')) {
      const partes = fechaStr.split('-');
      if (partes[0].length === 4) return fechaStr; 
      return `${partes[2]}-${partes[1]}-${partes[0]}`; 
    }
    return '';
  };

  const formatearFechaChile = (fechaStr) => {
    if (!fechaStr || fechaStr === 'nan' || fechaStr === '') return '—';
    if (fechaStr.includes('-')) {
      const partes = fechaStr.split('-');
      if (partes[0].length === 4) return `${partes[2]}-${partes[1]}-${partes[0]}`;
      return fechaStr;
    }
    return fechaStr;
  };

  const editar = async (codigo, campo, valor) => {
    try {
      const campoBackend = campo === 'FechaEfectiva' ? 'Fecha_E_Portal' : 
                           campo === 'Ingreso' ? 'Fecha_Ingreso' : campo;
      const res = await axios.post('http://localhost:8000/update-row', {
        Codigo: codigo, Campo: campoBackend, Valor: valor
      });
      if (res.data.detalles) setData(res.data);
    } catch (e) { console.error("Error al editar:", e); }
  };

  const marcarRealizado = async (codigo) => {
    const hoy = new Date().toISOString().split('T')[0];
    if (!window.confirm(`¿Confirmar entrega de respuesta para ${codigo}?`)) return;
    await editar(codigo, 'FechaEfectiva', hoy);
  };

  const toggleManualForm = async () => {
    if (!showManualForm) {
      try {
        const res = await axios.get('http://localhost:8000/get-next-codigo');
        setManualRow({ Codigo: res.data.next_codigo, Ingreso: '', Caducidad: '' });
      } catch (e) {
        console.error("Error obteniendo correlativo");
      }
    }
    setShowManualForm(!showManualForm);
  };

  const agregarManual = async () => {
    // Verificación estricta de campos
    if (!manualRow.Codigo || !manualRow.Ingreso || !manualRow.Caducidad) {
        return alert("Por favor, complete la Fecha de Ingreso para calcular el vencimiento.");
    }
    
    try {
      // Enviamos el objeto manualRow completo
      const res = await axios.post('http://localhost:8000/add-manual', manualRow);
      if (res.data.detalles) {
          setData(res.data);
          setShowManualForm(false);
          setManualRow({ Codigo: '', Ingreso: '', Caducidad: '' });
          alert("Solicitud guardada con éxito.");
      }
    } catch (e) { 
        console.error(e); 
        alert("Error al conectar con el servidor.");
    }
  };

  const eliminarFila = async (codigo) => {
    if (!window.confirm(`¿Está seguro de eliminar la solicitud ${codigo}?`)) return;
    const res = await axios.post('http://localhost:8000/delete-row', { Codigo: codigo });
    setData(res.data);
  };

  const datosFiltrados = data.detalles.filter(item => {
    const coincideBusqueda = item.Codigo.toLowerCase().includes(busqueda.toLowerCase()) ||
                             item.Responsable.toLowerCase().includes(busqueda.toLowerCase()) ||
                             item.Dependencia.toLowerCase().includes(busqueda.toLowerCase());
    if (isAdmin) return coincideBusqueda;
    return coincideBusqueda && item.Responsable === user;
  });

  if (!user) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: THEME.navy }}>
        <div style={{ backgroundColor: 'white', padding: '40px', borderRadius: '24px', width: '350px', textAlign: 'center', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.3)' }}>
          <img src="/logo_puyehue.png" alt="Logo" style={{ height: '80px', marginBottom: '20px' }} />
          <h2 style={{ color: THEME.navy, margin: 0, fontWeight: '800' }}>SGT Puyehue</h2>
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '15px', marginTop: '20px' }}>
            <input type="text" placeholder="Usuario" style={{ padding: '12px', borderRadius: '10px', border: `1px solid ${THEME.border}` }}
              onChange={(e) => setLoginData({...loginData, username: e.target.value})} />
            <input type="password" placeholder="Contraseña" style={{ padding: '12px', borderRadius: '10px', border: `1px solid ${THEME.border}` }}
              onChange={(e) => setLoginData({...loginData, password: e.target.value})} />
            <button type="submit" style={{ padding: '12px', backgroundColor: THEME.accent, color: 'white', border: 'none', borderRadius: '10px', fontWeight: 'bold', cursor: 'pointer' }}>Entrar al Sistema</button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '40px', backgroundColor: THEME.bg, minHeight: '100vh', fontFamily: 'Inter, sans-serif' }}>
      
      {/* HEADER */}
      <div style={{ maxWidth: '1400px', margin: '0 auto 40px auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <img src="/logo_puyehue.png" alt="Logo" style={{ height: '60px' }} />
          <div>
            <h1 style={{ margin: 0, color: THEME.navy, fontSize: '24px', fontWeight: '800' }}>Gestión de Transparencia</h1>
            <p style={{ margin: 0, color: THEME.accent, fontSize: '14px', fontWeight: 'bold' }}>👤 {isAdmin ? 'ADMINISTRADOR' : `RESPONSABLE: ${user}`}</p>
          </div>
        </div>
        <input placeholder="Buscar solicitud..." value={busqueda} onChange={(e) => setBusqueda(e.target.value)} style={{ flex: 1, maxWidth: '400px', padding: '12px', borderRadius: '12px', border: `1px solid ${THEME.border}`, outline: 'none' }} />
        
        <div style={{ display: 'flex', gap: '10px' }}>
          {isAdmin && (
            <>
              <button onClick={toggleManualForm} style={{ padding: '12px 18px', backgroundColor: THEME.accent, color: 'white', border: 'none', borderRadius: '12px', fontWeight: '600', cursor: 'pointer' }}>
                {showManualForm ? 'Cancelar' : '＋ Nueva'}
              </button>
              <button onClick={() => window.open('http://localhost:8000/export-excel', '_blank')} style={{ padding: '12px 18px', backgroundColor: THEME.navy, color: THEME.white, border: 'none', borderRadius: '12px', fontWeight: '600', cursor: 'pointer' }}>📊 Excel</button>
              <button onClick={() => window.open('http://localhost:8000/download-backup', '_blank')} style={{ padding: '12px 18px', backgroundColor: '#475569', color: 'white', border: 'none', borderRadius: '12px', fontWeight: '600', cursor: 'pointer' }}>💾 Respaldo</button>
            </>
          )}
          <button onClick={handleLogout} style={{ padding: '12px', color: '#94a3b8', background: 'none', border: 'none', cursor: 'pointer' }}>Salir</button>
        </div>
      </div>

      {/* SECCIÓN ANALÍTICA */}
      {isAdmin && (
        <div style={{ maxWidth: '1400px', margin: '0 auto 30px auto', display: 'grid', gridTemplateColumns: '1.2fr 2fr', gap: '25px' }}>
          <div style={{ backgroundColor: THEME.white, padding: '20px', borderRadius: '24px', border: `1px solid ${THEME.border}`, height: '260px' }}>
            <h4 style={{ margin: '0 0 15px 0', color: '#64748b', fontSize: '11px', fontWeight: 'bold', textTransform: 'uppercase' }}>Carga por Departamento</h4>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.chartData}>
                <XAxis dataKey="name" hide />
                <Tooltip />
                <Bar dataKey="cantidad" fill={THEME.accent} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
            {Object.entries(data.stats).map(([mes, total]) => (
              <div key={mes} style={{
                backgroundColor: THEME.white, padding: '15px', borderRadius: '16px', border: total > 0 ? `1.5px solid ${THEME.accent}` : `1px solid ${THEME.border}`,
                textAlign: 'center', opacity: total > 0 ? 1 : 0.4, transition: '0.3s'
              }}>
                <div style={{ fontSize: '10px', fontWeight: '800', color: total > 0 ? THEME.accent : '#94a3b8', textTransform: 'uppercase' }}>{mes}</div>
                <div style={{ fontSize: '22px', fontWeight: '900', color: THEME.navy }}>{total}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* FORMULARIO MANUAL ACTUALIZADO */}
      {isAdmin && showManualForm && (
        <div style={{ maxWidth: '1400px', margin: '0 auto 30px auto', backgroundColor: THEME.white, padding: '30px', borderRadius: '24px', border: `2px solid ${THEME.accent}`, boxShadow: '0 10px 25px rgba(0,0,0,0.1)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
            <div>
              <label style={{ fontSize: '11px', fontWeight: 'bold', color: '#475569' }}>CÓDIGO SIGT (AUTO)</label>
              <input value={manualRow.Codigo} readOnly style={{ width: '100%', padding: '12px', borderRadius: '10px', border: `1px solid ${THEME.border}`, backgroundColor: '#f8fafc', marginTop: '5px' }} />
            </div>
            <div>
              <label style={{ fontSize: '11px', fontWeight: 'bold', color: '#475569' }}>FECHA INGRESO</label>
              <input type="date" value={manualRow.Ingreso} onChange={async (e) => {
                const fechaIngreso = e.target.value;
                setManualRow(prev => ({ ...prev, Ingreso: fechaIngreso }));
                if (fechaIngreso) {
                  const res = await axios.post('http://localhost:8000/calcular-vencimiento-inicial', { Ingreso: fechaIngreso });
                  setManualRow(prev => ({ ...prev, Caducidad: res.data.Caducidad }));
                }
              }} style={{ width: '100%', padding: '12px', borderRadius: '10px', border: `1px solid ${THEME.border}`, marginTop: '5px' }} />
            </div>
            <div>
              <label style={{ fontSize: '11px', fontWeight: 'bold', color: '#475569' }}>VENCIMIENTO (AUTO)</label>
              <input type="date" value={manualRow.Caducidad} readOnly style={{ width: '100%', padding: '12px', borderRadius: '10px', border: `1px solid ${THEME.border}`, backgroundColor: '#f0fdf4', fontWeight: 'bold', marginTop: '5px' }} />
            </div>
          </div>
          <button onClick={agregarManual} style={{ width: '100%', marginTop: '20px', padding: '12px', backgroundColor: THEME.success, color: 'white', borderRadius: '10px', fontWeight: '700', border: 'none', cursor: 'pointer' }}>Guardar Solicitud</button>
        </div>
      )}

      {/* TABLA PRINCIPAL */}
      <div style={{ maxWidth: '1400px', margin: '0 auto', backgroundColor: THEME.white, borderRadius: '24px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.05)', overflow: 'hidden', border: `1px solid ${THEME.border}` }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead style={{ backgroundColor: '#f1f5f9' }}>
            <tr>
              <th style={{ padding: '20px', color: '#475569', fontWeight: '800' }}>IDENTIFICACIÓN / INGRESO</th>
              <th style={{ padding: '20px', color: '#475569', fontWeight: '800' }}>UNIDAD / RESPONSABLE</th>
              <th style={{ padding: '20px', textAlign: 'center', color: '#475569', fontWeight: '800' }}>PRÓRROGA</th>
              {!isAdmin && <th style={{ padding: '20px', color: '#475569', fontWeight: '800' }}>ARCHIVOS</th>}
              <th style={{ padding: '20px', color: '#475569', fontWeight: '800' }}>FECHA PORTAL</th>
              <th style={{ padding: '20px', color: '#475569', fontWeight: '800' }}>ESTADO</th>
              <th style={{ padding: '20px', textAlign: 'center' }}>ACCIONES</th>
            </tr>
          </thead>
          <tbody>
            {datosFiltrados.map((item, i) => {
              const isLocked = item.Estado === "RESPUESTA ENTREGADA";
              return (
                <tr key={i} style={{ 
                  borderBottom: `1px solid ${THEME.border}`, 
                  backgroundColor: isLocked ? '#f8fafc' : (item.SLA === 'critico' ? '#fff1f2' : THEME.white),
                }}>
                  <td style={{ padding: '20px' }}>
                    <div style={{ fontWeight: '800', color: THEME.navy, fontSize: '14px', marginBottom: '8px' }}>{item.Codigo}</div>
                    <input 
                        type="date" 
                        value={formatearFechaParaInput(item.Ingreso)} 
                        onChange={(e) => editar(item.Codigo, 'Ingreso', e.target.value)}
                        disabled={!isAdmin || isLocked}
                        style={{ padding: '6px', borderRadius: '6px', border: `1px solid ${THEME.border}`, fontSize: '11px', width: '130px' }}
                    />
                  </td>
                  <td style={{ padding: '20px' }}>
                    <select value={item.Dependencia} onChange={(e) => editar(item.Codigo, 'Dependencia', e.target.value)} disabled={!isAdmin || isLocked} style={{ width: '100%', padding: '8px', borderRadius: '8px', border: `1px solid ${THEME.border}`, marginBottom: '5px', fontSize: '12px' }}>
                      <option value="">-- Unidad --</option>
                      {DEPARTAMENTOS.map(d => <option key={d} value={d}>{d}</option>)}
                    </select>
                    <select value={item.Responsable} onChange={(e) => editar(item.Codigo, 'Responsable', e.target.value)} disabled={!isAdmin || isLocked} style={{ width: '100%', padding: '8px', borderRadius: '8px', border: `1px solid ${THEME.border}`, fontSize: '12px' }}>
                      <option value="">-- Responsable --</option>
                      {RESPONSABLES_BASE.map(r => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </td>
                  <td style={{ padding: '20px', textAlign: 'center' }}>
                    <button onClick={() => isAdmin && !isLocked && editar(item.Codigo, 'Prorroga', !item.Prorroga)} disabled={!isAdmin || isLocked} style={{ padding: '6px 12px', borderRadius: '20px', border: 'none', fontWeight: '700', fontSize: '10px', backgroundColor: item.Prorroga ? '#fee2e2' : '#f1f5f9', color: item.Prorroga ? THEME.danger : '#64748b' }}>
                        {item.Prorroga ? 'CON PRÓRROGA' : 'SIN PRÓRROGA'}
                    </button>
                  </td>
                  {!isAdmin && (
                    <td style={{ padding: '20px', textAlign: 'center' }}>
                        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                        {item.Adjunto_Solicitud ? (
                            <a href={`http://localhost:8000/descargas/${item.Adjunto_Solicitud}`} target="_blank" rel="noreferrer" style={{fontSize:'18px', textDecoration:'none'}}>📥</a>
                        ) : (
                            !isLocked && <label style={{cursor:'pointer', fontSize:'18px'}}>📎<input type="file" style={{display:'none'}} onChange={(e)=>manejarSubida(item.Codigo, e.target.files[0], 'solicitud')}/></label>
                        )}
                        {item.Adjunto_Respuesta ? (
                            <a href={`http://localhost:8000/descargas/${item.Adjunto_Respuesta}`} target="_blank" rel="noreferrer" style={{fontSize:'18px', textDecoration:'none'}}>📤</a>
                        ) : (
                            !isLocked && <label style={{cursor:'pointer', fontSize:'18px'}}>📁<input type="file" style={{display:'none'}} onChange={(e)=>manejarSubida(item.Codigo, e.target.files[0], 'respuesta')}/></label>
                        )}
                        </div>
                    </td>
                  )}
                  <td style={{ padding: '20px' }}>
                    <input 
                        type="date" 
                        value={formatearFechaParaInput(item.FechaEfectiva)} 
                        onChange={(e) => editar(item.Codigo, 'FechaEfectiva', e.target.value)} 
                        disabled={!isAdmin || isLocked} 
                        style={{ padding: '6px', borderRadius: '6px', border: `1px solid ${THEME.border}`, width: '100%', fontSize: '11px' }} 
                    />
                  </td>
                  <td style={{ padding: '20px' }}>
                    <div style={{ color: THEME.navy, fontWeight: '700', fontSize: '12px' }}>Vence: {formatearFechaChile(item.Caducidad)}</div>
                    <div style={{ fontSize: '10px', color: isLocked ? THEME.success : '#64748b', fontWeight: 'bold', marginTop: '4px' }}>{item.Estado}</div>
                  </td>
                  <td style={{ padding: '20px', textAlign: 'center' }}>
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', alignItems: 'center' }}>
                      {isAdmin && !isLocked && (
                        <button onClick={() => eliminarFila(item.Codigo)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '18px' }}>🗑️</button>
                      )}
                      {isLocked ? (
                        <span style={{ color: THEME.success, fontWeight: 'bold', fontSize: '11px' }}>CERRADA</span>
                      ) : (
                        <button onClick={() => marcarRealizado(item.Codigo)} style={{ padding: '8px 15px', backgroundColor: THEME.success, color: 'white', border: 'none', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer' }}>✓ Realizado</button>
                      )}
                    </div>
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