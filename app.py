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

# --- CSS: ESTABILIDAD Y MÓVIL ---
def local_css():
    st.markdown("""
<style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    section[data-testid="stSidebar"] { background-color: #121212 !important; }
    label, p, span, .stMarkdown { color: #FFFFFF !important; }
    
    /* Inputs */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background-color: #1E1E1E !important; color: #FFFFFF !important;
        border: 1px solid #444 !important; border-radius: 12px !important;
    }

    /* Botón Rojo MtyPass */
    div.stButton > button:first-child {
        background-color: #FF4B2B; color: white !important;
        border-radius: 12px; border: none; height: 3.5rem; width: 100%; font-weight: bold;
    }

    /* Tarjeta */
    .card-container {
        background-color: #111111; border-radius: 15px;
        border: 1px solid #333; margin-bottom: 5px; overflow: hidden;
    }
    .card-body { padding: 15px; }
    .price-tag { color: #FF4B2B; font-size: 1.5rem; font-weight: bold; }
    .ticket-img { width: 100%; height: 250px; object-fit: cover; }
    
    .wa-link {
        display: block; background-color: #25D366 !important; color: #FFFFFF !important;
        text-align: center; padding: 15px; border-radius: 12px;
        text-decoration: none; font-weight: 800; margin-bottom: 30px;
    }

    .stTabs [aria-selected="true"] { border-bottom-color: #FF4B2B !important; }
</style>
""", unsafe_allow_html=True)

local_css()

# --- CONEXIÓN SUPABASE (SIMPLIFICADA Y ROBUSTA) ---
@st.cache_resource
def init_connection():
    try:
        # Limpiamos posibles espacios o comillas extras de los secrets
        url = st.secrets["SUPABASE_URL"].strip().strip('"').strip("'")
        key = st.secrets["SUPABASE_KEY"].strip().strip('"').strip("'")
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
        return None

supabase = init_connection()

# --- FUNCIONES DE BASE DE DATOS ---
def obtener_config():
    try:
        res = supabase.table("configuracion_plataforma").select("*").eq("id", 1).execute()
        return res.data[0] if res.data else {"comision_vendedor": 5, "comision_comprador": 10}
    except:
        return {"comision_vendedor": 5, "comision_comprador": 10}

def guardar_boleto_financiero(ev, rec, precio_v, precio_p, comision, zn, wh, img, cat):
    data = {
        "evento": ev, "recinto": rec, "precio": precio_p,
        "precio_vendedor": precio_v, "precio_publicado": precio_p,
        "comision_applied": comision, "zona": zn, "whatsapp": wh,
        "imagen_url": str(img), "categoria": cat,
        "vendedor_email": st.session_state.user.email, "status_pago": "Pendiente"
    }
    return supabase.table("boletos").insert(data).execute()

