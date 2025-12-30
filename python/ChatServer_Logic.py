# print('ishlaydi Demaganmidim ku')

# version 1.0.0
# GitHub: 
# Telegram guruhidan xabarlarni olib, Firebase Realtime Database ga saqlaydi

from telethon import TelegramClient, events
import firebase_admin
from firebase_admin import credentials, db
import hashlib
import time
import re

# Firebase konfiguratsiyasi
firebase_config = {
    "apiKey": "AIzaSyAbfyNVpg0g_khth6HzU6W2QaCq6ZYJ9a8",
    "authDomain": "claudechat-98cfd.firebaseapp.com",
    "databaseURL": "https://claudechat-98cfd-default-rtdb.firebaseio.com/",
    "projectId": "claudechat-98cfd",
    "storageBucket": "claudechat-98cfd.firebasestorage.app",
    "messagingSenderId": "540336164827",
    "appId": "1:540336164827:web:052a24614aab740a6761fe",
    "measurementId": "G-FTQHD5ETF3"
}

# Telegram API ma'lumotlari
api_id = 39529573
api_hash = 'f71653a3c1242e59daa29eedde98c75f'

# Guruh username
group_username = 'isuzigrupa'  # havola_yomonmi

# Saqlangan xabarlarni takrorlanishini oldini olish uchun
sent_messages = set()
MAX_CACHE_SIZE = 1000
CLEANUP_INTERVAL = 100

message_counter = 0

def get_message_hash(message_id, sender_id, text):
    """Xabar uchun unique hash yaratish"""
    content = f"{message_id}_{sender_id}_{text[:100]}"
    return hashlib.md5(content.encode()).hexdigest()

def format_text_for_firebase(text):
    """Matndagi qator tashlashlarni saqlab, Firebase uchun formatlash"""
    if not text:
        return ""

    # HTML yoki maxsus formatlarni tekshirish
    if '<' in text and '>' in text:
        # HTML formatda bo'lsa, oddiy matnga o'tkazish
        text = re.sub(r'<[^>]+>', '', text)

    # Qator tashlashlarni saqlash
    # \n ni saqlash uchun almashtirish
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Ko'p bo'sh joylarni bittaga qisqartirish (agar kerak bo'lsa)
    # text = re.sub(r'\n{3,}', '\n\n', text)

    return text

def format_text_for_display(text):
    """Matnni ko'rish uchun formatlash (debug uchun)"""
    if not text:
        return ""

    # Qator tashlashlarni ko'rinishli qilish
    formatted = text.replace('\n', '↵\n')

    # Uzun matnlarni qisqartirish
    if len(formatted) > 100:
        formatted = formatted[:97] + "..."

    return formatted

# Firebase initialization
firebase_initialized = False
try:
    cred = credentials.Certificate("firebase-service-key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': firebase_config['databaseURL']
    })
    firebase_initialized = True
    print("✓ Firebase muvaffaqiyatli ulandi")
except Exception as e:
    print(f"✗ Firebase ulanish xatosi: {e}")
    print("Iltimos, Firebase service account faylini yuklang")
    print("Firebase Console > Project Settings > Service Accounts > Generate New Private Key")

# Telegram client
client = TelegramClient('session_name2_v100', api_id, api_hash)

