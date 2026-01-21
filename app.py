import streamlit as st
from supabase import create_client, Client
import urllib.parse

# Configuración inicial
st.set_page_config(
    page_title="MtyPass | Marketplace",
    page_icon="🎟️",
    layout="centered",
)

# --- CSS PERSONALIZADO (DARK MODE) ---
def local_css():
    st.markdown(
        """
        <style>
        .stApp { background-color: #121212; color: #FFFFFF; }
        div.stButton > button:first-child {
            background-color: #FF4B2B; color: white; border-radius: 12px;
            border: none; height: 3.5rem; width: 100%; font-weight: bold;
        }
        .event-card {
            background-color: #1E1E1E; padding: 1.5rem; border-radius: 15px;
            border: 1px solid #333; margin-bottom: 10px;
        }
        .price-tag { color: #FF4B2B; font-size: 1.3rem; font-weight: bold; }
        .stTextInput input, .stSelectbox div, .stNumberInput input {
            background-color: #1E1E1E !important; color: white !important;
        }
        /* Estilo para links tipo botón */
        .whatsapp-btn {
            background-color: #25D366; color: white; padding: 10px;
            text-decoration: none; border-radius: 10px; display: block;
            text-align: center; font-weight: bold; margin-top: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

local_css()

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- LÓGICA DE USUARIO (AUTH) ---
if 'user' not in st.session_state:
    st.session_state.user = None

def login_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

def register_user(email, password):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        st.success("¡Registro exitoso! Revisa tu correo o inicia sesión.")
    except Exception as e:
        st.error(f"Error: {e}")

# --- FUNCIONES DE BASE DE DATOS ---
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
    st.markdown("<h1 style='text-align: center;'>🎟️ MtyPass</h1>", unsafe_allow_html=True)

    # Sidebar para login/perfil
    with st.sidebar:
        if st.session_state.user:
            st.write(f"🤠 Qué onda, **{st.session_state.user.email}**")
            if st.button("Cerrar Sesión"):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.rerun()
        else:
            st.subheader("Inicia Sesión")
            email = st.text_input("Correo")
            password = st.text_input("Contraseña", type="password")
            col1, col2 = st.columns(2)
            if col1.button("Entrar"):
                login_user(email, password)
            if col2.button("Registrar"):
                register_user(email, password)

    menu = ["Explorar", "Vender", "Mis Ventas"]
    choice = st.tabs(menu)

    # --- EXPLORAR ---
    with choice[0]:
        recinto_filtro = st.selectbox("¿A dónde quieres ir, compadre?", 
                             ["Todos", "Arena Monterrey", "Auditorio Citibanamex", "Estadio BBVA", "Estadio Universitario"])
        
        boletos_lista = obtener_boletos(recinto_filtro)

        if not boletos_lista:
            st.info("Aún no hay boletos aquí. ¡Sé el primero en vender!")
        else:
            for boleto in boletos_lista:
                with st.container():
                    st.markdown(f"""
                    <div class="event-card">
                        <p style='color: #FF4B2B; font-weight: bold; margin-bottom: 0;'>{boleto['recinto']}</p>
                        <h3 style='margin: 0;'>{boleto['evento']}</h3>
                        <p style='color: #BBB;'>Zona: {boleto['zona']}</p>
                        <p class="price-tag">${boleto['precio']:,} MXN</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botón de WhatsApp
                    msg = urllib.parse.quote(f"¡Qué onda! Me interesa tu boleto para {boleto['evento']} en {boleto['recinto']} que vi en MtyPass.")
                    wa_link = f"https://wa.me/{boleto['whatsapp']}?text={msg}"
                    
                    st.markdown(f'<a href="{wa_link}" target="_blank" class="whatsapp-btn">📱 Contactar por WhatsApp</a>', unsafe_allow_html=True)
                    st.write("---")

    # --- VENDER ---
    with choice[1]:
        if not st.session_state.user:
            st.warning("🔒 Inicia sesión en la barra lateral para poder vender tus boletos.")
        else:
            st.subheader("Publica tu boleto")
            with st.form("vender_form"):
                evento = st.text_input("Evento")
                recinto_vta = st.selectbox("Recinto", ["Arena Monterrey", "Auditorio Citibanamex", "Estadio BBVA", "Estadio Universitario"])
                precio = st.number_input("Precio ($MXN)", min_value=100)
                zona = st.text_input("Zona")
                whatsapp = st.text_input("Tu WhatsApp (Ej: 528112345678)", help="Incluye código de país (52)")
                
                if st.form_submit_button("¡Publicar ahora!"):
                    if evento and zona and whatsapp:
                        guardar_boleto(evento, recinto_vta, precio, zona, whatsapp)
                        st.balloons()
                        st.success("¡Boleto publicado!")
                    else:
                        st.error("Llena todos los campos, no te bañes.")

    # --- MIS VENTAS ---
    with choice[2]:
        if not st.session_state.user:
            st.info("Inicia sesión para ver tus publicaciones.")
        else:
            st.subheader("Tus boletos activos")
            mis_boletos = supabase.table("boletos").select("*").eq("vendedor_email", st.session_state.user.email).execute().data
            if mis_boletos:
                for b in mis_boletos:
                    st.write(f"✅ {b['evento']} - {b['zona']} (${b['precio']})")
            else:
                st.write("No has publicado nada todavía.")

if __name__ == "__main__":
    main()
