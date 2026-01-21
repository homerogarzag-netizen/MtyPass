import streamlit as st
from supabase import create_client, Client
import urllib.parse

# Configuración inicial de la página (Layout móvil por defecto)
st.set_page_config(
    page_title="MtyPass | Marketplace",
    page_icon="🎟️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- INYECCIÓN DE CSS PERSONALIZADO (DARK MODE) ---
def local_css():
    st.markdown(
        """
        <style>
        .stApp { background-color: #121212; color: #FFFFFF; }
        
        /* Estilo de los Botones Principales */
        div.stButton > button:first-child {
            background-color: #FF4B2B; color: white; border-radius: 12px;
            border: none; height: 3.5rem; width: 100%; font-size: 1.1rem;
            font-weight: bold; margin-top: 10px;
        }

        /* Tarjetas de Eventos */
        .event-card {
            background-color: #1E1E1E; padding: 1.5rem; border-radius: 15px;
            border: 1px solid #333; margin-bottom: 5px;
        }
        
        .price-tag { color: #FF4B2B; font-size: 1.4rem; font-weight: bold; }

        /* Estilo del botón de WhatsApp */
        .whatsapp-btn {
            background-color: #25D366; color: white !important; padding: 12px;
            text-decoration: none; border-radius: 12px; display: block;
            text-align: center; font-weight: bold; margin-top: 10px;
            font-size: 1rem; transition: 0.3s;
        }
        .whatsapp-btn:hover { background-color: #128C7E; transform: scale(1.02); }

        /* Inputs */
        .stTextInput input, .stSelectbox div, .stNumberInput input {
            background-color: #1E1E1E !important; color: white !important;
            border-radius: 10px !important;
        }
        
        h1, h2, h3 { color: #FF4B2B; font-family: 'Inter', sans-serif; }
        </style>
        """,
        unsafe_allow_html=True
    )

local_css()

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error de conexión con Supabase: {e}")
        return None

supabase = init_connection()

# --- MANEJO DE SESIÓN ---
if 'user' not in st.session_state:
    st.session_state.user = None

def login_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        st.success("¡Bienvenido de vuelta, compadre!")
        st.rerun()
    except Exception as e:
        st.error(f"Error al entrar: {e}")

def register_user(email, password):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        st.info("¡Registro enviado! Si desactivaste 'Confirm Email' en Supabase, ya puedes iniciar sesión.")
    except Exception as e:
        st.error(f"Error al registrar: {e}")

# --- FUNCIONES DE DB ---
def obtener_boletos(filtro_recinto="Todos"):
    query = supabase.table("boletos").select("*").eq("estado", "disponible").order("created_at", desc=True)
    if filtro_recinto != "Todos":
        query = query.eq("recinto", filtro_recinto)
    return query.execute().data

def guardar_boleto(evento, recinto, precio, zona, whatsapp):
    data = {
        "evento": evento,
        "recinto": recinto,
        "precio": precio,
        "zona": zona,
        "whatsapp": whatsapp,
        "vendedor_email": st.session_state.user.email,
        "estado": "disponible"
    }
    return supabase.table("boletos").insert(data).execute()

# --- INTERFAZ PRINCIPAL ---
def main():
    st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>🎟️ MtyPass</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Mercado secundario de la Sultana del Norte</p>", unsafe_allow_html=True)

    # Sidebar: Gestión de Usuario
    with st.sidebar:
        if st.session_state.user:
            st.markdown(f"### 🤠 Perfil Regio")
            st.write(f"Email: {st.session_state.user.email}")
            if st.button("Cerrar Sesión"):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.rerun()
        else:
            st.markdown("### Acceso")
            email = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password")
            col1, col2 = st.columns(2)
            if col1.button("Entrar"):
                login_user(email, password)
            if col2.button("Registrar"):
                register_user(email, password)

    menu = ["Explorar", "Vender", "Mis Ventas"]
    choice = st.tabs(menu)

    # --- PESTAÑA: EXPLORAR ---
    with choice[0]:
        recinto_filtro = st.selectbox("¿A dónde quieres ir?", 
                             ["Todos", "Arena Monterrey", "Auditorio Citibanamex", "Estadio BBVA", "Estadio Universitario", "Foro Tims"])
        
        boletos_lista = obtener_boletos(recinto_filtro)

        if not boletos_lista:
            st.info("No hay boletos disponibles por ahora. ¡Sé el primero en vender!")
        else:
            for boleto in boletos_lista:
                with st.container():
                    st.markdown(f"""
                    <div class="event-card">
                        <p style='color: #FF4B2B; font-weight: bold; margin-bottom: 5px;'>{boleto['recinto']}</p>
                        <h3 style='margin: 0; color: white;'>{boleto['evento']}</h3>
                        <p style='color: #BBB; margin-bottom: 10px;'>Zona: {boleto['zona']}</p>
                        <p class="price-tag">${boleto['precio']:,} MXN</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Generar Link de WhatsApp
                    msg = urllib.parse.quote(f"¡Qué onda! Me interesa tu boleto para {boleto['evento']} en {boleto['recinto']} que vi en MtyPass.")
                    wa_link = f"https://wa.me/{boleto['whatsapp']}?text={msg}"
                    
                    st.markdown(f'<a href="{wa_link}" target="_blank" class="whatsapp-btn">📱 Contactar por WhatsApp</a>', unsafe_allow_html=True)
                    st.write("") # Espaciador

    # --- PESTAÑA: VENDER ---
    with choice[1]:
        if not st.session_state.user:
            st.warning("🔒 Inicia sesión en la barra lateral para publicar tus boletos.")
        else:
            st.subheader("Publica tu boleto")
            with st.form("vender_form", clear_on_submit=True):
                evento = st.text_input("Artista / Evento", placeholder="Ej: Luis Miguel")
                recinto_vta = st.selectbox("Recinto", ["Arena Monterrey", "Auditorio Citibanamex", "Estadio BBVA", "Estadio Universitario", "Foro Tims"])
                precio = st.number_input("Precio ($MXN)", min_value=100, step=100)
                zona = st.text_input("Zona / Sección", placeholder="Ej: VIP, Cancha A")
                whatsapp = st.text_input("Tu WhatsApp (Ej: 528188889999)", help="Incluye el 52 (código de país)")
                
                if st.form_submit_button("Publicar Boleto"):
                    if evento and zona and whatsapp:
                        try:
                            guardar_boleto(evento, recinto_vta, precio, zona, whatsapp)
                            st.balloons()
                            st.success("¡Ya quedó! Tu boleto está en línea.")
                        except Exception as e:
                            st.error(f"Error al guardar: {e}")
                    else:
                        st.warning("No te bañes, llena todos los campos.")

    # --- PESTAÑA: MIS VENTAS ---
    with choice[2]:
        if not st.session_state.user:
            st.info("Inicia sesión para gestionar tus publicaciones.")
        else:
            st.subheader("Tus publicaciones")
            mis_boletos = supabase.table("boletos").select("*").eq("vendedor_email", st.session_state.user.email).execute().data
            if mis_boletos:
                for b in mis_boletos:
                    with st.expander(f"📌 {b['evento']} - ${b['precio']} ({b['estado']})"):
                        st.write(f"Recinto: {b['recinto']}")
                        st.write(f"Zona: {b['zona']}")
                        if st.button("Marcar como Vendido", key=f"del_{b['id']}"):
                            supabase.table("boletos").update({"estado": "vendido"}).eq("id", b['id']).execute()
                            st.rerun()
            else:
                st.write("Aún no tienes ventas publicadas.")

if __name__ == "__main__":
    main()
