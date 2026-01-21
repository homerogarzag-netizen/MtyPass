import streamlit as st
from supabase import create_client, Client
import urllib.parse
import uuid

# Configuración inicial para móvil
st.set_page_config(
    page_title="MtyPass",
    page_icon="🎟️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- REDISEÑO MINIMALISTA (IPHONE OPTIMIZED) ---
def local_css():
    st.markdown("""
<style>
    /* Reset de fondo */
    .stApp { background-color: #000000; color: #FFFFFF; }
    
    /* Ocultar etiquetas de Streamlit para look minimalista */
    label { color: #FFFFFF !important; font-size: 0.85rem !important; font-weight: 300 !important; margin-bottom: 2px !important; }
    
    /* Input Styling (Minimalista) */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background-color: #1A1A1A !important;
        color: white !important;
        border: 1px solid #333 !important;
        border-radius: 12px !important;
        height: 45px !important;
    }
    
    /* Botón Principal (Grande y fácil de tocar) */
    div.stButton > button:first-child {
        background-color: #FF4B2B;
        color: white;
        border-radius: 14px;
        border: none;
        height: 3.5rem;
        width: 100%;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-top: 10px;
    }

    /* Tarjeta de Evento Estilo Apple */
    .card-container {
        background-color: #111111;
        border-radius: 20px;
        border: 1px solid #222;
        margin-bottom: 25px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    
    .card-body { padding: 18px; }
    
    .price-tag { 
        color: #FFFFFF; 
        font-size: 1.4rem; 
        font-weight: 700;
        margin-top: 8px;
    }

    .ticket-img {
        width: 100%;
        height: 280px;
        object-fit: cover;
    }

    /* Botón WhatsApp (Minimalista Verde) */
    .wa-link {
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #FFFFFF; /* Blanco para contraste moderno */
        color: #000000 !important;
        text-align: center;
        padding: 14px;
        border-radius: 14px;
        text-decoration: none;
        font-weight: 700;
        margin: 0px 18px 18px 18px;
        font-size: 0.9rem;
    }

    /* Tabs Minimalistas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: #1A1A1A;
        border-radius: 20px;
        color: #888;
        padding: 0px 20px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF4B2B !important;
        color: white !important;
    }

    /* Títulos */
    h1, h2, h3 { color: #FFFFFF; font-weight: 800; letter-spacing: -1px; }
    p { color: #888; }
</style>
""", unsafe_allow_html=True)

local_css()

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- MANEJO DE SESIÓN ---
if 'user' not in st.session_state:
    st.session_state.user = None

def auth_user(email, password, mode="login"):
    try:
        if mode == "login":
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
        else:
            supabase.auth.sign_up({"email": email, "password": password})
            st.info("Cuenta creada. Inicia sesión.")
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

# --- STORAGE Y DB ---
def upload_image(file):
    if file is None: return None
    try:
        file_ext = file.name.split('.')[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        supabase.storage.from_('boletos_imagenes').upload(file_name, file.getvalue())
        res = supabase.storage.from_('boletos_imagenes').get_public_url(file_name)
        return res
    except Exception as e:
        st.error(f"Error al subir imagen")
        return None

def guardar_boleto(evento, recinto, precio, zona, whatsapp, img_url, categoria):
    data = {
        "evento": evento, "recinto": recinto, "precio": precio,
        "zona": zona, "whatsapp": whatsapp, "imagen_url": str(img_url),
        "categoria": categoria, "vendedor_email": st.session_state.user.email, "estado": "disponible"
    }
    return supabase.table("boletos").insert(data).execute()

# --- INTERFAZ ---
def main():
    # Logo minimalista
    st.markdown("<h1 style='text-align: center; font-size: 2.5rem; margin-top: -20px;'>MtyPass</h1>", unsafe_allow_html=True)

    with st.sidebar:
        if st.session_state.user:
            st.markdown(f"### 🤠 Perfil\n{st.session_state.user.email}")
            if st.button("Cerrar Sesión"):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.rerun()
        else:
            mode = st.radio("Acceso", ["Iniciar Sesión", "Registrarse"])
            email = st.text_input("Correo")
            password = st.text_input("Contraseña", type="password")
            if st.button("Confirmar"):
                auth_user(email, password, "login" if mode == "Iniciar Sesión" else "register")

    menu = ["Explorar", "Vender", "Mis Ventas"]
    choice = st.tabs(menu)

    # --- EXPLORAR ---
    with choice[0]:
        search_query = st.text_input("", placeholder="🔍 Buscar concierto, equipo o evento...")
        
        c1, c2 = st.columns(2)
        with c1:
            cat_filtro = st.selectbox("", ["Todas", "Conciertos", "Deportes", "Teatro"], label_visibility="collapsed")
        with c2:
            recinto_f = st.selectbox("", ["Todos", "Arena Monterrey", "Estadio BBVA", "Estadio Universitario", "Citibanamex"], label_visibility="collapsed")
        
        # Query a Supabase
        query = supabase.table("boletos").select("*").eq("estado", "disponible").order("created_at", desc=True)
        if recinto_f != "Todos": query = query.eq("recinto", recinto_f)
        if cat_filtro != "Todas": query = query.eq("categoria", cat_filtro)
        if search_query: query = query.ilike("evento", f"%{search_query}%")
            
        boletos = query.execute().data

        if not boletos:
            st.markdown("<p style='text-align: center;'>No encontramos boletos con esos filtros.</p>", unsafe_allow_html=True)
        else:
            for b in boletos:
                img_url = b.get("imagen_url")
                img_tag = f'<img src="{img_url}" class="ticket-img">' if img_url and img_url != 'None' else ""
                
                card_html = f"""
<div class="card-container">
    {img_tag}
    <div class="card-body">
        <p style='color: #FF4B2B; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 2px;'>{b['recinto']} • {b.get('categoria', 'Evento')}</p>
        <h3 style='margin: 0; font-size: 1.5rem;'>{b['evento']}</h3>
        <p style='color: #888; font-size: 0.9rem; margin-bottom: 0;'>{b['zona']}</p>
        <p class="price-tag">${b['precio']:,} <span style='font-size: 0.8rem; font-weight: 400; color: #888;'>MXN</span></p>
    </div>
</div>
"""
                st.markdown(card_html, unsafe_allow_html=True)
                
                msg = urllib.parse.quote(f"¡Qué onda! Me interesa el boleto para {b['evento']} que vi en MtyPass.")
                wa_url = f"https://wa.me/{b['whatsapp']}?text={msg}"
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-link">📱 CONTACTAR VENDEDOR</a>', unsafe_allow_html=True)

    # --- VENDER ---
    with choice[1]:
        if not st.session_state.user:
            st.warning("Inicia sesión para publicar.")
        else:
            with st.form("vender_form", clear_on_submit=True):
                st.subheader("Publicar")
                evento = st.text_input("", placeholder="Nombre del Artista o Evento")
                lugar = st.selectbox("", ["Arena Monterrey", "Auditorio Citibanamex", "Estadio BBVA", "Estadio Universitario"], index=0)
                cat_v = st.selectbox("", ["Conciertos", "Deportes", "Teatro", "Festivales"], index=0)
                precio = st.number_input("Precio ($MXN)", min_value=100, step=100)
                zona = st.text_input("", placeholder="Sección / Zona")
                wa = st.text_input("", placeholder="WhatsApp (Ej: 5281...)")
                foto = st.file_uploader("Sube una foto clara", type=['jpg', 'png', 'jpeg'])
                
                if st.form_submit_button("PUBLICAR AHORA"):
                    if evento and wa:
                        with st.spinner("Subiendo..."):
                            url = upload_image(foto)
                            guardar_boleto(evento, lugar, precio, zona, wa, url, cat_v)
                            st.rerun()

    # --- MIS VENTAS ---
    with choice[2]:
        if st.session_state.user:
            mis_b = supabase.table("boletos").select("*").eq("vendedor_email", st.session_state.user.email).execute().data
            for b in mis_b:
                with st.expander(f"📌 {b['evento']} - {b['estado']}"):
                    if b['estado'] == 'disponible':
                        if st.button("Marcar Vendido", key=f"sold_{b['id']}"):
                            supabase.table("boletos").update({"estado": "vendido"}).eq("id", b['id']).execute()
                            st.rerun()
                    if st.button("Eliminar", key=f"del_{b['id']}"):
                        supabase.table("boletos").delete().eq("id", b['id']).execute()
                        st.rerun()
        else:
            st.info("Inicia sesión para ver tu actividad.")

if __name__ == "__main__":
    main()
