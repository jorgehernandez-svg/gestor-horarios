import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Sistema Académico 2026", layout="wide")

# Título y Diseño
st.title("☁️ Sistema de Gestión de Disponibilidad Docente")
st.markdown("""
Esta aplicación corre en la nube. 
**Instrucciones:**
1. Abre la barra lateral (izquierda).
2. Arrastra los archivos Excel de los docentes.
3. El sistema unificará todo automáticamente.
""")

# --- FUNCIÓN INTELIGENTE DE PROCESAMIENTO (EL ROBOT) ---
@st.cache_data # Esto hace que sea ultra rápido y no recargue todo el tiempo
def procesar_archivos(uploaded_files):
    lista_disponibilidad = []
    
    # Mapeo de columnas según tu formato (Columna 1 a 6 son los días)
    dias_map = {1: "LUNES", 2: "MARTES", 3: "MIÉRCOLES", 4: "JUEVES", 5: "VIERNES", 6: "SÁBADO"}
    
    progreso = st.progress(0)
    total = len(uploaded_files)
    
    for i, archivo in enumerate(uploaded_files):
        try:
            # Leemos el archivo en memoria
            df = pd.read_excel(archivo, header=None)
            
            # 1. BUSCAR NOMBRE DEL DOCENTE
            # Buscamos en las primeras filas donde dice "Apellidos"
            nombre_docente = "Desconocido"
            for fila in range(0, 20):
                texto_celda = str(df.iloc[fila, 0])
                if "Apellidos y Nombres" in texto_celda:
                    # Intentamos buscar el nombre en las columnas de la derecha
                    posibles_cols = [2, 3, 4, 5]
                    for col in posibles_cols:
                        if col < df.shape[1] and pd.notna(df.iloc[fila, col]):
                            nombre_docente = str(df.iloc[fila, col]).strip()
                            break
                    break
            
            # Si el nombre sigue siendo desconocido, usamos el nombre del archivo
            if nombre_docente == "Desconocido":
                nombre_docente = archivo.name.replace(".xlsx", "")

            # 2. BUSCAR LAS "X" DE DISPONIBILIDAD
            # Recorremos buscando patrones de hora (ej: "08:00 a 08:45")
            for idx, row in df.iterrows():
                celda_hora = str(row[0])
                if " a " in celda_hora and ":" in celda_hora:
                    for col_idx, dia_nombre in dias_map.items():
                        # Verificamos que la columna exista en el excel
                        if col_idx < df.shape[1]:
                            valor = str(row[col_idx]).upper()
                            # Si hay una marca (X, SI, OK, etc.)
                            if "X" in valor or "SI" in valor or "DISP" in valor:
                                lista_disponibilidad.append({
                                    "Docente": nombre_docente,
                                    "Día": dia_nombre,
                                    "Hora": celda_hora,
                                    "Estado": "DISPONIBLE"
                                })
        except Exception as e:
            st.sidebar.error(f"Error en {archivo.name}: {e}")
        
        # Actualizar barra de progreso
        progreso.progress((i + 1) / total)
            
    progreso.empty() # Ocultar barra al terminar
    return pd.DataFrame(lista_disponibilidad)

# --- INTERFAZ DE USUARIO ---

# 1. ZONA DE CARGA (SIDEBAR)
with st.sidebar:
    st.header("📂 Carga de Datos")
    archivos_subidos = st.file_uploader(
        "Sube los Excels de los Docentes aquí (puedes seleccionar 130 a la vez):", 
        type=["xlsx"], 
        accept_multiple_files=True
    )

# 2. LÓGICA PRINCIPAL
if archivos_subidos:
    df_total = procesar_archivos(archivos_subidos)
    
    if not df_total.empty:
        st.success(f"¡Éxito! Se han procesado {df_total['Docente'].nunique()} docentes correctamente.")
        
        # --- BUSCADOR ---
        lista_docentes = sorted(df_total["Docente"].unique())
        docente_sel = st.selectbox("🔍 Buscar Docente:", lista_docentes)
        
        # --- VISUALIZADOR ---
        df_filtrado = df_total[df_total["Docente"] == docente_sel]
        
        # Pivot Table para recrear el horario
        matriz = df_filtrado.pivot_table(index="Hora", columns="Día", values="Estado", aggfunc='first')
        
        # Ordenar columnas y filas
        orden_dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO"]
        cols_presentes = [d for d in orden_dias if d in matriz.columns]
        matriz = matriz[cols_presentes]
        
        # Estilos
        def estilo_verde(val):
            return 'background-color: #d4edda; color: #155724; font-weight: bold; border: 1px solid white' if val == "DISPONIBLE" else ''

        st.subheader(f"Horario de: {docente_sel}")
        st.dataframe(matriz.style.map(estilo_verde), use_container_width=True, height=600)
        
    else:
        st.warning("Se leyeron los archivos pero no se encontraron marcas 'X'. Revisa el formato.")
else:
    st.info("👈 Esperando archivos... Arrástralos en el panel de la izquierda.")