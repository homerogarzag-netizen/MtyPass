import streamlit as st
from supabase import create_client, Client
import os

# Configuración inicial de la página (Layout móvil por defecto)
st.set_page_config(
    page_title="MtyPass | Marketplace de Boletos",
    page_icon="🎟️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- INYECCIÓN DE CSS PERSONALIZADO (DARK MODE & MOBILE FIRST) ---
def local_css():
    st.markdown(
        """
        <style>
        /* Fondo y colores base */
        .stApp {
            background-color: #121212;
            color: #FFFFFF;
        }
        
        /* Estilo de los Botones Principales */
        div.stButton > button:first-child {
            background-color: #FF4B2B;
            color: white;
            border-radius: 12px;
            border: none;
            height: 3.5rem;
            width: 100%;
            font-size: 1.1rem;
            font-weight: bold;
            transition: 0.3s;
            margin-top: 10px;
        }
        
        div.stButton > button:first-child:hover {
            background-color: #FF320B;
            border: none;
            color: white;
            transform: scale(1.02);
        }

        /* Tarjetas de Eventos */
        .event-card {
            background-color: #1E1E1E;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #333;
            margin-bottom: 15px;
        }

        /* Inputs y Selects */
        .stTextInput input, .stSelectbox div {
            background-color: #1E1E1E !important;
            color: white !important;
            border-radius: 10px !important;
        }

        /* Ocultar elementos innecesarios de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Tipografía Regia */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            color: #FF4B2B;
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
        st.error(f"Error de conexión con Supabase: {e}")
        return None

supabase = init_connection()

# --- NAVEGACIÓN PRINCIPAL ---
def main():
    # Header minimalista para Monterrey
    st.markdown("<h1 style='text-align: center;'>🎟️ MtyPass</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>El marketplace oficial de la raza en Monterrey</p>", unsafe_allow_html=True)

    # Tabs de navegación inferior (Simulando App Móvil)
    menu = ["Explorar", "Vender", "Mi Perfil"]
    choice = st.tabs(menu)

    # --- SECCIÓN: EXPLORAR EVENTOS ---
    with choice[0]:
        st.subheader("Próximos Eventos")
        
        # Filtro rápido de recintos locales
        recinto = st.selectbox("Filtrar por recinto:", 
                             ["Todos", "Arena Monterrey", "Auditorio Citibanamex", "Estadio BBVA", "Estadio Universitario", "Live Out / Pa'l Norte"])

        # Placeholder de tarjetas de boletos
        # Nota: Aquí haremos la integración con la base de datos más adelante
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="event-card">
                <p style='font-size: 0.8rem; color: #FF4B2B; margin-bottom: 5px;'>Arena Monterrey</p>
                <h4 style='margin: 0;'>Luis Miguel</h4>
                <p style='font-size: 0.9rem; color: #BBB;'>Sección: VIP</p>
                <p style='font-weight: bold;'>$3,500 MXN</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Ver Boleto", key="btn1"):
                st.info("Función de compra próximamente")

        with col2:
            st.markdown(f"""
            <div class="event-card">
                <p style='font-size: 0.8rem; color: #FF4B2B; margin-bottom: 5px;'>Estadio BBVA</p>
                <h4 style='margin: 0;'>Clásico Regio</h4>
                <p style='font-size: 0.9rem; color: #BBB;'>Zona: Especial Oriente</p>
                <p style='font-weight: bold;'>$1,200 MXN</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Ver Boleto", key="btn2"):
                st.info("Función de compra próximamente")

    # --- SECCIÓN: VENDER BOLETO ---
    with choice[1]:
        st.subheader("Pon tu boleto a la venta")
        with st.form("vender_form"):
            evento = st.text_input("Nombre del Evento")
            recinto_vta = st.selectbox("Recinto", ["Arena Monterrey", "Auditorio Citibanamex", "Estadio BBVA", "Estadio Universitario", "Otro"])
            precio = st.number_input("Precio ($MXN)", min_value=100, step=50)
            zona = st.text_input("Zona (ej. Cancha Gral, Preferente)")
            archivo = st.file_uploader("Sube tu boleto (PDF o Imagen)", type=['pdf', 'jpg', 'png'])
            
            submitted = st.form_submit_button("Publicar Boleto")
            if submitted:
                if evento and precio and archivo:
                    st.success("¡Boleto enviado a revisión! En breve aparecerá en el marketplace.")
                else:
                    st.warning("Por favor llena todos los campos, compadre.")

    # --- SECCIÓN: MI PERFIL ---
    with choice[2]:
        st.subheader("Mi Perfil")
        st.write("Gestiona tus compras y ventas de boletos.")
        
        # Simulación de estado de cuenta
        st.metric(label="Vendido", value="$4,700 MXN", delta="15%")
        
        if st.button("Cerrar Sesión"):
            st.write("Saliendo de MtyPass...")

if __name__ == "__main__":
    main()
