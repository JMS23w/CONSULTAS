from DrissionPage import ChromiumPage, ChromiumOptions
import cv2
import pytesseract
import time
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def limpiar_captcha(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return ""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    config = r'--psm 7 -c tessedit_char_whitelist=0123456789'
    return pytesseract.image_to_string(thresh, config=config).strip()

def consultar_y_mostrar(placa_nro):
    # Config para Windows
    co = (
        ChromiumOptions()
        .set_browser_path("C:/Program Files/Google/Chrome/Application/chrome.exe")
        .set_argument('--disable-gpu')
        .set_argument('--start-maximized')
        .set_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    )
    
    page = ChromiumPage(co)

    try:
        print(f"\n[*] Consultando placa: {placa_nro}")
        page.get('https://rec.mtc.gob.pe/Citv/ArConsultaCitv')

        for intento in range(15):

            # Seleccionar búsqueda por placa
            selector = page.ele('#selBUS_Filtro')
            if selector:
                selector.click()
                time.sleep(0.3)
                page.ele('tag:option@@value=1').click()

            page.ele('#texFiltro').clear().input(placa_nro)

            # Captcha
            page.ele('#imgCaptcha').get_screenshot('temp_captcha.png')
            codigo = limpiar_captcha('temp_captcha.png')
            print(f"[*] OCR intento {intento+1}: {codigo}")

            if len(codigo) == 6:  
                page.ele('#texCaptcha').clear().input(codigo)
                time.sleep(1)
                page.ele('#btnBuscar').click()
                time.sleep(4)

                if page.handle_alert(timeout=1):
                    print("[-] Captcha incorrecto. Reintentando…")
                    page.refresh()
                    continue

                print("[OK] Consulta aceptada. Procesando tablas…")

                tablas = page.eles("tag:table")

                if len(tablas) == 0:
                    print("⚠️ No llegaron las tablas (headless o UA)")
                    return

                # Procesar tablas
                for i in range(0, len(tablas), 3):
                    try:
                        empresa = tablas[i].ele("tag:td").text.strip()

                        celdas_cert = [c.text.strip() for c in tablas[i+1].eles("tag:td")]
                        placa = celdas_cert[0]
                        nro_cert = celdas_cert[1]
                        vigente_desde = celdas_cert[2]
                        vigente_hasta = celdas_cert[3]
                        resultado = celdas_cert[4]
                        estado = celdas_cert[5]

                        celdas_obs = [c.text.strip() for c in tablas[i+2].eles("tag:td")]
                        ambito = celdas_obs[0]
                        servicio = celdas_obs[1]
                        observaciones = celdas_obs[2]

                        print("\n===== REVISION =====")
                        print("Empresa:", empresa)
                        print("Placa:", placa)
                        print("Certificado:", nro_cert)
                        print("Vigente Desde:", vigente_desde)
                        print("Vigente Hasta:", vigente_hasta)
                        print("Resultado:", resultado)
                        print("Estado:", estado)
                        print("Ámbito:", ambito)
                        print("Servicio:", servicio)
                        print("Observaciones:", observaciones)
                        print("=====================")

                    except Exception:
                        continue

                return

            page.ele('#btnCaptcha').click()
            time.sleep(2)

    except Exception as e:
        print("[ERROR]", e)
    finally:
        page.quit()


if __name__ == "__main__":
    placa = input("Placa: ").strip().upper()
    consultar_y_mostrar(placa)
