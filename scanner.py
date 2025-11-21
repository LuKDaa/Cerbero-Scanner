import time
import sys
import argparse
import subprocess
import os
import re
import platform
from datetime import datetime
import requests
import docker
import pdfkit
from bs4 import BeautifulSoup
from zapv2 import ZAPv2
from dotenv import load_dotenv
from colorama import init, Fore, Style

init(autoreset=True)
load_dotenv()

# Constantes de Colores
OK = Fore.GREEN + "[+]" + Fore.RESET
WARN = Fore.YELLOW + "[!]" + Fore.RESET
ERR = Fore.RED + "[-]" + Fore.RESET
INPUT_C = Fore.MAGENTA + "[?]" + Fore.RESET
INFO = Fore.CYAN + "[*]" + Fore.RESET

# --- CONFIGURACION DESDE .ENV ---
ZAP_PORT = int(os.getenv("ZAP_PORT", 8090))
API_KEY = os.getenv("ZAP_API_KEY", "12345")
ZAP_IMAGE = "zaproxy/zap-stable"
CONTAINER_NAME = "cerbero-engine"

def print_banner():
    banner = f"""
{Fore.RED}
   __    ___    ___     ___     ___    ___     ___
 / __|  | __|  | _ \   | __ )  | __|  | _ \   / _ \
| (__   | _|   |   /   | _\    | _|   |   /  | (_) |
 \___|  |___|  |_|_\   |___/   |___|  |_|_\   \___/ {Fore.RESET}
   
   {Fore.WHITE}>> AUTOMATED DAST PIPELINE v1.0 (Universal) <<{Fore.RESET}
   {Fore.CYAN}>> Creado por: Lucas (SysSecAdmin) <<{Fore.RESET}
    """
    print(banner)

# --- MOTORES ZAP (LOGICA CROSS-PLATFORM) ---
def start_zap_docker():
    print(f"\n{INFO} Iniciando Motor ZAP via Docker...")
    
    # Deteccion del Sistema Operativo
    current_os = platform.system()
    print(f"   {INFO} Sistema Operativo detectado: {Fore.YELLOW}{current_os}{Fore.RESET}")

    # Configuracion base del contenedor
    docker_config = {
        "image": ZAP_IMAGE,
        "name": CONTAINER_NAME,
        "detach": True,
        "command": f"zap.sh -daemon -port {ZAP_PORT} -config api.key={API_KEY} -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true"
    }

    # Logica condicional de Red
    if current_os == "Linux":
        # En Linux, el modo host es nativo y mas rapido
        print(f"   {OK} Configurando red: Modo Host (Nativo Linux)")
        docker_config["network_mode"] = "host"
    else:
        # En Windows/Mac, usa bridge y mapea puertos
        print(f"   {OK} Configurando red: Modo Bridge (Compatible Win/Mac)")
        docker_config["ports"] = {f"{ZAP_PORT}/tcp": ZAP_PORT}
        docker_config["extra_hosts"] = {"host.docker.internal": "host-gateway"}

    try:
        client = docker.from_env()
        try:
            old = client.containers.get(CONTAINER_NAME)
            old.stop()
            old.remove()
        except:
            pass
        
        # Lanza con la configuracion dinamica (desempaqueta el diccionario)
        container = client.containers.run(**docker_config)
        return container, "docker"
    except Exception as e:
        print(f"{ERR} Error Docker: {e}")
        sys.exit(1)

def start_zap_local():
    print(f"\n{INFO} Iniciando Motor ZAP Localmente...")
    cmd = ["zap.sh", "-daemon", "-port", str(ZAP_PORT), 
           "-config", f"api.key={API_KEY}", 
           "-config", "api.addrs.addr.name=.*", "-config", "api.addrs.addr.regex=true"]
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return process, "local"
    except FileNotFoundError:
        print(f"{ERR} No encuentro 'zap.sh' en el PATH.")
        sys.exit(1)

