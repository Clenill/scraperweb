import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os

# Inizializzazione costanti e vettori delle keyword
COSTANTE_S = "https://"
COSTANTE_NON_S = "http://"
keywords = ["Inserisci le keyword da verificare"]

# Funzione per uniformare gli URL rimuovendo http e https
def uniform_url(url):
    if url.startswith(COSTANTE_NON_S):
        url = url[len(COSTANTE_NON_S):]
    elif url.startswith(COSTANTE_S):
        url = url[len(COSTANTE_S):]
    return url

# Funzione per accettare i cookie
def accept_cookies(driver):
    try:
        cookie_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Accetta") or contains(text(), "Accept") or contains(text(), "Consent") or contains(text(), "Consent All") or contains(text(), "Consent all") or contains(text(), "Accept All") or contains(text(), "Accept all") or contains(text(), "Accetta tutti") or contains(text(), "Accetta Tutti") or contains(text(), "Acconsento selezionati") or contains(text(), "Acconsento Selezionati") or contains(text(), "tutti") or contains(text(), "Tutti") or contains(text(), "Agree to all") or contains(text(), "Technically required only") or contains(text(), "Accetta tutti i cookie") or contains(text(), "Agree") or contains(text(), "Agree all") or contains(text(), "TUTTI") or contains(text(), "tutti") or contains(text(), "ACCETTA TUTTI I COOKIES")]'))
        )
        cookie_button.click()
        print("Cookie accettati")
    except Exception as e:
        print("Nessun popup sui cookie trovato o errore nell'accettazione dei cookie", e)

# Funzione per estrarre link unici dalla pagina
def extract_unique_links(soup, base_url):
    links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('/'):
            href = base_url + href
        elif not href.startswith('http'):
            href = base_url + '/' + href
        links.add(href)
    return links

# Funzione per analizzare il testo della pagina
def analyze_page_text(soup, url, keywords):
    results = []
    if soup.body:
        body_text = soup.body.get_text(separator=' ', strip=True)
    else:
        body_text = ""
        print(f"Errore: Nessun tag <body> trovato nella pagina {url}")

    keyword_found = False
    for keyword in keywords:
        if keyword.lower() in body_text.lower():
            print(f"Keyword '{keyword}' trovata in {url}")
            results.append((url, keyword, "trovata"))
            keyword_found = True
            # Salva i risultati nel file di output in modalità append
            with open("output.txt", "a", encoding="utf-8") as file:
                file.write(f"Website: {url}\n")
                file.write(f"Keyword: {keyword} - trovata\n")
                file.write("=" * 80 + "\n")
            break  # Esce dal ciclo una volta trovata una keyword
        else:
            results.append((url, keyword, "non trovata"))

    return results, keyword_found

# Funzione principale per analizzare una pagina
def analyze_page(driver, url, keywords, base_url):
    results = []
    try:
        print(f"Analizzo la pagina: {url}")
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "body")))
        accept_cookies(driver)
        time.sleep(2)
        page_content = driver.page_source
        soup = BeautifulSoup(page_content, 'html.parser')

        # Analizza il testo della pagina
        page_results, keyword_found = analyze_page_text(soup, url, keywords)
        results.extend(page_results)

        if keyword_found:
            return results, set()

        # Estrae e analizza i link unici dalla pagina
        links_to_analyze = extract_unique_links(soup, base_url)
        return results, links_to_analyze
    except Exception as e:
        print(f"Errore nell'analisi della pagina {url}: {e}")
        return [(url, f"Errore: {e}")], set()

# Configurazioni iniziali
service = Service(r"percorso fino a chromedriver.exe")
chrome_options = Options()
chrome_options.binary_location = r"percorso fino a chrome.exe"
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.141 Safari/537.36")
driver = webdriver.Chrome(service=service, options=chrome_options)

# Assicura che il file di output esista
output_file = "output.txt"
if not os.path.exists(output_file):
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("")

# Legge il file Excel e ottiene la lista di URL
file_path = r"C:\Users\Diofe\Documents\Imprese_autoveicoli_sito.xlsx"
df = pd.read_excel(file_path)
websites = df['Website'].tolist()
uniformed_websites = [uniform_url(website) for website in websites]

# Rimuove i primi 185 elementi dal vettore
uniformed_websites = uniformed_websites[185:]

# Ciclo per analizzare ogni sito web
results = []
for website in uniformed_websites:
    base_url = COSTANTE_S + website
    url_to_visit = base_url

    try:
        print(f"Provo ad accedere a: {url_to_visit}")
        driver.get(url_to_visit)
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "body")))
        accept_cookies(driver)
        page_content = driver.page_source

        # Analizza la homepage
        page_results, links_to_analyze = analyze_page(driver, base_url, keywords, base_url)
        results.extend(page_results)

        # Se non abbiamo trovato nessuna keyword sulla homepage, analizziamo i link unici trovati
        if not any("trovata" in result for result in page_results):
            for link in links_to_analyze:
                if base_url in link:  # Assicuriamoci di non uscire dal dominio
                    page_results, keyword_found = analyze_page(driver, link, keywords, base_url)
                    results.extend(page_results)
                    if keyword_found:
                        break  # Passa al sito successivo se trova una keyword

    except Exception as e:
        print(f"Sito: {website}, Errore: {e}")
        results.append((website, f"Errore: {e}"))

driver.quit()

print("Risultati collezionati", results)
