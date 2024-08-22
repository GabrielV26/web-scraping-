# Web Scraping

Este projeto é uma aplicação web simples construída com Flask que realiza web scraping de URLs fornecidas pelos usuários. A aplicação permite que os usuários insiram uma URL e selecionem diferentes tipos de dados para extrair, como títulos, descrições, imagens, links e metadados. Os dados extraídos são exibidos na mesma página.

## Funcionalidades

- **Extração de Títulos:** Coleta todos os títulos `<h2>` da página.
- **Extração de Descrições:** Coleta todos os textos dos parágrafos `<p>`.
- **Extração de Imagens:** Coleta URLs de imagens e as exibe em miniatura, permitindo que sejam visualizadas em tamanho maior.
- **Extração de Links:** Coleta todos os links da página.
- **Extração de Metadados:** Coleta descrições e palavras-chave meta, se disponíveis.

## Como usar

1. Clone o repositório.
2. Crie e ative um ambiente virtual.
3. Instale as dependências: pip install -r requirements.txt
4. Inicie o servidor Flask: python app.py
5. Acesse a aplicação no navegador: http://127.0.0.1:5000/

## Como ficou

![image](https://github.com/user-attachments/assets/0694013a-91dd-4d94-b2cc-5f3d59824554)



