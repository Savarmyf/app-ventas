import streamlit as st
import requests
import json
from datetime import date, datetime, timedelta
import pandas as pd
import base64

# -------------------- CONFIG --------------------
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]  # lo vamos a cargar en Streamlit Cloud
OWNER = "Savarmyf"
REPO = "app-ventas"
DATA_PATH = "data.json"

GUIA_DRIVE_URL = "https://drive.google.com/file/d/1jq_fpB4g7ADA8bmOpi5Szo_FiTAwqT9V/view"

OBJ_CONTACTOS_SEMANAL = 30
OBJ_DEMOS_SEMANAL = 5

st.set_page_config(page_title="Constancia del Equipo", page_icon="📊", layout="centered")
st.title("📊 Constancia del Equipo")

# -------------------- GitHub Utils --------------------
def github_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def cargar_data():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{DATA_PATH}"
    r = requests.get(url, headers=github_headers())
    content = r.json()["content"]
    decoded = base64.b64decode(content).decode("utf-8")
    return json.loads(decoded), r.json()["sha"]

def guardar_data(data, sha):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{DATA_PATH}"
    encoded = base64.b64encode(json.dumps(data, indent=2).encode()).decode()
    payload = {
        "message": "Update data.json",
        "content": encoded,
        "sha": sha
    }
    requests.put(url, headers=github_headers(), json=payload)

data, sha = cargar_data()

usuarios = data["usuarios"]
registros = data["registros"]
demostraciones = data["demostraciones"]
notas = data["notas"]
productos = data["productos"]
ventas = data["ventas"]

# -------------------- Login --------------------
if "usuario" not in st.session_state:
    st.session_state.usuario = None
    st.session_state.rol = None

