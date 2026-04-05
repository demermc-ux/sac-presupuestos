import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection

# Configuración de página
st.set_page_config(page_title="SAC Contreras - Gestión Nube", layout="wide")

# Conector a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIÓN PARA GENERAR PDF ---
def generar_pdf(datos, piezas, reparaciones, repuestos, totales):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Intentar cargar logo (si no existe, sigue sin el logo)
        try:
            pdf.image("logo_sac.png", 10, 8, 33)
        except:
            pass
            
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "PRESUPUESTO DE SERVICIO", 0, 1, 'C')
        pdf.ln(10)
        
        # Datos del Cliente
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "DATOS DEL CLIENTE / VEHICULO", 0, 1, 'L')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 7, f"Cliente: {datos['Nombre']} | RUT: {datos['RUT']}", 0, 1)
        pdf.cell(0, 7, f"Vehiculo: {datos['Vehículo']} | Patente: {datos['Patente']}", 0, 1)
        pdf.cell(0, 7, f"Fecha: {datos['Fecha']}", 0, 1)
        pdf.ln(5)

        # Detalle de Trabajos
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "DETALLE DE TRABAJOS", 0, 1, 'L')
        pdf.set_font("Arial", '', 10)
        for p, v in piezas.items():
            if v > 0:
                pdf.cell(0, 7, f"- Pintura {p}: ${v:,}", 0, 1)
        
        for r in reparaciones:
            pdf.cell(0, 7, f"- {r['detalle']}: ${r['valor']:,}", 0, 1)
            
        for rep in repuestos:
            pdf.cell(0, 7, f"- Repuesto: {rep['detalle']}: ${rep['valor']:,}", 0, 1)

        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"TOTAL NETO: ${totales['Neto']:,}", 0, 1, 'R')
        pdf.cell(0, 10, f"TOTAL FINAL (IVA INC.): ${totales['Total']:,}", 0, 1, 'R')
        
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        return None

# --- INTERFAZ STREAMLIT ---
st.title("🛠️ SAC Contreras - Presupuestos")

col1, col2 = st.columns(2)

with col1:
    nombre = st.text_input("Nombre del Cliente")
    rut = st.text_input("RUT")
    marca = st.text_input("Marca/Modelo")
    patente = st.text_input("Patente")

with col2:
    color_v = st.text_input("Color")
    año_v = st.text_input("Año")
    tel_v = st.text_input("Teléfono")
    fecha_v = st.date_input("Fecha", datetime.now())

st.divider()

# Sección Pintura
st.subheader("🎨 Pintura por Pieza")
piezas_lista = ["Capot", "Techo", "Puerta DL", "Puerta DR", "Puerta TL", "Puerta TR", "Tapabarro DL", "Tapabarro DR", "Parachoques Del", "Parachoques Tras"]
valores_piezas = {}
cols = st.columns(3)
for i, pieza in enumerate(piezas_lista):
    valores_piezas[pieza] = cols[i % 3].number_input(f"{pieza} $", min_value=0, step=1000)

# Reparaciones y Repuestos (Usando Session State)
if 'reparaciones' not in st.session_state: st.session_state.reparaciones = []
if 'repuestos' not in st.session_state: st.session_state.repuestos = []

st.divider()
c1, c2 = st.columns(2)

with c1:
    st.subheader("🔧 Reparaciones Adicionales")
    det_rep = st.text_input("Detalle Reparación")
    val_rep = st.number_input("Valor Reparación $", min_value=0)
    if st.button("➕ Añadir Trabajo"):
        st.session_state.reparaciones.append({"detalle": det_rep, "valor": val_rep})

with c2:
    st.subheader("📦 Repuestos")
    det_res = st.text_input("Detalle Repuesto")
    val_res = st.number_input("Valor Repuesto $", min_value=0)
    if st.button("➕ Agregar Repuesto"):
        st.session_state.repuestos.append({"detalle": det_res, "valor": val_res})

# CÁLCULOS
neto_pintura = sum(valores_piezas.values())
neto_reparaciones = sum(item['valor'] for item in st.session_state.reparaciones)
neto_repuestos = sum(item['valor'] for item in st.session_state.repuestos)

neto = neto_pintura + neto_reparaciones + neto_repuestos
iva = int(neto * 0.19)
total = neto + iva

st.divider()
st.header(f"PRESUPUESTO TOTAL: ${total:,}")

# BOTÓN GUARDAR EN GOOGLE SHEETS
if st.button("💾 GUARDAR EN GOOGLE SHEETS"):
    if nombre and patente:
        try:
            df_actual = conn.read()
            nueva_fila = pd.DataFrame([{
                "fecha": fecha_v.strftime("%d/%m/%Y"),
                "cliente": nombre,
                "patente": patente,
                "total": total,
                "detalle": f"Pintura: {neto_pintura} | Otros: {neto_reparaciones + neto_repuestos}"
            }])
            df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
            conn.update(data=df_final)
            st.success("✅ Guardado exitosamente en la nube.")
        except Exception as e:
            st.error(f"Error de conexión: {e}")
    else:
        st.warning("Por favor rellena Cliente y Patente.")

# GENERACIÓN DE PDF SEGURO
if total > 0:
    datos_pdf = {
        "Nombre": nombre, "RUT": rut, "Vehículo": marca, "Patente": patente, "Fecha": fecha_v.strftime("%d/%m/%Y")
    }
    pdf_bytes = generar_pdf(datos_pdf, valores_piezas, st.session_state.reparaciones, st.session_state.repuestos, {"Neto": neto, "Total": total})
    
    if pdf_bytes:
        st.download_button("📩 DESCARGAR PDF", data=pdf_bytes, file_name=f"Presupuesto_{patente}.pdf", mime="application/pdf")

# HISTORIAL
st.divider()
st.subheader("📂 Historial Nube (Google Sheets)")
try:
    df_historial = conn.read()
    st.dataframe(df_historial.tail(10), use_container_width=True)
except:
    st.info("Aún no hay datos en la planilla de Google.")
