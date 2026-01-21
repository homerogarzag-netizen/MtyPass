import streamlit as st
from supabase import create_client, Client

# Configuración inicial de la página
st.set_page_config(
    page_title="MtyPass | Marketplace de Boletos",
    page_icon="🎟️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- INYECCIÓN DE CSS PERSONALIZADO ---
def local_css():
    st.markdown(
        """
        <style>
        .stApp { background-color: #121212; color: #FFFFFF; }
        
        /* Estilo de los Botones */
        div.stButton > button:first-child {
            background-color: #FF4B2B;
            color: white;
            border-radius: 12px;
            border: none;
            height: 3rem;
            width: 100%;
            font-weight: bold;
        }
        
        /* Tarjetas de Eventos */
        .event-card {
            background-color: #1E1E1E;
            padding: 1.5rem;
            border-radius: 15px;
            border: 1px solid #333;
            margin-bottom: 10px;
            min-height: 200px;
        }

        .price-tag {
            color: #FF4B2B;
            font-size: 1.2rem;
            font-weight: bold;
        }

        h1, h2, h3 { color: #FF4B2B; }
        
        /* Ajuste para inputs */
        .stTextInput input, .stSelectbox div, .stNumberInput input {
            background-color: #1E1E1E !important;
            color: white !important;
        }
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
        st.error(f"Error de conexión: {e}")
        return None

supabase = init_connection()

# --- FUNCIONES DE BASE DE DATOS ---
def obtener_boletos(filtro_recinto="Todos"):
    query = supabase.table("boletos").select("*").eq("estado", "disponible").order("created_at", desc=True)
    if filtro_recinto != "Todos":
        query = query.eq("recinto", filtro_recinto)
    
    resultado = query.execute()
    return resultado.data

def guardar_boleto(evento, recinto, precio, zona):
    data = {
        "evento": evento,
        "recinto": recinto,
        "precio": precio,
        "zona": zona,
        "estado": "disponible"
    }
    return supabase.table("boletos").insert(data).execute()

# --- INTERFAZ DE USUARIO ---
def main():
    st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>🎟️ MtyPass</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Mercado secundario oficial de Monterrey</p>", unsafe_allow_html=True)

    menu = ["Explorar", "Vender", "Mi Perfil"]
    choice = st.tabs(menu)

    # --- TRAYENDO DATOS REALES EN EXPLORAR ---
    with choice[0]:
        recinto_filtro = st.selectbox("¿A dónde quieres ir?", 
                             ["Todos", "Arena Monterrey", "Auditorio Citibanamex", "Estadio BBVA", "Estadio Universitario", "Live Out / Pa'l Norte"])
        
        boletos_lista = obtener_boletos(recinto_filtro)

        if not boletos_lista:
            st.warning("No hay boletos disponibles por ahora para ese recinto, compadre.")
        else:
            # Mostrar boletos en una cuadrícula de 2 columnas
            cols = st.columns(2)
            for i, boleto in enumerate(boletos_lista):
                with cols[i % 2]:
                    st.markdown(f"""
                    <div class="event-card">
                        <p style='font-size: 0.8rem; color: #FF4B2B; margin-bottom: 5px;'>{boleto['recinto']}</p>
                        <h4 style='margin: 0;'>{boleto['evento']}</h4>
                        <p style='font-size: 0.9rem; color: #BBB;'>Zona: {boleto['zona']}</p>
                        <p class="price-tag">${boleto['precio']:,} MXN</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Comprar #{boleto['id']}", key=f"buy_{boleto['id']}"):
                        st.success(f"¡Pedido enviado! Contactando al vendedor de {boleto['evento']}...")

    # --- FORMULARIO REAL EN VENDER ---
    with choice[1]:
        st.subheader("Publica tu boleto")
        with st.form("vender_form", clear_on_submit=True):
            evento = st.text_input("Nombre del Artista o Evento", placeholder="Ej: Bad Bunny")
            recinto_vta = st.selectbox("Recinto", ["Arena Monterrey", "Auditorio Citibanamex", "Estadio BBVA", "Estadio Universitario", "Otro"])
            precio = st.number_input("Precio de venta ($MXN)", min_value=100, step=100)
            zona = st.text_input("Zona / Sección", placeholder="Ej: Platea Especial")
            
            submitted = st.form_submit_button("¡Publicar ahora!")
            
            if submitted:
                if evento and zona:
                    try:
                        guardar_boleto(evento, recinto_vta, precio, zona)
                        st.balloons()
                        st.success("¡Ya quedó! Tu boleto ya es visible para toda la raza.")
                        st.info("Refresca la pestaña 'Explorar' para verlo.")
                    except Exception as e:
                        st.error(f"Hubo un error al guardar: {e}")
                else:
                    st.warning("Faltan datos, no te bañes.")

    # --- MI PERFIL ---
    with choice[2]:
        st.subheader("Mi Actividad")
        st.info("Aquí verás tus ventas activas próximamente.")
        st.metric(label="Boletos Vendidos", value="0", delta="Próximamente")

if __name__ == "__main__":
    main()
