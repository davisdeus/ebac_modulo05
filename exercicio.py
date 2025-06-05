from tkinter.messagebox import RETRY

import requests
import time
import csv
import random
import concurrent.futures
from bs4 import BeautifulSoup
from urllib3.filepost import writer

# Cabeçalhos para evitar bloqueios por sites
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'}

MAX_THREADS = 10
RETRY_LIMIT = 3 # Novo limite de tentativas de requisição
REQUEST_DELAY = (0.5, 2) # Novo: intervalo aleatório para evitar bloqueios

def get_page_content(url):
    """Solicita página com tentativas de recuperação em caso de erro."""
    for attempt in range(RETRY_LIMIT):
        try:
            response = requests.get(url, headers = headers, timeout = 5)
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException:
            print(f"Tentativa {attempt + 1} falhou. Tentando novamente...")
        time.sleep(random.uniform(* REQUEST_DELAY)) # Pausa aleatória para evitar bloqueios
    return None

def extract_movie_details(movie_link):
    time.sleep(random.uniform(*REQUEST_DELAY)) # Novo: Intervalo aleatório para evitar
    movie_soup = get_page_content(movie_link)

    if movie_soup is not None:
        title = None
        date = None
        rating = None
        plot_text = None

        # Encontrando a seção específica
        page_section = movie_soup.find('section', attrs={'class': 'ipc-page-section'})

        if page_section is not None:
            # Encontrando todas as divs dentro da seção
            divs = page_section.find_all('div', recursive=False)

            if len(divs) > 1:
                target_div = divs[1]

                # Encontrando o título do filme
                title_tag = target_div.find('h1')
                if title_tag:
                    title = title_tag.find('span').get_text()

                # Encontrando a data de lançamento
                date_tag = target_div.find('a', href=lambda href: href and 'releaseinfo' in href)
                if date_tag:
                    date = date_tag.get_text().strip()

                # Encontrando a classificação do filme
                rating_tag = movie_soup.find('div', attrs={'data-testid': 'hero-rating-bar__aggregate-rating__score'})
                rating = rating_tag.get_text() if rating_tag else None

                # Encontrando a sinopse do filme
                plot_tag = movie_soup.find('span', attrs={'data-testid': 'plot-xs_to_m'})
                plot_text = plot_tag.get_text().strip() if plot_tag else None

                if all([title, date, rating, plot_text] ):
                    with open('movies.csv', mode='a', newline='', encoding='utf-8') as file:
                        movie_writer = csv.writer(file, delimiter=',', quotechar= '"',  quoting=csv.QUOTE_MINIMAL)
                        movie_writer.writerow([title, date, rating, plot_text])

def extract_movies(soup):
    movies_table = soup.find('div', attrs={'data-testid': 'chart-layout-main-column'})
    if not movies_table:
        return
    movie_list = movies_table.find('ul')
    if not movie_list:
        return
    movies_table_rows = movie_list.find_all('li')
    movie_links = ['https://imdb.com' + movie.find('a')['href'] for movie in movies_table_rows]

    threads = min(MAX_THREADS, len(movie_links))
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(extract_movie_details, movie_links)


def main():
    start_time = time.time()

    # IMDB Most Popular Movies - 100 movies
    popular_movies_url = 'https://www.imdb.com/chart/moviemeter/?ref_=nv_mv_mpm'
    soup = get_page_content(popular_movies_url)
    if soup:
        extract_movies(soup)

    end_time = time.time()
    print(f"Tempo total gasto: {end_time - start_time:.2f} segundos")

if __name__ == '__main__':
    main()