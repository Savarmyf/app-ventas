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
tareas = data.get("tareas", {})
data["tareas"] = tareas
agenda = data.get("agenda", {})
data["agenda"] = agenda
costos = data.get("costos", {})
data["costos"] = costos
ingresos = data.get("ingresos", {})
data["ingresos"] = ingresos


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

hoy_str = date.today().isoformat()
registros_user = registros.get(usuario, [])
demos_user = demostraciones.get(usuario, [])

hoy_contactos = any(r["fecha"] == hoy_str and r["cantidad"] > 0 for r in registros_user)
hoy_demos = any(d["fecha"] == hoy_str and d["cantidad"] > 0 for d in demos_user)

if not hoy_contactos:
    st.warning("🔥 Hoy todavía no sumaste contactos. 1 acción ahora cambia el día.")
elif hoy_contactos and not hoy_demos:
    st.info("⚡ Buen arranque. Ahora convertí: ¿una demo hoy?")
else:
    st.success("🚀 Día completo: contactos + demos. Seguimos construyendo.")

FRASES_MOTIVACIONALES = [
    "El que insiste gana.",
    "Hoy es el día que estabas esperando.",
    "No es suerte, es volumen.",
    "Aunque sea 1 hoy, suma.",
    "Tu yo del futuro te va a agradecer lo que hagas hoy.",
]

import random
st.info("✨ " + random.choice(FRASES_MOTIVACIONALES))


# -------------------- Sidebar --------------------
with st.sidebar:
    st.success(f"👋 {usuario}")
    st.link_button("📘 Guía técnica", GUIA_DRIVE_URL)

st.divider()

# ================== UI PRO (SIDEBAR + SECCIONES) ==================
st.title("📊 Constancia del Equipo")

