import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
import io
import urllib.parse

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="SAC Contreras", page_icon="logo_sac.png", layout="wide")

# ID de tu carpeta que me pasaste
ID_CARPETA_DRIVE = "1L89gLrT_0RqoZxQH3-_dCv-SfeUGx-Oveuovpwf7izA"

# Autenticación para Google Drive (usa tus Secrets actuales)
def get_drive_service():
    info = st.secrets["connections"]["gsheets"]
    creds = service_account.Credentials.from_service_account_info(
        info, 
        scopes=["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    )
    return build('drive', 'v3', credentials=creds)

# --- 2. FUNCIÓN GENERAR PDF PROFESIONAL ---
def generar_pdf(datos, piezas, reparaciones, repuestos, totales):
    try:
        pdf = FPDF()
        pdf.add_page()
        try:
            pdf.image("logo_sac.png", 10, 8, 43)
        except: pass
            
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 10, "PRESUPUESTO DE SERVICIO", 0, 1, 'R')
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 5, "Servicio Automotriz Contreras", 0, 1, 'R')
        pdf.set_font("Arial", '', 9)
        pdf.cell(0, 5, "Av. Central Gonzalo Pérez Llona 598 B, Maipú", 0, 1, 'R')
        pdf.cell(0, 5, "Teléfono: +56 9 8687 6856", 0, 1, 'R')
        pdf.ln(10)
        
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 10, "  DATOS DEL CLIENTE / VEHÍCULO", 1, 1, 'L', fill=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(95, 8, f" Cliente: {datos['Nombre']}", 1, 0)
        pdf.cell(95, 8, f" RUT: {datos['RUT']}", 1, 1)
        pdf.cell(95, 8, f" Vehículo: {datos['Vehiculo']}", 1, 0)
        pdf.cell(95, 8, f" Patente: {datos['Patente']}", 1, 1)
        pdf.cell(190, 8, f" Fecha: {datos['Fecha']}", 1, 1)
        pdf.ln(5)

        pdf.set_fill_color(52, 58, 64)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(140, 10, "  DESCRIPCIÓN", 1, 0, 'L', fill=True)
        pdf.cell(50, 10, " VALOR", 1, 1, 'C', fill=True)
        pdf.set_text_color(0, 0, 0)
        
        fill = False
        def agregar_fila(desc, valor, f):
            pdf.set_fill_color(248, 249, 250)
            pdf.cell(140, 8, f"  {desc}", 1, 0, 'L', fill=f)
            pdf.cell(50, 8, f" ${valor:,} ", 1, 1, 'R', fill=f)
            return not f

        for p, v in piezas.items():
            if v > 0: fill = agregar_fila(f"Pintura: {p}", v, fill)
        for r in reparaciones:
            fill = agregar_fila(r['detalle'], r['valor'], fill)
        for rep in repuestos:
            fill = agregar_fila(f"Repuesto: {rep['detalle']}", rep['valor'], fill)

        pdf.ln(5)
        pdf.set_fill_color(33, 37, 41)
        pdf.set_text_color(255, 255, 255)
        pdf.set_x(110)
        pdf.cell(40, 12, "  TOTAL:", 1, 0, 'L', fill=True)
        pdf.cell(50, 12, f" ${totales['Total']:,}  ", 1, 1, 'R', fill=True)
        
        return pdf.output(dest='S').encode('latin-1')
    except: return None

# --- 3. INTERFAZ ---
st.title("🚗 SAC Contreras - Generador de Presupuestos")

if 'reparaciones' not in st.session_state: st.session_state.reparaciones = []
if 'repuestos' not in st.session_state: st.session_state.repuestos = []

col_d1, col_d2 = st.columns(2)
with col_d1:
    nombre = st.text_input("Nombre del Cliente")
    rut = st.text_input("RUT")
    marca = st.text_input("Vehículo (Modelo)")
with col_d2:
    patente = st.text_input("Patente")
    tel_v = st.text_input("Teléfono (+569...)")
    fecha_v = st.date_input("Fecha", datetime.now())

st.divider()
st.subheader("🎨 Pintura por Pieza")
piezas_nom = ["Capot", "Techo", "Puerta DL", "Puerta DR", "Puerta TL", "Puerta TR", "Tapabarro DL", "Tapabarro DR", "Parachoques Del", "Parachoques Tras"]
valores_p = {}
c_p = st.columns(3)
for i, p in enumerate(piezas_nom):
    valores_p[p] = c_p[i % 3].number_input(f"{p} $", min_value=0, step=5000, key=f"p_{i}")

st.divider()
c_a, c_b = st.columns(2)
with c_a:
    st.subheader("🔧 Otros Trabajos")
    d_t = st.text_input("Detalle")
    v_t = st.number_input("Valor $", min_value=0, key="v_t")
    if st.button("➕ Añadir"): st.session_state.reparaciones.append({"detalle": d_t, "valor": v_t})
with c_b:
    st.subheader("📦 Repuestos")
    d_s = st.text_input("Nombre Repuesto")
    v_s = st.number_input("Precio $", min_value=0, key="v_s")
    if st.button("➕ Agregar"): st.session_state.repuestos.append({"detalle": d_s, "valor": v_s})

# Totales
neto = sum(valores_p.values()) + sum(x['valor'] for x in st.session_state.reparaciones) + sum(x['valor'] for x in st.session_state.repuestos)
total_f = int(neto * 1.19)
st.header(f"TOTAL: ${total_f:,}")

st.divider()
b_nube, b_pdf, b_ws = st.columns(3)

with b_nube:
    if st.button("💾 GUARDAR PDF EN DRIVE", use_container_width=True):
        if nombre and patente:
            try:
                datos_p = {"Nombre": nombre, "RUT": rut, "Vehiculo": marca, "Patente": patente, "Fecha": fecha_v.strftime("%d/%m/%Y")}
                pdf_c = generar_pdf(datos_p, valores_p, st.session_state.reparaciones, st.session_state.repuestos, {"Total": total_f})
                
                if pdf_c:
                    service = get_drive_service()
                    nombre_archivo = f"Presupuesto_{patente}_{datetime.now().strftime('%H%M')}.pdf"
                    
                    file_metadata = {'name': nombre_archivo, 'parents': [ID_CARPETA_DRIVE]}
                    media = MediaIoBaseUpload(io.BytesIO(pdf_c), mimetype='application/pdf')
                    
                    service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                    st.success(f"✅ Archivo '{nombre_archivo}' guardado en tu Drive.")
            except Exception as e:
                st.error(f"Error: {e}")
        else: st.warning("Nombre y Patente obligatorios")

with b_pdf:
    # Opción de descarga manual
    datos_p = {"Nombre": nombre, "RUT": rut, "Vehiculo": marca, "Patente": patente, "Fecha": fecha_v.strftime("%d/%m/%Y")}
    pdf_c = generar_pdf(datos_p, valores_p, st.session_state.reparaciones, st.session_state.repuestos, {"Total": total_f})
    if pdf_c:
        st.download_button("📩 BAJAR PDF", data=pdf_c, file_name=f"SAC_{patente}.pdf", mime="application/pdf", use_container_width=True)

with b_ws:
    txt = f"Hola {nombre}, presupuesto SAC Contreras para {marca} ({patente}). Total: ${total_f:,}."
    st.link_button("📲 WHATSAPP", f"https://wa.me/{tel_v}?text={urllib.parse.quote(txt)}", use_container_width=True)
