from datetime import timedelta, datetime
import pytz
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import ADMINS, LOG_CHANNEL
from utils import get_seconds
from database.users_chats_db import db
import string
import random

VALID_REDEEM_CODES = {}

def generate_code(length=8):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for _ in range(length))

@Client.on_message(filters.command("add_redeem") & filters.user(ADMINS))
async def add_redeem_code(client, message):
    user_id = message.from_user.id
    if len(message.command) == 3:
        try:
            time = message.command[1]
            num_codes = int(message.command[2])
        except ValueError:
            await message.reply_text("Please provide a valid number of codes to generate.")
            return

        codes = []
        for _ in range(num_codes):
            code = generate_code()
            VALID_REDEEM_CODES[code] = time
            codes.append(code)

        codes_text = '\n'.join(f"➔ <code>/redeem {code}</code>" for code in codes)
        response_text = f"""
<b>Gɪғᴛᴄᴏᴅᴇ Gᴇɴᴇʀᴀᴛᴇᴅ ✅
Aᴍᴏᴜɴᴛ:</b> {num_codes}

{codes_text}
<b>Duration:</b> {time}

🔰<u>𝗥𝗲𝗱𝗲𝗲𝗺 𝗜𝗻𝘀𝘁𝗿𝘂𝗰𝘁𝗶𝗼𝗻</u>🔰
<b>𝙹𝚞𝚜𝚝 𝚌𝚕𝚒𝚌𝚔 𝚝𝚑𝚎 𝚊𝚋𝚘𝚟𝚎 𝚌𝚘𝚍𝚎 𝚝𝚘 𝚌𝚘𝚙𝚢 𝚊𝚗𝚍 𝚝𝚑𝚎𝚗 𝚜𝚎𝚗𝚍 𝚝𝚑𝚊𝚝 𝚌𝚘𝚍𝚎 𝚝𝚘 𝚝𝚑𝚎 𝙱𝚘𝚝, 𝚝𝚑𝚊𝚝'𝚜 𝚒𝚝 🔥</b>"""

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("♻️ Redeem Here ♻️", url="http://t.me/ordinary_helper")],
                [InlineKeyboardButton("❕ Any Query ❕", url="https://t.me/ordinary_helper")]
            ]
        )

        await message.reply_text(response_text, reply_markup=keyboard)
    else:
        await message.reply_text("<b>♻ Usage:\n\n➩ <code>/add_redeem 1min 1</code>,\n➩ <code>/add_redeem 1hour 10</code>,\n➩ <code>/add_redeem 1day 5</code></b>")

@Client.on_message(filters.command("redeem"))
async def redeem_code(client, message):
    user_id = message.from_user.id
    if len(message.command) == 2:
        redeem_code = message.command[1]

        if redeem_code in VALID_REDEEM_CODES:
            try:
                time = VALID_REDEEM_CODES.pop(redeem_code)
                user = await client.get_users(user_id)

                try:
                    seconds = await get_seconds(time)
                except Exception as e:
                    await message.reply_text("Invalid time format in redeem code.")
                    return

                if seconds > 0:
                    data = await db.get_user(user_id)
                    current_expiry = data.get("expiry_time") if data else None

                    now_aware = datetime.now(pytz.utc)

                    if current_expiry:
                        current_expiry = current_expiry.replace(tzinfo=pytz.utc)

                    if current_expiry and current_expiry > now_aware:
                        expiry_str_in_ist = current_expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ Expiry Time: %I:%M:%S %p")
                        await message.reply_text(
                            f"🚫 You already have premium access, which expires on {expiry_str_in_ist}.\nYou cannot redeem another code until your current premium expires.",
                            disable_web_page_preview=True
                        )
                        return

                    expiry_time = now_aware + timedelta(seconds=seconds)
                    user_data = {"id": user_id, "expiry_time": expiry_time}
                    await db.update_user(user_data)

                    expiry_str_in_ist = expiry_time.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ Expiry Time: %I:%M:%S %p")

                    await message.reply_text(
                        f"Premium activated successfully!\n\nUser: {user.mention}\nUser ID: {user_id}\nPremium Access: <code>{time}</code>\n\nExpiry Date: {expiry_str_in_ist}",
                        disable_web_page_preview=True
                    )

                    await client.send_message(
                        LOG_CHANNEL,
                        text=f"#Redeem_Premium\n\n👤 User: {user.mention}\n⚡ User ID: <code>{user_id}</code>\n⏰ Premium Access: <code>{time}</code>\n⌛️ Expiry Date: {expiry_str_in_ist}",
                        disable_web_page_preview=True
                    )
                else:
                    await message.reply_text("Invalid time format in redeem code.")
            except Exception as e:
                await message.reply_text(f"An error occurred while redeeming the code: {e}")
        else:
            await message.reply_text("Invalid Redeem Code or Expired.")
    else:
        await message.reply_text("Usage: /redeem <code>")
