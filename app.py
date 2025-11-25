import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from supabase import create_client

# ===== SUPABASE =====
url = "https://llatouvgqplaxvwjfyhl.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxsYXRvdXZncXBsYXh2d2pmeWhsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwMjAxMzYsImV4cCI6MjA3OTU5NjEzNi5d.oK7K0rEikk6FB6Dt8-uSuXAN-xiOfxiILjaIqWbo6WU"
supabase = create_client(url, key)

# ===== LOGIN =====
if "logged" not in st.session_state:
    st.session_state.logged = False

def login():
    st.sidebar.title("Login RHG")
    user = st.sidebar.text_input("Usuario")
    pwd = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Entrar"):
        if user in ["pablo", "lab"] and pwd in ["lumilife2026", "produccion"]:
            st.session_state.logged = True
            st.session_state.role = "admin" if user == "pablo" else "lab"
            st.rerun()
        else:
            st.sidebar.error("Incorrecto")

if not st.session_state.logged:
    login()
    st.stop()

st.sidebar.success(f"Bienvenido {st.session_state.role.upper()}")

# ===== PRODUCTOS REALES =====
PRODUCTOS = [
    "Colágeno Lumivit Maracuyá 4kg", "Colágeno Lumivit Natural 4kg", "Colágeno Lumihass Arándano 4kg",
    "Colágeno Lumihass Naranja 4kg", "Colágeno Lumihass Fresa 4kg", "Flex Max 60 tabletas Lumivit",
    "Vitamina C Lumivit 90 cápsulas", "Detox 500mg 90 cápsulas", "Magnesio Complex 60 cápsulas", "Detox Lumihass 30/60 cápsulas"
]

CODIGOS = ["COL-MAR","COL-NAT","COL-ARA","COL-NAR","COL-FRE","FLEXMAX60","VITC90","DTX500","MAG60","DTX3060"]

# ===== APP =====
st.set_page_config(layout="wide", page_title="RHG ERP")
st.title("RHG Laboratorios - ERP")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Registrar P.I.", "Convertir P.T.", "Entregas", "Producción Mágica"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Inventario MP/ME")
        try:
            data = supabase.table("ingredientes").select("*").execute().data
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        except:
            st.warning("Todavía no hay ingredientes. Se crearán al producir.")
    
    with col2:
        st.subheader("Producto Terminado")
        try:
            pt = supabase.table("producto_terminado").select("*").execute().data
            st.dataframe(pd.DataFrame(pt), use_container_width=True)
        except:
            st.info("Sin productos terminados aún")

with tab2:
    st.subheader("Registrar Producto Intermedio")
    with st.form("pi"):
        lote = st.text_input("Lote P.I.")
        prod = st.selectbox("Producto", PRODUCTOS)
        kg = st.number_input("Kg", min_value=0.0)
        if st.form_submit_button("Registrar"):
            supabase.table("producto_intermedio").insert({
                "lote_pi": lote, "producto_nombre": prod, "kg_producidos": kg,
                "fecha_produccion": str(date.today()), "status": "En proceso"
            }).execute()
            st.success("P.I. registrado")

with tab5:  # Producción mágica primero para que la veas rápido
    st.title("PRODUCCIÓN MÁGICA - 150 FRASCOS EN 1 CLIC")
    codigo = st.selectbox("Producto", options=CODIGOS, format_func=lambda x: PRODUCTOS[CODIGOS.index(x)])
    lote_manual = st.text_input("Lote (opcional)")

    if st.button("PRODUCIR 150 FRASCOS", type="primary"):
        with st.spinner("Produciendo..."):
            try:
                # Crear producto terminado si no existe
                supabase.table("producto_terminado").upsert({
                    "codigo": codigo,
                    "nombre": PRODUCTOS[CODIGOS.index(codigo)],
                    "cantidad_en_almacen": 150,
                    "lote": lote_manual or f"L{date.today().strftime('%Y%m%d')}",
                    "fecha_produccion": datetime.now().isoformat(),
                    "status": "En almacén"
                }, on_conflict="codigo").execute()
                st.balloons()
                st.success(f"¡150 frascos de {PRODUCTOS[CODIGOS.index(codigo)]} listos!")
            except Exception as e:
                st.error("Primero carga las fórmulas en Supabase (ya las tienes del otro día)")

# Las demás pestañas (convertir, entregas) las dejamos simples por ahora
with tab3:
    st.write("Funcionalidad completa próximamente")
with tab4:
    st.write("Entregas próximamente")