def wait_for_zap():
    print(f"   {INFO} Esperando conexion con API...", end="")
    retries = 0
    zap = ZAPv2(apikey=API_KEY, proxies={'http': f'http://localhost:{ZAP_PORT}', 'https': f'http://localhost:{ZAP_PORT}'})
    while retries < 40:
        try:
            zap.core.version
            print(f"\n   {OK} {Fore.GREEN}Motor ZAP Listo y Escuchando.{Fore.RESET}")
            return zap
        except:
            time.sleep(2)
            retries += 1
            sys.stdout.write(f"{Fore.YELLOW}.{Fore.RESET}")
            sys.stdout.flush()
    print(f"\n{ERR} Timeout esperando a ZAP.")
    sys.exit(1)

# --- AUTENTICACION ---
def login_dvwa(target_url, username, password):
    print(f"\n{INFO} Intentando Bypass de Login en: {target_url}")
    s = requests.Session()
    # Python corre en el Host, asi que siempre usa la URL original (localhost)
    login_url = target_url.rstrip('/') + "/login.php"
    try:
        r = s.get(login_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        token_input = soup.find('input', {'name': 'user_token'})
        
        if not token_input:
            print(f"   {WARN} No se detecto token CSRF. ¿Es VWA?")
            return None
        
        payload = {'username': username, 'password': password, 'Login': 'Login', 'user_token': token_input['value']}
        r = s.post(login_url, data=payload)
        
        if "Logout" in r.text:
            print(f"   {OK} {Fore.GREEN}Autenticacion Exitosa.{Fore.RESET}")
            return s.cookies.get("PHPSESSID")
        else:
            print(f"   {ERR} {Fore.RED}Fallo el Login.{Fore.RESET}")
            return None
    except Exception as e:
        print(f"   {ERR} Excepcion en login: {e}")
        return None

# --- REPORTING ---
def generate_pdf_report(zap, target_url):
    print(f"\n{INFO} Generando reporte forense...")
    
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', target_url)
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"Reporte_Cerbero_{clean_name}_{date_str}.pdf"
    
    try:
        html_content = zap.core.htmlreport()
        options = {
            'quiet': '',
            'page-size': 'A4',
            'encoding': "UTF-8",
            'title': f"Reporte de Seguridad - {target_url}"
        }
        
        pdfkit.from_string(html_content, filename, options=options)
        print(f"   {OK} {Fore.GREEN}Reporte generado: {filename}{Fore.RESET}")
        return filename
    except Exception as e:
        print(f"   {ERR} Error generando PDF: {e}")
        print(f"   {WARN} Guardando HTML de respaldo...")
        with open("backup_report.html", "w") as f:
            f.write(html_content)
        return None

# --- MAIN ---
def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description="Herramienta Ofensiva de Automatizacion")
    parser.add_argument("--no-docker", action="store_true", help="Usar motor local")
    parser.add_argument("--full", action="store_true", help="Habilitar Ataque Activo (Intrusivo)")
    parser.add_argument("-t", "--target", help="URL Objetivo (Sobrescribe input)")
    args = parser.parse_args()

    # 1. INICIO DE MOTOR
    zap_inst, mode = start_zap_local() if args.no_docker else start_zap_docker()
    zap = wait_for_zap()

    # 2. INPUTS INTELIGENTES
    if args.target:
        target_raw = args.target
    else:
        target_raw = input(f"{INPUT_C} URL Objetivo [http://localhost:8080]: ").strip() or "http://localhost:8080"

    # --- TRADUCCION DE OBJETIVO (CRITICO PARA DOCKER EN WINDOWS/MAC) ---
    # Python (Host) siempre usa target_raw (ej: localhost)
    # ZAP (Container) necesita target_zap (ej: host.docker.internal si no es Linux)
    target_zap = target_raw
    
    if mode == "docker" and platform.system() != "Linux":
        if "localhost" in target_raw or "127.0.0.1" in target_raw:
            print(f"   {WARN} Detectado Docker en Windows/Mac: Ajustando objetivo para el contenedor...")
            target_zap = target_raw.replace("localhost", "host.docker.internal").replace("127.0.0.1", "host.docker.internal")
            print(f"   {INFO} Python usara: {target_raw}")
            print(f"   {INFO} ZAP usara: {target_zap}")

    # Credenciales
    env_user = os.getenv("TARGET_USER")
    env_pass = os.getenv("TARGET_PASS")
    
    print(f"\n{INFO} Configuracion de Credenciales:")
    if env_user and env_pass:
        print(f"   {OK} Cargadas desde .env ({env_user})")
        user, password = env_user, env_pass
    else:
        print(f"   {WARN} No encontradas en .env")
        user = input(f"{INPUT_C} Usuario (Enter para anonimo): ").strip()
        password = input(f"{INPUT_C} Password: ").strip()

    # 3. LOGICA DE AUTENTICACION (Usa target_raw porque Python corre en el Host)
    if user and password:
        cookie = login_dvwa(target_raw, user, password)
        if cookie:
            zap.replacer.add_rule(description="Auth", enabled="true", matchtype="REQ_HEADER", matchregex="false", matchstring="Cookie", replacement=f"PHPSESSID={cookie}")
            print(f"   {OK} Sesion inyectada en el motor.")

    # 4. SPIDER (Usa target_zap porque es instruccion para el Contenedor)
    print(f"\n{INFO} Iniciando Mapeo (Spider) contra {target_zap}...")
    scan_id = zap.spider.scan(target_zap)
    while int(zap.spider.status(scan_id)) < 100:
        progreso = int(zap.spider.status(scan_id))
        bar_len = 30
        filled = int(progreso / 100 * bar_len)
        bar = "█" * filled + "-" * (bar_len - filled)
        sys.stdout.write(f"\r   [{Fore.CYAN}{bar}{Fore.RESET}] {progreso}%")
        sys.stdout.flush()
        time.sleep(0.5)
    print(f"\n   {OK} Spider finalizado.")

    # 5. ACTIVE SCAN (Usa target_zap)
    if args.full:
        print(f"\n{WARN} {Fore.RED}INICIANDO ATAQUE ACTIVO (DESTRUCTIVO){Fore.RESET}")
        scan_id = zap.ascan.scan(target_zap)
        while int(zap.ascan.status(scan_id)) < 100:
            progreso = int(zap.ascan.status(scan_id))
            sys.stdout.write(f"\r   {Fore.RED}Ataque en curso: {progreso}%{Fore.RESET}")
            sys.stdout.flush()
            time.sleep(5)
        print(f"\n   {OK} Ataque finalizado.")
    else:
        print(f"\n{INFO} Saltando Ataque Activo (Modo Seguro).")

    # 6. ALERTAS Y REPORTE
    # Para las alertas, la baseurl debe coincidir con lo que escaneo ZAP
    alerts = zap.core.alerts(baseurl=target_zap)
    high = len([a for a in alerts if a['risk'] == 'High'])
    medium = len([a for a in alerts if a['risk'] == 'Medium'])
    
    print(f"\n{INFO} Resumen de Hallazgos:")
    print(f"   {Fore.RED}Criticos/Altos: {high}{Fore.RESET}")
    print(f"   {Fore.YELLOW}Medios: {medium}{Fore.RESET}")
    print(f"   {Fore.GREEN}Bajos/Info: {len(alerts) - high - medium}{Fore.RESET}")

    generate_pdf_report(zap, target_raw) # Usa raw para el nombre del archivo limpio

    # 7. CIERRE
    print(f"\n{INFO} Deteniendo procesos...")
    if mode == "docker": zap_inst.stop()
    else: zap_inst.terminate()
    print(f"{OK} {Fore.GREEN}Operacion completada.{Fore.RESET}")

if __name__ == "__main__":
    main()