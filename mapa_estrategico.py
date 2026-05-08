import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# 1. Configuración de la interfaz
st.set_page_config(layout="wide", page_title="Proyección Electoral 2026")
st.title("🗺️ Radar Geopolítico - Proyección 2026")

# 2. Funciones de carga en caché (Para que el sistema vuele al hacer zoom o filtrar)
@st.cache_data
def cargar_datos():
    # Carga tu CSV proyectado
    df = pd.read_csv("Cerebro_Analitico_2026.csv")
    return df

@st.cache_data
def cargar_geojson():
    # GeoJSON público con los polígonos de los departamentos de Colombia
    url_geojson = "https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json"
    respuesta = requests.get(url_geojson)
    return respuesta.json()

# Inicializamos los datos
df = cargar_datos()
colombia_geojson = cargar_geojson()

# Estandarizamos los nombres de los departamentos para que crucen perfecto con el GeoJSON
df['Departamento'] = df['Departamento'].str.upper().str.strip()

# 3. Panel Lateral de Controles (Filtros)
st.sidebar.header("⚙️ Controles Analíticos")

# Filtro de Afinidad
lista_afinidades = df['Afinidad_Politica'].dropna().unique().tolist()
afinidad_seleccionada = st.sidebar.selectbox("Selecciona la Fuerza Política:", lista_afinidades)

# Filtro de Departamentos Relevantes (Opcional)
lista_deptos = ["Todos"] + sorted(df['Departamento'].dropna().unique().tolist())
depto_seleccionado = st.sidebar.selectbox("Enfocar en Departamento:", lista_deptos)

# 4. Procesamiento matemático en tiempo real
df_filtrado = df[df['Afinidad_Politica'] == afinidad_seleccionada]

if depto_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Departamento'] == depto_seleccionado]

# Consolidamos los votos proyectados por departamento
df_mapa = df_filtrado.groupby('Departamento')['Votos'].sum().reset_index()

# 5. Motor del Mapa Interactivo (Plotly)
if not df_mapa.empty:
    fig = px.choropleth_mapbox(
        df_mapa,
        geojson=colombia_geojson,
        locations='Departamento',
        featureidkey='properties.NOMBRE_DPT', # Llave del GeoJSON de Colombia
        color='Votos',
        color_continuous_scale="Reds" if afinidad_seleccionada == "IZQUIERDA" else "Blues",
        mapbox_style="carto-positron",
        zoom=4.5 if depto_seleccionado == "Todos" else 6.5,
        center={"lat": 4.5709, "lon": -74.2973},
        opacity=0.7,
        labels={'Votos': 'Proyección de Votos'}
    )
    
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    # Renderizamos el mapa en la pantalla
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostramos el top 5 para dar contexto analítico
    st.subheader(f"🏆 Top 5 Fortines: {afinidad_seleccionada}")
    st.dataframe(df_mapa.sort_values('Votos', ascending=False).head(5).style.format({"Votos": "{:,.0f}"}))
else:
    st.warning("No hay datos para la combinación seleccionada.")