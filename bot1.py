import os
import json
import logging
import asyncio
import yt_dlp
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message
from dotenv import load_dotenv
from collections import defaultdict

# .env faylni yuklash
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Fayl va kataloglar
DOWNLOAD_DIR = "downloads"
DATA_FILE = "stats.json"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Bot va dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Bir vaqtda 10ta foydalanuvchi limit
semaphore = asyncio.Semaphore(10)

# Statistika fayli yaratish yoki yuklash
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        stats = json.load(f)
        stats["users"] = set(stats.get("users", []))
        stats["banned_users"] = set(stats.get("banned_users", []))
        stats["admins"] = set(stats.get("admins", [ADMIN_ID]))
else:
    stats = {
        "users": set(),
        "downloads": defaultdict(list),
        "banned_users": set(),
        "admins": {ADMIN_ID}
    }

# JSON saqlash
def save_stats():
    data = {
        "users": list(stats["users"]),
        "downloads": dict(stats["downloads"]),
        "banned_users": list(stats["banned_users"]),
        "admins": list(stats["admins"]),
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Statistika va foydalanuvchini qo‘shish
def add_user(user_id):
    stats["users"].add(user_id)
    save_stats()

def add_download(user_id, filename):
    stats["downloads"].setdefault(str(user_id), []).append({
        "file": filename,
        "time": datetime.now().isoformat()
    })
    save_stats()

# /start va /help komandasi
@dp.message(Command("start", "help"))
async def send_welcome(message: Message):
    user_id = message.from_user.id
    if user_id in stats["banned_users"]:
        await message.answer("🚫 Siz bloklangansiz. @info0990 ga murojaat qiling.")
        return

    add_user(user_id)
    commands = "/start\n/help"
    if user_id in stats["admins"]:
        commands += "\n/stats\n/ban\n/unban\n/newadmin\n/warn\n/everyone"

    await message.answer(f"""
<b>🎬 YouTube & Instagram Downloader Bot</b>

Salom, {message.from_user.first_name}! 👋  
Men — YouTube va Instagram videolarini tez va sifatli yuklab beruvchi botman.  

<b>Biza umit qilamizki bizni qollan quvvatlaganinggizde bizaga yordam bergan odamiyam qullab quvvatlaysiz</b>
⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇⬇
https://youtube.com/@blzalex?si=Wlrocqu4xBr9wmKq

<b>🛠️ Nima qila olaman?</b>  
▫️ YouTube va Instagram linklarini yuborsang — video va audio yuklab beraman  
▫️ Yuklangan fayllar avtomatik 30 kun ichida o‘chadi  
▫️ Barcha yuklamalaring tarixini saqlamayman — maxfiylik ta’minlangan

<b>📋 Foydalanish qoidalari</b>  
✅ Faqat o‘zing uchun yuklab ol — tarqatish va tijorat maqsadida ishlatma  
❌ Noqonuniy, mualliflik huquqini buzuvchi, zo‘ravonlik, pornografiya va boshqa noqonuniy materiallarni yuklash taqiqlanadi  
⚠️ Qoidalarni buzsang — bloklash va ma’lumotlarni huquq-tartibot organlariga berishimiz mumkin

<b>💡 Qanday ishlataman?</b>  
1️⃣ YouTube yoki Instagram havolasini menga yubor  
2️⃣ Men video va audio fayllarni tayyorlab beraman  
3️⃣ Faylni yuklab ol va zavqlan! 😉

<b>📌 Asosiy komandalar:</b>  
{commands}

<b>🔗 Havola yuborish:</b>  
👉 YouTube linkini yubor: video/audio yuklanadi  
👉 Instagram post linkini yubor: video/audio yuklanadi

<b>🤖 Botdan to‘g‘ri foydalaning va qoidalarni buzmaylik!</b>  
<b>Yaxshi yuklashlar! 🚀</b>
""", parse_mode='HTML')

# /stats komandasi (adminlar uchun)
@dp.message(Command("stats"))
async def send_stats(message: Message):
    if message.from_user.id not in stats["admins"]:
        await message.answer("❌ Sizda ruxsat yo‘q.")
        return
    total_users = len(stats["users"])
    total_downloads = sum(len(lst) for lst in stats["downloads"].values())
    total_banned = len(stats["banned_users"])
    await message.answer(
        f"📊 Statistika:\n"
        f"👥 Foydalanuvchilar: {total_users}\n"
        f"🚫 Ban qilinganlar: {total_banned}\n"
        f"⬇️ Yuklangan fayllar: {total_downloads}"
    )

# /ban, /unban, /newadmin, /warn, /everyone komandasi
@dp.message(Command("ban"))
async def ban_user(message: Message):
    if message.from_user.id not in stats["admins"]:
        await message.answer("❌ Ruxsat yo‘q.")
        return
    try:
        user_id = int(message.text.split()[1])
        stats["banned_users"].add(user_id)
        save_stats()
        await message.answer(f"🚫 Foydalanuvchi {user_id} ban qilindi.")
    except:
        await message.answer("❗ Format: /ban USER_ID")

@dp.message(Command("unban"))
async def unban_user(message: Message):
    if message.from_user.id not in stats["admins"]:
        await message.answer("❌ Ruxsat yo‘q.")
        return
    try:
        user_id = int(message.text.split()[1])
        stats["banned_users"].discard(user_id)
        save_stats()
        await message.answer(f"✅ Foydalanuvchi {user_id} unban qilindi.")
    except:
        await message.answer("❗ Format: /unban USER_ID")

@dp.message(Command("newadmin"))
async def add_admin(message: Message):
    if message.from_user.id not in stats["admins"]:
        await message.answer("❌ Ruxsat yo‘q.")
        return
    try:
        new_admin_id = int(message.text.split()[1])
        stats["admins"].add(new_admin_id)
        save_stats()
        await message.answer(f"✅ Admin {new_admin_id} qo‘shildi.")
    except:
        await message.answer("❗ Format: /newadmin USER_ID")

@dp.message(Command("warn"))
async def warn_user(message: Message):
    if message.from_user.id not in stats["admins"]:
        await message.answer("❌ Ruxsat yo‘q.")
        return
    try:
        parts = message.text.split(maxsplit=2)
        user_id = int(parts[1])
        warning_text = parts[2]
        await bot.send_message(user_id, f"⚠️ Ogohlantirish: {warning_text}")
        await message.answer(f"✅ Ogohlantirish yuborildi.")
    except Exception as e:
        await message.answer(f"❗ Xatolik: {e}\nFormat: /warn USER_ID Matn")

@dp.message(Command("everyone"))
async def everyone(message: Message):
    if message.from_user.id not in stats["admins"]:
        await message.answer("❌ Ruxsat yo‘q.")
        return
    text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not text:
        await message.answer("❗ Format: /everyone Matn")
        return

    for user_id in stats["users"]:
        try:
            await bot.send_message(user_id, f"📢 Yangilik:\n{text}")
        except:
            continue
    await message.answer("✅ Hammaga yuborildi.")

# Media yuklash (YouTube + Instagram)
async def download_media(url, is_audio=False):
    out_format = "bestaudio[ext=m4a]" if is_audio else "best[ext=mp4]"
    ext = "m4a" if is_audio else "mp4"
    opts = {
        "format": out_format,
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": ext
    }

    loop = asyncio.get_running_loop()
    def run_ydl():
        with yt_dlp.YoutubeDL(opts) as ydl:
            result = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(result)
            if not filename.endswith(ext):
                filename = os.path.splitext(filename)[0] + f".{ext}"
            return filename

    file_path = await loop.run_in_executor(None, run_ydl)
    return file_path

# Faylni foydalanuvchiga yuborish
async def send_file(message: Message, file_path, caption):
    file_size = os.path.getsize(file_path) # Fayl hajmini olish
    if file_size > 50 * 1024 * 1024: # 50 MB dan katta bo'lsa
        # Faylni bo'lish
        chunk_size = 49 * 1024 * 1024 # 50 MB
        with open(file_path, 'rb') as f:
            chunk_number = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunk_file_path = f"{file_path}.part{chunk_number}" # Bo'lingan fayl nomi
                with open(chunk_file_path, 'wb') as chunk_file:
                    chunk_file. write(chunk)
                await message.answer_document(FSInputFile(chunk_file_path), caption=caption)
                os.remove(chunk_file_path) # Bo'lingan faylni o'chirish
                chunk_number += 1
    else:
# Oddiy faylni yuborish
        file = FSInputFile(file_path)
        await message.answer_document(file, caption=caption)
        
# Linkni qabul qilish (YouTube va Instagram)
@dp.message(F.text.regexp(r'https?://'))
async def handle_link(message: Message):
    user_id = message.from_user.id
    if user_id in stats["banned_users"]:
        await message.answer("🚫 Siz bloklangansiz. @info0990 ga murojaat qiling.")
        return

    add_user(user_id)
    url = message.text.strip()
    if not any(domain in url for domain in ["youtube.com", "youtu.be", "instagram.com"]):
        await message.answer("❌ Faqat YouTube yoki Instagram havolasini yuboring.")
        return

    await message.answer("⏳ Yuklab olinmoqda...\n1️⃣ Video tayyorlanmoqda...")

    try:
        if ADMIN_ID:
            await bot.send_message(
                ADMIN_ID,
                f"✅ Yangi yuklash:\n👤 @{message.from_user.username or 'Nomaʼlum'} (ID: {user_id})\n🔗 Link: {url}"
            )

        async with semaphore:
            video_path = await download_media(url, is_audio=False)
        await send_file(message, video_path, "🎬 Video tayyor!")
        add_download(user_id, os.path.basename(video_path))

        await message.answer("2️⃣ Endi audio tayyorlanmoqda...")
        async with semaphore:
            audio_path = await download_media(url, is_audio=True)
        await send_file(message, audio_path, "🎵 Audio tayyor!")
        add_download(user_id, os.path.basename(audio_path))

    except Exception as e:
        await message.answer(f"🚫 Xatolik: {e}")
        if ADMIN_ID:
            await bot.send_message(
                ADMIN_ID,
                f"🚨 Xatolik:\n👤 @{message.from_user.username or 'Nomaʼlum'} (ID: {user_id})\n🔗 Link: {url}\n❗ Xatolik: {e}"
            )

# Botni ishga tushirish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
         