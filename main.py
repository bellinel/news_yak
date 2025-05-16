import os
from typing import Dict
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
from dotenv import load_dotenv
from pars import get_all_news
import asyncio
from models import Session, GenProcNews, MVDNews, YKLNews


load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def get_or_create_news_record(session, model_class):
    """Получение или создание записи в базе данных"""
    record = session.query(model_class).first()
    if not record:
        record = model_class()
        session.add(record)
        session.commit()
    return record

async def update_news_record(session, model_class, new_title: str):
    """Обновление записи в базе данных с удалением старой"""
    # Удаляем все старые записи
    session.query(model_class).delete()
    session.commit()
    
    # Создаем новую запись
    record = model_class()
    record.last_title = new_title
    session.add(record)
    session.commit()
    return record

async def send_news_update(chat_id: int, news_type: str, news_data: Dict):
    """Отправка обновлений новостей"""
    # Получаем первый заголовок и текст из словаря
    title = next(iter(news_data))  # Первый ключ - это заголовок
    content = news_data[title]     # Значение - это контент
    url = news_data.get("url", "")  # URL новости
    
    if news_data.get("jpg"):
        photo = FSInputFile(news_data["jpg"])
        await bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            
        )
        await bot.send_message(
            chat_id=chat_id,
            text=f"<b>{title}</b>\n\n{content}\n\n<a href='{url}'>Читать в источнике...</a>",
            parse_mode='HTML'
        )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=f"<b>{title}</b>\n\n{content}\n\n<a href='{url}'>Читать в источнике...</a>",
            parse_mode='HTML'
        )
    await asyncio.sleep(10)  # Пауза между сообщениями

async def check_news_updates(chat_id: int):
    """Проверка обновлений новостей"""
    news_dict = await get_all_news()
    session = Session()
    
    try:
        # Обработка новостей УК РФ (YKL)
        ykl_news = news_dict.get("ykl_news", {})
        if ykl_news:
            ykl_record = await get_or_create_news_record(session, YKLNews)
            first_title = next(iter(ykl_news))
            if ykl_record.last_title != first_title:
                await send_news_update(chat_id, "УК РФ", ykl_news)
                await update_news_record(session, YKLNews, first_title)
        
        # Обработка новостей Генпрокуратуры
        genproc_news = news_dict.get("genproc_news", {})
        if genproc_news:
            genproc_record = await get_or_create_news_record(session, GenProcNews)
            first_title = next(iter(genproc_news))
            if genproc_record.last_title != first_title:
                await send_news_update(chat_id, "Генпрокуратура", genproc_news)
                await update_news_record(session, GenProcNews, first_title)
        
        # Обработка новостей МВД
        mvd_news = news_dict.get("mvd_news", {})
        if mvd_news:
            mvd_record = await get_or_create_news_record(session, MVDNews)
            first_title = next(iter(mvd_news))
            if mvd_record.last_title != first_title:
                await send_news_update(chat_id, "МВД", mvd_news)
                await update_news_record(session, MVDNews, first_title)
    
    finally:
        session.close()

async def news_monitor(chat_id: int):
    """Фоновая задача для мониторинга новостей"""
    while True:
        try:
            print("Проверка новостей...")
            await check_news_updates(chat_id)
            await asyncio.sleep(300)  # Пауза 30 минут между проверками
        except Exception as e:
            print(f"Ошибка в news_monitor: {e}")
            await asyncio.sleep(300)  # Пауза 5 минут при ошибке

@dp.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer("Привет!\nЯ бот, который будет присылать новости каждые 10 минут и пауза между проверками сайтов 30 минут с сайтов Генпрокуратуры, МВД и тд.")

async def main():
    print("Старт бота...")
    asyncio.create_task(news_monitor(CHAT_ID))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