if st.session_state.usuario is None:
    st.subheader("🔐 Ingresar / Registrarse")

    tab1, tab2 = st.tabs(["Ingresar", "Registrarse"])

    with tab1:
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if user in usuarios and usuarios[user]["password"] == password:
                st.session_state.usuario = user
                st.session_state.rol = usuarios[user]["rol"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

    with tab2:
        new_user = st.text_input("Nuevo usuario")
        new_pass = st.text_input("Nueva contraseña", type="password")
        new_rol = st.selectbox("Rol", ["miembro", "lider"])
        if st.button("Crear cuenta"):
            if new_user in usuarios:
                st.warning("Ese usuario ya existe")
            else:
                usuarios[new_user] = {"password": new_pass, "rol": new_rol, "lider": None, "equipo": []}
                guardar_data(data, sha)
                st.success("Usuario creado")
    st.stop()

usuario = st.session_state.usuario
rol = st.session_state.rol

with st.sidebar:
    st.success(f"👋 {usuario} ({rol})")
    st.link_button("📘 Guía técnica", GUIA_DRIVE_URL)
    if st.button("🚪 Cerrar sesión"):
        st.session_state.usuario = None
        st.session_state.rol = None
        st.rerun()
st.divider()
st.subheader("🌐 Tu red (upline / downline)")

# Inicializar campos si no existen (para usuarios viejos)
if "lider" not in usuarios[usuario]:
    usuarios[usuario]["lider"] = None
if "miembros" not in usuarios[usuario]:
    usuarios[usuario]["miembros"] = []

# Elegir líder (upline)
opciones_lideres = [u for u in usuarios.keys() if u != usuario]

if usuarios[usuario]["lider"] is None and opciones_lideres:
    lider_elegido = st.selectbox("Elegí tu líder (upline)", ["— seleccionar —"] + opciones_lideres)

    if lider_elegido != "— seleccionar —":
        if st.button("Confirmar líder"):
            usuarios[usuario]["lider"] = lider_elegido

            # Agregarme como miembro del líder
            if "miembros" not in usuarios[lider_elegido]:
                usuarios[lider_elegido]["miembros"] = []
            usuarios[lider_elegido]["miembros"].append(usuario)

            guardar_data(data, sha)
            st.success(f"✅ Ahora tu líder es {lider_elegido}")
            st.rerun()
else:
    st.info(f"Tu líder actual: **{usuarios[usuario]['lider'] or 'Sin líder'}**")

# Mostrar mis miembros directos
mis_miembros = usuarios[usuario].get("miembros", [])
if mis_miembros:
    st.write("👥 Tus miembros directos:")
    for m in mis_miembros:
        st.write(f"• {m}")
else:
    st.write("Todavía no tenés miembros directos.")

# -------------------- Cargas --------------------
st.subheader("🗓 Contactos del día")
fecha = st.date_input("Fecha", value=date.today())
cantidad = st.number_input("Contactos", min_value=0, step=1)

if st.button("Guardar contactos"):
    registros.setdefault(usuario, [])
    registros[usuario].append({"fecha": fecha.isoformat(), "cantidad": cantidad})
    guardar_data(data, sha)
    st.success("Guardado")

st.subheader("🎤 Demostraciones del día")
fecha_demo = st.date_input("Fecha de la demo", value=date.today(), key="fecha_demo")
cantidad_demo = st.number_input("Cantidad de demostraciones", min_value=0, step=1, key="cantidad_demo")

if st.button("Guardar demostraciones"):
    demostraciones.setdefault(usuario, [])
    demostraciones[usuario].append({
        "fecha": fecha_demo.isoformat(),
        "cantidad": cantidad_demo
    })
    guardar_data(data, sha)
    st.success("✅ Demostraciones guardadas")
    # -------------------- Analisis --------------------
st.subheader("📈 Análisis: Contactos vs Demostraciones")

mis_registros = registros.get(usuario, [])
mis_demos = demostraciones.get(usuario, [])

df_contactos = pd.DataFrame(mis_registros) if mis_registros else pd.DataFrame(columns=["fecha","cantidad"])
df_demos = pd.DataFrame(mis_demos) if mis_demos else pd.DataFrame(columns=["fecha","cantidad"])

if not df_contactos.empty:
    df_contactos["fecha"] = pd.to_datetime(df_contactos["fecha"])
    df_contactos = df_contactos.groupby("fecha")["cantidad"].sum().reset_index()

if not df_demos.empty:
    df_demos["fecha"] = pd.to_datetime(df_demos["fecha"])
    df_demos = df_demos.groupby("fecha")["cantidad"].sum().reset_index()

df = pd.merge(df_contactos, df_demos, on="fecha", how="outer", suffixes=("_contactos", "_demos")).fillna(0)

if not df.empty:
    st.line_chart(df.set_index("fecha"))
else:
    st.info("Todavía no hay datos para mostrar el análisis.")


# -------------------- Ventas de productos --------------------
st.subheader("🛒 Registrar venta de producto")

lista_productos = list(productos.keys())

if lista_productos:
    producto_seleccionado = st.selectbox("Productos vendidos:", lista_productos)
    cantidad_vendida = st.number_input("Cantidad", min_value=1, step=1, value=1)

    if st.button("Registrar venta"):
        productos[producto_seleccionado] += cantidad_vendida

        for _ in range(cantidad_vendida):
            ventas.append({
                "usuario": usuario,
                "producto": producto_seleccionado,
                "fecha": date.today().isoformat()
            })

        guardar_data(data, sha)
        st.success(f"✅ Venta registrada: {producto_seleccionado} x{cantidad_vendida}")
else:
    st.info("Todavía no hay productos cargados.")

st.subheader("🏆 Productos más vendidos")

ranking_prod = [(p, v) for p, v in productos.items() if v > 0]
ranking_prod = sorted(ranking_prod, key=lambda x: x[1], reverse=True)

if ranking_prod:
    for p, v in ranking_prod:
        st.write(f"• {p}: {v}")
else:
    st.info("Todavía no hay ventas registradas.")





