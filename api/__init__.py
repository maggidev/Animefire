from flask import Flask, request, jsonify, abort
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import json
import time
import re

app = Flask(__name__)

# Configurações
APP_SECRET_KEY = os.getenv('APP_SECRET_KEY', 'change-me-in-vercel-dashboard')
CACHE_DIR = '/tmp/animefire_cache'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Referer": "https://animefire.plus",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

session = requests.Session()
session.headers.update(HEADERS)

os.makedirs(CACHE_DIR, exist_ok=True)

def cache_get(key):
    path = os.path.join(CACHE_DIR, key + '.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data['expires'] > time.time():
                return data['value']
    return None

def cache_set(key, value, ttl=3600):
    path = os.path.join(CACHE_DIR, key + '.json')
    data = {'value': value, 'expires': time.time() + ttl}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def require_api_key():
    key = request.headers.get('X-App-Key')
    if not key or key != APP_SECRET_KEY:
        abort(403, description="Forbidden: Invalid or missing API key")

def get_soup(url):
    try:
        r = session.get(url, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, 'html.parser')
    except:
        return None

def parse_anime_card(card):
    a_tag = card.find_parent('a')
    if not a_tag:
        return None
    href = a_tag['href']
    if re.search(r'/\d+$', href):
        href = re.sub(r'/\d+$', '-todos-os-episodios', href)
    full_url = urljoin('https://animefire.plus', href)
    title_tag = card.find('h3', class_='animeTitle')
    title = title_tag.get_text(strip=True) if title_tag else "Sem título"
    img = card.find('img')
    thumb = img['data-src'] if img and img.get('data-src') else None
    return {
        "title": title,
        "url": full_url,
        "thumbnail": thumb,
        "type": "anime"
    }

@app.route('/health')
def health():
    return jsonify({"success": True, "message": "API is running", "version": "1.0.0"})

@app.route('/api/animes/popular')
def popular():
    require_api_key()
    page = int(request.args.get('page', 1))
    cache_key = f"popular_{page}"
    cached = cache_get(cache_key)
    if cached:
        return jsonify({"success": True, "data": cached})

    soup = get_soup(f"https://animefire.plus/top-animes/{page}")
    if not soup:
        return jsonify({"success": False, "error": "Falha ao carregar página"}), 500

    cards = soup.select('article.cardUltimosEps h3.animeTitle')
    animes = [parse_anime_card(c) for c in cards if parse_anime_card(c)]
    cache_set(cache_key, animes)
    return jsonify({"success": True, "data": animes})

@app.route('/api/animes/latest')
def latest():
    require_api_key()
    page = int(request.args.get('page', 1))
    cache_key = f"latest_{page}"
    cached = cache_get(cache_key)
    if cached:
        return jsonify({"success": True, "data": cached})

    soup = get_soup(f"https://animefire.plus/home/{page}")
    if not soup:
        return jsonify({"success": False, "error": "Falha ao carregar página"}), 500

    cards = soup.select('article.cardUltimosEps h3.animeTitle')
    animes = [parse_anime_card(c) for c in cards if parse_anime_card(c)]
    cache_set(cache_key, animes)
    return jsonify({"success": True, "data": animes})

@app.route('/api/animes/search')
def search():
    require_api_key()
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"success": False, "error": "Query required"}), 400
    page = int(request.args.get('page', 1))
    q = query.lower().replace(' ', '-')
    cache_key = f"search_{q}_{page}"
    cached = cache_get(cache_key)
    if cached:
        return jsonify({"success": True, "data": cached})

    soup = get_soup(f"https://animefire.plus/pesquisar/{q}/{page}")
    if not soup:
        return jsonify({"success": False, "error": "Falha ao carregar página"}), 500

    cards = soup.select('article.cardUltimosEps h3.animeTitle')
    animes = [parse_anime_card(c) for c in cards if parse_anime_card(c)]
    cache_set(cache_key, animes)
    return jsonify({"success": True, "data": animes})

@app.route('/api/animes/details')
def details():
    require_api_key()
    url = request.args.get('url')
    if not url:
        return jsonify({"success": False, "error": "URL required"}), 400

    cache_key = f"details_{hash(url)}"
    cached = cache_get(cache_key)
    if cached:
        return jsonify({"success": True, "data": cached})

    soup = get_soup(url)
    if not soup:
        return jsonify({"success": False, "error": "Falha ao carregar página"}), 500

    # Implementação completa da descrição como no addon Kodi (título, thumb, sinopse, gêneros, info, etc.)
    # ... (código similar ao addon, adaptado)

    data = { ... }  # preencha com os dados extraídos
    cache_set(cache_key, data)
    return jsonify({"success": True, "data": data})

@app.route('/api/animes/episodes')
def episodes():
    require_api_key()
    url = request.args.get('url')
    batch = int(request.args.get('batch', 1))
    if not url:
        return jsonify({"success": False, "error": "URL required"}), 400

    # Carrega todos os episódios, inverte ordem, aplica batch
    # Retorna pagination info + lista paginada

@app.route('/api/animes/video')
def video():
    require_api_key()
    url = request.args.get('url')
    if not url:
        return jsonify({"success": False, "error": "URL required"}), 400

    # Extrai data-video-src ou iframe → JSON ou fallback → retorna lista de videos com quality

if __name__ == '__main__':
    app.run()