import os
import json
import requests
from lxml import html
from pypdf import PdfReader
from requests.exceptions import MissingSchema, ConnectionError
import smtplib
from email.message import EmailMessage
from decouple import config
import logging
import sys
from datetime import datetime

CHECKED_URLS_FILE = os.environ.get("CHECKED_URLS_FILE", "checked_urls.json")

def setup_logging():
    """Configura o sistema de logging."""
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    log_dir = os.path.dirname(CHECKED_URLS_FILE)
    log_file = os.path.join(log_dir, 'scraper.log') if log_dir else 'scraper.log'

    handlers = [
        logging.StreamHandler(sys.stdout)
    ]

    # Só adiciona handler de arquivo se estiver em ambiente com filesystem
    try:
        handlers.append(logging.FileHandler(log_file))
    except (IOError, OSError):
        pass  # Sem filesystem disponível (ex: durante build do Docker)

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers,
        force=True  # Reconfigura mesmo que já tenha sido configurado antes
    )

    return logging.getLogger(__name__)

logger = setup_logging()

def load_checked_data():
    """Carrega as URLs e nomes já verificados de um arquivo JSON."""
    if os.path.exists(CHECKED_URLS_FILE):
        with open(CHECKED_URLS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

def save_checked_data(name, url):
    """Salva a URL e o nome no arquivo JSON."""
    checked_data = load_checked_data()
    
    if url not in checked_data:
        checked_data[url] = []  # Inicializa a URL se ainda não existir
    
    if name not in checked_data[url]:
        checked_data[url].append(name)  # Adiciona o nome à URL verificada
    
    with open(CHECKED_URLS_FILE, "w", encoding="utf-8") as file:
        json.dump(checked_data, file, indent=4)

def is_checked(name, url):
    """Verifica se o nome já foi processado para a URL."""
    checked_data = load_checked_data()
    return url in checked_data and name in checked_data[url]

def get_publications_links(url):
    """Obtém os links das publicações na página principal."""
    r = requests.get(url)
    page_content = r.content
    webpage = html.fromstring(page_content)
    xpath = '//div[contains(@class, "sb-integra-conteudo__arquivo")]//a/@href'
    return ['https://sebrae.com.br' + link for link in webpage.xpath(xpath)]


def get_file_link(publication_link):
    """Extrai o link do arquivo PDF a partir do link da publicação."""
    r = requests.get(publication_link)
    download_webpage = html.fromstring(r.content)
    xpath = '//input[@id="urlDownload"]/@value'
    try:
        file_link = download_webpage.xpath(xpath)[0]
    except IndexError:
        r = requests.get(publication_link)
        download_webpage = html.fromstring(r.content)

    return download_webpage.xpath(xpath)[0]

def download_file(file_link):
    """Baixa o arquivo PDF."""
    with open('download.pdf', 'wb') as file:
        try:
            content = requests.get(file_link, stream=True).content
        except MissingSchema:
            file_link = 'https://sebrae.com.br' + file_link[2:]
            logger.warning(f'Missing schema, retrying with https: {file_link}')
            content = requests.get(file_link, stream=True).content
        file.write(content)

def extract_text_from_pdf():
    """Extrai texto do PDF."""
    reader = PdfReader('download.pdf')
    text = ' '.join(page.extract_text() for page in reader.pages)
    return text

def send_mail(text):
    """Envia email se o nome for encontrado no PDF."""
    YOUR_GOOGLE_EMAIL = config('GOOGLE_EMAIL')  # The email you setup to send the email using app password
    YOUR_GOOGLE_EMAIL_APP_PASSWORD = config('GOOGLE_APP_PASSWORD')  # The app password you generated

    smtpserver = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    smtpserver.login(YOUR_GOOGLE_EMAIL, YOUR_GOOGLE_EMAIL_APP_PASSWORD)

    msg = EmailMessage()
    msg.set_content(text, 'html')
    msg['Subject'] = 'Convocação SEBRAE'
    msg['From'] = YOUR_GOOGLE_EMAIL
    msg['To'] = YOUR_GOOGLE_EMAIL

    logger.info('Sending email notification...')
    smtpserver.send_message(msg)
    logger.info('Email sent successfully')
    smtpserver.close()

# Nome a ser pesquisado
name = 'sebrae'
url = 'https://sebrae.com.br/sites/PortalSebrae/ufs/ba/sebraeaz/comunicado%200012024-processo-seletivo-analista%20tecnico,44d9fe7ce5db0910VgnVCM1000001b00320aRCRD?vgnextrefresh=1'

# Log início
start_time = datetime.now()
logger.info('='*60)
logger.info('SEBRAE Scraper started')
logger.info(f'Searching for name: {name}')
logger.info(f'Target URL: {url}')

message = ''

for publication_link in get_publications_links(url):
    if is_checked(name, publication_link):
        continue

    logger.info(f'Checking URL: {publication_link}')
    try:
        file_link = get_file_link(publication_link)
        download_file(file_link)
    except ConnectionError:
        logger.error('Connection error')
        continue
    text = extract_text_from_pdf()

    if name.lower() in text.lower():
        message += f'<p><b>{name}</b> encontrado em <a href="{file_link}">{file_link}</a></p>'
        logger.info(f'Name "{name}" found in {file_link}')
    save_checked_data(name, publication_link)

# Log final com métricas
duration = datetime.now() - start_time
try:
    all_links = get_publications_links(url)
    total_urls = len(all_links)
    checked_count = len([u for u in all_links if is_checked(name, u)])
    found_count = message.count('<p><b>')
except Exception:
    total_urls = 0
    checked_count = 0
    found_count = 0

logger.info('='*60)
logger.info('SEBRAE Scraper finished')
logger.info(f'Total URLs found: {total_urls}')
logger.info(f'URLs checked: {checked_count}')
logger.info(f'Name found: {found_count} times')
logger.info(f'Email sent: {"Yes" if message else "No"}')
logger.info(f'Duration: {duration}')
logger.info('='*60)

if message:
    send_mail(f'<html>{message}</html>')
