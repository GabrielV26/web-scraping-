import unittest
from unittest.mock import Mock, patch

import requests

import app as scraper


class URLValidationTests(unittest.TestCase):
    def test_rejects_non_http_scheme(self):
        with self.assertRaises(scraper.ScrapingError):
            scraper.validate_public_url("file:///etc/passwd")

    def test_rejects_localhost(self):
        with self.assertRaises(scraper.ScrapingError):
            scraper.validate_public_url("http://localhost")

    def test_rejects_private_ip(self):
        with self.assertRaises(scraper.ScrapingError):
            scraper.validate_public_url("http://127.0.0.1")

    def test_rejects_credentials_in_url(self):
        with self.assertRaises(scraper.ScrapingError):
            scraper.validate_public_url("https://user:pass@example.com")

    @patch("app.socket.getaddrinfo")
    def test_rejects_hostname_resolving_to_private_ip(self, getaddrinfo):
        getaddrinfo.return_value = [
            (2, 1, 6, "", ("10.0.0.2", 443))
        ]
        with self.assertRaises(scraper.ScrapingError):
            scraper.validate_public_url("https://example.test")


class ExtractionTests(unittest.TestCase):
    def test_extracts_selected_data_and_resolves_urls(self):
        html = b"""
        <html>
          <head><meta name="description" content="Resumo"></head>
          <body>
            <h2>  Titulo  </h2><p> Texto <b>importante</b> </p>
            <img src="/foto.png">
            <a href="/pagina">Pagina</a>
            <a href="javascript:alert(1)">nao seguro</a>
          </body>
        </html>
        """
        result = scraper.extract_data(
            html, "https://example.com/base", {"titles", "descriptions", "images", "links", "meta"}
        )

        self.assertEqual(result["titles"], ["Titulo"])
        self.assertEqual(result["descriptions"], ["Texto importante"])
        self.assertEqual(result["images"], ["https://example.com/foto.png"])
        self.assertEqual(result["links"], ["https://example.com/pagina"])
        self.assertEqual(result["description_meta"], "Resumo")

    def test_extracts_only_selected_types(self):
        result = scraper.extract_data(
            b"<h2>Title</h2><p>Text</p>", "https://example.com", {"titles"}
        )
        self.assertEqual(result, {"titles": ["Title"]})


class FetchTests(unittest.TestCase):
    @patch("app.requests.get")
    @patch("app.validate_public_url", return_value="https://example.com")
    def test_fetch_sets_timeout_and_rejects_redirect(self, _validate, get):
        response = Mock()
        response.status_code = 302
        response.headers = {"Location": "http://127.0.0.1"}
        get.return_value.__enter__.return_value = response

        with self.assertRaises(scraper.ScrapingError):
            scraper.fetch_html("https://example.com")

        get.assert_called_once()
        self.assertEqual(get.call_args.kwargs["timeout"], scraper.REQUEST_TIMEOUT)
        self.assertFalse(get.call_args.kwargs["allow_redirects"])

    @patch("app.requests.get", side_effect=requests.Timeout)
    @patch("app.validate_public_url", return_value="https://example.com")
    def test_timeout_becomes_safe_error(self, _validate, _get):
        with self.assertRaisesRegex(scraper.ScrapingError, "demorou demais"):
            scraper.fetch_html("https://example.com")


class FlaskRouteTests(unittest.TestCase):
    def setUp(self):
        scraper.app.config.update(TESTING=True)
        self.client = scraper.app.test_client()

    def test_get_displays_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Web Scraping", response.data)

    def test_rejects_missing_url(self):
        response = self.client.post("/", data={"data_types": "titles"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Informe a URL".encode(), response.data)

    def test_rejects_unknown_data_type(self):
        response = self.client.post(
            "/", data={"url": "https://example.com", "data_types": ["titles", "invalid"]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("tipo de dado válido".encode(), response.data)

    @patch("app.fetch_html", return_value=b"<h2>Teste</h2>")
    def test_successful_scrape(self, fetch_html):
        response = self.client.post(
            "/", data={"url": "https://example.com", "data_types": ["titles"]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Teste", response.data)
        fetch_html.assert_called_once_with("https://example.com")

    @patch("app.fetch_html", side_effect=scraper.ScrapingError("URL bloqueada"))
    def test_displays_safe_scraping_error(self, _fetch_html):
        response = self.client.post(
            "/", data={"url": "http://127.0.0.1", "data_types": ["titles"]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("URL bloqueada".encode(), response.data)


if __name__ == "__main__":
    unittest.main()
