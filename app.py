import streamlit as st  # Importa Streamlit para la interfaz web
from datetime import datetime  # Importa la gestión de fechas y horas
from zoneinfo import ZoneInfo  # Zona horaria nativa de Python (sin librerías extra)
from supabase import create_client, Client  # Importa la librería para conectar con Supabase
import pandas as pd  # Importa Pandas para manejar tablas
import io  # Importa io para manejar archivos en memoria

# --- ZONA HORARIA LOCAL (COCHABAMBA / BOLIVIA) ---
ZONA_BOLIVIA = ZoneInfo("America/La_Paz")

def ahora_bolivia():
    return datetime.now(ZONA_BOLIVIA)

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

# --- 3. SEGURIDAD DINÁMICA CON USUARIOS DE SUPABASE ---
def verificar_acceso():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
        st.session_state["usuario_actual"] = ""

    if not st.session_state["autenticado"]:
        st.title("🔐 Sistema de Control de Pagos")
        st.write("Por favor ingresa tus datos de acceso:")
        
        with st.form("form_login"):
            usuario_input = st.text_input("Usuario").strip().lower()
            password_input = st.text_input("Contraseña", type="password")
            btn_entrar = st.form_submit_button("Entrar al Sistema")
            
            if btn_entrar:
                if not usuario_input or not password_input:
                    st.warning("⚠️ Ingresa usuario y contraseña.")
                else:
                    try:
                        resp = supabase.table("usuarios").select("*").eq("nombre_usuario", usuario_input).eq("password", password_input).execute()
                        if resp.data:
                            st.session_state["autenticado"] = True
                            st.session_state["usuario_actual"] = usuario_input.upper()
                            st.rerun()
                        else:
                            st.error("Usuario o contraseña incorrectos.")
                    except Exception:
                        if usuario_input == "monica" and password_input == "12345":
                            st.session_state["autenticado"] = True
                            st.session_state["usuario_actual"] = "MONICA"
                            st.rerun()
                        else:
                            st.error("Usuario o contraseña incorrectos.")
        return False
    return True

if not verificar_acceso():
    st.stop()

