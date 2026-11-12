import os
import re
import tkinter as tk
from tkinter import messagebox, filedialog

def limpiar_mac(mac_sucia):
    # Remueve dos puntos, guiones, espacios y lo pasa a minúsculas
    return re.sub(r"[\s:-]", "", mac_sucia).lower()

def generar_xml(sv_ip, mac, extension, secret, pb_url, pb_name, firmware_url):
    # Plantilla XML estructurada para Htek
    plantilla = f"""<?xml version="1.0" encoding="UTF-8"?>
<hl_provision version="1">
  <config version="1">
    <!--1=Linea activa y 2=Linea inactiva-->
    <P271 para="Account1_Active">1</P271>

    <!--Nombre que se pone en la PBX-->
    <P20000 para="Account1_Label">{extension}</P20000>

    <!--SIP User ID-->
    <P35 para="Account1_SipUserId">{extension}</P35>

    <!--Authenticate ID-->
    <P36 para="Account1_AuthenticateID">{extension}</P36>

    <!--Pass de la extension en la PBX-->
    <P34 para="Account1_AuthenticatePassword">{secret}</P34>

    <!--Nombre que aparece en la pantalla física del teléfono-->
    <P3 para="Account1_DispalyName">{extension}</P3>

    <!--Puerto SIP-->
    <P40 para="Account1_LocalSipport">5060</P40>

    <!--Habilita el registro SIP (Importante, de lo contrario, no establece registro)-->
    <P31 para="Profile1_SipRegistration">1</P31>

    <!--IP Servidor SIP primario-->
    <P47 para="Profile1_Sipserver">{sv_ip}</P47>

    <!--Idioma del telefono, no de la WEB. "3" es igual a Español-->
    <P8621 para="Preference_LcdLanguage">3</P8621>

    <!--Zona horaria, "21" es -4 Chile(Santiago) y "28 es -3 Argentina(Buenos Aires)-->
    <P64 para="Preference_TimeZone">28</P64>

    <!--Servidor NTP-->
    <P30 para="NW_Adv_UrlOrIpAddress">ntp_shoa.cl</P30>

    <!--Ruta de actualización automática de Firmware para este Tel. IP-->
    <P192 para="Auto_Image_Url">{firmware_url}</P192>

    <!--Enlace de la agenda remota-->
    <P4401 para="RemotePhoneBook1_Url">{pb_url}</P4401>

    <!--Nombre en que aparece la agenda en el menú de usuario-->
    <P3316 para="RemotePhoneBook1_Name">{pb_name}</P3316>

    <!--Selecciona el usuario a modificar-->
    <P8681 para="LogUser_Admin">admin</P8681>
    
    <!--Modifica la clave de acceso de admin-->
    <P2 para="AdminPassword">ELIGE AQUI LA CONTRASEÑA WEB</P2>
  </config>
</hl_provision>"""
    return plantilla

def seleccionar_carpeta(entry_carpeta):
    # Abre una ventana para elegir la carpeta de destino de forma visual
    carpeta_elegida = filedialog.askdirectory(title="Selecciona la carpeta donde guardar los XML")
    if carpeta_elegida:
        entry_carpeta.delete(0, tk.END)
        entry_carpeta.insert(0, carpeta_elegida)

