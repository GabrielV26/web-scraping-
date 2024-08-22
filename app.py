from flask import Flask, request, render_template
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)


# Rota principal para o formulário
@app.route('/', methods=['GET', 'POST'])
def index():
    data = None
    # Verifica se a requisição é do tipo POST
    if request.method == 'POST':
        url = request.form['url']  # Obtém a URL fornecida pelo usuário
        data_types = request.form.getlist('data_types')  # Obtém os tipos de dados selecionados pelo usuário

        if url:
            try:
                # Realiza a requisição para a URL fornecida
                response = requests.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Dicionário para armazenar os dados extraídos
                extracted_data = {}

                # Extrai títulos <h2> se 'titles' estiver na lista de tipos de dados
                if 'titles' in data_types:
                    extracted_data['titles'] = [title.get_text() for title in soup.find_all('h2')]

                # Extrai descrições <p> se 'descriptions' estiver na lista de tipos de dados
                if 'descriptions' in data_types:
                    extracted_data['descriptions'] = [desc.get_text() for desc in soup.find_all('p')]

                # Extrai URLs de imagens se 'images' estiver na lista de tipos de dados
                if 'images' in data_types:
                    images = []
                    for img in soup.find_all('img', src=True):
                        img_src = img['src']
                        img_url = urljoin(url, img_src)  # Converte URL relativa para absoluta
                        images.append(img_url)
                    extracted_data['images'] = images

                # Extrai links se 'links' estiver na lista de tipos de dados
                if 'links' in data_types:
                    extracted_data['links'] = [link['href'] for link in soup.find_all('a', href=True)]

                # Extrai meta descrições e meta palavras-chave se 'meta' estiver na lista de tipos de dados
                if 'meta' in data_types:
                    meta_description = soup.find('meta', attrs={'name': 'description'})
                    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
                    extracted_data['description_meta'] = meta_description['content'] if meta_description else None
                    extracted_data['keywords_meta'] = meta_keywords['content'] if meta_keywords else None

                # Armazena os dados extraídos
                data = extracted_data

            except Exception as e:
                # Caso ocorra um erro, armazena uma mensagem de erro
                data = {'error': f"Erro ao tentar acessar a URL: {str(e)}"}

    # Renderiza o template com os dados extraídos
    return render_template('index.html', data=data)


# Inicia a aplicação Flask
if __name__ == '__main__':
    app.run(debug=True)
