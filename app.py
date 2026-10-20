import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
app.config["DEBUG"] = False

REQUEST_TIMEOUT = (3.05, 10)
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
ALLOWED_DATA_TYPES = {"titles", "descriptions", "images", "links", "meta"}
ALLOWED_CONTENT_TYPES = {"text/html", "application/xhtml+xml"}


class ScrapingError(Exception):
    """Expected, safe-to-display scraping error."""


def validate_public_url(url):
    """Allow only HTTP(S) URLs resolving exclusively to public IP addresses."""
    if not isinstance(url, str) or not url.strip() or len(url) > 2048:
        raise ScrapingError("Informe uma URL válida.")

    try:
        parsed = urlsplit(url.strip())
        if (
            parsed.scheme.lower() not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ScrapingError("Informe uma URL HTTP ou HTTPS pública válida.")

        hostname = parsed.hostname.rstrip(".")
        if hostname.lower() == "localhost" or hostname.lower().endswith(".localhost"):
            raise ScrapingError("O endereço informado não é permitido.")

        try:
            literal_ip = ipaddress.ip_address(hostname)
            addresses = [literal_ip]
        except ValueError:
            try:
                addresses = [
                    ipaddress.ip_address(result[4][0])
                    for result in socket.getaddrinfo(
                        hostname, parsed.port or (443 if parsed.scheme == "https" else 80),
                        type=socket.SOCK_STREAM,
                    )
                ]
            except (OSError, ValueError):
                raise ScrapingError("Não foi possível resolver o endereço informado.")

        if not addresses or any(not address.is_global for address in addresses):
            raise ScrapingError("O endereço informado não é público e não pode ser acessado.")

        return parsed.geturl()
    except (ValueError, UnicodeError):
        raise ScrapingError("Informe uma URL válida.")


def fetch_html(url):
    """Fetch a bounded HTML response without following unvalidated redirects."""
    safe_url = validate_public_url(url)

    try:
        with requests.get(
            safe_url,
            timeout=REQUEST_TIMEOUT,
            stream=True,
            allow_redirects=False,
            headers={"User-Agent": "PortfolioWebScraper/1.0"},
        ) as response:
            if 300 <= response.status_code < 400:
                raise ScrapingError("O site redirecionou a requisição. Informe a URL de destino diretamente.")
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type and content_type not in ALLOWED_CONTENT_TYPES:
                raise ScrapingError("A URL não retornou uma página HTML.")

            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    if int(content_length) > MAX_RESPONSE_BYTES:
                        raise ScrapingError("A página é muito grande para ser processada.")
                except ValueError:
                    pass

            chunks = []
            total_bytes = 0
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                total_bytes += len(chunk)
                if total_bytes > MAX_RESPONSE_BYTES:
                    raise ScrapingError("A página é muito grande para ser processada.")
                chunks.append(chunk)

            return b"".join(chunks)
    except ScrapingError:
        raise
    except requests.Timeout:
        raise ScrapingError("O site demorou demais para responder.")
    except requests.HTTPError:
        raise ScrapingError("O site retornou uma resposta HTTP de erro.")
    except requests.RequestException:
        raise ScrapingError("Não foi possível acessar o site informado.")


def extract_data(html, base_url, data_types):
    soup = BeautifulSoup(html, "html.parser")
    extracted_data = {}

    if "titles" in data_types:
        extracted_data["titles"] = [
            title.get_text(" ", strip=True) for title in soup.find_all("h2")
        ]

    if "descriptions" in data_types:
        extracted_data["descriptions"] = [
            paragraph.get_text(" ", strip=True) for paragraph in soup.find_all("p")
        ]

    if "images" in data_types:
        extracted_data["images"] = [
            urljoin(base_url, image["src"])
            for image in soup.find_all("img", src=True)
            if urlsplit(urljoin(base_url, image["src"])).scheme in {"http", "https"}
        ]

    if "links" in data_types:
        extracted_data["links"] = [
            urljoin(base_url, link["href"])
            for link in soup.find_all("a", href=True)
            if urlsplit(urljoin(base_url, link["href"])).scheme in {"http", "https"}
        ]

    if "meta" in data_types:
        meta_description = soup.find("meta", attrs={"name": "description"})
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        extracted_data["description_meta"] = (
            meta_description.get("content") if meta_description else None
        )
        extracted_data["keywords_meta"] = (
            meta_keywords.get("content") if meta_keywords else None
        )

    return extracted_data


@app.route("/", methods=["GET", "POST"])
def index():
    data = None

    if request.method == "POST":
        url = request.form.get("url", "").strip()
        selected_types = request.form.getlist("data_types")
        data_types = set(selected_types)

        if not url:
            data = {"error": "Informe a URL do site."}
        elif not data_types or not data_types.issubset(ALLOWED_DATA_TYPES):
            data = {"error": "Selecione pelo menos um tipo de dado válido para extrair."}
        else:
            try:
                html = fetch_html(url)
                data = extract_data(html, url, data_types)
            except ScrapingError as error:
                data = {"error": str(error)}

    return render_template("index.html", data=data)


@app.errorhandler(413)
def request_too_large(_error):
    return render_template(
        "index.html",
        data={"error": "A solicitação enviada é muito grande."},
    ), 413


if __name__ == "__main__":
    app.run(debug=False)
