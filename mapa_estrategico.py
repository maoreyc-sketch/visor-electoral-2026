import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# 1. Configuración de la interfaz
st.set_page_config(layout="wide", page_title="Visor Electoral Pro 2026")
st.title("🗺️ Radar Geopolítico de Precisión - Proyección 2026")

@st.cache_data
def cargar_datos():
    df = pd.read_csv("Cerebro_Geolocalizado_2026.csv")
    
    # --- DICCIONARIO TRADUCTOR PARA EL MAPA ---
    correcciones = {
        "BOGOTA D.C.": "SANTAFE DE BOGOTA D.C",
        "BOGOTÁ D.C.": "SANTAFE DE BOGOTA D.C",
        "BOGOTA": "SANTAFE DE BOGOTA D.C",
        "BOGOTÁ": "SANTAFE DE BOGOTA D.C",
        "VALLE": "VALLE DEL CAUCA",
        "NARIÑO":"NARIÑO",
        "SAN ANDRES": "ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA",
        "NARIÑO": "NARINO" # A veces el mapa no lee la Ñ
    }
    # Forzamos los nombres para que el mapa los reconozca a la perfección
    df['Departamento'] = df['Departamento'].replace(correcciones)
    
    return df

@st.cache_data
def cargar_geojson():
    url_geojson = "https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json"
    return requests.get(url_geojson).json()

df = cargar_datos()
colombia_geojson = cargar_geojson()

# 2. Panel Lateral: Filtros Estratégicos
st.sidebar.header("⚙️ Filtros de Escenario")
lista_afinidades = df['Afinidad_Politica'].dropna().unique().tolist()

# ⚡ ACTUALIZACIÓN: Selector Múltiple (Cargado con todas por defecto)
afinidad_sel = st.sidebar.multiselect("Fuerzas Políticas en Disputa:", lista_afinidades, default=lista_afinidades)

lista_deptos = ["NACIONAL"] + sorted(df['Departamento'].unique().tolist())
depto_sel = st.sidebar.selectbox("Enfocar Departamento:", lista_deptos)

if not afinidad_sel:
    st.warning("⚠️ Selecciona al menos una fuerza política para visualizar el escenario.")
    st.stop()

# 3. Procesamiento y Paleta de Colores
df_filtrado = df[df['Afinidad_Politica'].isin(afinidad_sel)]
# Ajusta estos colores según los nombres exactos de tu base
color_map = {"IZQUIERDA": "#EF553B", "DERECHA": "#636EFA", "CENTRO": "#00CC96", "NEUTRAL": "#AB63FA", "VOTO BLANCO": "#D3D3D3", "VOTO NULO": "#808080"} 
# ----------------------------------------------------
# ⚡ NUEVO: CUADRO EMERGENTE INICIAL (TARJETAS RESUMEN)
# ----------------------------------------------------
st.markdown("### 📊 Radiografía del Escenario Actual")
total_votos_escenario = df_filtrado['Votos'].sum()

# Calculamos los totales por cada fuerza seleccionada para el titular
resumen_fuerzas = df_filtrado.groupby('Afinidad_Politica')['Votos'].sum().sort_values(ascending=False)

# Creamos columnas visuales tipo "Dashboard"
col1, col2, = st.columns(2)


with col1:
    if len(resumen_fuerzas) > 0:
        fuerza_ganadora = resumen_fuerzas.index[0]
        votos_ganador = resumen_fuerzas.iloc[0]
        st.metric(label=f"🏆 Lidera: {fuerza_ganadora}", value=f"{votos_ganador:,.0f}")
with col2:
    if len(resumen_fuerzas) > 1:
        fuerza_segundo = resumen_fuerzas.index[1]
        votos_segundo = resumen_fuerzas.iloc[1]
        st.metric(label=f"🥈 Segundo: {fuerza_segundo}", value=f"{votos_segundo:,.0f}")
    else:
        st.metric(label="📊 Estado", value="Escenario Único")
st.markdown("---") # Una línea divisoria elegante antes del mapa
# ----------------------------------------------------
if depto_sel == "NACIONAL":
    # --- VISTA MACRO: POLÍGONOS DE DOMINIO ---
    # Calculamos quién gana en cada departamento
    df_agrupado = df_filtrado.groupby(['Departamento', 'Afinidad_Politica'])['Votos'].sum().reset_index()
    idx_ganador = df_agrupado.groupby('Departamento')['Votos'].idxmax()
    df_macro = df_agrupado.loc[idx_ganador].rename(columns={'Afinidad_Politica': 'Fuerza Dominante', 'Votos': 'Votos Ganador'})
    
    fig = px.choropleth_mapbox(
        df_macro, geojson=colombia_geojson, locations='Departamento',
        featureidkey='properties.NOMBRE_DPT', color='Fuerza Dominante',
        color_discrete_map=color_map,
        hover_name='Departamento',
        hover_data={'Departamento': False, 'Fuerza Dominante': True, 'Votos Ganador': ':,'},
        mapbox_style="carto-positron", zoom=4.5, center={"lat": 4.57, "lon": -74.29},
        opacity=0.6, title="Mapa de Dominio Nacional"
    )
else:
    # --- VISTA MICRO: BURBUJAS DE DISPUTA TÁCTICA ---
    df_micro = df_filtrado[df_filtrado['Departamento'] == depto_sel]
    
    # ⚡ ACTUALIZACIÓN: Pivoteamos la data para tener columnas por partido
    df_pivot = df_micro.pivot_table(index=['Municipio', 'Latitud', 'Longitud'], 
                                    columns='Afinidad_Politica', 
                                    values='Votos', 
                                    aggfunc='sum').fillna(0)
    
    # Calculamos el total de votos en disputa y quién va ganando
    fuerzas_presentes = [col for col in df_pivot.columns]
    df_pivot['Total Votos Escenario'] = df_pivot[fuerzas_presentes].sum(axis=1)
    df_pivot['Fuerza Dominante'] = df_pivot[fuerzas_presentes].idxmax(axis=1)
    df_pivot = df_pivot.reset_index()
    
    # ⚡ ACTUALIZACIÓN: Configuración milimétrica del cuadro emergente (Tooltip)
    # Ocultamos lat/lon y mostramos el resumen de fuerzas
    hover_dict = {'Latitud': False, 'Longitud': False, 'Fuerza Dominante': True, 'Total Votos Escenario': ':,'}
    for fuerza in fuerzas_presentes:
        hover_dict[fuerza] = ':,' # El ':,' le pone separador de miles a los votos

    fig = px.scatter_mapbox(
        df_pivot, lat="Latitud", lon="Longitud", size="Total Votos Escenario",
        color="Fuerza Dominante",
        color_discrete_map=color_map,
        hover_name="Municipio", 
        hover_data=hover_dict,
        size_max=35, zoom=6.5,
        mapbox_style="carto-positron", title=f"Radiografía de Dispersión en {depto_sel}"
    )

fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=600)
st.plotly_chart(fig, use_container_width=True)

# 4. Tabla de Inteligencia Actualizada
st.subheader(f"📊 Tabla de Control: {depto_sel}")
if depto_sel != "NACIONAL":
    # Mostramos la tabla pivoteada para leer fácilmente los resultados por municipio
    columnas_mostrar = ['Municipio', 'Fuerza Dominante', 'Total Votos Escenario'] + fuerzas_presentes
    df_mostrar = df_pivot[columnas_mostrar].sort_values('Total Votos Escenario', ascending=False)
    st.dataframe(df_mostrar.head(15).style.format({col: "{:,.0f}" for col in fuerzas_presentes + ['Total Votos Escenario']}), use_container_width=True)