def cleanup_cache():
    """Cache ni tozalash"""
    global sent_messages
    if len(sent_messages) > MAX_CACHE_SIZE:
        sent_messages = set(list(sent_messages)[-MAX_CACHE_SIZE//2:])
        print(f"Cache tozalandi. Joriy cache hajmi: {len(sent_messages)}")

@client.on(events.NewMessage(chats=group_username))
async def handler(event):
    global message_counter

    try:
        # Xabarni olish
        message = event.message

        # Xabar matnini to'liq olish (qator tashlashlar bilan)
        # Method 1: Raw text olish
        raw_text = message.raw_text if hasattr(message, 'raw_text') else None

        # Method 2: Message.text property
        message_text = message.text

        # Method 3: Format qilingan matnni olish
        formatted_text = None
        if hasattr(message, 'message'):
            formatted_text = message.message

        # Eng yaxshi matnni tanlash
        text = None
        if raw_text:  # Raw text bor bo'lsa (qator tashlashlar bilan)
            text = raw_text
        elif formatted_text:  # Format qilingan matn
            text = formatted_text
        elif message_text:  # Oddiy text property
            text = message_text
        else:
            # Agar matn bo'lmasa
            return

        # Matnni tekshirish
        if not text or text.strip() == "":
            return

        # Qator tashlashlarni saqlash uchun formatlash
        formatted_message = format_text_for_firebase(text)

        # Xabar ma'lumotlarini olish
        message_id = message.id

        # Yuboruvchi ma'lumotlari
        sender = await message.get_sender()
        sender_id = sender.id if sender else 0

        # Xabar hash yaratish (formatlangan matn bilan)
        msg_hash = get_message_hash(message_id, sender_id, formatted_message)

        # Bu xabar oldin yuborilganmi tekshirish
        if msg_hash in sent_messages:
            print(f"⚠️ Xabar takrorlanmoqda, o'tkazib yuborildi: {message_id}")
            return

        # Cache ga qo'shish
        sent_messages.add(msg_hash)
        message_counter += 1

        # To'liq ismni tayyorlash
        full_name = "Noma'lum"
        if sender:
            name_parts = []
            if sender.first_name:
                name_parts.append(sender.first_name)
            if sender.last_name:
                name_parts.append(sender.last_name)

            if name_parts:
                full_name = " ".join(name_parts)
            elif sender.username:
                full_name = sender.username
            else:
                full_name = f"User_{sender_id}"

        # Debug uchun qator tashlashlarni ko'rsatish
        display_text = format_text_for_display(formatted_message)
        print(f"📝 Original matn ({len(text)} belgi): {display_text}")
        print(f"📝 Formatlangan matn ({len(formatted_message)} belgi): {display_text}")

        # Qator tashlashlar sonini hisoblash
        newline_count = formatted_message.count('\n')
        if newline_count > 0:
            print(f"↵ Qator tashlashlar soni: {newline_count}")

        # Firebase ga saqlash uchun xabar tuzish
        message_data = {
            'text': formatted_message,  # Formatlangan matn (qator tashlashlar bilan)
            'username': full_name[:20],
            'timestamp': {
                '.sv': 'timestamp'
            },
            'userId': f"telegram_{sender_id}_{message_id}",
            'source': 'telegram',
            'telegram_message_id': message_id,
            'telegram_date': message.date.isoformat() if message.date else None,
            'hash': msg_hash,
            'newlines_count': newline_count  # Qator tashlashlar soni
        }

        # Firebase ga xabarni yuborish
        if firebase_initialized:
            try:
                ref = db.reference('messages')
                new_message_ref = ref.push()
                new_message_ref.set(message_data)
                print(f"✓ Firebase ga saqlandi [{message_counter}]: {full_name}")
                print(f"   Matn uzunligi: {len(formatted_message)} belgi")
                print(f"   Qator tashlashlar: {newline_count} ta")
            except Exception as e:
                print(f"✗ Firebase xatosi: {e}")
                sent_messages.remove(msg_hash)
                return
        else:
            # REST API orqali urinish
            await send_to_firebase_rest_api(message_data, msg_hash)

        # Cache ni tozalash
        if message_counter % CLEANUP_INTERVAL == 0:
            cleanup_cache()

        # O'z Saved Messages'ga yuborish (qator tashlashlar bilan)
        try:
            saved_msg = f"{full_name}:\n{formatted_message}"
            await client.send_message('me', saved_msg)
        except Exception as e:
            print(f"✗ Saved Messages ga yuborishda xatolik: {e}")

    except Exception as e:
        print(f"✗ Umumiy xatolik: {e}")
        import traceback
        traceback.print_exc()

async def send_to_firebase_rest_api(message_data, msg_hash):
    """Firebase REST API orqali xabarni yuborish"""
    try:
        import aiohttp
        import json

        database_url = firebase_config['databaseURL']
        messages_url = f"{database_url}/messages.json"

        # JSON formatida yuborish
        async with aiohttp.ClientSession() as session:
            async with session.post(messages_url, json=message_data) as response:
                if response.status == 200:
                    print(f"✓ REST API orqali saqlandi: {message_data['username']}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"✗ REST API xatosi: {response.status} - {error_text}")
                    sent_messages.remove(msg_hash)
                    return False
    except Exception as e:
        print(f"✗ REST API ulanish xatosi: {e}")
        sent_messages.remove(msg_hash)
        return False

@client.on(events.NewMessage(pattern='/test'))
async def test_handler(event):
    """Test xabar yuborish uchun handler"""
    test_text = "Bu test xabar\nIkkinchi qator\nUchinchi qator\n\nBo'sh qatordan keyin"
    await event.reply(test_text)
    print(f"Test xabar yuborildi:\n{test_text}")

@client.on(events.NewMessage(pattern='/status'))
async def status_handler(event):
    """Statusni tekshirish uchun handler"""
    status_msg = f"🤖 Bot ishlayapti\n"
    status_msg += f"📊 Xabarlar soni: {message_counter}\n"
    status_msg += f"💾 Cache hajmi: {len(sent_messages)}\n"
    status_msg += f"🔗 Firebase holati: {'Faol' if firebase_initialized else 'Oʻchirilgan'}\n"
    status_msg += f"👥 Monitoring: {group_username}"

    await event.reply(status_msg)

@client.on(events.NewMessage(pattern='/debug'))
async def debug_handler(event):
    """Debug ma'lumotlari uchun handler"""
    try:
        # Oxirgi 5 ta xabar hash larini ko'rsatish
        recent_hashes = list(sent_messages)[-5:] if sent_messages else []

        debug_msg = f"🔧 Debug ma'lumotlari:\n"
        debug_msg += f"Xabarlar soni: {message_counter}\n"
        debug_msg += f"Cache hajmi: {len(sent_messages)}\n"
        debug_msg += f"Oxirgi 5 hash: {recent_hashes}\n"
        debug_msg += f"Firebase: {'✅' if firebase_initialized else '❌'}"

        await event.reply(debug_msg)
    except Exception as e:
        await event.reply(f"Debug xatosi: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 Telegram -> Firebase Bot (Qator tashlashlar bilan)")
    print("=" * 50)
    print(f"📡 Monitoring guruh: {group_username}")
    print(f"📊 Firebase holati: {'Faol' if firebase_initialized else 'Oʻchirilgan'}")
    print("💡 Qator tashlashlar (↵) saqlanadi")
    print("=" * 50)
    print("Bot ishga tushdi...")
    print("Kutilayotgan xabarlar...")
    print("\nTest uchun /test komandasini yuboring")
    print("=" * 50)

    try:
        with client:
            client.run_until_disconnected()
    except KeyboardInterrupt:
        print("\n👋 Bot to'xtatildi")
    except Exception as e:
        print(f"\n❌ Xatolik: {e}")
        import traceback
        traceback.print_exc()
