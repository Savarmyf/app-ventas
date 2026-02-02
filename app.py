import streamlit as st
import requests
import json
from datetime import date, datetime, timedelta
import pandas as pd
import base64

# -------------------- CONFIG --------------------
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]  # lo vamos a cargar en Streamlit Cloud
OWNER = "TU_USUARIO_GITHUB"
REPO = "TU_REPO"
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
cantidad_demo = st.number_input("Demos", min_value=0, step=1)

if st.button("Guardar demos"):
    demostraciones.setdefault(usuario, [])
    demostraciones[usuario].append({"fecha": fecha.isoformat(), "cantidad": cantidad_demo})
    guardar_data(data, sha)
    st.success("Guardado")

# -------------------- Ventas de productos --------------------
st.subheader("🛒 Ventas de productos")

for prod in productos:
    col1, col2 = st.columns([3,1])
    col1.write(prod)
    if col2.button(f"+1 {prod}"):
        productos[prod] += 1
        ventas.append({"usuario": usuario, "producto": prod, "fecha": date.today().isoformat()})
        guardar_data(data, sha)
        st.success(f"Venta registrada: {prod}")

st.subheader("🏆 Productos más vendidos")
ranking_prod = sorted(productos.items(), key=lambda x: x[1], reverse=True)
for p, v in ranking_prod:
    st.write(f"{p}: {v}")

st.info("✅ Datos guardados en GitHub (no se pierden al redeploy)")
