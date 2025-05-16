# News Parser Bot

Телеграм бот для мониторинга и отправки новостей с сайтов:
- Генеральной прокуратуры
- МВД
- Следственного комитета (УК РФ)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/bellinel/news_yak.git
cd news_yak
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv venv
# Для Windows:
venv\Scripts\activate
# Для Linux/Mac:
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` в корневой директории проекта со следующими параметрами:
```env
BOT_TOKEN=ваш_токен_бота
CHAT_ID=ваш_id_чата
```

## Запуск

1. Активируйте виртуальное окружение (если еще не активировано):
```bash
# Для Windows:
venv\Scripts\activate
# Для Linux/Mac:
source venv/bin/activate
```

2. Запустите бот:
```bash
python main.py
```

## Функционал

- Мониторинг новостей с трёх источников
- Автоматическая отправка новых новостей в указанный чат
- Сохранение изображений из новостей
- Отправка ссылок на источники
- Пауза между проверками сайтов: 30 минут
- Пауза между отправкой сообщений: 10 минут

## Структура проекта

- `main.py` - основной файл бота
- `pars.py` - парсеры для каждого сайта
- `models.py` - модели базы данных
- `requirements.txt` - зависимости проекта
- `.env` - конфигурационный файл (необходимо создать)
- `images/` - директория для сохранения изображений (создается автоматически)

## Примечания

- Бот автоматически создает базу данных SQLite при первом запуске
- Старые изображения автоматически удаляются при получении новых
- В базе данных хранится только последний заголовок новости для каждого источника 

## Обработка изменений верстки сайтов

Если изменилась верстка одного из сайтов, необходимо обновить селекторы в файле `pars.py`:

### Генпрокуратура
```python
# Текущие селекторы:
news_block = soup.find('div', class_='feeds-list__list_body feeds-list__list_body--carousel')
title = news_soup.find('div', class_='wrapper test-label-enable').find('div', class_='feeds-page__subtitle')
content = news_soup.find('div', class_='wrapper test-label-enable').find('div', class_='feeds-page__article_text_block')
```

### МВД
```python
# Текущие селекторы:
news_block = soup.find('div', class_='b-news-holder')
title = news_soup.find('div', class_='ln-content wrapper clearfix').find('h1')
article = news_soup.find('div', class_='article')
```

### Следственный комитет (УК РФ)
```python
# Текущие селекторы:
container = soup.find('div', class_='bl-item clearfix')
title = news_soup.find('h1', class_='b-topic t-h1 m_b4')
article = news_soup.find('article', class_='c-detail m_b4')
image = news_soup.find('div', class_='news_image f_left').find('img')
```

Для обновления селекторов:
1. Откройте сайт в браузере
2. Используйте инструменты разработчика (F12)
3. Найдите новые классы или структуру HTML
4. Обновите соответствующие селекторы в `pars.py`
5. Протестируйте работу парсера 