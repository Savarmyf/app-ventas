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
else:
    st.success("👏 Vas muy bien hoy. Mantené el ritmo.")
    
st.info(f"✨ {random.choice(FRASES_MOTIVACIONALES)}")



# -------------------- Sidebar --------------------
with st.sidebar:
    st.success(f"👋 {usuario}")
    st.link_button("📘 Guía técnica", GUIA_DRIVE_URL)

st.divider()

# ================== UI PRO (TABS + DASHBOARD) ==================
st.title("📊 Constancia del Equipo")

# Sidebar prolija
with st.sidebar:
    st.markdown("## 🧭 Menú")
    seccion = st.radio(
        "Ir a:",
        ["📊 Dashboard", "🗓 Registro", "🛒 Ventas", "🌳 Red", "📝 Notas"],
        label_visibility="collapsed"
    )
    st.link_button("📘 Guía técnica", GUIA_DRIVE_URL)
    if st.button("🚪 Cerrar sesión"):
        st.session_state.usuario = None
        st.session_state.rol = None
        st.rerun()

# Helpers de métricas del día/semana
hoy = date.today()
hoy_str = hoy.isoformat()
ini_semana = hoy - timedelta(days=hoy.weekday())

mis_registros = registros.get(usuario, [])
mis_demos = demostraciones.get(usuario, [])
mis_planes = planes.get(usuario, [])

contactos_hoy_total = sum(r["cantidad"] for r in mis_registros if r["fecha"] == hoy_str)
demos_hoy_total = sum(r["cantidad"] for r in mis_demos if r["fecha"] == hoy_str)
planes_hoy_total = sum(r["cantidad"] for r in mis_planes if r["fecha"] == hoy_str)

contactos_semana = sum(r["cantidad"] for r in mis_registros if date.fromisoformat(r["fecha"]) >= ini_semana)
demos_semana = sum(r["cantidad"] for r in mis_demos if date.fromisoformat(r["fecha"]) >= ini_semana)
planes_semana = sum(r["cantidad"] for r in mis_planes if date.fromisoformat(r["fecha"]) >= ini_semana)

# ================== DASHBOARD ==================
if seccion == "📊 Dashboard":
    st.subheader("📊 Dashboard")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📞 Contactos hoy", contactos_hoy_total)
    c2.metric("🎤 Demos hoy", demos_hoy_total)
    c3.metric("📑 Planes hoy", planes_hoy_total)
    c4.metric("🎯 Objetivo semanal (contactos)", f"{contactos_semana}/{OBJ_CONTACTOS_SEMANAL}")

    # Progreso semanal
    st.markdown("### 🎯 Progreso semanal")
    st.progress(min(contactos_semana / OBJ_CONTACTOS_SEMANAL, 1.0))
    st.caption(f"Contactos: {contactos_semana} / {OBJ_CONTACTOS_SEMANAL}")

    st.progress(min(demos_semana / OBJ_DEMOS_SEMANAL, 1.0))
    st.caption(f"Demos: {demos_semana} / {OBJ_DEMOS_SEMANAL}")


# ================== REGISTRO ==================
elif seccion == "🗓 Registro":
    st.subheader("🗓 Registro del día")

    fecha = st.date_input("Fecha", value=date.today(), key="fecha_general")

    col1, col2, col3 = st.columns(3)
    with col1:
        contactos_hoy = st.number_input("📞 Contactos", min_value=0, step=1)
    with col2:
        demos_hoy = st.number_input("🎤 Demostraciones", min_value=0, step=1)
    with col3:
        planes_hoy = st.number_input("📑 Planes dados", min_value=0, step=1)

    if st.button("💾 Guardar registro del día", use_container_width=True):
        fecha_str = fecha.isoformat()

        registros.setdefault(usuario, []).append({"fecha": fecha_str, "cantidad": contactos_hoy})
        demostraciones.setdefault(usuario, []).append({"fecha": fecha_str, "cantidad": demos_hoy})
        planes.setdefault(usuario, []).append({"fecha": fecha_str, "cantidad": planes_hoy})

        guardar_data(data, sha)
        st.success("✅ Registro guardado")

# ================== VENTAS ==================
elif seccion == "🛒 Ventas":
    st.subheader("🛒 Ventas de productos")

    lista_productos = list(productos.keys())
    producto_seleccionado = st.selectbox("Producto", lista_productos)
    cantidad_vendida = st.number_input("Cantidad", min_value=1, step=1, value=1)

    if st.button("➕ Registrar venta", use_container_width=True):
        productos[producto_seleccionado] += cantidad_vendida
        for _ in range(cantidad_vendida):
            ventas.append({
                "usuario": usuario,
                "producto": producto_seleccionado,
                "fecha": date.today().isoformat()
            })
        guardar_data(data, sha)
        st.success("✅ Venta registrada")

    st.markdown("### 🏆 Más vendidos")
    ranking_prod = [(p, v) for p, v in productos.items() if v > 0]
    ranking_prod = sorted(ranking_prod, key=lambda x: x[1], reverse=True)

    if ranking_prod:
        for p, v in ranking_prod:
            st.write(f"• **{p}** — {v}")
    else:
        st.info("Todavía no hay ventas.")

# ================== RED ==================
elif seccion == "🌳 Red":
    st.subheader("🌳 Tu red")

    st.markdown("**Tu líder:**")
    st.info(usuarios[usuario].get("lider") or "Sin líder")

    st.markdown("**Tus miembros directos:**")
    mis_miembros = usuarios[usuario].get("miembros", [])
    if mis_miembros:
        for m in mis_miembros:
            st.write(f"• {m}")
    else:
        st.caption("Todavía no tenés miembros directos.")

    st.markdown("**Red completa:**")
    def mostrar_red(user, nivel=0):
        st.write(" " * nivel + f"• {user}")
        for m in usuarios.get(user, {}).get("miembros", []):
            mostrar_red(m, nivel + 1)

    mostrar_red(usuario)

# ================== NOTAS ==================
elif seccion == "📝 Notas":
    st.subheader("📝 Notas personales")
    nota_actual = notas.get(usuario, "")
    nota_nueva = st.text_area("Metas, pendientes, ideas", value=nota_actual, height=160)

    if st.button("💾 Guardar notas", use_container_width=True):
        notas[usuario] = nota_nueva
        guardar_data(data, sha)
        st.success("✅ Notas guardadas")





