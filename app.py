import streamlit as st
import requests
import json
from datetime import date, timedelta
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
    payload = {"message": "Update data.json", "content": encoded, "sha": sha}
    requests.put(url, headers=github_headers(), json=payload)

data, sha = cargar_data()

# -------- Blindaje --------
usuarios = data.get("usuarios", {})
registros = data.get("registros", {})
demostraciones = data.get("demostraciones", {})
planes = data.get("planes", {})
notas = data.get("notas", {})
productos = data.get("productos", {})
ventas = data.get("ventas", [])
tareas = data.get("tareas", {})
agenda = data.get("agenda", {})
ingresos = data.get("ingresos", {})
costos = data.get("costos", {})

data.update({
    "usuarios": usuarios,
    "registros": registros,
    "demostraciones": demostraciones,
    "planes": planes,
    "notas": notas,
    "productos": productos,
    "ventas": ventas,
    "tareas": tareas,
    "agenda": agenda,
    "ingresos": ingresos,
    "costos": costos
})

# -------------------- Login --------------------
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.subheader("🔐 Ingresar / Registrarse")

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Entrar"):
        if user in usuarios and usuarios[user]["password"] == password:
            st.session_state.usuario = user
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

    st.stop()

usuario = st.session_state.usuario

# -------------------- Mensaje motivacional --------------------
st.subheader("💡 Mensaje para hoy")

hoy_str = date.today().isoformat()

registros_user = registros.get(usuario, [])
demos_user = demostraciones.get(usuario, [])

hoy_contactos = any(r.get("fecha") == hoy_str and r.get("cantidad", 0) > 0 for r in registros_user if isinstance(r, dict))
hoy_demos = any(d.get("fecha") == hoy_str and d.get("cantidad", 0) > 0 for d in demos_user if isinstance(d, dict))

if not hoy_contactos:
    st.warning("🔥 Hoy todavía no sumaste contactos. 1 acción ahora cambia el día.")
elif hoy_contactos and not hoy_demos:
    st.info("⚡ Buen arranque. Ahora convertí: ¿una demo hoy?")
else:
    st.success("🚀 Día completo: contactos + demos. Seguimos construyendo.")

FRASES = [
    "El que insiste gana.",
    "Hoy es el día que estabas esperando.",
    "No es suerte, es volumen.",
    "Aunque sea 1 hoy, suma.",
    "Tu yo del futuro te va a agradecer lo que hagas hoy."
]
st.info("✨ " + random.choice(FRASES))

# -------------------- Sidebar --------------------
with st.sidebar:
    st.markdown("## 🧭 Menú")
    seccion = st.radio("Ir a:", ["📊 Dashboard", "🗓 Registro", "🛒 Ventas", "💰 Balance"])
    st.link_button("📘 Guía técnica", GUIA_DRIVE_URL)
    if st.button("🚪 Cerrar sesión"):
        st.session_state.usuario = None
        st.rerun()

# -------------------- DASHBOARD --------------------
if seccion == "📊 Dashboard":
    hoy = date.today().isoformat()
    contactos_hoy = sum(r.get("cantidad", 0) for r in registros.get(usuario, []) if r.get("fecha") == hoy)
    demos_hoy = sum(d.get("cantidad", 0) for d in demostraciones.get(usuario, []) if d.get("fecha") == hoy)

    c1, c2 = st.columns(2)
    c1.metric("📞 Contactos hoy", contactos_hoy)
    c2.metric("🎤 Demos hoy", demos_hoy)

# -------------------- REGISTRO --------------------
elif seccion == "🗓 Registro":
    fecha = st.date_input("Fecha", value=date.today())
    contactos = st.number_input("Contactos", 0)
    demos = st.number_input("Demos", 0)

    if st.button("Guardar"):
        registros.setdefault(usuario, []).append({"fecha": fecha.isoformat(), "cantidad": contactos})
        demostraciones.setdefault(usuario, []).append({"fecha": fecha.isoformat(), "cantidad": demos})
        guardar_data(data, sha)
        st.success("Guardado")

# -------------------- VENTAS --------------------
elif seccion == "🛒 Ventas":
    if not productos:
        st.info("Cargá productos primero en 💰 Balance")
    else:
        prod_name = st.selectbox("Producto", list(productos.keys()))
        cantidad = st.number_input("Cantidad", 1)

        prod = productos[prod_name]
        ganancia = prod["precio"] - prod["costo"]

        st.info(f"Ganancia por unidad: ${ganancia:,.0f}")

        if st.button("Registrar venta"):
            ingresos.setdefault(usuario, [])
            for _ in range(cantidad):
                ingresos[usuario].append({
                    "fecha": date.today().isoformat(),
                    "producto": prod_name,
                    "precio_venta": prod["precio"],
                    "costo": prod["costo"],
                    "ganancia": ganancia
                })
            guardar_data(data, sha)
            st.success("Venta registrada")

# -------------------- BALANCE --------------------
elif seccion == "💰 Balance":
    st.subheader("📦 Productos")

    with st.expander("Agregar producto"):
        nombre = st.text_input("Nombre")
        costo = st.number_input("Costo", min_value=0.0, step=100.0)
        precio = st.number_input("Precio", min_value=0.0, step=100.0)

        if st.button("Guardar producto"):
            productos[nombre] = {
                "vendidos": productos.get(nombre, {}).get("vendidos", 0),
                "costo": float(costo),
                "precio": float(precio)
            }
            guardar_data(data, sha)
            st.success("Producto guardado")

    st.subheader("📊 Resumen")

    ingresos_user = ingresos.get(usuario, [])
    total_ingresos = sum(i.get("precio_venta", 0) for i in ingresos_user)
    total_costos = sum(i.get("costo", 0) for i in ingresos_user)
    total_ganancia = sum(i.get("ganancia", 0) for i in ingresos_user)

    c1, c2, c3 = st.columns(3)
    c1.metric("Ingresos", f"${total_ingresos:,.0f}")
    c2.metric("Costos", f"${total_costos:,.0f}")
    c3.metric("Ganancia", f"${total_ganancia:,.0f}")

    st.markdown("### 🧾 Ventas registradas")
    if ingresos_user:
        df_ingresos = pd.DataFrame(ingresos_user)
        df_ingresos["fecha"] = pd.to_datetime(df_ingresos["fecha"])
        st.dataframe(df_ingresos.sort_values("fecha", ascending=False), use_container_width=True)
    else:
        st.caption("Todavía no hay ventas registradas.")


# -------------------- RED --------------------
elif seccion == "🌳 Red":
    st.subheader("🌳 Tu red")
    st.info(f"Tu líder: {usuarios[usuario].get('lider') or 'Sin líder'}")

    for m in usuarios[usuario].get("miembros", []):
        st.write(f"• {m}")


# -------------------- NOTAS --------------------
elif seccion == "📝 Notas":
    st.subheader("📝 Notas personales")

    nota_actual = notas.get(usuario, "")
    nota_nueva = st.text_area("Metas, pendientes, ideas", value=nota_actual, height=160)

    if st.button("💾 Guardar notas", use_container_width=True):
        notas[usuario] = nota_nueva
        guardar_data(data, sha)
        st.success("Notas guardadas")
