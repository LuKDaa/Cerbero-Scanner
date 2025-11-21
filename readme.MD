# 🐺 Cerbero-Scanner v1.0

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20MacOS-lightgrey)
![Status](https://img.shields.io/badge/Status-Stable-success)

**Cerbero-Scanner** es una herramienta de **DAST (Dynamic Application Security Testing)** automatizada y multiplataforma. Diseñada para integrarse en pipelines de CI/CD o para ejecuciones manuales por pentesters, orquesta **OWASP ZAP** para realizar escaneos de seguridad profundos, manejando autenticación compleja y generando reportes forenses en PDF.

---

## 🚀 Características Principales

*   **Multiplataforma Nativa:** Detecta automáticamente si corre en Linux, Windows o Mac y ajusta la red de Docker (`host` vs `bridge`) y los objetivos (`localhost` vs `host.docker.internal`).
*   **Híbrido (Docker/Local):** Puede levantar su propio contenedor de ZAP o conectarse a una instancia local existente.
*   **Bypass de Autenticación:** Capaz de loguearse automáticamente en aplicaciones (ej. DVWA), extraer cookies de sesión e inyectarlas en el motor de escaneo.
*   **Reportes Ejecutivos:** Genera reportes PDF profesionales con los hallazgos de seguridad.
*   **Seguridad por Diseño:** Manejo seguro de API Keys (generación aleatoria), credenciales vía `.env` y timeouts inteligentes.

---

## 📋 Requisitos Previos

1.  **Python 3.10+**
2.  **Docker Desktop** (Recomendado) o **OWASP ZAP** instalado localmente.
3.  **wkhtmltopdf**: Necesario para la generación de reportes PDF.
    *   [Descargar aquí](https://wkhtmltopdf.org/downloads.html) y asegurar que esté en el PATH del sistema.

---

## 🛠️ Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/tu-usuario/Cerbero-Scanner.git
    cd Cerbero-Scanner
    ```

2.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configurar entorno:**
    Copia el archivo de ejemplo y configura tus credenciales (opcional pero recomendado).
    ```bash
    cp .env.example .env
    ```
    *Edita `.env` con tu editor favorito para definir `TARGET_USER` y `TARGET_PASS` si deseas automatizar el login.*

---

## 💻 Uso

### Ejecución Básica (Docker)
Por defecto, el script intentará levantar un contenedor Docker de ZAP.
```bash
python scanner.py -t http://objetivo.com
```

### Ejecución con ZAP Local
Si ya tienes ZAP corriendo o prefieres usar la versión instalada en tu OS:
```bash
python scanner.py --no-docker -t http://localhost:8080
```

### Escaneo Completo (Intrusivo)
Para realizar un **Active Scan** (ataque real, puede ser destructivo/ruidoso):
```bash
python scanner.py --full -t http://objetivo.com
```

---

## 🚩 Flags y Argumentos

A continuación se detallan todos los argumentos disponibles para la línea de comandos:

| Flag / Argumento | Descripción | Ejemplo |
| :--- | :--- | :--- |
| `-t`, `--target` | **URL Objetivo.** Define la URL a escanear. Si no se provee, el script la pedirá interactivamente. | `-t http://dvwa.local` |
| `--no-docker` | **Modo Local.** Indica al script que NO use Docker. Intentará conectarse a una instancia de ZAP corriendo en el puerto definido (default 8090) o lanzará `zap.sh` si está en el PATH. | `--no-docker` |
| `--full` | **Modo Ataque.** Habilita el escaneo activo (`Active Scan`). Por defecto, solo se realiza Spider y escaneo pasivo. **Úsalo con precaución.** | `--full` |
| `-h`, `--help` | Muestra el mensaje de ayuda y sale. | `-h` |

---

## 📂 Estructura del Proyecto

```text
Cerbero-Scanner/
├── .github/workflows/  # Automatización CI/CD (Tests & Linting)
├── tests/              # Tests unitarios (pytest)
├── .env                # Variables de entorno
├── .gitignore          # Archivos ignorados
├── CONTRIBUTING.md     # Guía de contribución
├── LICENSE             # Licencia MIT
├── scanner.py          # Script principal
├── requirements.txt    # Dependencias de Python
└── README.md           # Documentación
```

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor lee [CONTRIBUTING.md](CONTRIBUTING.md) para detalles sobre nuestro código de conducta y el proceso para enviarnos Pull Requests.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

---
*Creado con ❤️ por Lucas (Intento de SysSecAdmin)*
