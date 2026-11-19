import streamlit as st  # Importa Streamlit para la interfaz web
from datetime import datetime  # Importa la gestión de fechas del sistema
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

# Lista oficial exacta de médicos y servicios (reutilizable)
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
                        "fecha": str(ahora_bolivia().date()),
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
        
        personal_opciones = ["MONICA", "JANET", "PATRICIA", "KARLA", "ADRIANA", "ZULEMA"]
        
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
                        "fecha": str(ahora_bolivia().date()),
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
        resp_cambios = supabase.table("cambios").select("*").eq("fecha", str(ahora_bolivia().date())).eq("turno", turno_actual).execute()
        if resp_cambios.data:
            st.dataframe(resp_cambios.data, use_container_width=True)
        else:
            st.info("No hay cambios QR/Tarjetas registrados en este turno hoy.")
    except:
        st.info("Configura la tabla 'cambios' en Supabase para ver el historial.")

with pestana_cierre:
    st.subheader("📊 Resumen para Cierre de Caja y Filtros")
    
    # Selector de fecha para auditar (usando fecha local de Bolivia)
    fecha_consulta = st.date_input("Selecciona la fecha a revisar", ahora_bolivia().date())
    
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
            if filtro_
