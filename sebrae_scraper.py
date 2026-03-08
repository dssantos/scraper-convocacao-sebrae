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

def ensure_data_directory():
    """Garante que o diretório de dados e o arquivo existam."""
    data_dir = os.path.dirname(CHECKED_URLS_FILE)

    # Criar diretório se não existir
    if data_dir and not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir, exist_ok=True)
            logger.debug(f"Created directory: {data_dir}")
        except OSError as e:
            logger.warning(f"Could not create directory {data_dir}: {e}")

    # Criar arquivo vazio se não existir
    if not os.path.exists(CHECKED_URLS_FILE):
        try:
            with open(CHECKED_URLS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f)
            logger.debug(f"Created file: {CHECKED_URLS_FILE}")
        except OSError as e:
            logger.warning(f"Could not create file {CHECKED_URLS_FILE}: {e}")

def load_checked_data():
    """Carrega as URLs e nomes já verificados de um arquivo JSON."""
    # Garantir que arquivo existe antes de tentar ler
    ensure_data_directory()

    if os.path.exists(CHECKED_URLS_FILE):
        try:
            with open(CHECKED_URLS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in {CHECKED_URLS_FILE}, creating new file")
            with open(CHECKED_URLS_FILE, "w", encoding="utf-8") as file:
                json.dump({}, file)
            return {}
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

if __name__ == "__main__":
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

    # Obter todos os links primeiro para análise
    all_links = get_publications_links(url)
    new_links = [link for link in all_links if not is_checked(name, link)]
    already_checked = [link for link in all_links if is_checked(name, link)]

    # Log de status inicial
    logger.info('-'*60)
    logger.info(f'Total publications found: {len(all_links)}')
    logger.info(f'Already checked: {len(already_checked)}')
    logger.info(f'New to check: {len(new_links)}')

    if len(new_links) == 0:
        logger.info('All publications already checked. Nothing to do.')
    else:
        logger.info(f'Starting to check {len(new_links)} new publications...')

    # Processar apenas links novos
    for i, publication_link in enumerate(new_links, 1):
        logger.info('-'*60)
        logger.info(f'[{i}/{len(new_links)}] Processing publication: {publication_link[:80]}...')

        try:
            # Passo 1: Obter link do arquivo PDF
            logger.debug('  [1/5] Extracting PDF link from publication page...')
            file_link = get_file_link(publication_link)
            logger.debug(f'  [1/5] PDF link found: {file_link[:80]}...')

            # Passo 2: Baixar arquivo PDF
            logger.debug('  [2/5] Downloading PDF file...')
            download_file(file_link)

            # Obter tamanho do arquivo baixado
            import os
            file_size = os.path.getsize('download.pdf')
            logger.debug(f'  [2/5] Downloaded {file_size:,} bytes')

            # Passo 3: Extrair texto do PDF
            logger.debug('  [3/5] Extracting text from PDF...')
            text = extract_text_from_pdf()
            text_length = len(text.strip())
            logger.debug(f'  [3/5] Extracted {text_length:,} characters')

            # Passo 4: Buscar nome no conteúdo
            logger.debug(f'  [4/5] Searching for name "{name}" in content...')
            if name.lower() in text.lower():
                logger.info(f'  [4/5] ✓ Name FOUND in document!')
                message += f'<p><b>{name}</b> encontrado em <a href="{file_link}">{file_link}</a></p>'
                logger.info(f'  [5/5] Added to email notification')
            else:
                logger.debug(f'  [4/5] Name not found in this document')
                logger.debug(f'  [5/5] Document processed (name not present)')

            # Passo 5: Salvar como verificado
            save_checked_data(name, publication_link)
            logger.debug(f'  [5/5] Marked as checked')

        except ConnectionError as e:
            logger.error(f'  ✗ Connection error: {e}')
            logger.info(f'  Skipping to next publication...')
            continue
        except Exception as e:
            logger.error(f'  ✗ Unexpected error: {e}')
            logger.info(f'  Skipping to next publication...')
            continue

    # Log final com métricas
    duration = datetime.now() - start_time
    found_count = message.count('<p><b>')

    logger.info('='*60)
    logger.info('SEBRAE Scraper finished')
    logger.info(f'Duration: {duration}')
    logger.info('-'*60)
    logger.info(f'Summary:')
    logger.info(f'  Total publications: {len(all_links)}')
    logger.info(f'  Already checked: {len(already_checked)}')
    logger.info(f'  New processed: {len(new_links)}')
    logger.info(f'  Name found: {found_count} times')
    logger.info(f'  Email sent: {"Yes" if message else "No"}')
    logger.info('='*60)

    if message:
        send_mail(f'<html>{message}</html>')
