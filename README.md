# Web Scraping

Aplicação web em Flask para extrair títulos, parágrafos, imagens, links e metadados de páginas HTML usando BeautifulSoup.

## Funcionalidades

- Seleção dos tipos de conteúdo que serão extraídos.
- Conversão de URLs relativas de imagens e links em URLs absolutas.
- Validação inicial de URLs HTTP/HTTPS e bloqueio de destinos locais/privados.
- Timeout de conexão/leitura, tratamento de erros HTTP e de rede.
- Limite de 2 MiB para o conteúdo HTML recebido.
- Testes automatizados e execução contínua pelo GitHub Actions.

## Requisitos

- Python 3.12 ou compatível.
- Acesso à internet para consultar sites públicos.

## Instalação e execução

```bash
git clone https://github.com/GabrielV26/web-scraping-.git
cd web-scraping-
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

No Windows, ative o ambiente virtual com `.venv\\Scripts\\activate`.

Abra http://127.0.0.1:5000 no navegador. O servidor de desenvolvimento destina-se apenas ao uso local; não o exponha diretamente à internet.

## Testes

```bash
python -m unittest discover -s tests -v
python -m compileall -q app.py tests
```

Os testes não precisam acessar sites externos; chamadas de rede são simuladas quando apropriado.

## Limitações e segurança

- Use o scraper apenas em páginas que você tem autorização para consultar e respeite os termos de uso, direitos autorais, políticas de acesso e limites de requisições dos sites.
- A aplicação aceita apenas URLs HTTP/HTTPS, bloqueia endereços não públicos detectados na resolução DNS, não segue redirecionamentos automaticamente e limita o tamanho da resposta.
- A validação de DNS não elimina sozinha todos os riscos de SSRF, incluindo DNS rebinding e mudanças de resolução entre a validação e a conexão. Para uma implantação pública, execute o serviço em ambiente isolado e aplique regras de saída de rede/firewall que impeçam o acesso a redes internas e serviços de metadados.
- Não use o servidor de desenvolvimento do Flask em produção. Para implantação real, use um servidor WSGI e configure limites de requisição, rate limiting e monitoramento.
- A estrutura HTML dos sites pode mudar; por isso, seletores e dados extraídos podem precisar de ajustes.

## Tecnologias

Python, Flask, Requests, BeautifulSoup, HTML e CSS.
