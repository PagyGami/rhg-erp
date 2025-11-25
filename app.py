import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from supabase import create_client

# ============= CONEXIÓN SUPABASE (SIN .schema) =============
supabase = create_client(
    "https://llatouvgqplaxvwjfyhl.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxsYXRvdXZncXBsYXh2d2pmeWhsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwMjAxMzYsImV4cCI6MjA3OTU5NjEzNi5d.oK7K0rEikk6FB6Dt8-uSuXAN-xiOfxiILjaIqWbo6WU"
)

# ============= LOGIN =============
if "logged" not in st.session_state:
    st.session_state.logged = False

if not st.session_state.logged:
    with st.sidebar:
        try:
            st.image("logo_rhg.jpg", width=180)
        except:
            st.title("RHG Laboratorios")
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        if st.button("Entrar", type="primary"):
            if (user == "pablo" and pwd == "lumilife2026") or (user == "lab" and pwd == "produccion"):
                st.session_state.logged = True
                st.rerun()
            else:
                st.error("Error")
    try:
        st.image("fondo_erp.jpg", use_column_width=True)
    except:
        pass
    st.stop()

st.sidebar.success("¡Conectado!")

# ============= PRODUCTOS =============
PRODUCTOS = {
    "COL-MAR": "Colágeno Lumivit Maracuyá 4kg", "COL-NAT": "Colágeno Lumivit Natural 4kg",
    "COL-ARA": "Colágeno Lumihass Arándano 4kg", "COL-NAR": "Colágeno Lumihass Naranja 4kg",
    "COL-FRE": "Colágeno Lumihass Fresa 4kg", "FLEXMAX60": "Flex Max 60 tabletas Lumivit",
    "VITC90": "Vitamina C Lumivit 90 cápsulas", "DTX500": "Detox 500mg 90 cápsulas",
    "MAG60": "Magnesio Complex 60 cápsulas", "DTX3060": "Detox Lumihass 30/60 cápsulas"
}

st.set_page_config(page_title="RHG ERP", layout="wide")
st.title("RHG Laboratorios - ERP")

tab1, tab2, tab3 = st.tabs(["Inventario MP/ME", "Registrar P.I.", "Producción Mágica"])

# ==================== INVENTARIO MP/ME ====================
with tab1:
    st.header("Control Total de Materia Prima y Empaque")

    try:
        # SIN .schema → funciona en todas las versiones
        resp = supabase.table("ingredientes").select("*").order("nombre").execute()
        ingredientes = resp.data
        df = pd.DataFrame(ingredientes)
    except Exception as e:
        st.error("Error al cargar ingredientes")
        st.write(e)
        st.stop()

    col1, col2 = st.columns([3,1])
    with col1:
        buscar = st.text_input("Buscar ingrediente")
        if buscar:
            df = df[df["nombre"].str.contains(buscar, case=False, na=False)]

    with col2:
        with st.expander("Nuevo ingrediente"):
            n = st.text_input("Nombre")
            t = st.selectbox("Tipo", ["MP","ME"])
            u = st.selectbox("Unidad", ["g","kg","piezas","ml"])
            s = st.number_input("Stock seguridad", min_value=0)
            if st.button("Crear"):
                supabase.table("ingredientes").insert({
                    "nombre": n, "tipo": t, "stock_actual": 0,
                    "stock_seguridad": s, "unidad_medida": u
                }).execute()
                st.success("¡Creado!")
                st.rerun()

    edited = st.data_editor(
        df[["nombre","tipo","stock_actual","stock_seguridad","unidad_medida"]],
        column_config={
            "stock_actual": st.column_config.NumberColumn("Stock Actual", min_value=0),
            "stock_seguridad": st.column_config.NumberColumn("Stock Seguridad", min_value=0)
        },
        use_container_width=True,
        hide_index=True
    )

    if st.button("GUARDAR CAMBIOS", type="primary"):
        cambios = 0
        for _, row in edited.iterrows():
            orig = df[df["nombre"] == row["nombre"]].iloc[0]
            if orig["stock_actual"] != row["stock_actual"] or orig["stock_seguridad"] != row["stock_seguridad"]:
                supabase.table("ingredientes").update({
                    "stock_actual": float(row["stock_actual"]),
                    "stock_seguridad": float(row["stock_seguridad"])
                }).eq("nombre", row["nombre"]).execute()
                cambios += 1
        if cambios:
            st.success(f"¡Guardados {cambios} cambios!")
            st.rerun()
        else:
            st.info("Sin cambios")

    st.subheader("Producto Terminado")
    try:
        pt = supabase.table("producto_terminado").select("codigo,nombre,cantidad_en_almacen,lote").eq("status","En almacén").execute().data
        st.dataframe(pt, use_container_width=True) if pt else st.info("Sin stock")
    except:
        st.info("Sin producto terminado")

# ==================== REGISTRAR P.I. ====================
with tab2:
    st.subheader("Registrar Producto Intermedio")
    with st.form("pi"):
        lote = st.text_input("Lote P.I.")
        prod = st.selectbox("Producto", list(PRODUCTOS.values()))
        kg = st.number_input("Kg", min_value=0.0)
        if st.form_submit_button("Registrar"):
            supabase.table("producto_intermedio").insert({
                "lote_pi": lote, "producto_nombre": prod,
                "kg_producidos": kg, "fecha_produccion": str(date.today()),
                "status": "En proceso"
            }).execute()
            st.success("¡Registrado!")

# ==================== PRODUCCIÓN MÁGICA ====================
with tab3:
    st.title("PRODUCCIÓN MÁGICA - 150 FRASCOS EN 1 CLIC")
    codigo = st.selectbox("Producto", options=list(PRODUCTOS.keys()), format_func=lambda x: PRODUCTOS[x])
    lote = st.text_input("Lote (opcional)")

    if st.button("PRODUCIR 150 FRASCOS", type="primary"):
        lote_final = lote or f"L{date.today():%Y%m%d}"
        supabase.table("producto_terminado").upsert({
            "codigo": codigo, "nombre": PRODUCTOS[codigo],
            "cantidad_en_almacen": 150, "lote": lote_final,
            "fecha_produccion": datetime.now().isoformat(),
            "fecha_vencimiento": (datetime.now() + timedelta(days=730)).isoformat(),
            "status": "En almacén"
        }, on_conflict="codigo").execute()
        st.balloons()
        st.success(f"¡150 frascos de {PRODUCTOS[codigo]} listos! Lote {lote_final}")

st.caption("RHG Laboratorios © 2025 - Hecho con amor por Pablo")
