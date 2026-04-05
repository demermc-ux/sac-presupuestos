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

# Conector a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. FUNCIÓN GENERAR PDF ---
def generar_pdf(datos, piezas, reparaciones, repuestos, totales):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Encabezado con Logo
        try:
            pdf.image("logo_sac.png", 10, 8, 43)
        except:
            pass
            
        pdf.set_font("Arial", 'B', 18)
        pdf.set_text_color(33, 37, 41)
        pdf.cell(0, 10, "PRESUPUESTO DE SERVICIO", 0, 1, 'R')
        
        # Datos del Taller
        pdf.set_font("Arial", 'B', 10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 5, "Servicio Automotriz Contreras", 0, 1, 'R')
        pdf.set_font("Arial", '', 9)
        pdf.cell(0, 5, "Av. Central Gonzalo Pérez Llona 598 B, Maipú", 0, 1, 'R')
        pdf.cell(0, 5, "Teléfono: +56 9 8687 6856", 0, 1, 'R')
        pdf.ln(10)
        
        # Cuadro Datos Cliente/Vehículo
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 10, "  DATOS DEL CLIENTE / VEHÍCULO", 1, 1, 'L', fill=True)
        
        pdf.set_font("Arial", '', 10)
        pdf.cell(95, 8, f" Cliente: {datos.get('Nombre')}", 1, 0)
        pdf.cell(95, 8, f" RUT: {datos.get('RUT')}", 1, 1)
        pdf.cell(95, 8, f" Vehículo: {datos.get('Vehiculo')}", 1, 0)
        pdf.cell(95, 8, f" Patente: {datos.get('Patente')}", 1, 1)
        pdf.cell(190, 8, f" Fecha: {datos.get('Fecha')}", 1, 1)
        pdf.ln(5)

        # Tabla de Detalles
        pdf.set_fill_color(52, 58, 64)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(140, 10, "  DESCRIPCIÓN DEL TRABAJO / REPUESTO", 1, 0, 'L', fill=True)
        pdf.cell(50, 10, " VALOR", 1, 1, 'C', fill=True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", '', 10)
        
        fill = False
        def agregar_fila(desc, valor, f):
            pdf.set_fill_color(248, 249, 250)
            pdf.cell(140, 8, f"  {desc}", 1, 0, 'L', fill=f)
            pdf.cell(50, 8, f" ${valor:,}  ", 1, 1, 'R', fill=f)
            return not f

        for p, v in piezas.items():
            if v > 0: fill = agregar_fila(f"Pintura: {p}", v, fill)
        for r in reparaciones:
            fill = agregar_fila(r['detalle'], r['valor'], fill)
        for rep in repuestos:
            fill = agregar_fila(f"Repuesto: {rep['detalle']}", rep['valor'], fill)

        pdf.ln(5)

        # Totales
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

# --- 3. ESTRUCTURA DE LA APP ---
tab1, tab2 = st.tabs(["📝 Nuevo Presupuesto", "📂 Historial en Drive"])

if 'reparaciones' not in st.session_state: st.session_state.reparaciones = []
if 'repuestos' not in st.session_state: st.session_state.repuestos = []

with tab1:
    try:
        st.image("logo_sac.png", width=350)
    except:
        st.title("SAC CONTRERAS")

    st.header("📋 Datos del Servicio")
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del Cliente")
        rut = st.text_input("RUT")
        marca = st.text_input("Vehículo (Marca/Modelo)")
        patente = st.text_input("Patente")
    with col2:
        color_v = st.text_input("Color")
        año_v = st.text_input("Año")
        tel_v = st.text_input("Teléfono (+569...)")
        fecha_v = st.date_input("Fecha", datetime.now())

    st.divider()
    st.subheader("🎨 Pintura")
    piezas = ["Capot", "Techo", "Puerta DL", "Puerta DR", "Puerta TL", "Puerta TR", "Tapabarro DL", "Tapabarro DR", "Parachoques Del", "Parachoques Tras"]
    valores_piezas = {}
    cols_p = st.columns(3)
    for i, p in enumerate(piezas):
        valores_piezas[p] = cols_p[i % 3].number_input(f"{p} $", min_value=0, step=5000, key=f"p_{p}")

    st.divider()
    c_rep, c_res = st.columns(2)
    with c_rep:
        st.subheader("🔧 Trabajos Adicionales")
        d_r = st.text_input("Descripción Trabajo")
        v_r = st.number_input("Valor Trabajo $", min_value=0, step=1000)
        if st.button("➕ Añadir Trabajo"):
            st.session_state.reparaciones.append({"detalle": d_r, "valor": v_r})
    with c_res:
        st.subheader("📦 Repuestos")
        d_s = st.text_input("Descripción Repuesto")
        v_s = st.number_input("Valor Repuesto $", min_value=0, step=1000)
        if st.button("➕ Añadir Repuesto"):
            st.session_state.repuestos.append({"detalle": d_s, "valor": v_s})

    # CÁLCULOS
    neto = sum(valores_piezas.values()) + sum(x['valor'] for x in st.session_state.reparaciones) + sum(x['valor'] for x in st.session_state.repuestos)
    iva = int(neto * 0.19)
    total = neto + iva

    st.divider()
    st.write(f"**Neto:** ${neto:,} | **IVA:** ${iva:,}")
    st.header(f"TOTAL: ${total:,}")

    # BOTONES
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("💾 GUARDAR EN NUBE", use_container_width=True):
            if nombre and patente:
                try:
                    # 1. LEER TODO Y ELIMINAR FILAS TOTALMENTE VACÍAS
                    try:
                        df_old = conn.read()
                        # Solo conservamos filas donde al menos haya un nombre o patente
                        df_old = df_old.dropna(subset=['cliente', 'patente'], how='all')
                    except:
                        df_old = pd.DataFrame()

                    # 2. CREAR NUEVA FILA
                    nueva_fila = pd.DataFrame([{
                        "fecha": fecha_v.strftime("%d/%m/%Y"),
                        "cliente": nombre,
                        "rut": rut,
                        "patente": patente,
                        "modelo": marca,
                        "color": color_v,
                        "año": año_v,
                        "telefono": tel_v,
                        "neto": neto,
                        "total": total
                    }])

                    # 3. UNIR Y LIMPIAR EL ÍNDICE
                    df_final = pd.concat([df_old, nueva_fila], ignore_index=True)
                    
                    # 4. SOBREESCRIBIR TODA LA TABLA CON LA LISTA EXTENDIDA
                    conn.update(data=df_final)
                    st.success(f"✅ Guardado en Drive. Total registros: {len(df_final)}")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
            else:
                st.warning("Nombre y Patente son obligatorios para guardar.")

    with b2:
        pdf_file = generar_pdf({"Nombre": nombre, "RUT": rut, "Vehiculo": marca, "Patente": patente, "Fecha": fecha_v.strftime("%d/%m/%Y")}, valores_piezas, st.session_state.reparaciones, st.session_state.repuestos, {"Neto": neto, "IVA": iva, "Total": total})
        if pdf_file:
            st.download_button("📩 DESCARGAR PDF", data=pdf_file, file_name=f"Presupuesto_{patente}.pdf", mime="application/pdf", use_container_width=True)

    with b3:
        msg = f"Hola {nombre}, te envío el presupuesto de SAC Contreras para el vehículo {marca} patente {patente}. Total: ${total:,}."
        st.link_button("📲 ENVIAR WHATSAPP", f"https://wa.me/{tel_v}?text={urllib.parse.quote(msg)}", use_container_width=True)

with tab2:
    st.subheader("📊 Registros Guardados")
    try:
        data = conn.read()
        # Filtramos para mostrar solo lo real en la tabla de la app
        data_show = data.dropna(subset=['cliente', 'patente'], how='all')
        if not data_show.empty:
            st.dataframe(data_show.iloc[::-1], use_container_width=True)
        else:
            st.info("No hay registros aún.")
    except:
        st.write("Conectando con Google Sheets...")
