import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection
import urllib.parse

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="SAC Contreras",
    page_icon="logo_sac.png", 
    layout="wide"
)

# Conector a Google Sheets (usa los Secrets configurados)
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. FUNCIÓN GENERAR PDF PROFESIONAL ---
def generar_pdf(datos, piezas, reparaciones, repuestos, totales):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Logo y Título
        try:
            pdf.image("logo_sac.png", 10, 8, 45)
        except:
            pass
            
        pdf.set_font("Arial", 'B', 18)
        pdf.set_text_color(33, 37, 41)
        pdf.cell(0, 10, "PRESUPUESTO DE SERVICIO", 0, 1, 'R')
        
        # Datos del Taller (Gabriel Contreras)
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 5, "Servicio Automotriz Contreras", 0, 1, 'R')
        pdf.set_font("Arial", '', 9)
        pdf.cell(0, 5, "Av. Central Gonzalo Pérez Llona 598 B, Maipú", 0, 1, 'R')
        pdf.cell(0, 5, "Teléfono: +56 9 8687 6856", 0, 1, 'R')
        pdf.ln(10)
        
        # Cuadro Datos Cliente
        pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 10, "  DATOS DEL CLIENTE / VEHÍCULO", 1, 1, 'L', fill=True)
        
        pdf.set_font("Arial", '', 10)
        pdf.cell(95, 8, f" Cliente: {datos.get('Nombre')}", 1, 0)
        pdf.cell(95, 8, f" RUT: {datos.get('RUT')}", 1, 1)
        pdf.cell(95, 8, f" Vehículo: {datos.get('Vehiculo')}", 1, 0)
        pdf.cell(95, 8, f" Patente: {datos.get('Patente')}", 1, 1)
        pdf.cell(190, 8, f" Fecha: {datos.get('Fecha')}", 1, 1)
        pdf.ln(5)

        # Tabla de Detalles (Diseño con cuadrículas)
        pdf.set_fill_color(52, 58, 64)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(140, 10, "  DESCRIPCIÓN DEL TRABAJO / REPUESTO", 1, 0, 'L', fill=True)
        pdf.cell(50, 10, " VALOR", 1, 1, 'C', fill=True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", '', 10)
        
        def agregar_fila(desc, valor, f):
            pdf.set_fill_color(248, 249, 250)
            pdf.cell(140, 8, f"  {desc}", 1, 0, 'L', fill=f)
            pdf.cell(50, 8, f" ${valor:,}  ", 1, 1, 'R', fill=f)
            return not f

        fill = False
        for p, v in piezas.items():
            if v > 0: fill = agregar_fila(f"Pintura: {p}", v, fill)
        for r in reparaciones:
            fill = agregar_fila(r['detalle'], r['valor'], fill)
        for rep in repuestos:
            fill = agregar_fila(f"Repuesto: {rep['detalle']}", rep['valor'], fill)

        pdf.ln(5)

        # Cuadro de Totales
        pdf.set_x(110)
        pdf.cell(40, 10, "  NETO:", 1, 0, 'L')
        pdf.cell(50, 10, f" ${totales['Neto']:,}  ", 1, 1, 'R')
        pdf.set_x(110)
        pdf.cell(40, 10, "  IVA (19%):", 1, 0, 'L')
        pdf.cell(50, 10, f" ${totales['IVA']:,}  ", 1, 1, 'R')
        
        pdf.set_fill_color(33, 37, 41)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 12)
        pdf.set_x(110)
        pdf.cell(40, 12, "  TOTAL:", 1, 0, 'L', fill=True)
        pdf.cell(50, 12, f" ${totales['Total']:,}  ", 1, 1, 'R', fill=True)
        
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        return None

# --- 3. INTERFAZ DE USUARIO ---
tab1, tab2 = st.tabs(["📝 Crear Presupuesto", "📂 Historial Nube"])

