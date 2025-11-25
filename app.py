import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from supabase import create_client

# ===== CONFIG SUPABASE =====
url = "https://llatouvgqplaxvwjfyhl.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxsYXRvdXZncXBsYXh2d2pmeWhsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwMjAxMzYsImV4cCI6MjA3OTU5NjEzNg.oK7K0rEikk6FB6Dt8-uSuXAN-xiOfxiILjaIqWbo6WU"
supabase = create_client(url, key)

# ===== LOGIN =====
if "logged" not in st.session_state:
    st.session_state.logged = False

def login():
    st.sidebar.title("Login RHG")
    user = st.sidebar.text_input("Usuario")
    pwd = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Entrar"):
        if user == "pablo" and pwd == "lumilife2026":
            st.session_state.logged = True
            st.session_state.role = "admin"
            st.rerun()
        elif user == "lab" and pwd == "produccion":
            st.session_state.logged = True
            st.session_state.role = "lab"
            st.rerun()
        else:
            st.sidebar.error("Incorrecto")

if not st.session_state.logged:
    login()
    st.stop()

st.sidebar.success(f"Rol: {st.session_state.role.upper()}")

# ===== TUS 10 PRODUCTOS REALES =====
PRODUCTOS_REALES = [
    "Colágeno Lumivit Maracuyá 4kg",
    "Colágeno Lumivit Natural 4kg",
    "Colágeno Lumihass Arándano 4kg",
    "Colágeno Lumihass Naranja 4kg",
    "Colágeno Lumihass Fresa 4kg",
    "Flex Max 60 tabletas Lumivit",
    "Vitamina C Lumivit 90 cápsulas",
    "Detox 500mg 90 cápsulas",
    "Magnesio Complex 60 cápsulas",
    "Detox Lumihass 30/60 cápsulas"
]

# ===== APP PRINCIPAL =====
st.set_page_config(layout="wide", page_title="RHG Laboratorios ERP")
st.title("RHG Laboratorios - ERP")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Registrar P.I.", "Convertir P.T.", "Entregas", "Producción Mágica"])

# ==================== TAB 1 - DASHBOARD ====================
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Inventario Materia Prima y Empaque")
        data = supabase.table("ingredientes").select("*").execute()
        df_mp = pd.DataFrame(data.data)
        st.dataframe(df_mp, use_container_width=True)

    with col2:
        st.subheader("Producto Terminado en Almacén")
        pt = supabase.table("producto_terminado").select("*").eq("status", "En almacén").execute()
        df_pt = pd.DataFrame(pt.data) if pt.data else pd.DataFrame(columns=["codigo", "nombre", "cantidad_en_almacen", "lote"])
        st.dataframe(df_pt, use_container_width=True)

# ==================== TAB 2 - REGISTRAR P.I. ====================
with tab2:
    st.subheader("Registrar Producto Intermedio (P.I.)")
    with st.form("form_pi"):
        lote_pi = st.text_input("Lote P.I.")
        producto_pi = st.selectbox("Producto", PRODUCTOS_REALES)
        kg = st.number_input("Kg producidos", min_value=0.0, step=0.1)
        fecha = st.date_input("Fecha de producción", date.today())
        if st.form_submit_button("Registrar P.I."):
            supabase.table("producto_intermedio").insert({
                "lote_pi": lote_pi,
                "producto_nombre": producto_pi,
                "kg_producidos": float(kg),
                "fecha_produccion": str(fecha),
                "status": "En proceso"
            }).execute()
            st.success("P.I. registrado correctamente")

# ==================== TAB 3 - CONVERTIR A P.T. ====================
with tab3:
    st.subheader("Convertir P.I. → Producto Terminado")
    try:
        pi_pendientes = supabase.table("producto_intermedio").select("*").eq("status", "En proceso").execute().data
    except:
        pi_pendientes = []

    if pi_pendientes:
        lote_elegido = st.selectbox("Seleccionar lote P.I.", [p["lote_pi"] for p in pi_pendientes])
        info_pi = next(p for p in pi_pendientes if p["lote_pi"] == lote_elegido)

        with st.form("form_convertir"):
            lote_nuevo = st.text_input("Lote Producto Terminado")
            envases = st.number_input("Cantidad de envases terminados", min_value=1)
            if st.form_submit_button("Convertir a P.T."):
                supabase.table("producto_terminado").upsert({
                    "codigo": info_pi["producto_nombre"].split()[-1][:-3],  # extrae código corto
                    "nombre": info_pi["producto_nombre"],
                    "cantidad_en_almacen": envases,
                    "lote": lote_nuevo,
                    "fecha_produccion": info_pi["fecha_produccion"],
                    "status": "En almacén"
                }, on_conflict="lote").execute()

                supabase.table("producto_intermedio").update({"status": "Convertido"}).eq("lote_pi", lote_elegido).execute()
                st.success("Convertido a Producto Terminado")
    else:
        st.info("No hay P.I. en proceso")

