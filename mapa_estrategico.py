import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# 1. Configuración de la interfaz
st.set_page_config(layout="wide", page_title="Visor Electoral Pro 2026")
st.title("🗺️ Radar Geopolítico de Precisión - Proyección 2026")

# 2. Carga de datos geolocalizados
@st.cache_data
def cargar_datos():
    # USAMOS EL NUEVO ARCHIVO CON COORDENADAS
    df = pd.read_csv("Cerebro_Geolocalizado_2026.csv")
    return df

@st.cache_data
def cargar_geojson():
    url_geojson = "https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json"
    return requests.get(url_geojson).json()

df = cargar_datos()
colombia_geojson = cargar_geojson()

# 3. Panel Lateral
st.sidebar.header("⚙️ Filtros Estratégicos")
lista_afinidades = df['Afinidad_Politica'].dropna().unique().tolist()
afinidad_sel = st.sidebar.selectbox("Fuerza Política:", lista_afinidades)

lista_deptos = ["NACIONAL"] + sorted(df['Departamento'].unique().tolist())
depto_sel = st.sidebar.selectbox("Enfocar Departamento:", lista_deptos)

# 4. Procesamiento
df_filtrado = df[df['Afinidad_Politica'] == afinidad_sel]
color_map = {"IZQUIERDA": "#EF553B", "DERECHA": "#636EFA", "CENTRO": "#00CC96", "NEUTRAL": "#AB63FA"}

# 5. Lógica de Visualización Dual
if depto_sel == "NACIONAL":
    # --- VISTA MACRO: POLÍGONOS ---
    df_mapa = df_filtrado.groupby('Departamento')['Votos'].sum().reset_index()
    fig = px.choropleth_mapbox(
        df_mapa, geojson=colombia_geojson, locations='Departamento',
        featureidkey='properties.NOMBRE_DPT', color='Votos',
        color_continuous_scale="Reds" if afinidad_sel == "IZQUIERDA" else "Blues",
        mapbox_style="carto-positron", zoom=4.5, center={"lat": 4.57, "lon": -74.29},
        opacity=0.5, labels={'Votos': 'Votos Proyectados'}
    )
else:
    # --- VISTA MICRO: BURBUJAS TÁCTICAS ---
    df_micro = df_filtrado[df_filtrado['Departamento'] == depto_sel]
    # Agrupamos por municipio para la burbuja
    df_micro = df_micro.groupby(['Municipio', 'Latitud', 'Longitud'])['Votos'].sum().reset_index()
    
    fig = px.scatter_mapbox(
        df_micro, lat="Latitud", lon="Longitud", size="Votos",
        color_discrete_sequence=[color_map.get(afinidad_sel, "#636EFA")],
        hover_name="Municipio", size_max=20, zoom=7,
        mapbox_style="carto-positron", title=f"Dispersión en {depto_sel}",
        labels={'Votos': 'Caudal Electoral'}
    )

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=600)
st.plotly_chart(fig, use_container_width=True)

# 6. Tabla de Inteligencia
st.subheader(f"📊 Detalle Territorial: {depto_sel}")
df_tabla = df_filtrado if depto_sel == "NACIONAL" else df_filtrado[df_filtrado['Departamento'] == depto_sel]
resumen = df_tabla.groupby('Municipio')['Votos'].sum().reset_index().sort_values('Votos', ascending=False)
st.dataframe(resumen.head(10).style.format({"Votos": "{:,.0f}"}), use_container_width=True)