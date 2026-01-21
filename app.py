import streamlit as st
from supabase import create_client, Client
import urllib.parse
import uuid

# Configuración inicial de la página
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
        div.stButton > button:first-child {
            background-color: #FF4B2B; color: white; border-radius: 12px;
            border: none; height: 3.5rem; width: 100%; font-weight: bold;
        }
        .event-card {
            background-color: #1E1E1E; border-radius: 15px;
            border: 1px solid #333; margin-bottom: 20px; overflow: hidden;
        }
        .card-content { padding: 1.5rem; }
        .price-tag { color: #FF4B2B; font-size: 1.4rem; font-weight: bold; }
        .whatsapp-btn {
            background-color: #25D366; color: white !important; padding: 12px;
            text-decoration: none; border-radius: 12px; display: block;
            text-align: center; font-weight: bold; margin: 0px 1.5rem 1.5rem 1.5rem;
        }
        .ticket-img {
            width: 100%; height: 220px; object-fit: cover;
            border-bottom: 1px solid #333;
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
            st.success("¡Qué onda de nuevo!")
        else:
            res = supabase.auth.sign_up({"email": email, "password": password})
            st.info("¡Cuenta creada! Ya puedes entrar.")
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

# --- FUNCIONES DE STORAGE Y DB ---
def upload_image(file):
    if file is None: return None
    try:
        file_ext = file.name.split('.')[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        # Subida
        supabase.storage.from_('boletos_imagenes').upload(file_name, file.getvalue())
        # Obtener URL pública (manejando el objeto que regresa supabase-py)
        res_url = supabase.storage.from_('boletos_imagenes').get_public_url(file_name)
        return res_url if isinstance(res_url, str) else res_url.get('publicURL', res_url)
    except Exception as e:
        st.error(f"Error subiendo foto: {e}")
        return None

def guardar_boleto(evento, recinto, precio, zona, whatsapp, img_url):
    data = {
        "evento": evento, "recinto": recinto, "precio": precio,
        "zona": zona, "whatsapp": whatsapp, "imagen_url": str(img_url),
        "vendedor_email": st.session_state.user.email, "estado": "disponible"
    }
    return supabase.table("boletos").insert(data).execute()

# --- INTERFAZ ---
def main():
    st.markdown("<h1 style='text-align: center;'>🎟️ MtyPass</h1>", unsafe_allow_html=True)

    with st.sidebar:
        if st.session_state.user:
            st.markdown(f"### 🤠 Bienvenido\n{st.session_state.user.email}")
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
        recinto_f = st.selectbox("Filtrar por recinto:", ["Todos", "Arena Monterrey", "Auditorio Citibanamex", "Estadio BBVA", "Estadio Universitario"])
        
        query = supabase.table("boletos").select("*").eq("estado", "disponible").order("created_at", desc=True)
        if recinto_f != "Todos":
            query = query.eq("recinto", recinto_f)
        
        boletos = query.execute().data

        if not boletos:
            st.info("Aún no hay boletos. ¡Sé el primero!")
        else:
            for b in boletos:
                # Limpiar la URL de la imagen por si viene como objeto
                img_url = b.get("imagen_url", "")
                img_tag = f'<img src="{img_url}" class="ticket-img">' if img_url and img_url != 'None' else ""
                
                st.markdown(f"""
                <div class="event-card">
                    {img_tag}
                    <div class="card-content">
                        <p style='color: #FF4B2B; font-weight: bold; margin-bottom: 5px;'>{b['recinto']}</p>
                        <h3 style='margin: 0;'>{b['evento']}</h3>
                        <p style='color: #BBB;'>Zona: {b['zona']}</p>
                        <p class="price-tag">${b['precio']:,} MXN</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                msg = urllib.parse.quote(f"¡Qué onda! Me interesa el boleto para {b['evento']} que vi en MtyPass.")
                st.markdown(f'<a href="https://wa.me/{b["whatsapp"]}?text={msg}" target="_blank" class="whatsapp-btn">📱 Contactar por WhatsApp</a>', unsafe_allow_html=True)

    # --- VENDER ---
    with choice[1]:
        if not st.session_state.user:
            st.warning("🔒 Inicia sesión para vender.")
        else:
            with st.form("vender_form", clear_on_submit=True):
                st.subheader("Publicar mi boleto")
                evento = st.text_input("Artista / Evento")
                recinto = st.selectbox("Lugar", ["Arena Monterrey", "Auditorio Citibanamex", "Estadio BBVA", "Estadio Universitario", "Otro"])
                precio = st.number_input("Precio ($MXN)", min_value=100)
                zona = st.text_input("Zona")
                whatsapp = st.text_input("Tu WhatsApp (Ej: 528188889999)")
                foto = st.file_uploader("Foto del boleto (Tapa códigos)", type=['jpg', 'jpeg', 'png'])
                
                if st.form_submit_button("Publicar ahora"):
                    if evento and whatsapp:
                        with st.spinner("Subiendo publicación..."):
                            url_foto = upload_image(foto)
                            guardar_boleto(evento, recinto, precio, zona, whatsapp, url_foto)
                            st.balloons()
                            st.success("¡Publicado! Ya lo puede ver la raza.")
                    else:
                        st.error("Nombre y WhatsApp son obligatorios.")

    # --- MIS VENTAS ---
    with choice[2]:
        if st.session_state.user:
            st.subheader("Gestionar mis boletos")
            mis_b = supabase.table("boletos").select("*").eq("vendedor_email", st.session_state.user.email).execute().data
            if not mis_b: st.write("No has publicado nada.")
            for b in mis_b:
                with st.expander(f"📌 {b['evento']} - {b['estado']}"):
                    if b['estado'] == 'disponible':
                        if st.button("Marcar como Vendido", key=f"sold_{b['id']}"):
                            supabase.table("boletos").update({"estado": "vendido"}).eq("id", b['id']).execute()
                            st.rerun()
        else:
            st.info("Inicia sesión para ver tu actividad.")

if __name__ == "__main__":
    main()
