import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import urllib.parse
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SAC Contreras - Gestión Nube", layout="wide", page_icon="🔧")

# Estilo Visual Gabriel
st.markdown("""
    <style>
        .stApp { background-color: #0e1117; color: white; }
        h1, h2, h3, h4, h5, h6, label, p { color: #ffffff !important; }
        .stButton>button { color: white; background-color: #004080; border-radius: 5px; width: 100%; }
        .item-lista { background-color: #1e2129; padding: 10px; border-radius: 5px; margin-bottom: 5px; border-left: 5px solid #004080; }
        div[data-testid="stExpander"] { background-color: #1a1c23; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LOGO ---
try:
    image_web = Image.open('logo_sac.png')
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c: st.image(image_web, use_container_width=True)
except:
    st.title("📋 SAC CONTRERAS")

# --- CLASE PDF ---
class PDF(FPDF):
    def header(self):
        try: self.image('logo_sac.png', 10, 8, 33)
        except: pass
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 50, 100)
        self.cell(40); self.cell(0, 10, 'PRESUPUESTO SERVICIO AUTOMOTRIZ', 0, 1, 'C')
        self.set_font('Arial', '', 9)
        self.cell(40); self.cell(0, 5, 'AV. CENTRAL GONZALO PEREZ LLONA 598 B, MAIPÚ', 0, 1, 'C')
        self.cell(40); self.cell(0, 5, 'TELÉFONO: +56 9 8687 6856', 0, 1, 'C')
        self.ln(10)

def generar_pdf(datos_c, piezas_v, reparaciones, repuestos, totales):
    pdf = PDF()
    pdf.add_page()
    pdf.set_fill_color(0, 64, 128); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 8, "DATOS DEL CLIENTE Y VEHÍCULO", 0, 1, 'L', fill=True)
    pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", '', 10); pdf.ln(2)
    
    pdf.cell(95, 7, f"CLIENTE: {datos_c.get('Nombre','')}", 0); pdf.cell(95, 7, f"RUT: {datos_c.get('RUT','')}", 0, 1)
    pdf.cell(95, 7, f"VEHÍCULO: {datos_c.get('Vehículo','')}", 0); pdf.cell(95, 7, f"COLOR: {datos_c.get('Color','')}", 0, 1)
    pdf.cell(95, 7, f"PATENTE: {datos_c.get('Patente','')}", 0); pdf.cell(95, 7, f"AÑO: {datos_c.get('Año','')}", 0, 1)
    pdf.cell(95, 7, f"FECHA: {datos_c.get('Fecha','')}", 0); pdf.cell(95, 7, f"TELÉFONO: {datos_c.get('Teléfono','')}", 0, 1)
    pdf.ln(5)

    pdf.set_fill_color(0, 64, 128); pdf.set_text_color(255, 255, 255)
    pdf.cell(140, 8, "DESCRIPCIÓN PIEZA / TRABAJO", 1, 0, 'C', fill=True)
    pdf.cell(50, 8, "VALOR", 1, 1, 'C', fill=True)
    pdf.set_text_color(0, 0, 0)
    
    for p, v in piezas_v.items():
        if v > 0:
            pdf.cell(140, 8, f"  PINTURA: {p}", 1); pdf.cell(50, 8, f"${v:,}", 1, 1, 'R')
    for r in reparaciones:
        pdf.cell(140, 8, f"  TRABAJO: {r['desc']}", 1); pdf.cell(50, 8, f"${r['val']:,}", 1, 1, 'R')
    for s in repuestos:
        pdf.cell(140, 8, f"  REPUESTO: {s['desc']}", 1); pdf.cell(50, 8, f"${s['val']:,}", 1, 1, 'R')
            
    pdf.ln(5); pdf.set_font('Arial', 'B', 11)
    pdf.cell(140, 8, "NETO:", 0, 0, 'R'); pdf.cell(50, 8, f"${totales['Neto']:,}", 0, 1, 'R')
    pdf.cell(140, 8, "IVA (19%):", 0, 0, 'R'); pdf.cell(50, 8, f"${totales['IVA']:,}", 0, 1, 'R')
    pdf.set_font('Arial', 'B', 13); pdf.set_text_color(0, 64, 128)
    pdf.cell(140, 10, "TOTAL:", 0, 0, 'R'); pdf.cell(50, 10, f"${totales['Total']:,}", 0, 1, 'R')
    return bytes(pdf.output())

# --- ESTADO DE SESIÓN ---
if 'reparaciones' not in st.session_state: st.session_state.reparaciones = []
if 'repuestos' not in st.session_state: st.session_state.repuestos = []

tab1, tab2 = st.tabs(["📝 Nuevo Presupuesto", "📁 Historial Nube"])

with tab1:
    st.subheader("Datos Generales")
    c1, c2, c3 = st.columns(3)
    nombre = c1.text_input("Cliente")
    rut = c1.text_input("RUT")
    marca = c2.text_input("Marca/Modelo")
    color_v = c2.text_input("Color")
    patente = c3.text_input("Patente").upper()
    año_v = c3.text_input("Año")
    
    col_tel1, col_tel2 = st.columns([1, 2])
    tel_v = col_tel1.text_input("Teléfono")
    fecha_v = col_tel2.date_input("Fecha", datetime.now())

    st.markdown("---")
    st.subheader("🛠️ Detalle Pintura")
    piezas = ["PARACHOQUE DEL", "PARACHOQUE TRA", "TAPABARRO IZQ", "TAPABARRO DER", "PUERTA DEL IZQ", "PUERTA DEL DER", "PUERTA TRA IZQ", "PUERTA TRA DER", "TAPABARRO TRAS IZQ", "TAPABARRO TRAS DER", "TECHO", "MALETA", "ZOCALO IZQ", "ZOCALO DER", "ESPEJO IZQ", "ESPEJO DER", "CAPOT"]
    valores_piezas = {}
    col_p1, col_p2 = st.columns(2)
    for i, p in enumerate(piezas):
        target_col = col_p1 if i % 2 == 0 else col_p2
        valores_piezas[p] = target_col.number_input(f"{p} $", min_value=0, step=500, key=f"p_{p}")

    st.markdown("---")
    c_r, c_s = st.columns(2)
    with c_r:
        st.subheader("👨‍🔧 Trabajos Adicionales")
        d_r = st.text_input("Descripción Trabajo", key="txt_r")
        v_r = st.number_input("Valor Trabajo $", min_value=0, key="val_r")
        if st.button("➕ Añadir Trabajo"):
            if d_r and v_r > 0:
                st.session_state.reparaciones.append({"desc": d_r, "val": v_r}); st.rerun()
        for r in st.session_state.reparaciones: st.markdown(f"<div class='item-lista'>🔧 {r['desc']} - ${r['val']:,}</div>", unsafe_allow_html=True)

    with c_s:
        st.subheader("📦 Repuestos")
        d_s = st.text_input("Descripción Repuesto", key="txt_s")
        v_s = st.number_input("Valor Repuesto $", min_value=0, key="val_s")
        if st.button("➕ Añadir Repuesto"):
            if d_s and v_s > 0:
                st.session_state.repuestos.append({"desc": d_s, "val": v_s}); st.rerun()
        for s in st.session_state.repuestos: st.markdown(f"<div class='item-lista'>📦 {s['desc']} - ${s['val']:,}</div>", unsafe_allow_html=True)

    # CÁLCULOS
    neto = sum(valores_piezas.values()) + sum(r['val'] for r in st.session_state.reparaciones) + sum(s['val'] for s in st.session_state.repuestos)
    iva = int(neto * 0.19)
    total = neto + iva

    st.markdown("---")
    st.write(f"### TOTAL PRESUPUESTO: ${total:,}")

    if st.button("💾 GUARDAR EN GOOGLE SHEETS"):
        if nombre and patente:
            try:
                df_actual = conn.read()
                nueva_fila = pd.DataFrame([{
                    "fecha": fecha_v.strftime("%d/%m/%Y"), "cliente": nombre, "rut": rut,
                    "patente": patente, "modelo": marca, "color": color_v, "año": año_v,
                    "telefono": tel_v, "neto": neto, "total": total, "detalle": f"Items: {len(st.session_state.reparaciones) + len(st.session_state.repuestos)}"
                }])
                df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
                conn.update(data=df_final)
                st.success("✅ Guardado exitosamente en la nube.")
            except Exception as e: st.error(f"Error de conexión: {e}")
        else: st.warning("Por favor rellena Cliente y Patente.")

    # Generación de PDF
    datos_pdf = {"Nombre": nombre, "RUT": rut, "Vehículo": marca, "Color": color_v, "Patente": patente, "Año": año_v, "Teléfono": tel_v, "Fecha": fecha_v.strftime("%d/%m/%Y")}
    pdf_bytes = generar_pdf(datos_pdf, valores_piezas, st.session_state.reparaciones, st.session_state.repuestos, {"Neto": neto, "IVA": iva, "Total": total})
    st.download_button("📩 DESCARGAR PDF", data=pdf_bytes, file_name=f"Presupuesto_{patente}.pdf", mime="application/pdf")

with tab2:
    st.subheader("Historial de Presupuestos (Nube)")
    try:
        df_cloud = conn.read()
        if not df_cloud.empty:
            # Mostrar de más reciente a más antiguo
            for i, row in df_cloud.iloc[::-1].iterrows():
                with st.expander(f"📄 {row['fecha']} - {row['cliente']} | {row['patente']} | ${row['total']:,}"):
                    c_h1, c_h2 = st.columns([2, 1])
                    with c_h1:
                        st.write(f"**Vehículo:** {row['modelo']} ({row['color']})")
                        st.write(f"**RUT:** {row['rut']} | **Tel:** {row['telefono']}")
                    with c_h2:
                        # Re-generar PDF desde historial (datos básicos)
                        datos_h = {"Nombre": row['cliente'], "RUT": row['rut'], "Vehículo": row['modelo'], "Color": row['color'], "Patente": row['patente'], "Año": row['año'], "Teléfono": row['telefono'], "Fecha": row['fecha']}
                        pdf_h = generar_pdf(datos_h, {}, [], [], {"Neto": int(row['neto']), "IVA": int(row['total']-row['neto']), "Total": int(row['total'])})
                        st.download_button("📥 Descargar Copia", data=pdf_h, file_name=f"Copia_{row['patente']}.pdf", key=f"btn_{i}")
        else:
            st.info("Aún no hay datos en la planilla de Google.")
    except Exception as e:
        st.error("Error al leer Google Sheets. Verifica los 'Secrets' en Streamlit Cloud.")