def procesar_datos(entry_sv_ip, entry_pb_url, entry_pb_name, entry_firmware_url, entry_carpeta, text_datos):
    sv_ip = entry_sv_ip.get().strip()
    pb_url = entry_pb_url.get().strip()
    pb_name = entry_pb_name.get().strip()
    firmware_default = entry_firmware_url.get().strip()
    
    # Obtener la carpeta elegida por el usuario, o usar una por defecto si está vacío
    carpeta_personalizada = entry_carpeta.get().strip()
    if carpeta_personalizada:
        carpeta_salida = carpeta_personalizada
    else:
        carpeta_salida = os.path.join(os.getcwd(), "cfg_htek")

    if not sv_ip:
        messagebox.showerror("Error", "Debes ingresar al menos la IP del Servidor SIP.")
        return

    texto_bruto = text_datos.get("1.0", tk.END).strip()
    if not texto_bruto:
        messagebox.showerror("Error", "La lista está vacía. Pega las filas desde Excel.")
        return

    try:
        os.makedirs(carpeta_salida, exist_ok=True)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo crear o acceder a la carpeta de salida:\n{e}")
        return

    conteo = 0
    lineas = texto_bruto.split("\n")

    try:
        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue

            # Separador flexible: detecta tabulaciones (\t), comas (,) o espacios múltiples (\s+)
            partes = [p.strip() for p in re.split(r'[\t,\s]+', linea) if p.strip()]

            # Mínimo 3 columnas obligatorias: MAC, Extensión, Secret
            if len(partes) < 3:
                continue

            mac_limpia = limpiar_mac(partes[0])
            ext = partes[1]
            secret = partes[2]

            if len(mac_limpia) != 12:
                print(f"Advertencia: MAC inválida omitida -> {partes[0]}")
                continue

            # 4ta columna opcional para Firmware personalizado por fila
            if len(partes) >= 4 and partes[3]:
                firmware_url = partes[3]
            else:
                firmware_url = firmware_default

            contenido_xml = generar_xml(sv_ip, mac_limpia, ext, secret, pb_url, pb_name, firmware_url)

            nombre_archivo = f"cfg{mac_limpia}.xml"
            ruta_completa = os.path.join(carpeta_salida, nombre_archivo)

            with open(ruta_completa, mode='w', encoding='utf-8') as xml_file:
                xml_file.write(contenido_xml)

            conteo += 1

        if conteo > 0:
            messagebox.showinfo(
                "¡Éxito!",
                f"Se han generado {conteo} archivos XML exitosamente.\n\nRevisa la carpeta:\n{carpeta_salida}"
            )
        else:
            messagebox.showwarning(
                "Atención",
                "No se procesó ninguna línea válida. Asegúrate de copiar al menos las columnas: MAC, Extensión y Secret."
            )

    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un problema al procesar los datos:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Generador masivo Htek")
    root.geometry("680x760")
    root.minsize(580, 600)

    label = tk.Label(
        root,
        text="Generador masivo de configuración Htek",
        font=("Arial", 11, "bold"),
        pady=5
    )
    label.pack()

    # Marco de parámetros generales
    frame_params = tk.LabelFrame(root, text=" Parámetros Generales (Por defecto) ", font=("Arial", 9, "bold"), padx=10, pady=8)
    frame_params.pack(padx=15, pady=5, fill="x")

    tk.Label(frame_params, text="IP Servidor SIP (sv_ip):", anchor="w").grid(row=0, column=0, sticky="w", pady=3)
    entry_sv_ip = tk.Entry(frame_params, width=45)
    entry_sv_ip.grid(row=0, column=1, pady=3, sticky="we", columnspan=2)

    tk.Label(frame_params, text="URL Agenda (pb_url):", anchor="w").grid(row=1, column=0, sticky="w", pady=3)
    entry_pb_url = tk.Entry(frame_params, width=45)
    entry_pb_url.grid(row=1, column=1, pady=3, sticky="we", columnspan=2)

    tk.Label(frame_params, text="Nombre Agenda (pb_name):", anchor="w").grid(row=2, column=0, sticky="w", pady=3)
    entry_pb_name = tk.Entry(frame_params, width=45)
    entry_pb_name.grid(row=2, column=1, pady=3, sticky="we", columnspan=2)

    tk.Label(frame_params, text="URL Firmware por defecto:", anchor="w").grid(row=3, column=0, sticky="w", pady=3)
    entry_firmware_url = tk.Entry(frame_params, width=45)
    entry_firmware_url.grid(row=3, column=1, pady=3, sticky="we", columnspan=2)

    # NUEVO: Fila para elegir la carpeta de exportación
    tk.Label(frame_params, text="Carpeta de Exportación:", anchor="w").grid(row=4, column=0, sticky="w", pady=3)
    entry_carpeta = tk.Entry(frame_params, width=33)
    entry_carpeta.grid(row=4, column=1, pady=3, sticky="we")
    entry_carpeta.insert(0, "") # Vacío por defecto (creará la carpeta cfg_htek automáticamente)

    btn_examinar = tk.Button(
        frame_params,
        text="Examinar...",
        command=lambda: seleccionar_carpeta(entry_carpeta),
        bg="#e0e0e0",
        font=("Arial", 8, "bold")
    )
    btn_examinar.grid(row=4, column=2, padx=5, pady=3)

    frame_params.columnconfigure(1, weight=1)

    # Marco para la tabla de Excel (Expandible con scroll horizontal/vertical)
    frame_tabla = tk.LabelFrame(root, text=" Datos de los Teléfonos ", font=("Arial", 9, "bold"), padx=10, pady=8)
    frame_tabla.pack(padx=15, pady=5, fill="both", expand=True)

    tk.Label(
        frame_tabla,
        text="Pega tus filas directamente desde Excel (Orden de Columnas: MAC | Extensión | Secret | Firmware [opcional]):",
        font=("Arial", 8),
        fg="gray"
    ).pack(anchor="w", pady=2)

    text_container = tk.Frame(frame_tabla)
    text_container.pack(fill="both", expand=True, pady=5)

    text_datos = tk.Text(text_container, height=10, font=("Consolas", 9), wrap="none")
    
    scroll_y = tk.Scrollbar(text_container, orient="vertical", command=text_datos.yview)
    scroll_x = tk.Scrollbar(text_container, orient="horizontal", command=text_datos.xview)
    
    text_datos.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

    text_datos.grid(row=0, column=0, sticky="nsew")
    scroll_y.grid(row=0, column=1, sticky="ns")
    scroll_x.grid(row=1, column=0, sticky="ew")

    text_container.rowconfigure(0, weight=1)
    text_container.columnconfigure(0, weight=1)

    # Botón principal
    btn = tk.Button(
        root,
        text="Generar Archivos XML Masivamente",
        command=lambda: procesar_datos(entry_sv_ip, entry_pb_url, entry_pb_name, entry_firmware_url, entry_carpeta, text_datos),
        bg="#4CAF50",
        fg="white",
        font=("Arial", 10, "bold"),
        padx=10,
        pady=8
    )
    btn.pack(pady=10)

    root.mainloop()