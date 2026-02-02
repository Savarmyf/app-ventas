import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import gspread
from google.oauth2.service_account import Credentials

# -------------------- CONFIG --------------------
st.set_page_config(page_title="Constancia del Equipo", page_icon="📊", layout="centered")
st.title("📊 Constancia del Equipo")

GUIA_DRIVE_URL = "https://drive.google.com/file/d/1jq_fpB4g7ADA8bmOpi5Szo_FiTAwqT9V/view"
OBJ_CONTACTOS_SEMANAL = 30
OBJ_DEMOS_SEMANAL = 5

# -------------------- GOOGLE SHEETS --------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
)
gc = gspread.authorize(creds)

SPREADSHEET_NAME = "app_ventas_equipo"  # poné este nombre a tu Sheet
sh = gc.open(SPREADSHEET_NAME)

ws_usuarios = sh.worksheet("usuarios")
ws_contactos = sh.worksheet("contactos")
ws_demos = sh.worksheet("demostraciones")
ws_notas = sh.worksheet("notas")
ws_productos = sh.worksheet("productos")
ws_ventas = sh.worksheet("ventas")

# -------------------- UTILS --------------------
def get_df(ws):
    data = ws.get_all_records()
    return pd.DataFrame(data)

def append_row(ws, row):
    ws.append_row(row)

def update_ws(ws, df):
    ws.clear()
    ws.update([df.columns.values.tolist()] + df.values.tolist())

# -------------------- DATA --------------------
df_usuarios = get_df(ws_usuarios)
df_contactos = get_df(ws_contactos)
df_demos = get_df(ws_demos)
df_notas = get_df(ws_notas)
df_productos = get_df(ws_productos)
df_ventas = get_df(ws_ventas)

# -------------------- LOGIN --------------------
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
            fila = df_usuarios[(df_usuarios["usuario"] == user) & (df_usuarios["password"] == password)]
            if not fila.empty:
                st.session_state.usuario = user
                st.session_state.rol = fila.iloc[0]["rol"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

    with tab2:
        new_user = st.text_input("Nuevo usuario")
        new_pass = st.text_input("Nueva contraseña", type="password")
        new_rol = st.selectbox("Rol", ["miembro", "lider"])
        if st.button("Crear cuenta"):
            if new_user in df_usuarios["usuario"].values:
                st.warning("Ese usuario ya existe")
            else:
                append_row(ws_usuarios, [new_user, new_pass, new_rol, ""])
                st.success("Usuario creado, ahora podés ingresar")

    st.stop()

# -------------------- SIDEBAR --------------------
usuario = st.session_state.usuario
rol = st.session_state.rol

with st.sidebar:
    st.success(f"👋 {usuario} ({rol})")
    st.link_button("📘 Guía técnica", GUIA_DRIVE_URL)
    if st.button("🚪 Cerrar sesión"):
        st.session_state.usuario = None
        st.session_state.rol = None
        st.rerun()

# -------------------- CARGAS --------------------
st.subheader("🗓 Cargar contactos del día")
fecha = st.date_input("Fecha", value=date.today())
cantidad = st.number_input("Contactos de hoy", min_value=0, step=1)

if st.button("Guardar contactos"):
    append_row(ws_contactos, [usuario, fecha.isoformat(), cantidad])
    st.success("Contactos guardados")

st.subheader("🎤 Cargar demostraciones del día")
fecha_demo = st.date_input("Fecha demo", value=date.today(), key="demo")
cantidad_demo = st.number_input("Demostraciones", min_value=0, step=1)

if st.button("Guardar demos"):
    append_row(ws_demos, [usuario, fecha_demo.isoformat(), cantidad_demo])
    st.success("Demostraciones guardadas")

# -------------------- MÉTRICAS --------------------
st.subheader("📊 Progreso")

mis_contactos = df_contactos[df_contactos["usuario"] == usuario]
mis_demos = df_demos[df_demos["usuario"] == usuario]

if not mis_contactos.empty or not mis_demos.empty:
    dfc = mis_contactos.copy()
    dfd = mis_demos.copy()

    if not dfc.empty:
        dfc["fecha"] = pd.to_datetime(dfc["fecha"])
        dfc = dfc.groupby("fecha")["cantidad"].sum().reset_index()

    if not dfd.empty:
        dfd["fecha"] = pd.to_datetime(dfd["fecha"])
        dfd = dfd.groupby("fecha")["cantidad"].sum().reset_index()

    df = pd.merge(dfc, dfd, on="fecha", how="outer", suffixes=("_contactos", "_demos")).fillna(0)
    if not df.empty:
        st.line_chart(df.set_index("fecha"))

# -------------------- OBJETIVOS --------------------
def inicio_semana(fecha):
    return fecha - timedelta(days=fecha.weekday())

ini = inicio_semana(date.today())

contactos_sem = mis_contactos[mis_contactos["fecha"] >= ini.isoformat()]["cantidad"].sum() if not mis_contactos.empty else 0
demos_sem = mis_demos[mis_demos["fecha"] >= ini.isoformat()]["cantidad"].sum() if not mis_demos.empty else 0

st.subheader("🎯 Objetivo semanal")
st.progress(min(contactos_sem / OBJ_CONTACTOS_SEMANAL, 1.0))
st.write(f"Contactos: {contactos_sem} / {OBJ_CONTACTOS_SEMANAL}")

st.progress(min(demos_sem / OBJ_DEMOS_SEMANAL, 1.0))
st.write(f"Demostraciones: {demos_sem} / {OBJ_DEMOS_SEMANAL}")

# -------------------- PRODUCTOS --------------------
st.subheader("🛒 Ventas de productos")

if rol == "lider":
    nuevo_producto = st.text_input("Nuevo producto")
    if st.button("Agregar producto"):
        append_row(ws_productos, [nuevo_producto, 0])
        st.success("Producto agregado")

productos = get_df(ws_productos)

if not productos.empty:
    for i, row in productos.iterrows():
        if st.button(f"➕ Vender {row['producto']}"):
            append_row(ws_ventas, [usuario, row["producto"], date.today().isoformat()])
            productos.loc[i, "vendidos"] += 1
            update_ws(ws_productos, productos)
            st.success(f"Venta registrada: {row['producto']}")

    st.subheader("🔥 Ranking de productos")
    st.dataframe(productos.sort_values("vendidos", ascending=False))
