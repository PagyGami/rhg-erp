import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client

# Tus datos de Supabase (no cambies)
url = "https://llatouvgqplaxvwjfyhl.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxsYXRvdXZncXBsYXh2d2pmeWhsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwMjAxMzYsImV4cCI6MjA3OTU5NjEzNn0.oK7K0rEikk6FB6Dt8-uSuXAN-xiOfxiILjaIqWbo6WU"
supabase = create_client(url, key)

# Login simple
if "logged" not in st.session_state:
    st.session_state.logged = False
    st.session_state.role = None

def login():
    st.sidebar.title("🔐 Login RHG")
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
            st.sidebar.error("❌ Incorrecto")

if not st.session_state.logged:
    login()
    st.stop()

st.sidebar.success(f"Rol: {st.session_state.role}")

# Carga datos de ejemplo si vacío
count = supabase.table("ingredientes").select("*", count="exact").execute()
if count.count == 0:
    sample = [
        {"nombre": "Creatina", "tipo": "MP", "stock_actual": 150.0, "stock_seguridad": 10.0, "unidad_medida": "kg"},
        {"nombre": "Proteína Whey", "tipo": "MP", "stock_actual": 80.0, "stock_seguridad": 15.0, "unidad_medida": "kg"},
        {"nombre": "Cápsulas Vacías", "tipo": "ME", "stock_actual": 5000.0, "stock_seguridad": 500.0, "unidad_medida": "unidades"}
    ]
    supabase.table("ingredientes").insert(sample).execute()
    st.success("Datos de ejemplo cargados")

# App principal
st.set_page_config(layout="wide")
st.title("🧪 RHG Laboratorios - ERP")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🔄 Registrar P.I.", "📦 Convertir P.T.", "🚚 Entregas"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Inventario MP/ME")
        data = supabase.table("ingredientes").select("*").execute()
        df = pd.DataFrame(data.data)
        st.dataframe(df)
    with col2:
        st.subheader("P.T. en Almacén")
        pt_data = supabase.table("producto_terminado").select("*").eq("status", "En almacén").execute()
        st.dataframe(pd.DataFrame(pt_data.data) if pt_data.data else pd.DataFrame())

with tab2:
    st.subheader("Registrar Producto Intermedio (P.I.)")
    with st.form("pi_form"):
        lote_pi = st.text_input("Lote P.I.")
        producto = st.selectbox("Producto", ["Lumihast Burner", "Lumivit Omega", "Maquila Personalizada"])
        kg = st.number_input("Kg producidos", min_value=0.0)
        fecha = st.date_input("Fecha producción", value=date.today())
        submitted = st.form_submit_button("Registrar P.I.")
        if submitted:
            supabase.table("producto_intermedio").insert({
                "lote_pi": lote_pi, "producto_nombre": producto, "kg_producidos": kg,
                "fecha_produccion": fecha, "status": "En proceso"
            }).execute()
            st.success("¡P.I. registrado!")

with tab3:
    st.subheader("Convertir P.I. a P.T.")
    pi_data = supabase.table("producto_intermedio").select("*").eq("status", "En proceso").execute()
    if pi_data.data:
        lote_pi = st.selectbox("Lote P.I.", [r["lote_pi"] for r in pi_data.data])
        with st.form("pt_form"):
            lote_pt = st.text_input("Lote P.T. nuevo")
            envases = st.number_input("Cantidad de envases", min_value=1)
            submitted = st.form_submit_button("Convertir")
            if submitted:
                supabase.table("producto_terminado").insert({
                    "lote_pt": lote_pt, "producto_nombre": pi_data.data[0]["producto_nombre"],
                    "cantidad_envases": envases, "fecha_terminado": date.today(), "status": "En almacén"
                }).execute()
                supabase.table("producto_intermedio").update({"status": "Convertido"}).eq("lote_pi", lote_pi).execute()
                st.success("¡P.T. creado!")
    else:
        st.info("No hay P.I. pendientes")

with tab4:
    st.subheader("Registrar Entrega P.T.")
    pt_data = supabase.table("producto_terminado").select("*").eq("status", "En almacén").execute()
    if pt_data.data:
        lote_pt = st.selectbox("Lote P.T.", [r["lote_pt"] for r in pt_data.data])
        with st.form("entrega_form"):
            cliente = st.text_input("Cliente")
            responsable = st.selectbox("Responsable Logística", ["Juan", "Pedro", "Ana", "María"])
            cantidad = st.number_input("Envases entregados", min_value=1)
            submitted = st.form_submit_button("Entregar")
            if submitted:
                supabase.table("entregas_clientes").insert({
                    "lote_pt": lote_pt, "cliente_nombre": cliente, "responsable_entrega": responsable,
                    "cantidad_envases": cantidad, "fecha_entrega": date.today()
                }).execute()
                supabase.table("producto_terminado").update({"status": "Entregado"}).eq("lote_pt", lote_pt).execute()
                st.success("¡Entrega registrada!")
    else:
        st.info("No hay P.T. disponibles")
