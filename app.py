import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from supabase import create_client

# ===== SUPABASE =====
supabase = create_client(
    "https://llatouvgqplaxvwjfyhl.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxsYXRvdXZncXBsYXh2d2pmeWhsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwMjAxMzYsImV4cCI6MjA3OTU5NjEzNi5d.oK7K0rEikk6FB6Dt8-uSuXAN-xiOfxiILjaIqWbo6WU"
)

# ===== LOGIN =====
if "logged" not in st.session_state:
    st.session_state.logged = False

def login():
    st.sidebar.title("Login RHG")
    user = st.sidebar.text_input("Usuario")
    pwd = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Entrar"):
        if user == "pablo" and pwd == "lumilife2026" or user == "lab" and pwd == "produccion":
            st.session_state.logged = True
            st.rerun()

if not st.session_state.logged:
    login()
    st.stop()

st.sidebar.success("¡Conectado!")

# ===== TUS PRODUCTOS REALES =====
PRODUCTOS_DICT = {
    "COL-MAR": "Colágeno Lumivit Maracuyá 1.2 kg",
    "COL-NAT": "Colágeno Lumivit Natural 1.2 kg",
    "COL-ARA": "Colágeno Lumihass Arándano 1.2 kg",
    "COL-NAR": "Colágeno Lumihass Naranja 1.2 kg",
    "COL-FRE": "Colágeno Lumihass Fresa 1.2 kg",
    "FLEXMAX60": "Flex Max 60 tabletas Lumivit",
    "VITC90": "Vitamina C Lumivit 90 cápsulas",
    "DTX500": "Detox 500mg 90 cápsulas",
    "MAG60": "Magnesio Complex 60 cápsulas",
    "DTX3060": "Detox Lumihass 30/60 cápsulas"
}

# ===== APP =====
st.set_page_config(layout="wide", page_title="RHG ERP")
st.title("RHG Laboratorios - ERP")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Registrar P.I.", "Convertir P.T.", "Entregas", "Producción Mágica"])

# ==================== DASHBOARD ====================
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Inventario Materia Prima y Empaque")
        ingredientes = supabase.table("ingredientes").select("*").execute().data
        if ingredientes:
            df_ing = pd.DataFrame(ingredientes)
            st.dataframe(df_ing, use_container_width=True)
        else:
            st.info("No hay ingredientes registrados aún")
    
    with col2:
        st.subheader("Producto Terminado en Almacén")
        pt = supabase.table("producto_terminado").select("*").eq("status", "En almacén").execute().data
        if pt:
            df_pt = pd.DataFrame(pt)
            st.dataframe(df_pt[["codigo", "nombre", "cantidad_en_almacen", "lote"]], use_container_width=True)
        else:
            st.info("No hay producto terminado en almacén")

# ==================== REGISTRAR P.I. ====================
with tab2:
    st.subheader("Registrar Producto Intermedio (P.I.)")
    with st.form("pi_form"):
        lote = st.text_input("Lote P.I.")
        producto = st.selectbox("Producto", list(PRODUCTOS_DICT.values()))
        kg = st.number_input("Kg producidos", min_value=0.0)
        if st.form_submit_button("Registrar"):
            supabase.table("producto_intermedio").insert({
                "lote_pi": lote,
                "producto_nombre": producto,
                "kg_producidos": kg,
                "fecha_produccion": str(date.today()),
                "status": "En proceso"
            }).execute()
            st.success("P.I. registrado")

# ==================== PRODUCCIÓN MÁGICA (la que más quieres) ====================
with tab5:
    st.title("PRODUCCIÓN MÁGICA - 150 FRASCOS EN 1 CLIC")
    
    codigo = st.selectbox("Producto a producir", options=list(PRODUCTOS_DICT.keys()), 
                         format_func=lambda x: PRODUCTOS_DICT[x])
    lote_manual = st.text_input("Lote (opcional - si no pones nada se genera automático)")

    if st.button("CALCULAR Y PRODUCIR 150 FRASCOS", type="primary"):
        with st.spinner("Revisando inventario y fórmulas..."):
            # 1. Buscar ID del producto terminado
            pt_id_resp = supabase.table("producto_terminado").select("id").eq("codigo", codigo).execute()
            if not pt_id_resp.data:
                st.error(f"No existe el producto {codigo} en la tabla producto_terminado")
                st.stop()
            pt_id = pt_id_resp.data[0]["id"]

            # 2. Traer fórmula
            formula = supabase.table("formulas")\
                .select("ingrediente_id, cantidad_por_unidad, unidad_medida, ingredientes(nombre, stock_actual)")\
                .eq("producto_id", pt_id).execute().data

            if not formula:
                st.error("Este producto no tiene fórmula cargada aún")
                st.stop()

            # 3. Revisar inventario
            faltan = []
            necesidades = []
            for f in formula:
                req = f["cantidad_por_unidad"] * 150
                act = f["ingredientes"]["stock_actual"] or 0
                necesidades.append({
                    "Ingrediente": f["ingredientes"]["nombre"],
                    "Necesitas": f"{req:,.2f} {f['unidad_medida']}",
                    "Tienes": f"{act:,.2f} {f['unidad_medida']}"
                })
                if req > act:
                    faltan.append(f["ingredientes"]["nombre"])

            df = pd.DataFrame(necesidades)

            if faltan:
                st.error(f"TE FALTAN {len(faltan)} INGREDIENTES:")
                st.dataframe(df, use_container_width=True)
            else:
                st.success("¡TODO LISTO! Puedes producir")
                st.dataframe(df, use_container_width=True)

                if st.button("PRODUCIR LOS 150 FRASCOS AHORA", type="primary"):
                    with st.spinner("Descontando y creando lote..."):
                        # Descontar ingredientes
                        for f in formula:
                            supabase.rpc("descontar_stock", {
                                "ingrediente_id": f["ingrediente_id"],
                                "cantidad": f["cantidad_por_unidad"] * 150
                            }).execute()

                        # Crear lote terminado
                        lote_final = lote_manual or f"L{date.today():%Y%m%d}"
                        supabase.table("producto_terminado").upsert({
                            "codigo": codigo,
                            "nombre": PRODUCTOS_DICT[codigo],
                            "cantidad_en_almacen": 150,
                            "lote": lote_final,
                            "fecha_produccion": datetime.now().isoformat(),
                            "fecha_vencimiento": (datetime.now() + timedelta(days=730)).isoformat(),
                            "status": "En almacén"
                        }, on_conflict="codigo").execute()

                    st.balloons()
                    st.success(f"¡150 FRASCOS DE {PRODUCTOS_DICT[codigo]} LISTOS! Lote: {lote_final}")

# Las otras pestañas las dejamos por ahora
with tab3:
    st.write("Convertir P.I. → P.T. (próximamente)")
with tab4:
    st.write("Entregas (próximamente)")
