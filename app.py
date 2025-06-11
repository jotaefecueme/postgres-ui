import os
import logging
from dotenv import load_dotenv
import psycopg2
import pandas as pd
import streamlit as st

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

st.set_page_config(page_title="postgres-ui | Lekta ES", layout="wide")

CSS = """
.respuesta-box {
    padding: 15px 20px;
    border-radius: 10px;
    border: 1px solid #ccc;
    margin-bottom: 1em;
}
@media (prefers-color-scheme: dark) {
    .respuesta-box {
        background-color: #222;
        color: #eee;
        border: 1px solid #444;
    }
}
@media (prefers-color-scheme: light) {
    .respuesta-box {
        background-color: #f9f9f9;
        color: #000;
        border: 1px solid #ddd;
    }
}

/* Ajusta el espacio vertical general */
main .block-container {
    padding-top: 0rem;
    padding-bottom: 0rem;
}
"""

st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    st.error("La variable de entorno DATABASE_URL no está configurada. Revisa tu archivo .env.")
    st.stop()

@st.cache_data(show_spinner=False)
def get_table_names():
    try:
        with psycopg2.connect(DATABASE_URL, sslmode='require') as conn:
            with conn.cursor() as cur:
                cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';""")
                tables = [row[0] for row in cur.fetchall()]
        logging.info(f"Tablas recuperadas: {tables}")
        return tables
    except Exception as e:
        logging.error(f"Error en get_table_names: {e}")
        st.error(f"Error de conexión a la base de datos: {e}")
        return []

if st.sidebar.button("🔄 Actualizar datos"):
    st.cache_data.clear()

@st.cache_data(show_spinner=False)
def get_table_data(table):
    try:
        with psycopg2.connect(DATABASE_URL, sslmode='require') as conn:
            safe_table = table.replace('"', '""')
            query = f'SELECT * FROM "{safe_table}"'
            df = pd.read_sql(query, conn)
            logging.info(f"Datos cargados para tabla {table} con {len(df)} filas")
            return df
    except Exception as e:
        logging.error(f"Error en get_table_data para tabla {table}: {e}")
        st.error(f"Error al obtener datos de la tabla {table}: {e}")
        return None

st.title("postgres-ui | Lekta ES")

tables = get_table_names()

if not tables:
    st.warning("No se encontraron tablas en el esquema público o no se pudo conectar a la base de datos.")
    st.stop()

table_selected = st.sidebar.selectbox("Tablas:", tables)

if table_selected:
    data = get_table_data(table_selected)
    if data is not None:
        if len(data) > 10000:
            st.warning(f"La tabla '{table_selected}' tiene {len(data):,} filas. La carga y renderizado pueden ser lentos.")
        st.markdown('<div class="respuesta-box">', unsafe_allow_html=True)
        st.dataframe(data, use_container_width=True, height=1000)
        st.markdown('</div>', unsafe_allow_html=True)
