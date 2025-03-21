from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import requests
import time
import asyncio

MOVIES_URL = "https://raw.githubusercontent.com/mdnazmul582378/Link-Bot/main/dd.json"
cached_movies = []

def fetch_movies():
    global cached_movies
    response = requests.get(MOVIES_URL)
    if response.status_code == 200:
        cached_movies = response.json()

def relevance_score(query, title):
    query_words = query.lower().split()
    score = sum(word in title.lower() for word in query_words)
    return score

def smart_search_movies(query):
    query_lower = query.lower().strip()
    results = []

    if query_lower.isdigit():
        results = [m for m in cached_movies if m["year"] == query_lower]
    elif query_lower in ["action", "thriller", "romance", "comedy", "drama"]:
        results = [m for m in cached_movies if query_lower in m["genre"].lower()]
    else:
        results = sorted(
            [m for m in cached_movies if all(q in m["title"].lower() for q in query_lower.split()) or query_lower in m["title"].lower()],
            key=lambda x: relevance_score(query_lower, x["title"]),
            reverse=True
        )
    return results

bot = Client(
    "advanced_search_bot",
    api_id=25534833,
    api_hash="8ec7028f3b0871fe6f0ee68e8230e4bc",
    bot_token="7904443875:AAGjAEP9TPljt3f9XbANw0AAfXgm-20u4XY"
)

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 Just send a movie name, and I will find it for you!\n\n👉 Use `/update` to refresh database manually.")

@bot.on_message(filters.command("update"))
async def update_cache(client, message):
    fetch_movies()
    await message.reply_text("✅ Movie database updated successfully!")

@bot.on_message(filters.text & ~filters.command(["start", "update"]))
async def movie_search(client, message):
    if not cached_movies:
        fetch_movies()

    query = message.text.strip()
    searching_msg = await message.reply_text(f"🔎 Searching for {query.upper()}...")
    await asyncio.sleep(1)

    start_time = time.time()
    results = smart_search_movies(query)

    await searching_msg.delete()

    if not results:
        no_result_msg = await message.reply_text("❌ No results found.")
        await asyncio.sleep(10)
        await no_result_msg.delete()
        return

    await send_paginated_results(client, message, results, query, 1, start_time)

async def send_paginated_results(client, message, results, query, page, start_time):
    total_pages = (len(results) + 4) // 5
    start_idx = (page - 1) * 5
    end_idx = start_idx + 5
    current_page_results = results[start_idx:end_idx]

    buttons = [
        [InlineKeyboardButton(f"🎬 {m['title']} | {m['year']} | {m['genre']}", url=f"https://t.me/autolinkersbot?start={m['id']}")]
        for m in current_page_results
    ]

    nav_buttons = []
    if total_pages > 1:
        prev_btn = InlineKeyboardButton("⬅️ Prev", callback_data=f"prev|{query}|{page}") if page > 1 else InlineKeyboardButton(" ", callback_data="ignore")
        page_btn = InlineKeyboardButton(f"{page}/{total_pages}", callback_data="ignore")
        next_btn = InlineKeyboardButton("Next ➡️", callback_data=f"next|{query}|{page}") if page < total_pages else InlineKeyboardButton(" ", callback_data="ignore")
        nav_buttons.append([prev_btn, page_btn, next_btn])

    response_time = round(time.time() - start_time, 2)

    caption_text = f"""✅ Results shown in: {response_time} seconds  
🔎 Search query: `{query}`  
🙋 Requested by: {message.from_user.first_name}  
📽️ Group: 4K Movie  

⚠️ This message will auto-delete after 2 minutes."""

    sent_msg = await message.reply_text(
        caption_text,
        reply_markup=InlineKeyboardMarkup(buttons + nav_buttons),
        protect_content=True
    )
    await asyncio.sleep(120)
    await sent_msg.delete()

@bot.on_callback_query()
async def handle_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    if data.startswith("next") or data.startswith("prev"):
        action, query, current_page = data.split("|")
        current_page = int(current_page)
        page = current_page + 1 if action == "next" else current_page - 1
        results = smart_search_movies(query)
        await callback_query.message.delete()
        await send_paginated_results(client, callback_query.message, results, query, page, time.time())
    else:
        await callback_query.answer("")

bot.run()
