import streamlit as st
import json
from datetime import date
import pandas as pd
import random
import hashlib
from pathlib import Path

# -------------------- CONFIG --------------------
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "data.json"
ADMIN_USERNAME = "admin"

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
            "costos": {},
            "mensajes_admin": []
        }
        DATA_FILE.write_text(json.dumps(base, indent=2))

def load_data():
    return json.loads(DATA_FILE.read_text())

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, indent=2))

# -------------------- Data --------------------
init_data()
data = load_data()

for k in ["usuarios","registros","demostraciones","planes","notas","productos","ingresos","costos","mensajes_admin"]:
    data.setdefault(k, {} if k != "mensajes_admin" else [])

usuarios = data["usuarios"]
registros = data["registros"]
demostraciones = data["demostraciones"]
productos = data["productos"]
notas = data["notas"]
ingresos = data["ingresos"]
mensajes_admin = data["mensajes_admin"]

# Blindaje usuarios
for u, info in usuarios.items():
    info.setdefault("rol", "miembro")
    info.setdefault("lider", None)
    info.setdefault("miembros", [])

# Crear admin
if ADMIN_USERNAME not in usuarios:
    usuarios[ADMIN_USERNAME] = {
        "password": hash_password("admin123"),
        "rol": "admin",
        "lider": None,
        "miembros": []
    }

save_data(data)

# -------------------- Login --------------------
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.subheader("🔐 Ingresar / Registrarse")

    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("Entrar"):
            if user in usuarios and usuarios[user]["password"] == hash_password(password):
                st.session_state.usuario = user
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

    with c2:
        if st.button("Registrarme"):
            if user in usuarios:
                st.error("Usuario ya existe")
            elif not user or not password:
                st.error("Completá usuario y contraseña")
            else:
                usuarios[user] = {"password": hash_password(password), "rol": "miembro", "lider": None, "miembros": []}
                save_data(data)
                st.session_state.usuario = user
                st.rerun()

    st.divider()

    if st.button("Olvidé mi contraseña"):
        if user:
            mensajes_admin.append({"fecha": date.today().isoformat(), "usuario": user, "mensaje": "Olvidó la contraseña"})
            save_data(data)
            st.success("Aviso enviado al admin.")
        else:
            st.error("Ingresá tu usuario primero.")

    st.stop()

usuario = st.session_state.usuario
rol = usuarios.get(usuario, {}).get("rol", "miembro")

# -------------------- Sidebar --------------------
st.sidebar.success(f"👤 {usuario} ({rol})")

if st.sidebar.button("Cerrar sesión"):
    st.session_state.usuario = None
    st.rerun()

with st.sidebar:
    seccion = st.radio("Menú", ["📊 Dashboard", "🗓 Registro", "🛒 Ventas", "💰 Balance", "📝 Notas"] + (["👑 Admin"] if rol == "admin" else []))

# -------------------- Dashboard --------------------
if seccion == "📊 Dashboard":
    hoy = date.today().isoformat()

    st.subheader("💡 Mensaje para hoy")

    hoy_contactos = any(r.get("fecha") == hoy and r.get("cantidad", 0) > 0 for r in registros.get(usuario, []))
    hoy_demos = any(d.get("fecha") == hoy and d.get("cantidad", 0) > 0 for d in demostraciones.get(usuario, []))

    if not hoy_contactos:
        st.warning("🔥 Hoy todavía no sumaste contactos.")
    elif hoy_contactos and not hoy_demos:
        st.info("⚡ Buen arranque. ¿Una demo hoy?")
    else:
        st.success("🚀 Día completo.")

    st.info("✨ " + random.choice(["El que insiste gana.","No es suerte, es volumen.","Aunque sea 1 hoy, suma."]))

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
        st.info("No hay productos cargados.")
    else:
        prod_name = st.selectbox("Producto", list(productos.keys()))
        cantidad = st.number_input("Cantidad", 1, min_value=1)

        prod = productos[prod_name]
        ganancia = prod["precio"] - prod["costo"]
        puntos = prod.get("puntos", 0)

        st.info(f"Ganancia: ${ganancia:,.0f} | Puntos: {puntos}")

        if st.button("Registrar venta"):
            ingresos.setdefault(usuario, [])
            for _ in range(cantidad):
                ingresos[usuario].append({
                    "fecha": date.today().isoformat(),
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
    st.subheader("📦 Productos")

    if rol == "admin":
        with st.expander("Agregar producto"):
            nombre = st.text_input("Nombre")
            costo = st.number_input("Costo", min_value=0.0)
            precio = st.number_input("Precio", min_value=0.0)
            puntos = st.number_input("Puntos", min_value=0.0)

            if st.button("Guardar producto"):
                if not nombre:
                    st.error("Nombre requerido")
                else:
                    productos[nombre] = {"costo": float(costo), "precio": float(precio), "puntos": float(puntos)}
                    save_data(data)
                    st.success("Producto guardado")
    else:
        st.info("Solo admin puede modificar productos.")

# -------------------- Notas --------------------
elif seccion == "📝 Notas":
    nota = st.text_area("Notas", value=notas.get(usuario, ""))

    if st.button("Guardar notas"):
        notas[usuario] = nota
        save_data(data)
        st.success("Notas guardadas")

# -------------------- Admin --------------------
elif seccion == "👑 Admin" and rol == "admin":
    st.subheader("👑 Panel Admin")

    st.markdown("### 📩 Mensajes")
    for m in mensajes_admin:
        st.info(f"{m['fecha']} - {m['usuario']}: {m['mensaje']}")

    st.markdown("### 👤 Resetear contraseña")
    u = st.selectbox("Usuario", list(usuarios.keys()))
    new_pass = st.text_input("Nueva contraseña", type="password")

    if st.button("Resetear"):
        if new_pass:
            usuarios[u]["password"] = hash_password(new_pass)
            save_data(data)
            st.success("Clave actualizada")
        else:
            st.error("Ingresá una contraseña")
