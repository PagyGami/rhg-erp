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
        st.title("🚀 PRODUCCIÓN MÁGICA - 150 FRASCOS EN 1 CLIC")

# Conexión a Supabase (ya la tienes, solo copia tu URL y key)
supabase_client = supabase.create_client(
    st.secrets["supabase_url"],
    st.secrets["supabase_anon_key"]
)

# Lista de productos (los mismos que ya cargamos)
productos = {
    "COL-MAR": "Colágeno Maracuyá 4kg",
    "COL-NAT": "Colágeno Natural 4kg",
    "COL-ARA": "Colágeno Arándano 4kg",
    "COL-NAR": "Colágeno Naranja 4kg",
    "COL-FRE": "Colágeno Fresa 4kg",
    "FLEXMAX60": "Flex Max 60 tabletas",
    "VITC90": "Vitamina C 90 cápsulas",
    "DTX500": "Detox 500mg",
    "MAG60": "Magnesio Complex",
    "DTX3060": "Detox 30/60 cápsulas"
}

producto = st.selectbox("Selecciona el producto a producir (lote de 150 frascos)", 
                       options=list(productos.keys()), 
                       format_func=lambda x: productos[x])

lote = st.text_input("Lote (opcional, si no pones nada se genera automático)", "")

if st.button("🔥 CALCULAR Y PRODUCIR 150 FRASCOS", type="primary"):
    with st.spinner("Revisando inventario..."):
        # 1. Traer fórmula completa
        formula = supabase_client.table("formulas")\
            .select("ingrediente_id, cantidad_por_unidad, unidad_medida, ingredientes(nombre, stock_actual)")\
            .eq("producto_id", supabase_client.table("producto_terminado").select("id").eq("codigo", producto).execute().data[0]["id"])\
            .execute().data

        # 2. Calcular cuánto necesitamos para 150 frascos
        necesidades = []
        faltan = []
        for item in formula:
            req = item["cantidad_por_unidad"] * 150
            actual = item["ingredientes"]["stock_actual"] or 0
            necesidades.append({
                "Ingrediente": item["ingredientes"]["nombre"],
                "Necesitas": f"{req:,.2f} {item['unidad_medida']}",
                "Tienes": f"{actual:,.2f} {item['unidad_medida']}",
                "Falta": req > actual
            })
            if req > actual:
                faltan.append(item["ingredientes"]["nombre"])

        df = pd.DataFrame(necesidades)

    if faltan:
        st.error(f"⚠️ TE FALTAN {len(faltan)} INGREDIENTES:")
        st.dataframe(df.style.apply(lambda x: ['background: #ffcccc' if x.Falta else '' for _ in x], axis=1))
        st.stop()
    else:
        st.success("✅ ¡TODO LISTO! Tienes todo el inventario")
        st.dataframe(df)

        if st.button("¡PRODUCIR LOS 150 FRASCOS AHORA! 💥", type="primary"):
            with st.spinner("Descontando inventario y creando lote..."):
                # Descontar todo
                for item in formula:
                    supabase_client.rpc("descontar_stock", {
                        "ingrediente_id": item["ingrediente_id"],
                        "cantidad": item["cantidad_por_unidad"] * 150
                    }).execute()

                # Crear/Sumar producto terminado
                lote_final = lote or f"L{datetime.now().strftime('%Y%m%d')}"
                supabase_client.table("producto_terminado").upsert({
                    "codigo": producto,
                    "cantidad_en_almacen": 150,
                    "lote": lote_final,
                    "fecha_produccion": datetime.now().isoformat(),
                    "fecha_vencimiento": (datetime.now() + timedelta(days=730)).isoformat(),  # 2 años
                    "status": "En almacén"
                }, on_conflict="codigo").execute()

            st.balloons()
            st.success(f"¡PRODUCCIÓN COMPLETADA! 150 frascos de {productos[producto]} con lote {lote_final} listos en almacén 🎉")
        