# --- INTERFAZ ---
def main():
    if not supabase:
        st.error("No se pudo establecer la conexión. Revisa que SUPABASE_URL y SUPABASE_KEY estén bien escritos en Streamlit.")
        return

    if 'user' not in st.session_state: st.session_state.user = None
    
    st.markdown("<h1 style='text-align:center;'>MtyPass</h1>", unsafe_allow_html=True)

    with st.sidebar:
        if st.session_state.user:
            st.markdown(f"### 🤠 Bienvenido")
            st.write(st.session_state.user.email)
            if st.button("Salir"):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.rerun()
        else:
            st.markdown("### Acceso")
            mode = st.radio("Acción", ["Entrar", "Registrar"])
            e = st.text_input("Correo")
            p = st.text_input("Pass", type="password")
            if st.button("Confirmar"):
                try:
                    if mode == "Entrar":
                        res = supabase.auth.sign_in_with_password({"email": e, "password": p})
                        st.session_state.user = res.user
                    else:
                        supabase.auth.sign_up({"email": e, "password": p})
                        st.info("Cuenta creada. Ya puedes entrar.")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error de acceso: {ex}")

    # Tabs principales
    tabs = ["Explorar", "Vender", "Mi Perfil"]
    if st.session_state.user and st.session_state.user.email == "homero.garza.g@gmail.com":
        tabs.append("Panel Admin")
    
    choice = st.tabs(tabs)

    # --- EXPLORAR ---
    with choice[0]:
        try:
            query = supabase.table("boletos").select("*").eq("estado", "disponible").order("created_at", desc=True).execute()
            if not query.data:
                st.info("No hay boletos publicados por ahora.")
            for b in query.data:
                img = b.get("imagen_url")
                img_tag = f'<img src="{img}" class="ticket-img">' if img and img != 'None' else ""
                card_html = f"""
<div class="card-container">
{img_tag}
<div class="card-body">
<p style='color:#FF4B2B; font-weight:700; margin-bottom:0;'>{b['recinto']}</p>
<h3 style='margin:0;'>{b['evento']}</h3>
<p style='color:#DDD; margin-bottom:0;'>Zona: {b['zona']}</p>
<p class="price-tag">${b['precio']:,} MXN</p>
</div>
</div>
"""
                st.markdown(card_html, unsafe_allow_html=True)
                wa_url = f"https://wa.me/{b['whatsapp']}?text=Me+interesa+el+boleto+para+{b['evento']}"
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-link">📱 CONTACTAR POR WHATSAPP</a>', unsafe_allow_html=True)
        except:
            st.error("Error al cargar eventos.")

    # --- VENDER ---
    with choice[1]:
        if not st.session_state.user: 
            st.warning("Inicia sesión en la barra lateral para vender.")
        else:
            config = obtener_config()
            st.subheader("Publica tu Boleto")
            with st.form("vender_financiero", clear_on_submit=True):
                ev = st.text_input("Artista / Evento")
                rec = st.selectbox("Lugar", ["Arena Monterrey", "Estadio BBVA", "Estadio Universitario", "Auditorio Citibanamex"])
                precio_deseado = st.number_input("¿Cuánto quieres recibir? ($MXN)", min_value=100, step=100)
                
                # Cálculos
                comision_monto = precio_deseado * (config['comision_vendedor'] / 100)
                precio_publicado = precio_deseado + (precio_deseado * (config['comision_comprador'] / 100))
                
                st.markdown(f"""
                <div style="background-color:#1E1E1E; padding:15px; border-radius:10px; margin:10px 0;">
                    <p style='margin:0; color:#888;'>Desglose MtyPass:</p>
                    <h3 style='margin:0;'>Recibes: ${precio_deseado:,} MXN</h3>
                    <p style='margin:0; color:#FF4B2B;'>Precio en App: ${precio_publicado:,} MXN</p>
                    <p style='font-size:0.8rem; color:#888; margin-top:5px;'>
                    🔒 Pago liberado 48h tras el evento.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                zn = st.text_input("Zona / Sección")
                wh = st.text_input("WhatsApp (52...)")
                ft = st.file_uploader("Foto del boleto", type=['jpg', 'png', 'jpeg'])
                cat = st.selectbox("Categoría", ["Conciertos", "Deportes", "Teatro"])
                acepto = st.checkbox("Acepto los Términos y esquema de pagos diferidos.")
                
                if st.form_submit_button("PUBLICAR BOLETO"):
                    if ev and wh and acepto and ft:
                        with st.spinner("Subiendo publicación..."):
                            try:
                                fname = f"{uuid.uuid4()}.jpg"
                                supabase.storage.from_('boletos_imagenes').upload(fname, ft.getvalue())
                                url = supabase.storage.from_('boletos_imagenes').get_public_url(fname)
                                guardar_boleto_financiero(ev, rec, precio_deseado, precio_publicado, comision_monto, zn, wh, url, cat)
                                st.success("¡Publicado exitosamente!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al subir: {e}")
                    else:
                        st.warning("Llena todos los campos y acepta los términos.")

    # --- MI PERFIL ---
    with choice[2]:
        if st.session_state.user:
            st.subheader("Mis Publicaciones")
            res = supabase.table("boletos").select("*").eq("vendedor_email", st.session_state.user.email).execute()
            for b in res.data:
                st.info(f"{b['evento']} | Publicado: ${b['precio_publicado']} | Pago: {b['status_pago']}")
        else: st.write("Inicia sesión.")

    # --- PANEL ADMIN ---
    if st.session_state.user and st.session_state.user.email == "homero.garza.g@gmail.com":
        with choice[-1]:
            st.subheader("Configuración Admin")
            config = obtener_config()
            with st.form("config_admin"):
                cv = st.slider("% Comisión Vendedor", 0, 30, int(config['comision_vendedor']))
                cc = st.slider("% Comisión Comprador", 0, 30, int(config['comision_comprador']))
                if st.form_submit_button("Actualizar"):
                    supabase.table("configuracion_plataforma").update({"comision_vendedor": cv, "comision_comprador": cc}).eq("id", 1).execute()
                    st.success("Configuración guardada.")
                    st.rerun()

if __name__ == "__main__":
    main()
