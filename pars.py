import asyncio
from hmac import new
import requests
import json
import time
from bs4 import BeautifulSoup
import aiohttp
from typing import Dict, Any
import os
from datetime import datetime
import glob



async def fetch(session: aiohttp.ClientSession, url: str, headers: Dict[str, str]) -> str:
    async with session.get(url, headers=headers) as response:
        return await response.text()

def cleanup_old_images(max_keep: int = 5):
    """Delete old images, keeping only the most recent ones"""
    try:
        # Get list of all images in the images directory
        image_files = glob.glob('images/news_*.jpg')
        
        # Sort files by modification time (newest first)
        image_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Delete all files except the most recent max_keep
        for old_file in image_files[max_keep:]:
            try:
                os.remove(old_file)
                print(f"Deleted old image: {old_file}")
            except Exception as e:
                print(f"Error deleting {old_file}: {e}")
    except Exception as e:
        print(f"Error during cleanup: {e}")

async def download_image(session: aiohttp.ClientSession, url: str, headers: Dict[str, str]) -> str:
    """Download image and save it to the images directory"""
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                # Create images directory if it doesn't exist
                os.makedirs('images', exist_ok=True)
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"images/news_{timestamp}.jpg"
                
                # Save image
                content = await response.read()
                with open(filename, 'wb') as f:
                    f.write(content)
                
                # Cleanup old images after successful download
                cleanup_old_images()
                
                return filename
    except Exception as e:
        print(f"Error downloading image: {e}")
    return None

async def genproc_news() -> Dict[str, str]:
    url = 'https://epp.genproc.gov.ru/web/proc_14/mass-media/news'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            html = await fetch(session, url, headers)
            soup = BeautifulSoup(html, 'lxml')
            
            # Получаем ссылку на новость
            news_block = soup.find('div', class_='feeds-list__list_body feeds-list__list_body--carousel')
            if not news_block:
                return {}
                
            news_url = news_block.find('div', class_='feeds-list__list_item').find('a').get('href')
            if not news_url:
                return {}
            
            # Получаем содержимое новости
            news_html = await fetch(session, news_url, headers)
            news_soup = BeautifulSoup(news_html, 'lxml')
            
            title = news_soup.find('div', class_='wrapper test-label-enable').find('div', class_='feeds-page__subtitle').text
            content = news_soup.find('div', class_='wrapper test-label-enable').find('div', class_='feeds-page__article_text_block').text
            
            # Очистка текста
            title = ' '.join(title.split())
            content = ' '.join(content.split("Распечатать")[0].split())
            
            return {title: content, "url": news_url}
            
        except Exception as e:
            print(f"Error in genproc_news: {e}")
            return {}

async def get_ykl_news() -> Dict[str, str]:
    url = 'https://ykt.sledcom.ru/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            html = await fetch(session, url, headers)
            soup = BeautifulSoup(html, 'lxml')
            
            container = soup.find('div', class_='bl-item clearfix')
            if not container:
                return {}
                
            news_url = f"https://ykt.sledcom.ru/{container.find('a').get('href')}"
            
            # Получаем содержимое новости
            news_html = await fetch(session, news_url, headers)
            news_soup = BeautifulSoup(news_html, 'lxml')
            
            # Download image if available
            
            try:
                jpg = news_soup.find('div', class_='news_image f_left').find('img').get('src')
                if jpg:
                    jpg_url = f"https://ykt.sledcom.ru/{jpg}"
                    jpg_filename = await download_image(session, jpg_url, headers)
            except Exception as e:
                jpg_filename = None

            title = news_soup.find('h1', class_='b-topic t-h1 m_b4').text
            paragraphs = news_soup.find('article', class_='c-detail m_b4').find_all('p')
            content = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            
            # Очистка заголовка
            title = ' '.join(title.split())
            
            return {title: content, "url": news_url, "jpg": jpg_filename}
            
        except Exception as e:
            print(f"Error in get_ykl_news: {e}")
            return {}

async def get_mvd_news(max_retries: int = 2) -> Dict[str, str]:
    """
    Получает новости МВД с автоматическим повторным запуском при ошибках
    
    Args:
        max_retries: максимальное количество попыток (включая первый запуск)
        
    Returns:
        Словарь с заголовком и текстом новости или пустой словарь при неудаче
    """
    url = 'https://14.мвд.рф/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        async with aiohttp.ClientSession() as session:
            try:
                html = await fetch(session, url, headers)
                soup = BeautifulSoup(html, 'lxml')
                
                news_block = soup.find('div', class_='b-news-holder')
                if not news_block:
                    raise ValueError("Не найден блок новостей на странице")
                    
                news_url_element = news_block.find('div', class_='sl-item-title')
                if not news_url_element:
                    raise ValueError("Не найден элемент с ссылкой на новость")
                
                news_url = f"https://14.мвд.рф/{news_url_element.find('a').get('href')}"
                
                # Получаем содержимое новости
                news_html = await fetch(session, news_url, headers)
                news_soup = BeautifulSoup(news_html, 'lxml')
                
                title_element = news_soup.find('div', class_='ln-content wrapper clearfix')
                if not title_element:
                    raise ValueError("Не найден заголовок новости")
                
                title = title_element.find('h1').text
                
                article = news_soup.find('div', class_='article')
                if not article:
                    raise ValueError("Не найден текст статьи")
                
                paragraphs = article.find_all('p')
                content = " ".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                return {title: content, "url": news_url}
                

                
                
            except Exception as e:
                last_error = e
                print(f"Попытка {attempt} из {max_retries} не удалась: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(1 * attempt)  # Увеличивающаяся задержка
                continue
    
    print(f"Все {max_retries} попытки завершились ошибкой. Последняя ошибка: {last_error}")
    return {}

async def get_all_news() -> Dict[str, Dict[str, str]]:
    # Запускаем все запросы параллельно
    ykl, genproc, mvd = await asyncio.gather(
        get_ykl_news(),
        genproc_news(),
        get_mvd_news()
    )
    
    result = {
        "ykl_news": ykl,
        "genproc_news": genproc,
        "mvd_news": mvd
    }
    
    # Сохранение в JSON (раскомментировать при необходимости)
    # async with aiofiles.open('all_news.json', 'w', encoding='utf-8') as f:
    #     await f.write(json.dumps(result, ensure_ascii=False, indent=4))
    
    return result

asyncio.run(get_all_news())
