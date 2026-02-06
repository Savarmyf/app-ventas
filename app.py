import streamlit as st
import json
from datetime import date
import pandas as pd
import random
import os
import hashlib
from pathlib import Path

# -------------------- CONFIG --------------------
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "data.json"

st.set_page_config(page_title="Constancia del Equipo", page_icon="📊", layout="centered")
st.title("📊 Constancia del Equipo")

# -------------------- Utils --------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def init_data():
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        base = {
            "usuarios": {},
            "registros": {},
            "demostraciones": {},
            "planes": {},
            "notas": {},
            "productos": {},
            "ingresos": {},
            "costos": {}
        }
        DATA_FILE.write_text(json.dumps(base, indent=2))

def load_data():
    return json.loads(DATA_FILE.read_text())

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, indent=2))

init_data()
data = load_data()

# Blindaje de estructura (por si el archivo está vacío o incompleto)
data.setdefault("usuarios", {})
data.setdefault("registros", {})
data.setdefault("demostraciones", {})
data.setdefault("planes", {})
data.setdefault("notas", {})
data.setdefault("productos", {})
data.setdefault("ingresos", {})
data.setdefault("costos", {})

save_data(data)  # asegura estructura mínima

usuarios = data["usuarios"]
registros = data["registros"]
demostraciones = data["demostraciones"]
productos = data["productos"]
notas = data["notas"]
ingresos = data["ingresos"]


# -------------------- Login --------------------
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.subheader("🔐 Ingresar / Registrarse")

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Entrar"):
            if user in usuarios and usuarios[user]["password"] == hash_password(password):
                st.session_state.usuario = user
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

    with col2:
        if st.button("Registrarme"):
            if user in usuarios:
                st.error("Usuario ya existe")
            elif not user or not password:
                st.error("Completá usuario y contraseña")
            else:
                usuarios[user] = {
                    "password": hash_password(password),
                    "rol": "miembro",
                    "lider": None,
                    "miembros": []
                }
                save_data(data)
                st.success("Usuario creado")
                st.session_state.usuario = user
                st.rerun()

    st.stop()

usuario = st.session_state.usuario

# -------------------- Mensaje motivacional --------------------
st.subheader("💡 Mensaje para hoy")
hoy = date.today().isoformat()

hoy_contactos = any(r.get("fecha") == hoy and r.get("cantidad", 0) > 0 for r in registros.get(usuario, []))
hoy_demos = any(d.get("fecha") == hoy and d.get("cantidad", 0) > 0 for d in demostraciones.get(usuario, []))

if not hoy_contactos:
    st.warning("🔥 Hoy todavía no sumaste contactos.")
elif hoy_contactos and not hoy_demos:
    st.info("⚡ Buen arranque. ¿Una demo hoy?")
else:
    st.success("🚀 Día completo.")

FRASES = [
    "El que insiste gana.",
    "No es suerte, es volumen.",
    "Aunque sea 1 hoy, suma.",
]
st.info("✨ " + random.choice(FRASES))

# -------------------- Sidebar --------------------
with st.sidebar:
    seccion = st.radio("Menú", ["📊 Dashboard", "🗓 Registro", "🛒 Ventas", "💰 Balance", "📝 Notas"])
    if st.button("Cerrar sesión"):
        st.session_state.usuario = None
        st.rerun()

# -------------------- Dashboard --------------------
if seccion == "📊 Dashboard":
    contactos_hoy = sum(r.get("cantidad", 0) for r in registros.get(usuario, []) if r.get("fecha") == hoy)
    demos_hoy = sum(d.get("cantidad", 0) for d in demostraciones.get(usuario, []) if d.get("fecha") == hoy)
    c1, c2 = st.columns(2)
    c1.metric("📞 Contactos hoy", contactos_hoy)
    c2.metric("🎤 Demos hoy", demos_hoy)

# -------------------- Registro --------------------
elif seccion == "🗓 Registro":
    fecha = st.date_input("Fecha", value=date.today())
    contactos = st.number_input("Contactos", 0)
    demos = st.number_input("Demos", 0)

    if st.button("Guardar"):
        registros.setdefault(usuario, []).append({"fecha": fecha.isoformat(), "cantidad": contactos})
        demostraciones.setdefault(usuario, []).append({"fecha": fecha.isoformat(), "cantidad": demos})
        save_data(data)
        st.success("Guardado")

# -------------------- Ventas --------------------
elif seccion == "🛒 Ventas":
    if not productos:
        st.info("Cargá productos primero en 💰 Balance")
    else:
        prod_name = st.selectbox("Producto", list(productos.keys()))
        cantidad = st.number_input("Cantidad", 1)

        prod = productos[prod_name]
        ganancia = prod["precio"] - prod["costo"]
        puntos = prod.get("puntos", 0)

        st.info(f"Ganancia por unidad: ${ganancia:,.0f} | Puntos por unidad: {puntos}")

        if st.button("Registrar venta"):
            ingresos.setdefault(usuario, [])
            for _ in range(cantidad):
                ingresos[usuario].append({
                    "fecha": hoy,
                    "producto": prod_name,
                    "precio_venta": prod["precio"],
                    "costo": prod["costo"],
                    "ganancia": ganancia,
                    "puntos": puntos
                })
            save_data(data)
            st.success("Venta registrada")

# -------------------- Balance --------------------
elif seccion == "💰 Balance":
with st.expander("Agregar producto"):
    nombre = st.text_input("Nombre")
    costo = st.number_input("Costo", min_value=0.0)
    precio = st.number_input("Precio", min_value=0.0)
    puntos = st.number_input("Puntos", min_value=0.0, step=1.0)

    if st.button("Guardar producto"):
        productos[nombre] = {
            "costo": float(costo),
            "precio": float(precio),
            "puntos": float(puntos)
        }
        save_data(data)
        st.success("Producto guardado")


ingresos_user = ingresos.get(usuario, [])
total_ingresos = sum(i.get("precio_venta", 0) for i in ingresos_user)
total_costos = sum(i.get("costo", 0) for i in ingresos_user)
total_ganancia = sum(i.get("ganancia", 0) for i in ingresos_user)
total_puntos = sum(i.get("puntos", 0) for i in ingresos_user)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ingresos", f"${total_ingresos:,.0f}")
c2.metric("Costos", f"${total_costos:,.0f}")
c3.metric("Ganancia", f"${total_ganancia:,.0f}")
c4.metric("Puntos", f"{total_puntos:,.0f}")

# -------------------- Notas --------------------
elif seccion == "📝 Notas":
    nota_actual = notas.get(usuario, "")
    nota_nueva = st.text_area("Notas", value=nota_actual)

    if st.button("Guardar notas"):
        notas[usuario] = nota_nueva
        save_data(data)
        st.success("Notas guardadas")



