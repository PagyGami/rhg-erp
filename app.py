import streamlit as st
import pandas as pd
from datetime import date, datetime
from supabase import create_client

# KEY NUEVA Y FUNCIONANDO 100 %
supabase = create_client(
    "https://llatouvgqplaxvwjfyhl.supabase.co",
    "sb_publishable_PLesx6f6D6H2G4v00dbbdw_B6DXylNa"
)

# ============= LOGIN =============
if "logged" not in st.session_state:
    st.session_state.logged = False

if not st.session_state.logged:
    with st.sidebar:
        try: st.image("logo_rhg.jpg", width=180)
        except: st.title("RHG Laboratorios")
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        if st.button("Entrar", type="primary"):
            if (user == "pablo" and pwd == "lumilife2026") or (user == "lab" and pwd == "produccion"):
                st.session_state.logged = True
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    try: st.image("fondo_erp.jpg", use_column_width=True)
    except: pass
    st.stop()

st.sidebar.success("¡Conectado!")

# LOGO EN ESQUINA SUPERIOR DERECHA - VERSIÓN ÉPICA
logo_col = st.columns([5, 1.3])[1]  # crea una columna chiquita a la derecha
with logo_col:
    try:
        st.image("logo_rhg.jpg", width=140, use_column_width=True)
    except:
        st.markdown(
            """
            <div style="text-align: right; padding: 10px;">
                <h2 style="color: #E91E63;">RHG</h2>
            </div>
            """,
            unsafe_allow_html=True
        )

st.title("RHG Laboratorios - ERP")

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

# ==================== INVENTARIO ====================
with tab1:
    st.header("Control Total de Materia Prima y Empaque")
    try:
        df = pd.DataFrame(supabase.table("ingredientes").select("*").order("nombre").execute().data)
    except Exception as e:
        st.error("Error de conexión")
        st.code(str(e))
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
        use_container_width=True, hide_index=True,
        column_config={
            "stock_actual": st.column_config.NumberColumn("Stock Actual", min_value=0),
            "stock_seguridad": st.column_config.NumberColumn("Stock Seguridad", min_value=0)
        }
    )

    if st.button("GUARDAR CAMBIOS", type="primary"):
        for _, r in edited.iterrows():
            supabase.table("ingredientes").update({
                "stock_actual": float(r["stock_actual"]),
                "stock_seguridad": float(r["stock_seguridad"])
            }).eq("nombre", r["nombre"]).execute()
        st.success("¡Todo actualizado!")
        st.rerun()

    st.subheader("Producto Terminado en Almacén")
    try:
        pt = supabase.table("producto_terminado").select("codigo,nombre,cantidad_en_almacen,lote").eq("status","En almacén").execute().data
        if pt:  # ← Aquí estaba el error
            st.dataframe(pt, use_container_width=True)
        else:
            st.info("No hay stock de producto terminado")
    except:
        st.info("Sin datos de producto terminado")

# ==================== REGISTRAR P.I. ====================
with tab2:
    st.subheader("Registrar Producto Intermedio")
    with st.form("pi"):
        lote = st.text_input("Lote P.I.")
        prod = st.selectbox("Producto", list(PRODUCTOS.values()))
        kg = st.number_input("Kg producidos", min_value=0.0)
        if st.form_submit_button("Registrar"):
            supabase.table("producto_intermedio").insert({
                "lote_pi": lote,
                "producto_nombre": prod,
                "kg_producidos": kg,
                "fecha_produccion": str(date.today()),
                "status": "En proceso"
            }).execute()
            st.success("P.I. registrado")

# ==================== PRODUCCIÓN MÁGICA ====================
with tab3:
    st.title("PRODUCCIÓN MÁGICA - 150 FRASCOS EN 1 CLIC")
    codigo = st.selectbox("Producto", options=list(PRODUCTOS.keys()), format_func=lambda x: PRODUCTOS[x])
    lote_manual = st.text_input("Lote (opcional)")

    if st.button("PRODUCIR 150 FRASCOS", type="primary"):
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
        st.success(f"150 frascos de {PRODUCTOS[codigo]} listos! → Lote {lote_final}")

st.caption("RHG Laboratorios © 2025 - Hecho con amor por Pablo")
