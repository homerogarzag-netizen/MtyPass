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

# --- CSS: CORRECCIÓN DE COLORES EN MÓVIL Y SIDEBAR ---
def local_css():
    st.markdown("""
<style>
    /* Fondo General Negro */
    .stApp { background-color: #000000; color: #FFFFFF; }
    
    /* FIX SIDEBAR: Forzar color oscuro y letras blancas en móvil */
    section[data-testid="stSidebar"] {
        background-color: #121212 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    
    /* Botón de flecha para desplegar sidebar en móvil */
    button[kind="header"] {
        color: #FFFFFF !important;
        background-color: transparent !important;
    }

    /* Inputs y Selectores: Letras Blancas */
    label, p, span, .stMarkdown { color: #FFFFFF !important; }
    
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #444 !important;
        border-radius: 12px !important;
    }

    /* Botón Principal Rojo MtyPass */
    div.stButton > button:first-child {
        background-color: #FF4B2B;
        color: white !important;
        border-radius: 12px;
        border: none;
        height: 3.5rem;
        width: 100%;
        font-weight: bold;
    }

    /* Tarjeta de Evento */
    .card-container {
        background-color: #111111;
        border-radius: 15px;
        border: 1px solid #333;
        margin-bottom: 5px;
        overflow: hidden;
    }
    
    .card-body { padding: 15px; }
    
    .price-tag { 
        color: #FF4B2B; 
        font-size: 1.5rem; 
        font-weight: bold; 
    }

    .ticket-img {
        width: 100%;
        height: 250px;
        object-fit: cover;
    }

    /* BOTÓN WHATSAPP: Verde con letras blancas */
    .wa-link {
        display: block;
        background-color: #25D366 !important;
        color: #FFFFFF !important;
        text-align: center;
        padding: 15px;
        border-radius: 12px;
        text-decoration: none;
        font-weight: 800;
        margin-bottom: 30px;
        font-size: 1rem;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab"] { color: #FFFFFF !important; }
    .stTabs [aria-selected="true"] { border-bottom-color: #FF4B2B !important; }
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
            st.info("Cuenta creada. Ya puedes entrar.")
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
    st.markdown("<h1 style='text-align:center;'>MtyPass</h1>", unsafe_allow_html=True)

    # BARRA LATERAL (SIDEBAR)
    with st.sidebar:
        if st.session_state.user:
            st.markdown(f"### 🤠 Perfil")
            st.write(st.session_state.user.email)
            if st.button("Cerrar Sesión"):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.rerun()
        else:
            st.markdown("### Acceso")
            mode = st.radio("Acción", ["Entrar", "Registrar"])
            e = st.text_input("Correo")
            p = st.text_input("Contraseña", type="password")
            if st.button("Confirmar"):
                auth_user(e, p, "login" if mode == "Entrar" else "reg")

    menu = ["Explorar", "Vender", "Mis Ventas"]
    choice = st.tabs(menu)

    # --- EXPLORAR ---
    with choice[0]:
        busqueda = st.text_input("🔍 Buscar artista...", placeholder="Ej: Luis Miguel")
        
        c1, c2 = st.columns(2)
        with c1:
            cat = st.selectbox("Categoría", ["Todas", "Conciertos", "Deportes", "Teatro"])
        with c2:
            lug = st.selectbox("Lugar", ["Todos", "Arena Monterrey", "Auditorio Citibanamex", "Estadio BBVA", "Estadio Universitario"])
        
        query = supabase.table("boletos").select("*").eq("estado", "disponible").order("created_at", desc=True)
        if lug != "Todos": query = query.eq("recinto", lug)
        if cat != "Todas": query = query.eq("categoria", cat)
        if busqueda: query = query.ilike("evento", f"%{busqueda}%")
            
        boletos = query.execute().data

        if not boletos:
            st.write("No hay boletos por ahora.")
        else:
            for b in boletos:
                img = b.get("imagen_url")
                img_tag = f'<img src="{img}" class="ticket-img">' if img and img != 'None' else ""
                
                # HTML DE TARJETA (PÉGADO AL MARGEN)
                card_html = f"""
<div class="card-container">
{img_tag}
<div class="card-body">
<p style='color:#FF4B2B; font-weight:700; margin-bottom:0;'>{b['recinto']} • {b.get('categoria', 'Evento')}</p>
<h3 style='margin:0; color:white;'>{b['evento']}</h3>
<p style='color:#DDD; margin-bottom:0;'>Zona: {b['zona']}</p>
<p class="price-tag">${b['precio']:,} MXN</p>
</div>
</div>
"""
                st.markdown(card_html, unsafe_allow_html=True)
                
                # BOTÓN DE WHATSAPP CORREGIDO
                msg = urllib.parse.quote(f"¡Qué onda! Me interesa el boleto para {b['evento']} en MtyPass.")
                wa_url = f"https://wa.me/{b['whatsapp']}?text={msg}"
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-link">📱 CONTACTAR POR WHATSAPP</a>', unsafe_allow_html=True)

    # --- VENDER ---
    with choice[1]:
        if not st.session_state.user:
            st.warning("Inicia sesión en la barra lateral para publicar.")
        else:
            with st.form("vender_form", clear_on_submit=True):
                ev = st.text_input("Nombre del Artista o Evento")
                col1, col2 = st.columns(2)
                with col1:
                    rec = st.selectbox("Recinto", ["Arena Monterrey", "Auditorio Citibanamex", "Estadio BBVA", "Estadio Universitario"])
                with col2:
                    ct = st.selectbox("Categoría", ["Conciertos", "Deportes", "Teatro"])
                pr = st.number_input("Precio ($MXN)", min_value=100)
                zn = st.text_input("Sección / Zona")
                wh = st.text_input("Tu WhatsApp (Ej: 5281...)")
                ft = st.file_uploader("Foto del boleto", type=['jpg', 'png', 'jpeg'])
                
                if st.form_submit_button("PUBLICAR BOLETO"):
                    if ev and wh:
                        with st.spinner("Subiendo..."):
                            url = upload_image(ft)
                            guardar_boleto(ev, rec, pr, zn, wh, url, ct)
                            st.success("¡Publicado!")
                            st.rerun()

    # --- MIS VENTAS ---
    with choice[2]:
        if st.session_state.user:
            mis = supabase.table("boletos").select("*").eq("vendedor_email", st.session_state.user.email).execute().data
            if not mis: st.write("No tienes ventas aún.")
            for b in mis:
                with st.expander(f"{b['evento']} - {b['estado']}"):
                    if b['estado'] == 'disponible':
                        if st.button("Marcar Vendido", key=f"s_{b['id']}"):
                            supabase.table("boletos").update({"estado": "vendido"}).eq("id", b['id']).execute()
                            st.rerun()
                    if st.button("Borrar Publicación", key=f"d_{b['id']}"):
                        supabase.table("boletos").delete().eq("id", b['id']).execute()
                        st.rerun()
        else:
            st.write("Inicia sesión para ver tus ventas.")

if __name__ == "__main__":
    main()