with tab1:
    col_logo, _ = st.columns([1, 1])
    with col_logo:
        try:
            st.image("logo_sac.png", width=400)
        except:
            st.info("Sube el archivo 'logo_sac.png' a tu repositorio de GitHub.")
    
    st.divider()
    st.header("📋 Datos del Cliente")
    
    c1, c2 = st.columns(2)
    with c1:
        nombre = st.text_input("Nombre del Cliente")
        rut = st.text_input("RUT")
        marca = st.text_input("Marca/Modelo")
        patente = st.text_input("Patente")
    with c2:
        color_v = st.text_input("Color")
        año_v = st.text_input("Año")
        tel_v = st.text_input("Teléfono Cliente")
        fecha_v = st.date_input("Fecha", datetime.now())

    st.divider()
    st.subheader("🎨 Pintura por Pieza")
    piezas_lista = ["Capot", "Techo", "Puerta DL", "Puerta DR", "Puerta TL", "Puerta TR", "Tapabarro DL", "Tapabarro DR", "Parachoques Del", "Parachoques Tras"]
    valores_piezas = {}
    cols = st.columns(3)
    for i, pieza in enumerate(piezas_lista):
        valores_piezas[pieza] = cols[i % 3].number_input(f"{pieza} $", min_value=0, step=1000, key=f"p_{i}")

    if 'reparaciones' not in st.session_state: st.session_state.reparaciones = []
    if 'repuestos' not in st.session_state: st.session_state.repuestos = []

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🔧 Reparaciones / Desabolladura")
        det_rep = st.text_input("Detalle del Trabajo", key="det_rep")
        val_rep = st.number_input("Valor Trabajo $", min_value=0, key="val_rep")
        if st.button("➕ Añadir Trabajo"):
            st.session_state.reparaciones.append({"detalle": det_rep, "valor": val_rep})
            st.rerun()
    with col_b:
        st.subheader("📦 Repuestos")
        det_res = st.text_input("Detalle Repuesto", key="det_res")
        val_res = st.number_input("Valor Repuesto $", min_value=0, key="val_res")
        if st.button("➕ Agregar Repuesto"):
            st.session_state.repuestos.append({"detalle": det_res, "valor": val_res})
            st.rerun()

    # Cálculos Finales
    neto_total = sum(valores_piezas.values()) + sum(r['valor'] for r in st.session_state.reparaciones) + sum(rep['valor'] for rep in st.session_state.repuestos)
    iva_calc = int(neto_total * 0.19)
    total_final = neto_total + iva_calc

    st.divider()
    st.write(f"**Neto:** ${neto_total:,}")
    st.write(f"**IVA (19%):** ${iva_calc:,}")
    st.header(f"TOTAL: ${total_final:,}")

    # BOTONES DE ACCIÓN
    b1, b2, b3 = st.columns(3)
    
    with b1:
        if st.button("💾 GUARDAR EN NUBE", use_container_width=True):
            if nombre and patente:
                try:
                    # LEER HISTORIAL ACTUAL PARA NO SOBREESCRIBIR
                    try:
                        df_actual = conn.read()
                    except:
                        df_actual = pd.DataFrame()

                    nueva_fila = pd.DataFrame([{
                        "fecha": fecha_v.strftime("%d/%m/%Y"), 
                        "cliente": nombre, 
                        "patente": patente,
                        "neto": neto_total, 
                        "total": total_final
                    }])
                    
                    # CONCATENAR (AÑADIR AL FINAL)
                    df_final = pd.concat([df_actual, nueva_fila], ignore_index=True)
                    conn.update(data=df_final)
                    st.success(f"✅ Guardado: {nombre}")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")
            else: st.error("Faltan datos obligatorios (Nombre/Patente)")

    with b2:
        datos_pdf = {"Nombre": nombre, "RUT": rut, "Vehiculo": marca, "Patente": patente, "Fecha": fecha_v.strftime("%d/%m/%Y")}
        pdf_bytes = generar_pdf(datos_pdf, valores_piezas, st.session_state.reparaciones, st.session_state.repuestos, {"Neto": neto_total, "IVA": iva_calc, "Total": total_final})
        if pdf_bytes:
            st.download_button("📩 DESCARGAR PDF", data=pdf_bytes, file_name=f"Presupuesto_{patente}.pdf", mime="application/pdf", use_container_width=True)

    with b3:
        msj = f"Hola {nombre}, adjunto presupuesto SAC Contreras para {marca} ({patente}). Total: ${total_final:,}."
        url_ws = f"https://wa.me/{tel_v}?text={urllib.parse.quote(msj)}"
        st.link_button("📲 ENVIAR WHATSAPP", url_ws, use_container_width=True)

# --- 4. PESTAÑA HISTORIAL ---
with tab2:
    st.subheader("📊 Historial de Presupuestos Guardados")
    try:
        data = conn.read()
        if not data.empty:
            st.dataframe(data.iloc[::-1], use_container_width=True) # Muestra el más reciente arriba
        else:
            st.write("No hay datos registrados aún.")
    except:
        st.info("Esperando conexión con Google Sheets...")
