import streamlit as st
import pandas as pd
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Sistema Académico 2026", layout="wide")

# Título y Diseño
st.title("☁️ Sistema de Gestión de Disponibilidad Docente")
st.markdown("""
**Instrucciones:**
1. Abre la barra lateral (izquierda) con la flechita `>`.
2. Arrastra los archivos Excel de los docentes.
3. El sistema unificará todo automáticamente.
""")

# --- FUNCIÓN INTELIGENTE DE PROCESAMIENTO ---
@st.cache_data(show_spinner=False)
def procesar_archivos(uploaded_files):
    lista_disponibilidad = []
    
    # Mapeo de columnas según tu formato (Columna 1 a 6 son los días)
    dias_map = {1: "LUNES", 2: "MARTES", 3: "MIÉRCOLES", 4: "JUEVES", 5: "VIERNES", 6: "SÁBADO"}
    
    progreso = st.progress(0)
    total = len(uploaded_files)
    
    for i, archivo in enumerate(uploaded_files):
        try:
            # Leemos el archivo directamente de la memoria
            df = pd.read_excel(archivo, header=None)
            
            # 1. BUSCAR NOMBRE DEL DOCENTE
            nombre_docente = "Desconocido"
            # Buscamos en las primeras 20 filas
            for fila in range(0, 20):
                texto_celda = str(df.iloc[fila, 0])
                if "Apellidos y Nombres" in texto_celda:
                    # Buscamos el nombre en columnas a la derecha (C, D, E...)
                    for col in [2, 3, 4, 5]:
                        if col < df.shape[1] and pd.notna(df.iloc[fila, col]):
                            val = str(df.iloc[fila, col]).strip()
                            if len(val) > 2: # Validación simple
                                nombre_docente = val
                                break
                    break
            
            # Si no halló nombre dentro del excel, usa el nombre del archivo
            if nombre_docente == "Desconocido":
                nombre_docente = archivo.name.replace(".xlsx", "")

            # 2. BUSCAR LAS "X"
            # Recorremos buscando patrones de hora
            for idx, row in df.iterrows():
                celda_hora = str(row[0])
                # Detectamos si la celda parece una hora (ej: "08:00 a 08:45")
                if " a " in celda_hora and ":" in celda_hora:
                    for col_idx, dia_nombre in dias_map.items():
                        if col_idx < df.shape[1]:
                            valor = str(row[col_idx]).upper()
                            # Si hay marca de disponibilidad
                            if "X" in valor or "SI" in valor or "DISP" in valor:
                                lista_disponibilidad.append({
                                    "Docente": nombre_docente,
                                    "Día": dia_nombre,
                                    "Hora": celda_hora,
                                    "Estado": "DISPONIBLE"
                                })
        except Exception as e:
            # Si un archivo falla, no detenemos todo, solo avisamos
            st.toast(f"Error en {archivo.name}: {e}", icon="⚠️")
        
        # Actualizar barra
        progreso.progress((i + 1) / total)
            
    progreso.empty()
    return pd.DataFrame(lista_disponibilidad)

# --- INTERFAZ ---
with st.sidebar:
    st.header("📂 Carga de Datos")
    st.info("Sube aquí los archivos Excel de disponibilidad.")
    archivos_subidos = st.file_uploader(
        "Arrastra los archivos aquí:", 
        type=["xlsx"], 
        accept_multiple_files=True
    )

if archivos_subidos:
    with st.spinner('Procesando archivos...'):
        df_total = procesar_archivos(archivos_subidos)
    
    if not df_total.empty:
        st.success(f"✅ Se cargaron **{df_total['Docente'].nunique()} docentes** correctamente.")
        st.divider()
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("### 🔍 Buscador")
            lista_docentes = sorted(df_total["Docente"].unique())
            docente_sel = st.selectbox("Selecciona un Docente:", lista_docentes)
        
        with col2:
            # Filtrar y Pivotear
            df_filtrado = df_total[df_total["Docente"] == docente_sel]
            matriz = df_filtrado.pivot_table(index="Hora", columns="Día", values="Estado", aggfunc='first')
            
            # Ordenar
            dias_orden = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO"]
            cols = [d for d in dias_orden if d in matriz.columns]
            matriz = matriz[cols]
            
            # Estilos
            def pintar_verde(val):
                return 'background-color: #28a745; color: white' if val == "DISPONIBLE" else ''

            st.markdown(f"#### Disponibilidad de: **{docente_sel}**")
            st.dataframe(matriz.style.map(pintar_verde), use_container_width=True, height=500)
            
    else:
        st.warning("⚠️ No se encontraron marcas 'X' en los archivos subidos. Revisa el formato.")
else:
    st.info("👈 Esperando archivos... Usa el panel de la izquierda.")