with st.sidebar:
    st.markdown("## 🧭 Menú")

    seccion = st.radio(
        "Ir a:",
        ["📊 Dashboard", "🗓 Registro", "🛒 Ventas", "💰 Balance", "🌳 Red", "📝 Notas"],
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
    st.header("📊 Dashboard")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📞 Contactos hoy", contactos_hoy_total)
    c2.metric("🎤 Demos hoy", demos_hoy_total)
    c3.metric("📑 Planes hoy", planes_hoy_total)
    c4.metric("🎯 Objetivo semanal (contactos)", f"{contactos_semana}/{OBJ_CONTACTOS_SEMANAL}")

    st.markdown("### 🎯 Progreso semanal")
    st.progress(min(contactos_semana / OBJ_CONTACTOS_SEMANAL, 1.0))
    st.caption(f"Contactos: {contactos_semana} / {OBJ_CONTACTOS_SEMANAL}")

    st.progress(min(demos_semana / OBJ_DEMOS_SEMANAL, 1.0))
    st.caption(f"Demos: {demos_semana} / {OBJ_DEMOS_SEMANAL}")

    st.subheader("✅ Tareas del día")
    tareas.setdefault(usuario, [])

    with st.expander("➕ Agregar tarea"):
        desc = st.text_input("Descripción (ej: Llamar a Juan)")
        fecha_limite = st.date_input("Fecha límite", value=date.today())
        if st.button("Agregar tarea"):
            tareas[usuario].append({
                "desc": desc,
                "fecha": fecha_limite.isoformat(),
                "hecha": False
            })
            guardar_data(data, sha)
            st.success("Tarea agregada")

    for i, t in enumerate(tareas[usuario]):
        col1, col2, col3 = st.columns([4, 2, 1])
        col1.write(f"• {t['desc']}")
        col2.write(f"📅 {t['fecha']}")
        if not t["hecha"]:
            if col3.button("✔️", key=f"tarea_{i}"):
                tareas[usuario][i]["hecha"] = True
                guardar_data(data, sha)
                st.rerun()
        else:
            col3.write("✅")

    st.subheader("📅 Agenda")
    agenda.setdefault(usuario, [])

    with st.expander("➕ Agendar evento"):
        tipo = st.selectbox("Tipo", ["Demo", "Reunión", "Seguimiento"])
        titulo = st.text_input("Título (ej: Demo con Juan)")
        fecha_evento = st.date_input("Fecha del evento", value=date.today())
        if st.button("Agendar"):
            agenda[usuario].append({
                "tipo": tipo,
                "titulo": titulo,
                "fecha": fecha_evento.isoformat(),
                "hecho": False
            })
            guardar_data(data, sha)
            st.success("Evento agendado")

    for i, e in enumerate(sorted(agenda[usuario], key=lambda x: x["fecha"])):
        col1, col2, col3 = st.columns([4, 2, 1])
        col1.write(f"• [{e['tipo']}] {e['titulo']}")
        col2.write(f"📅 {e['fecha']}")
        if not e["hecho"]:
            if col3.button("✔️ Hecho", key=f"agenda_{i}"):
                agenda[usuario][i]["hecho"] = True
                guardar_data(data, sha)
                st.rerun()
        else:
            col3.write("✅")


elif seccion == "🗓 Registro":
    st.header("🗓 Registro del día")

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


elif seccion == "🛒 Ventas":
    st.header("🛒 Registrar venta")

    lista_productos = list(productos.keys())

    if not lista_productos:
        st.info("Primero cargá productos en la sección 💰 Balance")
    else:
        producto_seleccionado = st.selectbox("Producto", lista_productos)
        cantidad_vendida = st.number_input("Cantidad", min_value=1, step=1, value=1)

        prod = productos[producto_seleccionado]
        precio = prod["precio"]
        costo = prod["costo"]
        ganancia = precio - costo

        st.info(f"💰 Ganancia por unidad: ${ganancia:,.0f}")

        if st.button("➕ Registrar venta", use_container_width=True):
            productos[producto_seleccionado]["vendidos"] += cantidad_vendida

            for _ in range(cantidad_vendida):
                ingresos.setdefault(usuario, []).append({
                    "fecha": date.today().isoformat(),
                    "producto": producto_seleccionado,
                    "precio_venta": precio,
                    "costo": costo,
                    "ganancia": ganancia
                })

            guardar_data(data, sha)
            st.success("✅ Venta registrada")


elif seccion == "💰 Balance":
    st.header("💰 Balance financiero")

    # Inicializar estructuras
    costos = data.get("costos", {})
    ingresos = data.get("ingresos", {})
    data["costos"] = costos
    data["ingresos"] = ingresos

    costos.setdefault(usuario, [])
    ingresos.setdefault(usuario, [])

    # ---------- Alta de productos ----------
    st.subheader("📦 Productos (costos y precios)")

    with st.expander("➕ Agregar / editar producto"):
        nombre_prod = st.text_input("Nombre del producto")
        costo_prod = st.number_input("Costo del producto", min_value=0.0, step=500.0)
        precio_prod = st.number_input("Precio de venta", min_value=0.0, step=500.0)

        if st.button("Guardar producto"):
            productos[nombre_prod] = {
                "vendidos": productos.get(nombre_prod, {}).get("vendidos", 0),
                "costo": float(costo_prod),
                "precio": float(precio_prod)
            }
            guardar_data(data, sha)
            st.success("✅ Producto guardado")

    # ---------- Resumen ----------
    st.subheader("📊 Resumen financiero")

    total_costos = sum(c["monto"] for c in costos[usuario]) if costos[usuario] else 0
    total_ingresos = sum(i["precio_venta"] for i in ingresos[usuario]) if ingresos[usuario] else 0
    total_ganancia = sum(i["ganancia"] for i in ingresos[usuario]) if ingresos[usuario] else 0
    balance = total_ganancia - total_costos

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💵 Costos", f"${total_costos:,.0f}")
    c2.metric("💸 Ingresos", f"${total_ingresos:,.0f}")
    c3.metric("📈 Ganancia", f"${total_ganancia:,.0f}")
    c4.metric("🧮 Balance neto", f"${balance:,.0f}")

    # ---------- Historial ----------
    st.markdown("### 🧾 Ventas registradas")
    if ingresos[usuario]:
        df_ingresos = pd.DataFrame(ingresos[usuario])
        df_ingresos["fecha"] = pd.to_datetime(df_ingresos["fecha"])
        st.dataframe(df_ingresos.sort_values("fecha", ascending=False), use_container_width=True)
    else:
        st.caption("Todavía no hay ventas registradas.")

    st.markdown("### 🧾 Costos registrados")
    if costos[usuario]:
        df_costos = pd.DataFrame(costos[usuario])
        df_costos["fecha"] = pd.to_datetime(df_costos["fecha"])
        st.dataframe(df_costos.sort_values("fecha", ascending=False), use_container_width=True)
    else:
        st.caption("Todavía no hay costos registrados.")

elif seccion == "🌳 Red":
    st.subheader("🌳 Tu red")
    st.info(f"Tu líder: {usuarios[usuario].get('lider') or 'Sin líder'}")
    for m in usuarios[usuario].get("miembros", []):
        st.write(f"• {m}")


elif seccion == "📝 Notas":
    st.subheader("📝 Notas personales")
    nota_actual = notas.get(usuario, "")
    nota_nueva = st.text_area("Metas, pendientes, ideas", value=nota_actual, height=160)

    if st.button("💾 Guardar notas", use_container_width=True):
        notas[usuario] = nota_nueva
        guardar_data(data, sha)
        st.success("Notas guardadas")






