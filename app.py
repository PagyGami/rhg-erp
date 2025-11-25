import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from supabase import create_client

# ... (imports y conexión a Supabase se mantienen arriba)

# ============= LOGIN CON LOGO Y FONDO =============
if "logged" not in st.session_state:
    st.session_state.logged = False

if not st.session_state.logged:
    
    # --- BARRA LATERAL (Login) ---
    with st.sidebar:
        try:
            st.image("logo_rhg.jpg", width=150) 
        except:
            st.title("RHG Laboratorios") 
            
        st.subheader("Acceso al Sistema ERP")
        
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")

        if st.button("Entrar"):
            if user == "pablo" and pwd == "lumilife2026":
                st.session_state.logged = True
                st.session_state.role = "admin"
                st.rerun()
            elif user == "lab" and pwd == "produccion":
                st.session_state.logged = True
                st.session_state.role = "lab"
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

    # --- CUERPO PRINCIPAL (Parte blanca) ---
    # Aquí puedes agregar el fondo o la imagen principal que quieres que se vea.
    st.image("fondo_erp.jpg", 
             caption="RHG Laboratorios | Control total de producción.", 
             use_column_width=True) # use_column_width=True para que ocupe todo el ancho
    
    # Detiene la ejecución de la app principal hasta hacer login
    st.stop() 

st.sidebar.success(f"¡Conectado como {st.session_state.role.upper()}!")


# ============= TUS PRODUCTOS REALES (Mantenemos esta lista para el resto del código) =============
PRODUCTOS = {
    "COL-MAR": "Colágeno Lumivit Maracuyá 4kg",
    "COL-NAT": "Colágeno Lumivit Natural 4kg",
    "COL-ARA": "Colágeno Lumihass Arándano 4kg",
    "COL-NAR": "Colágeno Lumihass Naranja 4kg",
    "COL-FRE": "Colágeno Lumihass Fresa 4kg",
    "FLEXMAX60": "Flex Max 60 tabletas Lumivit",
    "VITC90": "Vitamina C Lumivit 90 cápsulas",
    "DTX500": "Detox 500mg 90 cápsulas",
    "MAG60": "Magnesio Complex 60 cápsulas",
    "DTX3060": "Detox Lumihass 30/60 cápsulas"
}

# (El resto del código de la aplicación irá después de este punto)

# ============= TUS 10 PRODUCTOS REALES =============
PRODUCTOS = {
    "COL-MAR": "Colágeno Lumivit Maracuyá 4kg",
    "COL-NAT": "Colágeno Lumivit Natural 4kg",
    "COL-ARA": "Colágeno Lumihass Arándano 4kg",
    "COL-NAR": "Colágeno Lumihass Naranja 4kg",
    "COL-FRE": "Colágeno Lumihass Fresa 4kg",
    "FLEXMAX60": "Flex Max 60 tabletas Lumivit",
    "VITC90": "Vitamina C Lumivit 90 cápsulas",
    "DTX500": "Detox 500mg 90 cápsulas",
    "MAG60": "Magnesio Complex 60 cápsulas",
    "DTX3060": "Detox Lumihass 30/60 cápsulas"
}

# ============= APP =============
st.set_page_config(layout="wide", page_title="RHG ERP")
st.title("RHG Laboratorios - ERP")

tab1, tab2, tab5 = st.tabs(["Dashboard", "Registrar P.I.", "Producción Mágica"])

# ============= DASHBOARD =============
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Inventario Materia Prima y Empaque")
        try:
            # ESTA ES LA LÍNEA QUE ARREGLA TODO (todo en minúsculas)
            ingredientes = supabase.table("ingredientes").select("*").execute().data
            if ingredientes:
                df = pd.DataFrame(ingredientes)
                st.dataframe(df[["nombre", "stock_actual", "unidad_medida"]], use_container_width=True)
            else:
                st.info("No hay ingredientes registrados")
        except Exception as e:
            st.error("Error al cargar ingredientes. Revisa el nombre de la tabla en Supabase (debe ser exactamente 'ingredientes')")

    with col2:
        st.subheader("Producto Terminado")
        try:
            pt = supabase.table("producto_terminado").select("*").eq("status", "En almacén").execute().data
            if pt:
                df_pt = pd.DataFrame(pt)
                st.dataframe(df_pt[["codigo", "nombre", "cantidad_en_almacen", "lote"]], use_container_width=True)
            else:
                st.info("No hay productos terminados")
        except:
            st.info("Tabla producto_terminado vacía o no existe aún")

# ============= REGISTRAR P.I. =============
with tab2:
    st.subheader("Registrar Producto Intermedio")
    with st.form("pi_form"):
        lote = st.text_input("Lote P.I.")
        producto = st.selectbox("Producto", list(PRODUCTOS.values()))
        kg = st.number_input("Kg producidos", min_value=0.0)
        if st.form_submit_button("Registrar P.I."):
            try:
                supabase.table("producto_intermedio").insert({
                    "lote_pi": lote,
                    "producto_nombre": producto,
                    "kg_producidos": kg,
                    "fecha_produccion": str(date.today()),
                    "status": "En proceso"
                }).execute()
                st.success("P.I. registrado correctamente")
            except:
                st.error("Error al registrar P.I. ¿Existe la tabla producto_intermedio?")

# ============= PRODUCCIÓN MÁGICA (LA QUE MÁS QUIERES) =============
with tab5:
    st.title("PRODUCCIÓN MÁGICA - 150 FRASCOS EN 1 CLIC")
    
    codigo = st.selectbox("Producto", options=list(PRODUCTOS.keys()), format_func=lambda x: PRODUCTOS[x])
    lote_manual = st.text_input("Lote (opcional)")

    if st.button("PRODUCIR 150 FRASCOS", type="primary"):
        with st.spinner("Produciendo lote..."):
            try:
                # Crear o actualizar producto terminado
                lote_final = lote_manual or f"L{date.today():%Y%m%d}"
                supabase.table("producto_terminado").upsert({
                    "codigo": codigo,
                    "nombre": PRODUCTOS[codigo],
                    "cantidad_en_almacen": 150,
                    "lote": lote_final,
                    "fecha_produccion": datetime.now().isoformat(),
                    "fecha_vencimiento": (datetime.now() + timedelta(days=730)).isoformat(),
                    "status": "En almacén"
                }, on_conflict="codigo").execute()

                st.balloons()
                st.success(f"¡150 FRASCOS DE {PRODUCTOS[codigo]} LISTOS!\nLote: {lote_final}")
                
            except Exception as e:
                st.error("Error: Asegúrate de tener las tablas y fórmulas cargadas")

st.caption("RHG Laboratorios © 2025 - Hecho con amor por Pablo")
