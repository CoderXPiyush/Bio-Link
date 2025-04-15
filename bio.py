from pyrogram import Client, filters, enums, errors
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
import re

# User Client setup
api_id = "22321019"     # Replace this api_id
api_hash = "8746334865761149185b4263cc626e359"       # Replace this api_hash
bot_token = "7803060450:AAGh_qcYUrYupdfBmNGSIrO842z59MxC9u4"
app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

url_pattern = re.compile(
    r'(https?://|www\.)[a-zA-Z0-9.\-]+(\.[a-zA-Z]{2,})+(/[a-zA-Z0-9._%+-]*)*'
)

warnings = {}
punishment = {}

default_warning_limit = 3  #Default Warning Limit
default_punishment = "mute" #Default punishment Limit 
default_punishment_set = ("warn", default_warning_limit, default_punishment)

async def is_admin(client, chat_id, user_id):
    async for member in client.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
        if member.user.id == user_id:
            return True
    return False

async def has_permissions(client, chat_id, user_id, permissions):
    chat_member = await client.get_chat_member(chat_id, user_id)
    for perm in permissions:
        if not getattr(chat_member.privileges, perm, False):
            return False
    return True

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_name = message.from_user.first_name
    start_message = (
        f"Hello {user_name}!\n\n"
        "Welcome to the Bio Link Monitor Bot! I help keep Telegram groups clean by monitoring user bios for unauthorized links. "
        "Group admins can configure me to warn, mute, or ban users who have links in their bios.\n\n"
        "Use the buttons below to join our support group or add me to your group!"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Support Group", url="https://t.me/itsSmartDev")],
        [InlineKeyboardButton("Add to Group", url=f"https://t.me/{(await client.get_me()).username}?startgroup=true")]
    ])
    await message.reply_text(start_message, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)

@app.on_message(filters.group & filters.command("config"))
async def configure(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not await is_admin(client, chat_id, user_id):
        await message.reply_text("<b>❌ You are not administrator</b>", parse_mode=enums.ParseMode.HTML)
        await message.delete()  # Delete the command message
        return

    current_punishment = punishment.get(chat_id, default_punishment_set)[2]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Warn", callback_data="warn")],
        [InlineKeyboardButton("Mute ✅" if current_punishment == "mute" else "Mute", callback_data="mute"), 
         InlineKeyboardButton("Ban ✅" if current_punishment == "ban" else "Ban", callback_data="ban"),
         InlineKeyboardButton("Delete ✅" if current_punishment == "delete" else "Delete", callback_data="delete")],
        [InlineKeyboardButton("Close", callback_data="close")]
    ])
    await message.reply_text("<b>Select punishment for users who have links in their bio:</b>", reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
    await message.delete()  # Delete the command message

@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if not await is_admin(client, chat_id, user_id):
        await callback_query.answer("❌ You are not administrator", show_alert=True)
        return

    if data == "close":
        await callback_query.message.delete()
        return

    if data == "back":
        current_punishment = punishment.get(chat_id, default_punishment_set)[2]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Warn", callback_data="warn")],
            [InlineKeyboardButton("Mute ✅" if current_punishment == "mute" else "Mute", callback_data="mute"), 
             InlineKeyboardButton("Ban ✅" if current_punishment == "ban" else "Ban", callback_data="ban"),
             InlineKeyboardButton("Delete ✅" if current_punishment == "delete" else "Delete", callback_data="delete")],
            [InlineKeyboardButton("Close", callback_data="close")]
        ])
        await callback_query.message.edit_text("<b>Select punishment for users who have links in their bio:</b>", reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
        return

    if data == "warn":
        current_warning_limit = punishment.get(chat_id, default_punishment_set)[1]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("3 ✅" if current_warning_limit == 3 else "3", callback_data="warn_3"), 
             InlineKeyboardButton("4 ✅" if current_warning_limit == 4 else "4", callback_data="warn_4"),
             InlineKeyboardButton("5 ✅" if current_warning_limit == 5 else "5", callback_data="warn_5")],
            [InlineKeyboardButton("Back", callback_data="back"), InlineKeyboardButton("Close", callback_data="close")]
        ])
        await callback_query.message.edit_text("<b>Select the number of warnings before punishment:</b>", reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
        return

    if data in ["mute", "ban", "delete"]:
        punishment[chat_id] = ("warn", punishment.get(chat_id, default_punishment_set)[1], data)
        selected_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Warn", callback_data="warn")],
            [InlineKeyboardButton("Mute ✅" if data == "mute" else "Mute", callback_data="mute"), 
             InlineKeyboardButton("Ban ✅" if data == "ban" else "Ban", callback_data="ban"),
             InlineKeyboardButton("Delete ✅" if data == "delete" else "Delete", callback_data="delete")],
            [InlineKeyboardButton("Close", callback_data="close")]
        ])
        await callback_query.message.edit_text("<b>Punishment selected:</b>", reply_markup=selected_keyboard, parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
    elif data.startswith("warn_"):
        num_warnings = int(data.split("_")[1])
        punishment[chat_id] = ("warn", num_warnings, punishment.get(chat_id, default_punishment_set)[2])
        current_warning_limit = punishment.get(chat_id, default_punishment_set)[1]
        selected_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("3 ✅" if num_warnings == 3 else "3", callback_data="warn_3"), 
             InlineKeyboardButton("4 ✅" if num_warnings == 4 else "4", callback_data="warn_4"),
             InlineKeyboardButton("5 ✅" if num_warnings == 5 else "5", callback_data="warn_5")],
            [InlineKeyboardButton("Back", callback_data="back"), InlineKeyboardButton("Close", callback_data="close")]
        ])
        await callback_query.message.edit_text(f"<b>Warning limit set to {num_warnings}</b>", reply_markup=selected_keyboard, parse_mode=enums.ParseMode.HTML)
        await callback_query.answer()
    elif data.startswith("unmute_"):
        target_user_id = int(data.split("_")[1])
        target_user = await client.get_chat(target_user_id)
        target_user_name = f"{target_user.first_name} {target_user.last_name}" if target_user.last_name else target_user.first_name
        try:
            await client.restrict_chat_member(chat_id, target_user_id, ChatPermissions(can_send_messages=True))
            await callback_query.message.edit(f"{target_user_name} [<code>{target_user_id}</code>] has been unmuted", parse_mode=enums.ParseMode.HTML)
        except errors.ChatAdminRequired:
            await callback_query.message.edit("I don't have permission to unmute users.")
        await callback_query.answer()
    elif data.startswith("unban_"):
        target_user_id = int(data.split("_")[1])
        target_user = await client.get_chat(target_user_id)
        target_user_name = f"{target_user.first_name} {target_user.last_name}" if target_user.last_name else target_user.first_name
        try:
            await client.unban_chat_member(chat_id, target_user_id)
            await callback_query.message.edit(f"{target_user_name} [<code>{target_user_id}</code>] has been unbanned", parse_mode=enums.ParseMode.HTML)
        except errors.ChatAdminRequired:
            await callback_query.message.edit("I don't have permission to unban users.")
        await callback_query.answer()
    elif data.startswith("undelete_"):
        target_user_id = int(data.split("_")[1])
        target_user = await client.get_chat(target_user_id)
        target_user_name = f"{target_user.first_name} {target_user.last_name}" if target_user.last_name else target_user.first_name
        try:
            await client.restrict_chat_member(chat_id, target_user_id, ChatPermissions(can_send_messages=True))
            await callback_query.message.edit(f"{target_user_name} [<code>{target_user_id}</code>] has been allowed to send messages again", parse_mode=enums.ParseMode.HTML)
        except errors.ChatAdminRequired:
            await callback_query.message.edit("I don't have permission to restore message sending rights.")
        await callback_query.answer()

