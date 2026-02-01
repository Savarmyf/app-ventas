import streamlit as st
import json
from datetime import datetime, date, timedelta

USUARIOS_FILE = "usuarios.json"
REGISTROS_FILE = "registros.json"
NOTAS_FILE = "notas.json"

GUIA_DRIVE_URL = "PEGAR_ACA_TU_LINK_DE_DRIVE"

st.set_page_config(page_title="Constancia del Equipo", page_icon="📊")
st.title("📊 Registro de Constancia del Equipo")

# -------------------- Utils --------------------
def cargar_json(ruta, default):
    try:
        with open(ruta, "r") as f:
            return json.load(f)
    except:
        return default

def guardar_json(ruta, data):
    with open(ruta, "w") as f:
        json.dump(data, f, indent=2)

usuarios = cargar_json(USUARIOS_FILE, {})
registros = cargar_json(REGISTROS_FILE, {})
notas = cargar_json(NOTAS_FILE, {})

# -------------------- Login / Registro --------------------
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.subheader("🔐 Ingresar / Registrarse")

    tab1, tab2 = st.tabs(["Ingresar", "Registrarse"])

    with tab1:
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if user in usuarios and usuarios[user] == password:
                st.session_state.usuario = user
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

    with tab2:
        new_user = st.text_input("Nuevo usuario")
        new_pass = st.text_input("Nueva contraseña", type="password")
        if st.button("Crear cuenta"):
            if new_user in usuarios:
                st.warning("Ese usuario ya existe")
            elif not new_user or not new_pass:
                st.warning("Completá usuario y contraseña")
            else:
                usuarios[new_user] = new_pass
                guardar_json(USUARIOS_FILE, usuarios)
                st.success("✅ Usuario creado, ahora podés ingresar")

    st.stop()

# -------------------- App --------------------
usuario = st.session_state.usuario
st.success(f"👋 Bienvenido {usuario}")

st.divider()

# -------------------- Guía del equipo --------------------
st.subheader("📘 Guía técnica del equipo")
if GUIA_DRIVE_URL != "https://drive.google.com/file/d/1jq_fpB4g7ADA8bmOpi5Szo_FiTAwqT9V/view?usp=drive_link"
:
    st.link_button("Abrir guía en Drive", GUIA_DRIVE_URL)
else:
    st.info("Pegá el link de Drive en la variable GUIA_DRIVE_URL")

st.divider()

# -------------------- Cargar registro diario --------------------
st.subheader("🗓 Cargar registro del día")

fecha = st.date_input("Fecha", value=date.today())
cantidad = st.number_input("Contactos de hoy", min_value=0, step=1)

if st.button("Guardar registro"):
    registros.setdefault(usuario, [])
    fecha_str = fecha.strftime("%Y-%m-%d")

    existe = any(r["fecha"] == fecha_str for r in registros[usuario])

    if existe:
        st.warning("⚠️ Ya cargaste un registro para ese día")
    else:
        registros[usuario].append({"fecha": fecha_str, "cantidad": cantidad})
        guardar_json(REGISTROS_FILE, registros)
        st.success("✅ Registro guardado")

st.divider()

# -------------------- Métricas --------------------
st.subheader("📊 Tus métricas")

mis_registros = registros.get(usuario, [])

if mis_registros:
    total = sum(r["cantidad"] for r in mis_registros)
    promedio = total / len(mis_registros)

    col1, col2 = st.columns(2)
    col1.metric("Total de contactos", total)
    col2.metric("Promedio diario", round(promedio, 2))

    if promedio >= 10:
        st.success("🚀 Nivel crack. Estás jugando en serio.")
    elif promedio >= 5:
        st.info("💪 Muy bien. Constancia real.")
    else:
        st.warning("🧠 Tranqui. Hoy sumá 1 más que ayer.")

    # ---- Racha real por fechas consecutivas ----
    fechas = sorted([datetime.strptime(r["fecha"], "%Y-%m-%d").date() for r in mis_registros], reverse=True)

    racha = 1
    for i in range(len(fechas) - 1):
        if fechas[i] - fechas[i + 1] == timedelta(days=1):
            racha += 1
        else:
            break

    st.write(f"🔥 Tu racha actual: **{racha} días seguidos**")
else:
    st.info("Todavía no cargaste registros.")

st.divider()

# -------------------- Notas personales --------------------
st.subheader("📝 Notas personales (metas, pendientes, ideas)")

nota_actual = notas.get(usuario, "")
nota_nueva = st.text_area("Escribí tus notas", value=nota_actual, height=150)

if st.button("Guardar notas"):
    notas[usuario] = nota_nueva
    guardar_json(NOTAS_FILE, notas)
    st.success("✅ Notas guardadas")

st.divider()

# -------------------- Ranking equipo --------------------
st.subheader("🏆 Ranking del equipo")

ranking = {}
for user, regs in registros.items():
    ranking[user] = sum(r["cantidad"] for r in regs)

if ranking:
    for user, total in sorted(ranking.items(), key=lambda x: x[1], reverse=True):
        st.write(f"**{user}**: {total} contactos")
else:
    st.info("Todavía no hay registros del equipo")

# -------------------- Logout --------------------
if st.button("Cerrar sesión"):
    st.session_state.usuario = None
    st.rerun()

