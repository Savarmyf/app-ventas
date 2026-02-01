import streamlit as st
import json
from datetime import datetime, date, timedelta
import pandas as pd

USUARIOS_FILE = "usuarios.json"
REGISTROS_FILE = "registros.json"
NOTAS_FILE = "notas.json"
DEMOS_FILE = "demostraciones.json"

GUIA_DRIVE_URL = "https://drive.google.com/file/d/1jq_fpB4g7ADA8bmOpi5Szo_FiTAwqT9V/view"

OBJ_CONTACTOS_SEMANAL = 30
OBJ_DEMOS_SEMANAL = 5

st.set_page_config(page_title="Constancia del Equipo", page_icon="📊", layout="centered")
st.title("📊 Constancia del Equipo")

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

def inicio_semana(fecha):
    return fecha - timedelta(days=fecha.weekday())

usuarios = cargar_json(USUARIOS_FILE, {})
registros = cargar_json(REGISTROS_FILE, {})
notas = cargar_json(NOTAS_FILE, {})
demostraciones = cargar_json(DEMOS_FILE, {})

# -------------------- Login --------------------
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
                st.success("Usuario creado, ahora podés ingresar")

    st.stop()

# -------------------- App --------------------
usuario = st.session_state.usuario

with st.sidebar:
    st.success(f"👋 {usuario}")
    st.link_button("📘 Guía técnica", GUIA_DRIVE_URL)
    if st.button("🚪 Cerrar sesión"):
        st.session_state.usuario = None
        st.rerun()

st.divider()

# -------------------- Cargas --------------------
with st.expander("🗓 Cargar contactos del día", expanded=True):
    fecha = st.date_input("Fecha", value=date.today(), key="fecha_contactos")
    cantidad = st.number_input("Contactos de hoy", min_value=0, step=1)

    if st.button("Guardar contactos"):
        registros.setdefault(usuario, [])
        fecha_str = fecha.strftime("%Y-%m-%d")

        if any(r["fecha"] == fecha_str for r in registros[usuario]):
            st.warning("Ya cargaste contactos ese día")
        else:
            registros[usuario].append({"fecha": fecha_str, "cantidad": cantidad})
            guardar_json(REGISTROS_FILE, registros)
            st.success("Contactos guardados")

with st.expander("🎤 Cargar demostraciones del día"):
    fecha_demo = st.date_input("Fecha demo", value=date.today(), key="fecha_demo")
    cantidad_demo = st.number_input("Demostraciones de hoy", min_value=0, step=1)

    if st.button("Guardar demos"):
        demostraciones.setdefault(usuario, [])
        fecha_str = fecha_demo.strftime("%Y-%m-%d")

        if any(r["fecha"] == fecha_str for r in demostraciones[usuario]):
            st.warning("Ya cargaste demos ese día")
        else:
            demostraciones[usuario].append({"fecha": fecha_str, "cantidad": cantidad_demo})
            guardar_json(DEMOS_FILE, demostraciones)
            st.success("Demostraciones guardadas")

# -------------------- Métricas --------------------
st.subheader("📊 Progreso")

mis_registros = registros.get(usuario, [])
mis_demos = demostraciones.get(usuario, [])

if mis_registros or mis_demos:
    df_contactos = pd.DataFrame(mis_registros) if mis_registros else pd.DataFrame(columns=["fecha","cantidad"])
    df_demos = pd.DataFrame(mis_demos) if mis_demos else pd.DataFrame(columns=["fecha","cantidad"])

    if not df_contactos.empty:
        df_contactos["fecha"] = pd.to_datetime(df_contactos["fecha"])
        df_contactos = df_contactos.groupby("fecha").sum().reset_index()

    if not df_demos.empty:
        df_demos["fecha"] = pd.to_datetime(df_demos["fecha"])
        df_demos = df_demos.groupby("fecha").sum().reset_index()

    df = pd.merge(df_contactos, df_demos, on="fecha", how="outer", suffixes=("_contactos", "_demos")).fillna(0)

    if not df.empty:
        st.line_chart(df.set_index("fecha"))

# -------------------- Objetivo semanal --------------------
hoy = date.today()
ini = inicio_semana(hoy)

contactos_semana = sum(r["cantidad"] for r in mis_registros if date.fromisoformat(r["fecha"]) >= ini)
demos_semana = sum(r["cantidad"] for r in mis_demos if date.fromisoformat(r["fecha"]) >= ini)

st.subheader("🎯 Objetivo semanal")

st.progress(min(contactos_semana / OBJ_CONTACTOS_SEMANAL, 1.0))
st.write(f"Contactos: {contactos_semana} / {OBJ_CONTACTOS_SEMANAL}")

st.progress(min(demos_semana / OBJ_DEMOS_SEMANAL, 1.0))
st.write(f"Demostraciones: {demos_semana} / {OBJ_DEMOS_SEMANAL}")

# -------------------- Racha + Medallas --------------------
st.subheader("🔥 Racha y medallas")

fechas = set()
for r in mis_registros:
    fechas.add(date.fromisoformat(r["fecha"]))
for d in mis_demos:
    fechas.add(date.fromisoformat(d["fecha"]))

racha = 0
hoy_tmp = hoy
while hoy_tmp in fechas:
    racha += 1
    hoy_tmp -= timedelta(days=1)

medalla = "🥉 Bronce" if racha >= 3 else "—"
medalla = "🥈 Plata" if racha >= 7 else medalla
medalla = "🥇 Oro" if racha >= 14 else medalla
medalla = "🏆 Leyenda" if racha >= 30 else medalla

st.write(f"Racha actual: **{racha} días seguidos**")
st.write(f"Medalla: **{medalla}**")

# -------------------- Notas --------------------
st.subheader("📝 Notas personales")
nota_actual = notas.get(usuario, "")
nota_nueva = st.text_area("Metas, pendientes, ideas", value=nota_actual, height=120)

if st.button("Guardar notas"):
    notas[usuario] = nota_nueva
    guardar_json(NOTAS_FILE, notas)
    st.success("Notas guardadas")

# -------------------- Ranking --------------------
st.subheader("🏆 Ranking del equipo (contactos totales)")
ranking = {u: sum(r["cantidad"] for r in regs) for u, regs in registros.items()}
for user, total in sorted(ranking.items(), key=lambda x: x[1], reverse=True):
    st.write(f"**{user}**: {total}")
