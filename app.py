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

# --- CSS: ESTABILIDAD Y VISIBILIDAD ---
def local_css():
    st.markdown("""
<style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    section[data-testid="stSidebar"] { background-color: #121212 !important; }
    section[data-testid="stSidebar"] * { color: #FFFFFF !important; }
    button[kind="header"] { background-color: #1E1E1E !important; color: #FF4B2B !important; }

    /* Inputs y Selectores */
    label, p, span { color: #FFFFFF !important; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #444 !important;
        border-radius: 12px !important;
    }

    /* Botones */
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
    .view-count { color: #888; font-size: 0.8rem; margin-top: 5px; }

    /* Botón WhatsApp */
    .wa-link {
        display: block; background-color: #25D366 !important; color: #FFFFFF !important;
        text-align: center; padding: 15px; border-radius: 12px;
        text-decoration: none; font-weight: 800; margin-bottom: 10px; font-size: 1rem;
    }

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

# --- MANEJO DE SESIÓN Y LÓGICA ---
if 'user' not in st.session_state:
    st.session_state.user = None
if 'vistos' not in st.session_state:
    st.session_state.vistos = set()

def registrar_vista(boleto_id, vistas_actuales):
    # Solo contar una vista por sesión para no inflar el número
    if boleto_id not in st.session_state.vistos:
        nuevas_vistas = (vistas_actuales or 0) + 1
        supabase.table("boletos").update({"vistas": nuevas_vistas}).eq("id", boleto_id).execute()
        st.session_state.vistos.add(boleto_id)

def toggle_favorito(boleto_id):
    if not st.session_state.user:
        st.error("Inicia sesión primero")
        return
    email = st.session_state.user.email
    existente = supabase.table("favoritos").select("*").eq("user_email", email).eq("boleto_id", boleto_id).execute().data
    if existente:
        supabase.table("favoritos").delete().eq("user_email", email).eq("boleto_id", boleto_id).execute()
        st.toast("Eliminado de favoritos")
    else:
        supabase.table("favoritos").insert({"user_email": email, "boleto_id": boleto_id}).execute()
        st.toast("❤️ Guardado en favoritos")
    st.rerun()

# --- INTERFAZ ---
def main():
    st.markdown("<h1 style='text-align:center;'>MtyPass</h1>", unsafe_allow_html=True)

    with st.sidebar:
        if st.session_state.user:
            st.markdown(f"### 🤠 Perfil\n{st.session_state.user.email}")
            if st.button("Cerrar Sesión"):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.rerun()
        else:
            mode = st.radio("Acceso", ["Entrar", "Registrar"])
            e = st.text_input("Correo")
            p = st.text_input("Contraseña", type="password")
            if st.button("Confirmar"):
                try:
                    if mode == "Entrar":
                        res = supabase.auth.sign_in_with_password({"email": e, "password": p})
                        st.session_state.user = res.user
                    else:
                        supabase.auth.sign_up({"email": e, "password": p})
                        st.info("Cuenta creada")
                    st.rerun()
                except Exception as ex: st.error(f"Error: {ex}")

    menu = ["Explorar", "Vender", "Mi Perfil"]
    choice = st.tabs(menu)

    # --- EXPLORAR ---
    with choice[0]:
        busqueda = st.text_input("🔍 Buscar artista...", placeholder="Ej: Luis Miguel")
        c1, c2 = st.columns(2)
        with c1: cat = st.selectbox("Categoría", ["Todas", "Conciertos", "Deportes", "Teatro"])
        with c2: lug = st.selectbox("Lugar", ["Todos", "Arena Monterrey", "Estadio BBVA", "Estadio Universitario"])
        
        query = supabase.table("boletos").select("*").eq("estado", "disponible").order("created_at", desc=True)
        if lug != "Todos": query = query.eq("recinto", lug)
        if cat != "Todas": query = query.eq("categoria", cat)
        if busqueda: query = query.ilike("evento", f"%{busqueda}%")
        boletos = query.execute().data

        for b in boletos:
            # Registrar vista automáticamente
            registrar_vista(b['id'], b.get('vistas', 0))
            
            img = b.get("imagen_url")
            img_tag = f'<img src="{img}" class="ticket-img">' if img and img != 'None' else ""
            card_html = f"""
<div class="card-container">
{img_tag}
<div class="card-body">
<p style='color:#FF4B2B; font-weight:700; margin-bottom:0;'>{b['recinto']} • {b.get('categoria', 'Evento')}</p>
<h3 style='margin:0; color:white;'>{b['evento']}</h3>
<p style='color:#DDD; margin-bottom:0;'>Zona: {b['zona']}</p>
<p class="price-tag">${b['precio']:,} MXN</p>
<p class="view-count">👁️ {b.get('vistas', 0)} personas han visto esto</p>
</div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)
            
            col_wa, col_fav = st.columns([4, 1])
            with col_wa:
                msg = urllib.parse.quote(f"¡Qué onda! Me interesa el boleto para {b['evento']} en MtyPass.")
                wa_url = f"https://wa.me/{b['whatsapp']}?text={msg}"
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-link">📱 WHATSAPP</a>', unsafe_allow_html=True)
            with col_fav:
                if st.button("❤️", key=f"fav_{b['id']}"):
                    toggle_favorito(b['id'])

    # --- VENDER ---
    with choice[1]:
        if not st.session_state.user: st.warning("Inicia sesión para publicar.")
        else:
            with st.form("vender_form", clear_on_submit=True):
                ev = st.text_input("Artista / Evento")
                col1, col2 = st.columns(2)
                with col1: rec = st.selectbox("Recinto", ["Arena Monterrey", "Estadio BBVA", "Estadio Universitario", "Citibanamex"])
                with col2: ct = st.selectbox("Categoría", ["Conciertos", "Deportes", "Teatro"])
                pr = st.number_input("Precio ($MXN)", min_value=100)
                zn = st.text_input("Sección / Zona")
                wh = st.text_input("WhatsApp (52...)")
                ft = st.file_uploader("Foto", type=['jpg', 'png', 'jpeg'])
                if st.form_submit_button("PUBLICAR"):
                    if ev and wh:
                        try:
                            file_name = f"{uuid.uuid4()}.jpg"
                            supabase.storage.from_('boletos_imagenes').upload(file_name, ft.getvalue())
                            url = supabase.storage.from_('boletos_imagenes').get_public_url(file_name)
                            supabase.table("boletos").insert({"evento": ev, "recinto": rec, "precio": pr, "zona": zn, "whatsapp": wh, "imagen_url": str(url), "categoria": ct, "vendedor_email": st.session_state.user.email}).execute()
                            st.success("¡Publicado!")
                            st.rerun()
                        except: st.error("Error al subir")

    # --- MI PERFIL ---
    with choice[2]:
        if st.session_state.user:
            st.subheader("Favoritos ❤️")
            # Traer los boletos guardados haciendo un join manual
            favs_data = supabase.table("favoritos").select("boleto_id").eq("user_email", st.session_state.user.email).execute().data
            if favs_data:
                for f in favs_data:
                    b_data = supabase.table("boletos").select("*").eq("id", f['boleto_id']).execute().data
                    if b_data:
                        b = b_data[0]
                        c1, c2 = st.columns([3, 1])
                        c1.write(f"⭐ **{b['evento']}** - {b['recinto']} (${b['precio']})")
                        if c2.button("Quitar", key=f"del_fav_{b['id']}"):
                            toggle_favorito(b['id'])
            else: st.write("No tienes boletos guardados.")
            
            st.divider()
            st.subheader("Mis Publicaciones 📌")
            mis = supabase.table("boletos").select("*").eq("vendedor_email", st.session_state.user.email).execute().data
            for b in mis:
                with st.expander(f"{b['evento']} ({b.get('vistas', 0)} vistas)"):
                    if b['estado'] == 'disponible':
                        if st.button("Vendido", key=f"s_{b['id']}"):
                            supabase.table("boletos").update({"estado": "vendido"}).eq("id", b['id']).execute()
                            st.rerun()
                    if st.button("Borrar", key=f"d_{b['id']}"):
                        supabase.table("boletos").delete().eq("id", b['id']).execute()
                        st.rerun()
        else: st.write("Inicia sesión para ver tu actividad.")

if __name__ == "__main__":
    main()
