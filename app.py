import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection
import urllib.parse

# Configuración de página
st.set_page_config(page_title="SAC Contreras - Gestión Nube", layout="wide")

# Conector a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNCIÓN GENERAR PDF ---
def generar_pdf(datos, piezas, reparaciones, repuestos, totales):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Logo en el PDF
        try:
            pdf.image("logo_sac.png", 10, 8, 33)
        except:
            pass
            
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "PRESUPUESTO DE SERVICIO", 0, 1, 'C')
        pdf.ln(10)
        
        # Datos Cliente
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "DATOS DEL CLIENTE / VEHICULO", 0, 1, 'L')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 7, f"Cliente: {datos.get('Nombre')} | RUT: {datos.get('RUT')}", 0, 1)
        pdf.cell(0, 7, f"Vehiculo: {datos.get('Vehiculo')} | Patente: {datos.get('Patente')}", 0, 1)
        pdf.cell(0, 7, f"Fecha: {datos.get('Fecha')}", 0, 1)
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
        pdf.cell(0, 10, f"NETO: ${totales['Neto']:,}", 0, 1, 'R')
        pdf.cell(0, 10, f"IVA (19%): ${totales['IVA']:,}", 0, 1, 'R')
        pdf.cell(0, 10, f"TOTAL FINAL: ${totales['Total']:,}", 0, 1, 'R')
        
        return pdf.output(dest='S').encode('latin-1')
    except:
        return None

# --- ESTRUCTURA DE PESTAÑAS ---
tab1, tab2 = st.tabs(["📝 Crear Presupuesto", "📂 Historial Nube"])

with tab1:
    # --- LOGO EN LA APP (MÁS GRANDE) ---
    col_logo, col_vacia = st.columns([1, 1]) # Ajuste de columnas para el logo más grande
    with col_logo:
        try:
            st.image("logo_sac.png", width=500) # LOGO DOBLE DE GRANDE
        except:
            st.info("Sube 'logo_sac.png' a GitHub para verlo aquí.")
    
    st.divider()
    
    # --- TÍTULO "DATOS" ---
    st.header("📋 Datos")
    
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del Cliente")
        rut = st.text_input("RUT")
        marca = st.text_input("Marca/Modelo")
        patente = st.text_input("Patente")
    with col2:
        color_v = st.text_input("Color")
        año_v = st.text_input("Año")
        tel_v = st.text_input("Teléfono (Ej: 56912345678)")
        fecha_v = st.date_input("Fecha", datetime.now())

    st.divider()

    # Sección Pintura
    st.subheader("🎨 Pintura por Pieza")
    piezas_lista = ["Capot", "Techo", "Puerta DL", "Puerta DR", "Puerta TL", "Puerta TR", "Tapabarro DL", "Tapabarro DR", "Parachoques Del", "Parachoques Tras"]
    valores_piezas = {}
    cols = st.columns(3)
    for i, pieza in enumerate(piezas_lista):
        valores_piezas[pieza] = cols[i % 3].number_input(f"{pieza} $", min_value=0, step=1000, key=f"p_{i}")

    # Reparaciones y Repuestos (Uso de Session State)
    if 'reparaciones' not in st.session_state: st.session_state.reparaciones = []
    if 'repuestos' not in st.session_state: st.session_state.repuestos = []

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔧 Reparaciones Adicionales")
        det_rep = st.text_input("Detalle Trabajo", key="det_rep")
        val_rep = st.number_input("Valor $", min_value=0, key="val_rep")
        if st.button("➕ Añadir Trabajo"):
            st.session_state.reparaciones.append({"detalle": det_rep, "valor": val_rep})
    with c2:
        st.subheader("📦 Repuestos")
        det_res = st.text_input("Detalle Repuesto", key="det_res")
        val_res = st.number_input("Valor Repuesto $", min_value=0, key="val_res")
        if st.button("➕ Agregar Repuesto"):
            st.session_state.repuestos.append({"detalle": det_res, "valor": val_res})

    # CÁLCULOS
    neto_p = sum(valores_piezas.values())
    neto_r = sum(item['valor'] for item in st.session_state.reparaciones)
    neto_rep = sum(item['valor'] for item in st.session_state.repuestos)
    
    neto_total = neto_p + neto_r + neto_rep
    iva_calc = int(neto_total * 0.19)
    total_final = neto_total + iva_calc

    st.divider()
    
    # Resumen de Totales
    st.write(f"**Neto:** ${neto_total:,}")
    st.write(f"**IVA (19%):** ${iva_calc:,}")
    st.header(f"TOTAL: ${total_final:,}")

    # BOTONES DE ACCIÓN
    b1, b2, b3 = st.columns(3)
    
    with b1:
        if st.button("💾 GUARDAR EN NUBE", use_container_width=True):
            if nombre and patente:
                try:
                    df_actual = conn.read()
                    nueva_fila = pd.DataFrame([{
                        "fecha": fecha_v.strftime("%d/%m/%Y"), "cliente": nombre, "rut": rut,
                        "patente": patente, "modelo": marca, "color": color_v, "año": año_v,
                        "telefono": tel_v, "neto": neto_total, "total": total_final
                    }])
                    df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
                    conn.update(data=df_final)
                    st.success("✅ Datos guardados en Google Sheets")
                except Exception as e:
                    st.error(f"Error al conectar con la nube: {e}")
            else: st.error("Falta Nombre o Patente")

    with b2:
        datos_pdf = {"Nombre": nombre, "RUT": rut, "Vehiculo": marca, "Patente": patente, "Fecha": fecha_v.strftime("%d/%m/%Y")}
        pdf_bytes = generar_pdf(datos_pdf, valores_piezas, st.session_state.reparaciones, st.session_state.repuestos, {"Neto": neto_total, "IVA": iva_calc, "Total": total_final})
        if pdf_bytes:
            st.download_button("📩 DESCARGAR PDF", data=pdf_bytes, file_name=f"Presupuesto_{patente}.pdf", mime="application/pdf", use_container_width=True)

    with b3:
        # Generar link de WhatsApp
        msj = f"Hola {nombre}, te adjunto el presupuesto de SAC Contreras para el vehículo {marca} ({patente}). Total: ${total_final:,}. Saludos!"
        msj_codificado = urllib.parse.quote(msj)
        url_ws = f"https://wa.me/{tel_v}?text={msj_codificado}"
        st.link_button("📲 ENVIAR POR WHATSAPP", url_ws, use_container_width=True)

with tab2:
    st.subheader("📊 Historial de Presupuestos (Google Sheets)")
    try:
        data = conn.read()
        # Mostrar los últimos registros primero
        st.dataframe(data.iloc[::-1], use_container_width=True)
    except:
        st.info("Conecta tu Google Sheet en 'Advanced Settings' para ver el historial.")