# ==================== TAB 4 - ENTREGAS ====================
with tab4:
    st.subheader("Registrar Entrega")
    pt_disponibles = supabase.table("producto_terminado").select("*").eq("status", "En almacén").execute().data
    if pt_disponibles:
        lote_entrega = st.selectbox("Lote a entregar", [p["lote"] for p in pt_disponibles])
        with st.form("form_entrega"):
            cliente = st.text_input("Nombre del cliente")
            responsable = st.selectbox("Responsable", ["Juan", "Pedro", "Ana", "María"])
            cantidad = st.number_input("Envases entregados", min_value=1)
            if st.form_submit_button("Registrar entrega"):
                supabase.table("entregas_clientes").insert({
                    "lote_pt": lote_entrega,
                    "cliente_nombre": cliente,
                    "responsable_entrega": responsable,
                    "cantidad_envases": cantidad,
                    "fecha_entrega": date.today()
                }).execute()
                supabase.table("producto_terminado").update({"status": "Entregado"}).eq("lote", lote_entrega).execute()
                st.success("Entrega registrada")
    else:
        st.info("No hay P.T. en almacén")

# ==================== TAB 5 - PRODUCCIÓN MÁGICA ====================
with tab5:
    st.title("PRODUCCIÓN MÁGICA - 150 FRASCOS EN 1 CLIC")

    productos_dict = {
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

    producto_codigo = st.selectbox("Producto a producir", options=list(productos_dict.keys()), format_func=lambda x: productos_dict[x])
    lote_manual = st.text_input("Lote (opcional)")

    if st.button("CALCULAR Y PRODUCIR 150 FRASCOS", type="primary"):
        with st.spinner("Revisando inventario..."):
            try:
                pt_id = supabase.table("producto_terminado").select("id").eq("codigo", producto_codigo).execute().data[0]["id"]
                formula = supabase.table("formulas")\
                    .select("ingrediente_id, cantidad_por_unidad, unidad_medida, ingredientes(nombre, stock_actual)")\
                    .eq("producto_id", pt_id).execute().data

                necesidades = []
                faltan = False
                for item in formula:
                    req = item["cantidad_por_unidad"] * 150
                    act = item["ingredientes"]["stock_actual"] or 0
                    if req > act:
                        faltan = True
                    necesidades.append({
                        "Ingrediente": item["ingredientes"]["nombre"],
                        "Necesitas": f"{req:,.2f} {item['unidad_medida']}",
                        "Tienes": f"{act:,.2f} {item['unidad_medida']}",
                        "Falta": req > act
                    })

                df = pd.DataFrame(necesidades)
                if faltan:
                    st.error("TE FALTAN INGREDIENTES")
                    st.dataframe(df.style.apply(lambda x: ["background: #ffcccc" if v else "" for v in x["Falta"]], axis=1))
                else:
                    st.success("TODO LISTO")
                    st.dataframe(df)

                    if st.button("PRODUCIR LOS 150 FRASCOS AHORA", type="primary"):
                        with st.spinner("Produciendo..."):
                            for item in formula:
                                supabase.rpc("descontar_stock", {
                                    "ingrediente_id": item["ingrediente_id"],
                                    "cantidad": item["cantidad_por_unidad"] * 150
                                }).execute()

                            lote_final = lote_manual or f"L{datetime.now().strftime('%Y%m%d')}"
                            supabase.table("producto_terminado").upsert({
                                "codigo": producto_codigo,
                                "nombre": productos_dict[producto_codigo],
                                "cantidad_en_almacen": 150,
                                "lote": lote_final,
                                "fecha_produccion": datetime.now().isoformat(),
                                "fecha_vencimiento": (datetime.now() + timedelta(days=730)).isoformat(),
                                "status": "En almacén"
                            }, on_conflict="codigo").execute()

                        st.balloons()
                        st.success(f"¡150 FRASCOS DE {productos_dict[producto_codigo]} LISTOS CON LOTE {lote_final}!")

            except Exception as e:
                st.error("Error: Asegúrate de tener fórmulas cargadas para este producto")