@app.on_message(filters.group)
async def check_bio(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # Fetch user bio
    user_full = await client.get_chat(user_id)
    bio = user_full.bio
    if user_full.username:
        user_name = f"@{user_full.username} [<code>{user_id}</code>]"
    else:
        user_name = f"{user_full.first_name} {user_full.last_name} [<code>{user_id}</code>]" if user_full.last_name else f"{user_full.first_name} [<code>{user_id}</code>]"

    if bio and re.search(url_pattern, bio):
        try:
            await message.delete()
        except errors.MessageDeleteForbidden:
            await message.reply_text("Please grant me delete permission.")
            return

        action = punishment.get(chat_id, default_punishment_set)
        if action[0] == "warn":
            if user_id not in warnings:
                warnings[user_id] = 0
            warnings[user_id] += 1
            sent_msg = await message.reply_text(f"{user_name} please remove any links from your bio. Warned {warnings[user_id]}/{action[1]}", parse_mode=enums.ParseMode.HTML)
            if warnings[user_id] >= action[1]:
                try:
                    if action[2] == "mute":
                        await client.restrict_chat_member(chat_id, user_id, ChatPermissions())
                        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Unmute ✅", callback_data=f"unmute_{user_id}")]])
                        await sent_msg.edit(f"{user_name} has been 🔇 muted for [ Link In Bio ].", reply_markup=keyboard)
                    elif action[2] == "ban":
                        await client.ban_chat_member(chat_id, user_id)
                        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Unban ✅", callback_data=f"unban_{user_id}")]])
                        await sent_msg.edit(f"{user_name} has been 🔨 banned for [ Link In Bio ].", reply_markup=keyboard)
                    elif action[2] == "delete":
                        await client.restrict_chat_member(chat_id, user_id, ChatPermissions())
                        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Restore Messages ✅", callback_data=f"undelete_{user_id}")]])
                        await sent_msg.edit(f"{user_name}'s messages will be deleted and they cannot send new messages until they remove the link from their bio.", reply_markup=keyboard)
                except errors.ChatAdminRequired:
                    await sent_msg.edit(f"I don't have permission to {action[2]} users.")
        elif action[2] == "mute":
            try:
                await client.restrict_chat_member(chat_id, user_id, ChatPermissions())
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Unmute", callback_data=f"unmute_{user_id}")]])
                await message.reply_text(f"{user_name} has been 🔇 muted for [ Link In Bio ].", reply_markup=keyboard)
            except errors.ChatAdminRequired:
                await message.reply_text("I don't have permission to mute users.")
        elif action[2] == "ban":
            try:
                await client.ban_chat_member(chat_id, user_id)
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Unban", callback_data=f"unban_{user_id}")]])
                await message.reply_text(f"{user_name} has been 🔨 banned for [ Link In Bio ].", reply_markup=keyboard)
            except errors.ChatAdminRequired:
                await message.reply_text("I don't have permission to ban users.")
        elif action[2] == "delete":
            try:
                await client.restrict_chat_member(chat_id, user_id, ChatPermissions())
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Restore Messages", callback_data=f"undelete_{user_id}")]])
                await message.reply_text(f"{user_name}'s messages will be deleted and they cannot send new messages until they remove the link from their bio.", reply_markup=keyboard)
            except errors.ChatAdminRequired:
                await message.reply_text("I don't have permission to restrict message sending.")
    else:
        # If user has removed the link, reset their warnings
        if user_id in warnings:
            del warnings[user_id]

app.run()