# --- FUNCIONES PARA CARGAR DATOS DINÁMICAMENTE DESDE SUPABASE ---
def obtener_medicos():
    try:
        resp = supabase.table("medicos").select("nombre").execute()
        if resp.data:
            lista = [m["nombre"] for m in resp.data]
            return ["Selecciona un médico o servicio..."] + sorted(lista)
    except Exception:
        pass
    return [
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

def obtener_personal():
    try:
        resp = supabase.table("personal").select("nombre").execute()
        if resp.data:
            return sorted([p["nombre"] for p in resp.data])
    except Exception:
        pass
    return ["MONICA", "JANET", "PATRICIA", "KARLA", "ADRIANA", "ZULEMA"]

lista_medicos = obtener_medicos()
personal_opciones = obtener_personal()

# --- 4. APLICACIÓN PRINCIPAL ---
fecha_hora_actual = ahora_bolivia()
fecha_hoy_date = fecha_hora_actual.date()
fecha_hoy_str = str(fecha_hoy_date)

st.title("💰 Control Diario de Pagos")
st.write(f"Sesión activa: **{st.session_state['usuario_actual']}** | Fecha local: **{fecha_hora_actual.strftime('%d/%m/%Y %H:%M')}**")

# --- TURNO AUTOMÁTICO SEGÚN LA HORA LOCAL DE BOLIVIA ---
tiempo_en_minutos = fecha_hora_actual.hour * 60 + fecha_hora_actual.minute
indice_turno_default = 1 if tiempo_en_minutos >= 1010 else 0

turno_actual = st.radio(
    "🕒 Turno Actual (Calculado Automáticamente por el Reloj)",
    ["Turno Mañana", "Turno Tarde"],
    index=indice_turno_default,
    horizontal=True
)

st.divider()

# Cuatro pestañas ordenadas
pestana_registro, pestana_cambios, pestana_cierre, pestana_config = st.tabs([
    "📝 Registrar Nuevo Pago", 
    "🔄 Cambios QR-Tarjetas", 
    "📊 Ver Cierre de Caja y Reportes",
    "⚙️ Configuración"
])

with pestana_registro:
    st.subheader(f"Nuevo registro para: **{turno_actual}**")
    
    with st.form("form_registro", clear_on_submit=True):
        medico = st.selectbox("1. Médico Tratante / Servicio", lista_medicos)
        paciente = st.text_input("2. Nombre del Paciente (Copiado de Odoo)")
        quien_cancela = st.text_input("3. Nombre de quien cancela")
        tipo_pago = st.selectbox("4. Forma de Pago", ["EFECTIVO", "QR", "TARJETA"])
        
        opciones_entrega = personal_opciones if "MONI" in personal_opciones else ["MONI"] + [p for p in personal_opciones if p != "MONICA"]
        pagado_a = st.selectbox("5. ¿A quién se le entregó el dinero?", opciones_entrega)
        
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
                    ahora_reg = ahora_bolivia()
                    turno_automatico = "Turno Tarde" if ahora_reg.hour >= 17 else "Turno Mañana"

                    datos_a_guardar = {
                        "fecha": str(ahora_reg.date()),
                        "turno": turno_automatico,
                        "medico": medico,
                        "paciente": paciente,
                        "quien_cancela": quien_cancela,
                        "tipo_pago": tipo_pago,
                        "pagado": pagado_a,
                        "monto": float(monto)
                    }
                    supabase.table("pagos").insert(datos_a_guardar).execute()
                    st.success(f"✅ ¡Pago guardado con éxito! ({turno_automatico} - {monto} Bs)")
                except Exception as e:
                    st.error(f"Hubo un error al guardar en la base de datos: {e}")

with pestana_cambios:
    st.subheader(f"🔄 Registro de Cambios QR / Tarjetas ({turno_actual})")
    st.write("Registra aquí los intercambios o transferencias cruzadas de dinero.")
    
    with st.form("form_cambios", clear_on_submit=True):
        fecha_cambio = st.date_input("Fecha del Cambio", value=fecha_hoy_date)
        tipo_cambio = st.selectbox("1. Tipo de Cambio", ["QR", "TARJETA"])
        descripcion = st.text_input("2. Descripción / Motivo (Opcional)", placeholder="Ej. Cambio de sencillo, devolución, etc.")
        
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
                    ahora_camb = ahora_bolivia()
                    turno_automatico_cambio = "Turno Tarde" if ahora_camb.hour >= 17 else "Turno Mañana"

                    datos_cambio = {
                        "fecha": str(fecha_cambio),
                        "turno": turno_automatico_cambio,
                        "tipo_cambio": tipo_cambio,
                        "descripcion": descripcion if descripcion else "Sin descripción",
                        "origen": origen,
                        "destino": destino,
                        "monto": float(monto_cambio)
                    }
                    supabase.table("cambios").insert(datos_cambio).execute()
                    st.success(f"✅ ¡Cambio registrado con éxito! ({fecha_cambio} | {turno_automatico_cambio} - {monto_cambio} Bs)")
                except Exception as e:
                    st.error(f"Hubo un error al guardar el cambio: {e}")
                    
    st.divider()
    st.subheader("📋 Validar cambios registrados por fecha")
    
    col_val1, col_val2 = st.columns(2)
    with col_val1:
        fecha_validar_cambios = st.date_input("Selecciona la fecha a validar", value=fecha_hoy_date, key="fecha_val_cambios")
    with col_val2:
        filtro_turno_cambios = st.selectbox("Turno a validar", ["TODOS", "Turno Mañana", "Turno Tarde"], key="turno_val_cambios")
        
    try:
        query_cambios = supabase.table("cambios").select("*").eq("fecha", str(fecha_validar_cambios))
        if filtro_turno_cambios != "TODOS":
            query_cambios = query_cambios.eq("turno", filtro_turno_cambios)
        resp_cambios = query_cambios.execute()
        
        if resp_cambios.data:
            df_cambios = pd.DataFrame(resp_cambios.data)
            total_cambios = df_cambios["monto"].sum() if "monto" in df_cambios.columns else 0
            st.metric(label="🔄 Total Cambios en Fecha/Turno Seleccionado", value=f"{total_cambios:.2f} Bs")
            st.dataframe(df_cambios, use_container_width=True)
        else:
            st.info("No hay cambios QR/Tarjetas registrados para la fecha y turno seleccionados.")
    except Exception:
        st.info("Configura la tabla 'cambios' en Supabase para ver el historial.")

with pestana_cierre:
    st.subheader("📊 Resumen para Cierre de Caja y Filtros")
    
    fecha_consulta = st.date_input("Selecciona la fecha a revisar", fecha_hoy_date)
    
    try:
        respuesta = supabase.table("pagos").select("*").eq("fecha", str(fecha_consulta)).execute()
        registros = respuesta.data
        
        if registros:
            df = pd.DataFrame(registros)
            
            st.divider()
            st.write("🔍 **Filtros de Búsqueda Rápida:**")
            
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filtro_turno = st.selectbox("Filtrar por Turno", ["TODOS", "Turno Mañana", "Turno Tarde"])
            with col_f2:
                medicos_disponibles = ["TODOS"] + sorted(list(df["medico"].unique()))
                filtro_medico = st.selectbox("Filtrar por Médico", medicos_disponibles)
            with col_f3:
                filtro_pago = st.selectbox("Filtrar por Tipo de Pago", ["TODOS", "EFECTIVO", "QR", "TARJETA"])
            
            df_filtrado = df.copy()
            if filtro_turno != "TODOS":
                df_filtrado = df_filtrado[df_filtrado["turno"] == filtro_turno]
            if filtro_medico != "TODOS":
                df_filtrado = df_filtrado[df_filtrado["medico"] == filtro_medico]
            if filtro_pago != "TODOS":
                df_filtrado = df_filtrado[df_filtrado["tipo_pago"] == filtro_pago]
            
            st.divider()
            
            total_efectivo = df_filtrado[df_filtrado["tipo_pago"] == "EFECTIVO"]["monto"].sum() if not df_filtrado.empty else 0
            total_qr = df_filtrado[df_filtrado["tipo_pago"] == "QR"]["monto"].sum() if not df_filtrado.empty else 0
            total_tarjeta = df_filtrado[df_filtrado["tipo_pago"] == "TARJETA"]["monto"].sum() if not df_filtrado.empty else 0
            
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
            
            st.divider()
            with st.expander("⚙️ ¿Necesitas corregir paciente, médico, monto, tipo de pago o eliminar un registro?"):
                st.write("Selecciona el paciente y monto correspondiente:")
                
                if not df_filtrado.empty:
                    opciones_pacientes = []
                    mapeo_ids = {}
                    
                    for _, row in df_filtrado.iterrows():
                        etiqueta = f"{row['paciente']} — {row['monto']} Bs ({row['tipo_pago']} - Méd.: {row['medico']})"
                        opciones_pacientes.append(etiqueta)
                        mapeo_ids[etiqueta] = row['id']
                        
                    seleccion_usuario = st.selectbox("Busca y selecciona el pago a modificar:", opciones_pacientes)
                    id_a_gestionar = mapeo_ids[seleccion_usuario]
                    
                    reg_actual = df[df["id"] == id_a_gestionar].iloc[0]
                    
                    col_edit, col_del = st.columns(2)
                    
                    with col_edit:
                        with st.form(f"form_editar_{id_a_gestionar}"):
                            st.write("✏️ **Modificar Datos del Pago**")
                            
                            nuevo_paciente = st.text_input("Nombre del Paciente", value=str(reg_actual['paciente']))
                            
                            medico_actual = reg_actual['medico']
                            indice_medico = lista_medicos.index(medico_actual) if medico_actual in lista_medicos else 0
                            nuevo_medico = st.selectbox("Médico Tratante / Servicio", lista_medicos, index=indice_medico)
                            
                            nuevo_monto = st.number_input("Monto (Bs.)", value=float(reg_actual['monto']), step=10.0, format="%.2f")
                            
                            opciones_tipo = ["EFECTIVO", "QR", "TARJETA"]
                            indice_tipo = opciones_tipo.index(reg_actual['tipo_pago']) if reg_actual['tipo_pago'] in opciones_tipo else 0
                            nuevo_tipo = st.selectbox("Tipo de Pago", opciones_tipo, index=indice_tipo)
                            
                            btn_actualizar = st.form_submit_button("🔄 Actualizar Datos")
                            
                            if btn_actualizar:
                                if nuevo_medico == "Selecciona un médico o servicio...":
                                    st.warning("⚠️ Selecciona un médico válido.")
                                elif not nuevo_paciente:
                                    st.warning("⚠️ El nombre del paciente no puede estar vacío.")
                                else:
                                    try:
                                        supabase.table("pagos").update({
                                            "paciente": nuevo_paciente,
                                            "medico": nuevo_medico,
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

            st.divider()
            
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
            
    except Exception:
        st.info("Registra algunos pagos para habilitar los reportes y filtros.")

with pestana_config:
    st.subheader("⚙️ Configuración y Gestión General")
    st.write("Administra los usuarios de acceso, los médicos y el personal.")
    
    st.write("🔑 **Gestión de Usuarios de Acceso**")
    col_u1, col_u2 = st.columns(2)
    
    with col_u1:
        with st.form("form_nuevo_usuario", clear_on_submit=True):
            st.write("➕ **Crear Nuevo Usuario**")
            nuevo_user = st.text_input("Nombre de Usuario (Ej: janet)").strip().lower()
            nuevo_pass = st.text_input("Contraseña", type="password")
            btn_add_user = st.form_submit_button("Crear Acceso")
            
            if btn_add_user:
                if not nuevo_user or not nuevo_pass:
                    st.warning("⚠️ Llena ambos campos.")
                else:
                    try:
                        supabase.table("usuarios").insert({"nombre_usuario": nuevo_user, "password": nuevo_pass}).execute()
                        st.success(f"✅ ¡Usuario '{nuevo_user}' creado con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                        
    with col_u2:
        try:
            resp_users = supabase.table("usuarios").select("nombre_usuario").execute()
            lista_usuarios_db = [u["nombre_usuario"] for u in resp_users.data] if resp_users.data else ["monica"]
        except Exception:
            lista_usuarios_db = ["monica"]
            
        with st.form("form_del_usuario"):
            st.write("❌ **Eliminar Acceso de Usuario**")
            user_a_borrar = st.selectbox("Selecciona usuario a revocar", lista_usuarios_db)
            btn_del_user = st.form_submit_button("Revocar Acceso")
            
            if btn_del_user:
                if user_a_borrar == "monica":
                    st.warning("⚠️ No puedes eliminar al usuario principal 'monica'.")
                else:
                    try:
                        supabase.table("usuarios").delete().eq("nombre_usuario", user_a_borrar).execute()
                        st.success(f"🗑️ ¡Acceso revocado para '{user_a_borrar}'!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    st.divider()
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.write("👨‍⚕️ **Médicos y Servicios**")
        with st.form("form_nuevo_medico", clear_on_submit=True):
            nuevo_medico_input = st.text_input("Agregar Nuevo Médico")
            btn_add_medico = st.form_submit_button("➕ Registrar Médico")
            
            if btn_add_medico:
                if not nuevo_medico_input:
                    st.warning("⚠️ Ingresa un nombre válido.")
                else:
                    try:
                        supabase.table("medicos").insert({"nombre": nuevo_medico_input.strip().upper()}).execute()
                        st.success("✅ ¡Médico agregado con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                        
    with col_c2:
        st.write("👩‍💼 **Gestión de Compañeras (Personal)**")
        
        with st.form("form_nueva_companera", clear_on_submit=True):
            nueva_comp_input = st.text_input("Agregar Nueva Compañera")
            btn_add_comp = st.form_submit_button("➕ Registrar Compañera")
            
            if btn_add_comp:
                if not nueva_comp_input:
                    st.warning("⚠️ Ingresa un nombre válido.")
                else:
                    try:
                        supabase.table("personal").insert({"nombre": nueva_comp_input.strip().upper()}).execute()
                        st.success("✅ ¡Compañera agregada con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        with st.form("form_eliminar_companera"):
            st.write("❌ **Dar de baja compañera**")
            comp_a_borrar = st.selectbox("Selecciona a quién eliminar", personal_opciones)
            btn_del_comp = st.form_submit_button("🗑️ Eliminar Compañera")
            
            if btn_del_comp:
                if len(personal_opciones) <= 1:
                    st.warning("⚠️ No puedes eliminar a todos los miembros.")
                else:
                    try:
                        supabase.table("personal").delete().eq("nombre", comp_a_borrar).execute()
                        st.success(f"🗑️ ¡Compañera {comp_a_borrar} eliminada con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al eliminar: {e}")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state["autenticado"] = False
    st.session_state["usuario_actual"] = ""
    st.rerun()
