import streamlit as st  # Importa Streamlit para la interfaz web
from datetime import datetime  # Importa la gestión de fechas del sistema
from supabase import create_client, Client  # Importa la librería para conectar con Supabase
import pandas as pd  # Importa Pandas para manejar tablas
import io  # Importa io para manejar archivos en memoria

# --- 1. CONEXIÓN A SUPABASE ---
SUPABASE_URL = "https://xfxmmcaxqheedltfhgbv.supabase.co"  # Tu URL correcta de Supabase
SUPABASE_KEY = "sb_publishable_BonlVDcM9GJX_v5FtNEJYg_u_2VrPv0"  # Tu llave pública de Supabase

@st.cache_resource  # Guarda la conexión en memoria caché para que la app sea rápida
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()  # Inicializa el cliente de la base de datos

# --- 2. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Control de Pagos - Mónica",  # Título en la pestaña del navegador
    page_icon="💰",  # Ícono de la pestaña
    layout="centered"  # Centra el diseño en la pantalla
)

# Estilo visual personalizado para los botones (grandes y verdes)
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #2e7d32;
        color: white;
        font-size: 18px;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px;
    }
    .stButton>button:hover {
        background-color: #1b5e20;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SEGURIDAD SENCILLA (Contraseña para Mónica) ---
def verificar_acceso():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False  # Estado inicial de sesión cerrada

    if not st.session_state["autenticado"]:
        st.title("🔐 Sistema de Control de Pagos")
        st.write("Hola Mónica, por favor ingresa tu contraseña para comenzar:")
        
        st.text_input("Usuario", value="monica", disabled=True)  # Usuario fijo
        password = st.text_input("Contraseña", type="password")  # Campo seguro de contraseña
        
        if st.button("Entrar al Sistema"):
            if password == "12345":  # Contraseña de acceso
                st.session_state["autenticado"] = True
                st.rerun()  # Recarga la app al ingresar bien
            else:
                st.error("Contraseña incorrecta. Inténtalo de nuevo.")
        return False
    return True

if not verificar_acceso():
    st.stop()  # Detiene la ejecución si no ha puesto la contraseña

# --- 4. APLICACIÓN PRINCIPAL ---
st.title("💰 Control Diario de Pagos")
st.write("Registra tus cobros rápido y sin enredos para que el cierre de caja salga perfecto.")

# Selector horizontal de turnos para evitar confusiones
turno_actual = st.radio(
    "🕒 ¿En qué turno estás ahora?",
    ["Turno Mañana", "Turno Tarde"],
    horizontal=True
)

st.divider()

# Tres pestañas ordenadas: Registro, Cambios de QR/Tarjetas, y Cierre/Reportes
pestana_registro, pestana_cambios, pestana_cierre = st.tabs([
    "📝 Registrar Nuevo Pago", 
    "🔄 Cambios QR-Tarjetas", 
    "📊 Ver Cierre de Caja y Reportes"
])

with pestana_registro:
    st.subheader(f"Nuevo registro para: **{turno_actual}**")
    
    with st.form("form_registro", clear_on_submit=True):
        # Lista oficial exacta de médicos y servicios
        lista_medicos = [
            "Selecciona un médico o servicio...",
            "DR DANIEL COSCIO", "DR RAUL COSCIO", "DR GASTON CORNEJO", "DR SERGIO APARICIO",
            "DRA INES RAMIREZ", "DRA CARLA SAAVEDRA", "DR CRISTIAN ATUE", "DRA ANNELIS CAZON",
            "DR WILDER INTURIAS", "DR MARCELO TORRICO", "DR JUAN CARLOS GIL", "DRA CORAL RUIZ",
            "DRA ROSARIO CASTRO", "DR OMAR ANGULO", "DR HUMBERTO GARCIA", "DRA ALEXANDRA ROMAN",
            "DR ELIGIO ARCIENEGA", "DR CARLOS BROCKMAN", "DR DANIEL MENDIETA", "DR ALEJANDRO TORRICO",
            "DRA MARIA LOURDES CORNEJO", "DRA KARINA CARTAGENA", "DA ANA CLAROS", "LIC ELBA GAMBOA",
            "DR DIEGO ANTEZANA", "LIC SOFIA REYNOSO", "DR ERICK SALAS", "DR GEOFRI VELASQUEZ",
            "DR JAVIER ENCINAS", "DRA PATRICIA PEÑA", "DR COCA", "DR RONALD APARICIO",
            "DRA CARMEN ARAUCO", "DR MARIO SAAVEDRA", "DR RODRIGO PINTO", "DR FRANZ SANJINEZ",
            "DR PABLO CESPEDES", "DR JHONNY RIOS", "DRA ANA FLORES", "DR RAMIRO ROJAS",
            "DR MARIO URQUIDI", "LIC ROXANA ALBA", "DR REMY URIONA", "DR JIMMY ACEVEDO",
            "ENFERMERIA", "ECOGRAFIA", "RX", "TOMOGRAFIA", "PAP", "HISTOPATOLOGIA",
            "ELECTROCARDIOGRAMA", "ECOCARDIOGRAMA", "UROFLUJOMETRIA", "EXPENSAS", "LABORATORIO"
        ]
        
        medico = st.selectbox("1. Médico Tratante / Servicio", lista_medicos)
        paciente = st.text_input("2. Nombre del Paciente (Copiado de Odoo)")
        quien_cancela = st.text_input("3. Nombre de quien cancela")
        tipo_pago = st.selectbox("4. Forma de Pago", ["EFECTIVO", "QR", "TARJETA"])
        
        # MONI colocada arriba por defecto en la opción 5
        pagado_a = st.selectbox("5. ¿A quién se le entregó el dinero?", ["MONI", "JANET", "PATI"])
        
        monto = st.number_input("6. Monto Pagado (Bs.)", min_value=0.0, step=10.0, format="%.2f")
        
        enviar = st.form_submit_button("💾 Guardar Este Pago")
        
        if enviar:
            if medico == "Selecciona un médico o servicio...":
                st.warning("⚠️ Por favor selecciona un médico o servicio de la lista.")
            elif not paciente or not quien_cancela:
                st.warning("⚠️ Por favor completa el nombre del paciente y de quién cancela.")
            elif monto <= 0:
                st.warning("⚠️ El monto debe ser mayor a 0.")
            else:
                try:
                    datos_a_guardar = {
                        "fecha": str(datetime.now().date()),
                        "turno": turno_actual,
                        "medico": medico,
                        "paciente": paciente,
                        "quien_cancela": quien_cancela,
                        "tipo_pago": tipo_pago,
                        "pagado": pagado_a,
                        "monto": float(monto)
                    }
                    supabase.table("pagos").insert(datos_a_guardar).execute()
                    st.success(f"✅ ¡Pago guardado con éxito! ({turno_actual} - {monto} Bs)")
                except Exception as e:
                    st.error(f"Hubo un error al guardar en la base de datos: {e}")

with pestana_cambios:
    st.subheader(f"🔄 Registro de Cambios QR / Tarjetas ({turno_actual})")
    st.write("Registra aquí los intercambios o transferencias cruzadas de dinero.")
    
    with st.form("form_cambios", clear_on_submit=True):
        tipo_cambio = st.selectbox("1. Tipo de Cambio", ["QR", "TARJETA"])
        descripcion = st.text_input("2. Descripción / Motivo (Opcional)", placeholder="Ej. Cambio de sencillo, devolución, etc.")
        
        personal_opciones = ["MONICA", "JANET", "PATRICIA", "CARLA", "ADRIANA", "ZULEMA"]
        
        col_orig, col_dest = st.columns(2)
        with col_orig:
            origen = st.selectbox("3. Origen (Quién entrega)", personal_opciones)
        with col_dest:
            destino = st.selectbox("4. Destino (Quién recibe)", personal_opciones)
            
        monto_cambio = st.number_input("5. Monto del Cambio (Bs.)", min_value=0.0, step=10.0, format="%.2f")
        
        guardar_cambio = st.form_submit_button("💾 Guardar Cambio QR / Tarjeta")
        
        if guardar_cambio:
            if origen == destino:
                st.warning("⚠️ El origen y el destino no pueden ser la misma persona.")
            elif monto_cambio <= 0:
                st.warning("⚠️ El monto debe ser mayor a 0.")
            else:
                try:
                    datos_cambio = {
                        "fecha": str(datetime.now().date()),
                        "turno": turno_actual,
                        "tipo_cambio": tipo_cambio,
                        "descripcion": descripcion if descripcion else "Sin descripción",
                        "origen": origen,
                        "destino": destino,
                        "monto": float(monto_cambio)
                    }
                    supabase.table("cambios").insert(datos_cambio).execute()
                    st.success(f"✅ ¡Cambio registrado con éxito! ({tipo_cambio} - {monto_cambio} Bs)")
                except Exception as e:
                    st.error(f"Hubo un error al guardar el cambio: {e}")
                    
    st.divider()
    st.subheader("📋 Cambios registrados hoy")
    try:
        resp_cambios = supabase.table("cambios").select("*").eq("fecha", str(datetime.now().date())).eq("turno", turno_actual).execute()
        if resp_cambios.data:
            st.dataframe(resp_cambios.data, use_container_width=True)
        else:
            st.info("No hay cambios QR/Tarjetas registrados en este turno hoy.")
    except:
        st.info("Configura la tabla 'cambios' en Supabase para ver el historial.")

with pestana_cierre:
    st.subheader("📊 Resumen para Cierre de Caja y Filtros")
    
    # Selector de fecha para auditar
    fecha_consulta = st.date_input("Selecciona la fecha a revisar", datetime.today())
    
    try:
        # Traemos todos los registros del día seleccionado
        respuesta = supabase.table("pagos").select("*").eq("fecha", str(fecha_consulta)).execute()
        registros = respuesta.data
        
        if registros:
            df = pd.DataFrame(registros) # Convertimos los datos a una tabla inteligente de Pandas
            
            st.divider()
            st.write("🔍 **Filtros de Búsqueda Rápida:**")
            
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filtro_turno = st.selectbox("Filtrar por Turno", ["TODOS", "Turno Mañana", "Turno Tarde"])
            with col_f2:
                # Lista única de médicos presentes en los registros del día
                medicos_disponibles = ["TODOS"] + list(df["medico"].unique())
                filtro_medico = st.selectbox("Filtrar por Médico", medicos_disponibles)
            with col_f3:
                filtro_pago = st.selectbox("Filtrar por Tipo de Pago", ["TODOS", "EFECTIVO", "QR", "TARJETA"])
            
            # Aplicar los filtros seleccionados a la tabla
            df_filtrado = df.copy()
            if filtro_turno != "TODOS":
                df_filtrado = df_filtrado[df_filtrado["turno"] == filtro_turno]
            if filtro_medico != "TODOS":
                df_filtrado = df_filtrado[df_filtrado["medico"] == filtro_medico]
            if filtro_pago != "TODOS":
                df_filtrado = df_filtrado[df_filtrado["tipo_pago"] == filtro_pago]
            
            st.divider()
            
            # Calcular totales basados en lo que está filtrado en pantalla
            total_efectivo = df_filtrado[df_filtrado["tipo_pago"] == "EFECTIVO"]["monto"].sum() if not df_filtrado.empty else 0
            total_qr = df_filtrado[df_filtrado["tipo_pago"] == "QR"]["monto"].sum() if not df_filtrado.empty else 0
            total_tarjeta = df_filtrado[df_filtrado["tipo_pago"] == "TARJETA"]["monto"].sum() if not df_filtrado.empty else 0
            
            # Tarjetas métricas con totales
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric(label="💵 Efectivo Filtrado", value=f"{total_efectivo:.2f} Bs")
            with m2:
                st.metric(label="📱 QR Filtrado", value=f"{total_qr:.2f} Bs")
            with m3:
                st.metric(label="💳 Tarjeta Filtrado", value=f"{total_tarjeta:.2f} Bs")
                
            st.write("")
            st.write(f"📋 **Resultados ({len(df_filtrado)} registros encontrados):**")
            st.dataframe(df_filtrado, use_container_width=True)
            
            # --- SECCIÓN: MODIFICAR O ELIMINAR REGISTROS ---
            st.divider()
            with st.expander("⚙️ ¿Necesitas corregir el monto, cambiar tipo de pago o eliminar un registro?"):
                st.write("Selecciona el paciente y monto correspondiente:")
                
                if not df_filtrado.empty:
                    opciones_pacientes = []
                    mapeo_ids = {}
                    
                    for _, row in df_filtrado.iterrows():
                        etiqueta = f"{row['paciente']} — {row['monto']} Bs ({row['tipo_pago']} - Méd.: {row['medico']})"
                        opciones_pacientes.append(etiqueta)
                        mapeo_ids[etiqueta] = row['id']
                        
                    seleccion_usuario = st.selectbox("Busca y selecciona el pago:", opciones_pacientes)
                    id_a_gestionar = mapeo_ids[seleccion_usuario]
                    
                    reg_actual = df[df["id"] == id_a_gestionar].iloc[0]
                    
                    col_edit, col_del = st.columns(2)
                    
                    with col_edit:
                        with st.form(f"form_editar_{id_a_gestionar}"):
                            st.write("✏️ **Modificar Monto / Tipo**")
                            nuevo_monto = st.number_input("Nuevo Monto (Bs.)", value=float(reg_actual['monto']), step=10.0, format="%.2f")
                            
                            opciones_tipo = ["EFECTIVO", "QR", "TARJETA"]
                            indice_actual = opciones_tipo.index(reg_actual['tipo_pago']) if reg_actual['tipo_pago'] in opciones_tipo else 0
                            nuevo_tipo = st.selectbox("Nuevo Tipo de Pago", opciones_tipo, index=indice_actual)
                            
                            btn_actualizar = st.form_submit_button("🔄 Actualizar Datos")
                            
                            if btn_actualizar:
                                try:
                                    supabase.table("pagos").update({
                                        "monto": float(nuevo_monto),
                                        "tipo_pago": nuevo_tipo
                                    }).eq("id", int(id_a_gestionar)).execute()
                                    st.success("✅ ¡Registro actualizado con éxito!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al actualizar: {e}")
                                    
                    with col_del:
                        with st.form(f"form_eliminar_{id_a_gestionar}"):
                            st.write("🗑️ **Eliminar Registro**")
                            st.warning("⚠️ Borrará este pago por completo.")
                            
                            confirmar_eliminar = st.checkbox("Confirmo la eliminación")
                            btn_eliminar = st.form_submit_button("❌ Eliminar Permanentemente")
                            
                            if btn_eliminar:
                                if confirmar_eliminar:
                                    try:
                                        supabase.table("pagos").delete().eq("id", int(id_a_gestionar)).execute()
                                        st.success("🗑️ ¡Registro eliminado con éxito!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error al eliminar: {e}")
                                else:
                                    st.warning("⚠️ Marca la casilla para confirmar.")
                else:
                    st.warning("No hay registros disponibles para modificar con los filtros actuales.")

            # --- BOTÓN DE EXPORTAR A EXCEL REAL (.XLSX) ---
            st.divider()
            
            # Generar archivo Excel en memoria usando openpyxl
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filtrado.to_excel(writer, index=False, sheet_name='Cierre de Caja')
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Descargar Reporte en Excel Real (.xlsx)",
                data=excel_data,
                file_name=f"cierre_caja_{fecha_consulta}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.info("No hay registros guardados para la fecha seleccionada.")
            
    except Exception as e:
        st.info("Registra algunos pagos para habilitar los reportes y filtros.")

# Botón lateral para salir
if st.sidebar.button("Cerrar Sesión"):
    st.session_state["autenticado"] = False
    st.rerun()
