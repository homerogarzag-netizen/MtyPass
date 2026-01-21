import streamlit as st
from supabase import create_client, Client
import urllib.parse
import uuid

# Configuración inicial
st.set_page_config(page_title="MtyPass", page_icon="🎟️", layout="centered", initial_sidebar_state="collapsed")

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
    
    /* Panel Admin Info */
    .admin-box { background-color: #1E1E1E; padding: 20px; border-radius: 15px; border-left: 5px solid #FF4B2B; }
</style>
""", unsafe_allow_html=True)

local_css()

# --- CONEXIÓN SUPABASE ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# --- LÓGICA DE NEGOCIO ---
def obtener_config():
    res = supabase.table("configuracion_plataforma").select("*").eq("id", 1).execute()
    return res.data[0] if res.data else {"comision_vendedor": 5, "comision_comprador": 10}

def guardar_boleto_financiero(ev, rec, precio_v, precio_p, comision, zn, wh, img, cat):
    data = {
        "evento": ev, "recinto": rec, "precio": precio_p, # El precio principal es el publicado
        "precio_vendedor": precio_v, "precio_publicado": precio_p,
        "comision_aplicada": comision, "zona": zn, "whatsapp": wh,
        "imagen_url": str(img), "categoria": cat,
        "vendedor_email": st.session_state.user.email, "status_pago": "Pendiente"
    }
    return supabase.table("boletos").insert(data).execute()

# --- INTERFAZ ---
def main():
    if 'user' not in st.session_state: st.session_state.user = None
    
    st.markdown("<h1 style='text-align:center;'>MtyPass</h1>", unsafe_allow_html=True)

    with st.sidebar:
        if st.session_state.user:
            st.write(f"🤠 {st.session_state.user.email}")
            if st.button("Salir"):
                supabase.auth.sign_out()
                st.session_state.user = None
                st.rerun()
        else:
            e = st.text_input("Correo")
            p = st.text_input("Pass", type="password")
            if st.button("Entrar"):
                res = supabase.auth.sign_in_with_password({"email": e, "password": p})
                st.session_state.user = res.user
                st.rerun()

    # Tabs principales
    tabs = ["Explorar", "Vender", "Mi Perfil"]
    # Agregar Tab de Admin si es Homero
    if st.session_state.user and st.session_state.user.email == "homero.garza.g@gmail.com":
        tabs.append("Panel Admin")
    
    choice = st.tabs(tabs)

    # --- EXPLORAR ---
    with choice[0]:
        query = supabase.table("boletos").select("*").eq("estado", "disponible").order("created_at", desc=True).execute()
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
            wa_url = f"https://wa.me/{b['whatsapp']}?text=Me+interesa+el+boleto"
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-link">📱 CONTACTAR</a>', unsafe_allow_html=True)

    # --- VENDER (CÁLCULOS EN TIEMPO REAL) ---
    with choice[1]:
        if not st.session_state.user: st.warning("Inicia sesión para vender.")
        else:
            config = obtener_config()
            st.subheader("Publica tu Boleto")
            
            with st.form("vender_financiero"):
                ev = st.text_input("Artista / Evento")
                rec = st.selectbox("Lugar", ["Arena Monterrey", "Estadio BBVA", "Estadio Universitario", "Auditorio Citibanamex"])
                
                # Cálculo Dinámico
                precio_deseado = st.number_input("¿Cuánto quieres recibir? ($MXN)", min_value=100, step=100)
                
                comision_monto = precio_deseado * (config['comision_vendedor'] / 100)
                precio_publicado = precio_deseado + (precio_deseado * (config['comision_comprador'] / 100))
                
                st.markdown(f"""
                <div style="background-color:#1E1E1E; padding:15px; border-radius:10px; margin:10px 0;">
                    <p style='margin:0; color:#888;'>Desglose MtyPass:</p>
                    <h3 style='margin:0;'>Recibes: ${precio_deseado:,} MXN</h3>
                    <p style='margin:0; color:#FF4B2B;'>Precio en App: ${precio_publicado:,} MXN</p>
                    <p style='font-size:0.8rem; color:#888; margin-top:5px;'>
                    🔒 Tu pago se liberará 48 horas después de que el evento finalice, una vez validado el acceso del comprador.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                zn = st.text_input("Zona / Sección")
                wh = st.text_input("WhatsApp (52...)")
                ft = st.file_uploader("Foto del boleto", type=['jpg', 'png', 'jpeg'])
                cat = st.selectbox("Categoría", ["Conciertos", "Deportes", "Teatro"])

                st.divider()
                with st.expander("Términos y Condiciones (Escrow MtyPass)"):
                    st.write("""
                    MtyPass retiene el pago del comprador para garantizar la validez del boleto. 
                    El vendedor acepta que el dinero será depositado 48 horas después del evento. 
                    Cualquier reporte de boleto falso resultará en la cancelación del pago y baneo permanente.
                    """)
                
                acepto = st.checkbox("Acepto los Términos y esquema de pagos diferidos.")
                
                if st.form_submit_button("PUBLICAR BOLETO"):
                    if ev and wh and acepto:
                        try:
                            # Subir imagen
                            fname = f"{uuid.uuid4()}.jpg"
                            supabase.storage.from_('boletos_imagenes').upload(fname, ft.getvalue())
                            url = supabase.storage.from_('boletos_imagenes').get_public_url(fname)
                            # Guardar con datos financieros
                            guardar_boleto_financiero(ev, rec, precio_deseado, precio_publicado, comision_monto, zn, wh, url, cat)
                            st.success("¡Publicado! Se verá con el precio ajustado por comisión.")
                            st.rerun()
                        except: st.error("Error al publicar")
                    elif not acepto: st.error("Debes aceptar los términos, compadre.")

    # --- MI PERFIL ---
    with choice[2]:
        if st.session_state.user:
            st.subheader("Mis Ventas")
            res = supabase.table("boletos").select("*").eq("vendedor_email", st.session_state.user.email).execute()
            for b in res.data:
                st.info(f"{b['evento']} | Publicado: ${b['precio_publicado']} | Status Pago: {b['status_pago']}")
        else: st.write("Inicia sesión.")

    # --- PANEL ADMIN (SOLO HOMERO) ---
    if st.session_state.user and st.session_state.user.email == "homero.garza.g@gmail.com":
        with choice[-1]:
            st.subheader("Panel de Control MtyPass")
            config = obtener_config()
            
            with st.form("config_admin"):
                cv = st.slider("% Comisión Vendedor", 0, 30, int(config['comision_vendedor']))
                cc = st.slider("% Comisión Comprador", 0, 30, int(config['comision_comprador']))
                
                if st.form_submit_button("Guardar Configuración"):
                    supabase.table("configuracion_plataforma").update({
                        "comision_vendedor": cv,
                        "comision_comprador": cc
                    }).eq("id", 1).execute()
                    st.success("¡Configuración actualizada!")
                    st.rerun()
            
            st.markdown("---")
            st.write("Ventas Totales en la Plataforma")
            # Aquí podrías agregar un resumen de todas las ventas de la DB

if __name__ == "__main__":
    main()
