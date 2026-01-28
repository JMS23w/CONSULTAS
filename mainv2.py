import asyncio
from playwright.async_api import async_playwright
import easyocr
import os

reader = easyocr.Reader(['en'], gpu=False)

async def consultar_mtc():
    placa_nro = input("\nIngrese la Placa a consultar: ").strip().upper()
    if not placa_nro:
        print("[!] Placa vacía.")
        return

    async with async_playwright() as p:
        # Lanzamiento oculto
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"[*] Conectando con MTC y resolviendo captcha...")
        
        try:
            await page.goto('https://rec.mtc.gob.pe/Citv/ArConsultaCitv')

            for intento in range(12):
                # Llenar Formulario
                await page.select_option('#selBUS_Filtro', '1')
                await page.fill('#texFiltro', placa_nro)

                # Captcha
                captcha_el = await page.wait_for_selector('#imgCaptcha')
                await captcha_el.screenshot(path="temp_captcha.png")
                
                # Leer Captcha
                result = reader.readtext("temp_captcha.png", allowlist='0123456789')
                codigo = "".join([res[1] for res in result]).replace(" ", "")
                
                if len(codigo) == 6:
                    await page.fill('#texCaptcha', codigo)
                    await page.click('#btnBuscar')
                    
                    # Espera a que carguen los resultados
                    await page.wait_for_timeout(3000)

                    if "Certificado" in await page.content():
                        print(f"\n[+++] DATOS ENCONTRADOS PARA: {placa_nro}")
                        
                        # Extraer tablas de resultados
                        tablas = await page.query_selector_all('table.table')
                        
                        for tabla in tablas:
                            filas = await tabla.query_selector_all('tr')
                            if len(filas) < 2: continue

                            # Mapear Cabecera vs Datos
                            cabeceras = await filas[0].query_selector_all('th, td')
                            datos = await filas[1].query_selector_all('td')

                            h_texts = [await h.inner_text() for h in cabeceras]
                            d_texts = [await d.inner_text() for d in datos]

                            print("\n" + "="*50)
                            for i in range(len(h_texts)):
                                tit = h_texts[i].strip()
                                val = d_texts[i].strip() if i < len(d_texts) else "---"
                                if tit:
                                    print(f"{tit:25}: {val}")
                        
                        # Salir del bucle de intentos al tener éxito
                        break
                
                await page.click('#btnCaptcha')
                await page.wait_for_timeout(1000)
            else:
                print(f"[!] No se pudo obtener resultados tras varios intentos.")

        except Exception as e:
            print(f"[!] Error inesperado: {e}")
        finally:
            await browser.close()
            if os.path.exists("temp_captcha.png"):
                os.remove("temp_captcha.png")
            print("\n[*] Consulta finalizada. Script cerrado.")

if __name__ == "__main__":
    asyncio.run(consultar_mtc())
