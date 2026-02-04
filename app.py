import streamlit as st
import requests
import json
from datetime import date, datetime, timedelta
import pandas as pd
import base64
import random

# -------------------- CONFIG --------------------
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
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
planes = data.get("planes", {})
data["planes"] = planes

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
        if st.button("Crear cuenta"):
            if new_user in usuarios:
                st.warning("Ese usuario ya existe")
            else:
                usuarios[new_user] = {"password": new_pass, "rol": "miembro", "lider": None, "miembros": []}
                guardar_data(data, sha)
                st.success("Usuario creado, ahora podés ingresar")

    st.stop()

usuario = st.session_state.usuario
rol = usuarios[usuario]["rol"]

# -------------------- Mensaje motivacional --------------------
st.subheader("💡 Mensaje para hoy")

FRASES_MOTIVACIONALES = [
    "Sos importante. Tu constancia hoy cambia tu futuro. 💪",
    "La paz no es una opción, es una necesidad. Elegí avanzar hoy.",
    "Aunque hoy cueste, mañana te lo vas a agradecer.",
    "No se trata de motivación, se trata de disciplina.",
    "Un contacto hoy es una oportunidad que ayer no existía.",
    "No abandones en el día que más necesitás avanzar.",
    "Paso a paso también es progreso.",
    "No tenés que hacerlo perfecto, tenés que hacerlo.",
    "Tu versión de dentro de 6 meses depende de lo que hagas hoy.",
    "Constancia > ganas. Siempre."
]

hoy_str = date.today().strftime("%Y-%m-%d")
mis_contactos = registros.get(usuario, [])
contactos_hoy = any(r["fecha"] == hoy_str for r in mis_contactos)

if not contactos_hoy:
    st.warning("🔥 Hoy es un gran día para contactar, ¿ya lo hiciste?")
else:
    st.success("🚀 Bien ahí, ya sumaste contactos hoy. ¿Vamos por una demo o un plan?")

st.info(f"✨ {random.choice(FRASES_MOTIVACIONALES)}")

# -------------------- Sidebar --------------------
with st.sidebar:
    st.success(f"👋 {usuario}")
    st.link_button("📘 Guía técnica", GUIA_DRIVE_URL)
    if st.button("🚪 Cerrar sesión"):
        st.session_state.usuario = None
        st.session_state.rol = None
        st.rerun()

st.divider()

# -------------------- Red en red --------------------
st.subheader("🌐 Tu red")

usuarios.setdefault(usuario, {}).setdefault("lider", None)
usuarios.setdefault(usuario, {}).setdefault("miembros", [])

opciones_lideres = [u for u in usuarios.keys() if u != usuario]

if usuarios[usuario]["lider"] is None and opciones_lideres:
    lider_elegido = st.selectbox("Elegí tu líder (upline)", ["— seleccionar —"] + opciones_lideres)
    if lider_elegido != "— seleccionar —" and st.button("Confirmar líder"):
        usuarios[usuario]["lider"] = lider_elegido
        usuarios.setdefault(lider_elegido, {}).setdefault("miembros", []).append(usuario)
        guardar_data(data, sha)
        st.success(f"Ahora tu líder es {lider_elegido}")
        st.rerun()
else:
    st.info(f"Tu líder actual: {usuarios[usuario]['lider'] or 'Sin líder'}")

mis_miembros = usuarios[usuario].get("miembros", [])
if mis_miembros:
    st.write("👥 Tus miembros:")
    for m in mis_miembros:
        st.write(f"• {m}")
else:
    st.write("Todavía no tenés miembros.")

# -------------------- Registro del día --------------------
st.subheader("🗓 Registro del día")

fecha = st.date_input("Fecha", value=date.today())
c1, c2, c3 = st.columns(3)

with c1:
    contactos = st.number_input("Contactos", min_value=0, step=1)
with c2:
    demos = st.number_input("Demostraciones", min_value=0, step=1)
with c3:
    planes_hoy = st.number_input("Planes dados", min_value=0, step=1)

if st.button("Guardar registro"):
    fecha_str = fecha.isoformat()
    registros.setdefault(usuario, []).append({"fecha": fecha_str, "cantidad": contactos})
    demostraciones.setdefault(usuario, []).append({"fecha": fecha_str, "cantidad": demos})
    planes.setdefault(usuario, []).append({"fecha": fecha_str, "cantidad": planes_hoy})
    guardar_data(data, sha)
    st.success("Registro guardado")

# -------------------- Análisis --------------------
st.subheader("📈 Análisis")

df_c = pd.DataFrame(registros.get(usuario, []), columns=["fecha", "cantidad"])
df_d = pd.DataFrame(demostraciones.get(usuario, []), columns=["fecha", "cantidad"])
df_p = pd.DataFrame(planes.get(usuario, []), columns=["fecha", "cantidad"])

if not df_c.empty:
    df_c["fecha"] = pd.to_datetime(df_c["fecha"])
    df_c = df_c.groupby("fecha").sum().reset_index()

if not df_d.empty:
    df_d["fecha"] = pd.to_datetime(df_d["fecha"])
    df_d = df_d.groupby("fecha").sum().reset_index()

if not df_p.empty:
    df_p["fecha"] = pd.to_datetime(df_p["fecha"])
    df_p = df_p.groupby("fecha").sum().reset_index()

df = df_c.merge(df_d, on="fecha", how="outer", suffixes=("_contactos", "_demos"))
df = df.merge(df_p, on="fecha", how="outer").fillna(0)

if not df.empty:
    st.line_chart(df.set_index("fecha"))
else:
    st.info("Todavía no hay datos.")

# -------------------- Ventas --------------------
st.subheader("🛒 Ventas de productos")

ranking_prod = [(p, v) for p, v in productos.items() if v > 0]
ranking_prod.sort(key=lambda x: x[1], reverse=True)

producto = st.selectbox("Productos vendidos", list(productos.keys()))
cant = st.number_input("Cantidad", 1, 1)

if st.button("Registrar venta"):
    productos[producto] += cant
    for _ in range(cant):
        ventas.append({"usuario": usuario, "producto": producto, "fecha": date.today().isoformat()})
    guardar_data(data, sha)
    st.success("Venta registrada")

st.subheader("🏆 Productos más vendidos")
if ranking_prod:
    for p, v in ranking_prod:
        st.write(f"{p}: {v}")
else:
    st.info("Todavía no hay ventas.")

# -------------------- Red completa --------------------
st.subheader("🌳 Tu red completa")

def mostrar_red(u, nivel=0):
    st.write(" " * nivel + f"• {u}")
    for m in usuarios.get(u, {}).get("miembros", []):
        mostrar_red(m, nivel + 1)

mostrar_red(usuario)






