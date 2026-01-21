import streamlit as st
from supabase import create_client, Client
import urllib.parse
import uuid

# Configuración inicial
st.set_page_config(
    page_title="MtyPass | Marketplace",
    page_icon="🎟️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS PERSONALIZADO (DARK MODE) ---
def local_css():
    st.markdown(
        """
        <style>
        .stApp { background-color: #121212; color: #FFFFFF; }
        
        /* Botones */
        div.stButton > button:first-child {
            background-color: #FF4B2B; color: white; border-radius: 12px;
            border: none; height: 3.5rem; width: 100%; font-weight: bold;
        }

        /* Tarjetas estilo iPhone */
        .card-container {
            background-color: #1E1E1E;
            border-radius: 15px;
            border: 1px solid #333;
            margin-bottom: 20px;
            overflow: hidden;
            color: white;
        }
        
        .card-body { padding: 15px; }
        
        .price-tag { 
            color: #FF4B2B; 
            font-size: 1.5rem; 
            font-weight: bold; 
            margin-top: 5px;
        }

        .ticket-img {
            width: 100%;
            height: 200px;
            object-fit: cover;
        }

        /* WhatsApp botón */
        .wa-link {
            display: block;
            background-color: #25D366;
            color: white !important;
            text-align: center;
            padding: 12px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: bold;
            margin-top: 10px;
        }

        .stTextInput input, .stSelectbox div, .stNumberInput input {
            background-color: #1E1E1E !important; color: white !important;
        }
        h1, h2, h3 { color: #FF4B2B; }
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

# --- MANEJO DE SESIÓN ---
if 'user' not in st.session_state:
    st.session_state.user = None

def auth_user(email, password, mode="login"):
    try:
        if mode == "login":
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
        else:
            res = supabase.auth.sign_up({"email": email, "password": password})
            st.info("Cuenta creada, ya puedes iniciar sesión.")
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
        # Forzar la obtención de la URL como string
        res = supabase.storage.from_('boletos_imagenes').get_public_url(file_name)
        return res if isinstance(res, str) else res
    except Exception as e:
        st.error(f"Error subiendo: {e}")
        return None

def guardar_boleto(evento, recinto, precio, zona, whatsapp, img_url):
    # Asegurar que la URL sea un string limpio
    clean_url = str(img_url) if img_url else None
    data = {
        "evento": evento, "recinto": recinto, "precio": precio,
        "zona": zona, "whatsapp": whatsapp, "imagen_url": clean_url,
        "vendedor_email": st.session_state.user.email, "estado": "disponible"
    }
    return supabase.table("boletos").insert(data).execute()

# --- INTERFAZ ---
def main():
    st.markdown("<h1 style='text-align: center;'>🎟️ MtyPass</h1>", unsafe_allow_html=True)

    with st.sidebar:
        if st.session_state.user:
            st.markdown(f"### 🤠 Qué onda\n{st.session_state.user.email}")
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
        recinto_f = st.selectbox("¿A dónde quieres ir?", ["Todos", "Arena Monterrey", "Auditorio Citibanamex", "Estadio BBVA", "Estadio Universitario"])
        
        query = supabase.table("boletos").select("*").eq("estado", "disponible").order("created_at", desc=True)
        if recinto_f != "Todos":
            query = query.eq("recinto", recinto_f)
        
        boletos = query.execute().data

        if not boletos:
            st.info("No hay boletos disponibles.")
        else:
            for b in boletos:
                # Renderizado SEGURO del HTML
                img_url = b.get("imagen_url")
                img_html = f'<img src="{img_url}" class="ticket-img">' if img_url and img_url != 'None' else ""
                
                card_html = f"""
                <div class="card-container">
                    {img_html}
                    <div class="card-body">
                        <p style='color: #FF4B2B; font-weight: bold; margin-bottom: 0;'>{b['recinto']}</p>
                        <h3 style='margin-top: 0; margin-bottom: 5px; color: white;'>{b['evento']}</h3>
                        <p style='color: #BBB; margin-bottom: 0;'>Zona: {b['zona']}</p>
                        <p class="price-tag">${b['precio']:,} MXN</p>
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Botón de WhatsApp aparte para evitar problemas de clicks
                msg = urllib.parse.quote(f"¡Qué onda! Me interesa el boleto para {b['evento']} que vi en MtyPass.")
                wa_url = f"https://wa.me/{b['whatsapp']}?text={msg}"
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-link">📱 Contactar por WhatsApp</a>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

    # --- VENDER ---
    with choice[1]:
        if not st.session_state.user:
            st.warning("Inicia sesión para publicar.")
        else:
            with st.form("vender_form", clear_on_submit=True):
                st.subheader("Publica tu boleto")
                evento = st.text_input("Artista / Evento")
                lugar = st.selectbox("Lugar", ["Arena Monterrey", "Auditorio Citibanamex", "Estadio BBVA", "Estadio Universitario"])
                precio = st.number_input("Precio ($MXN)", min_value=100)
                zona = st.text_input("Zona")
                wa = st.text_input("WhatsApp (Ej: 5281...)")
                foto = st.file_uploader("Foto del boleto", type=['jpg', 'png', 'jpeg'])
                
                if st.form_submit_button("Publicar"):
                    if evento and wa:
                        with st.spinner("Subiendo..."):
                            url = upload_image(foto)
                            guardar_boleto(evento, lugar, precio, zona, wa, url)
                            st.success("¡Publicado!")
                            st.rerun()

    # --- MIS VENTAS ---
    with choice[2]:
        if st.session_state.user:
            mis_b = supabase.table("boletos").select("*").eq("vendedor_email", st.session_state.user.email).execute().data
            for b in mis_b:
                with st.expander(f"📌 {b['evento']} - {b['estado']}"):
                    if b['estado'] == 'disponible':
                        if st.button("Marcar como Vendido", key=f"sold_{b['id']}"):
                            supabase.table("boletos").update({"estado": "vendido"}).eq("id", b['id']).execute()
                            st.rerun()
        else:
            st.info("Inicia sesión para ver tus boletos.")

if __name__ == "__main__":
    main()
