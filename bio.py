from pyrogram import client, filters, enums, errors
from pyrogram.types import inlinekeyboardmarkup, inlinekeyboardbutton, chatpermissions
import re
import logging

# configure logging
logging.basicconfig(level=logging.info, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getlogger(__name__)

# constants
default_warning_limit = 3
default_punishment = "mute"
default_punishment_set = ("warn", default_warning_limit, default_punishment)
api_id = "12345678"  # replace with your api_id
api_hash = "abcdefghijklm123456789"  # replace with your api_hash
bot_token = "123456789:abcdefh-k6lryjqj7a28eocxy"  # replace with your bot_token

# initialize client
app = client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# storage
warnings = {}
punishment = {}
url_pattern = re.compile(
    r'(https?://|www\.)[a-z0-9.\-]+(\.[a-z]{2,})+(/[a-z0-9._%+-]*)*',
    re.ignorecase
)

async def is_admin(client, chat_id, user_id):
    """check if user is an admin in the chat."""
    try:
        async for member in client.get_chat_members(chat_id, filter=enums.chatmembersfilter.administrators):
            if member.user.id == user_id:
                return true
        return false
    except errors.floodwait as e:
        logger.warning(f"flood wait error: {e}")
        return false
    except exception as e:
        logger.error(f"error checking admin status: {e}")
        return false

async def get_user_name(client, user_id):
    """fetch formatted user name or username."""
    try:
        user = await client.get_chat(user_id)
        if user.username:
            return f"@{user.username} [<code>{user_id}</code>]"
        return f"{user.first_name} {user.last_name or ''} [<code>{user_id}</code>]".strip()
    except exception as e:
        logger.error(f"error fetching user name: {e}")
        return f"user [<code>{user_id}</code>]"

@app.on_message(filters.group & filters.command("config"))
async def configure(client, message):
    """configure punishment settings for the group."""
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not await is_admin(client, chat_id, user_id):
        await message.reply_text("<b>❌ you are not an administrator</b>", parse_mode=enums.parsemode.html)
        await message.delete()
        return

    current_punishment = punishment.get(chat_id, default_punishment_set)[2]
    keyboard = inlinekeyboardmarkup([
        [inlinekeyboardbutton("warn", callback_data="warn")],
        [inlinekeyboardbutton(f"mute ✅" if current_punishment == "mute" else "mute", callback_data="mute"),
         inlinekeyboardbutton(f"ban ✅" if current_punishment == "ban" else "ban", callback_data="ban")],
        [inlinekeyboardbutton("close", callback_data="close")]
    ])
    await message.reply_text(
        "<b>select punishment for users with links in bio:</b>",
        reply_markup=keyboard,
        parse_mode=enums.parsemode.html
    )
    await message.delete()

@app.on_callback_query()
async def callback_handler(client, callback_query):
    """handle all callback queries."""
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if not await is_admin(client, chat_id, user_id):
        await callback_query.answer("❌ you are not an administrator", show_alert=true)
        return

    try:
        if data == "close":
            await callback_query.message.delete()
            return

        if data == "back":
            current_punishment = punishment.get(chat_id, default_punishment_set)[2]
            keyboard = inlinekeyboardmarkup([
                [inlinekeyboardbutton("warn", callback_data="warn")],
                [inlinekeyboardbutton(f"mute ✅" if current_punishment == "mute" else "mute", callback_data="mute"),
                 inlinekeyboardbutton(f"ban ✅" if current_punishment == "ban" else "ban", callback_data="ban")],
                [inlinekeyboardbutton("close", callback_data="close")]
            ])
            await callback_query.message.edit_text(
                "<b>select punishment for users with links in bio:</b>",
                reply_markup=keyboard,
                parse_mode=enums.parsemode.html
            )
            return

        if data == "warn":
            current_warning_limit = punishment.get(chat_id, default_punishment_set)[1]
            keyboard = inlinekeyboardmarkup([
                [inlinekeyboardbutton(f"3 ✅" if current_warning_limit == 3 else "3", callback_data="warn_3"),
                 inlinekeyboardbutton(f"4 ✅" if current_warning_limit == 4 else "4", callback_data="warn_4"),
                 inlinekeyboardbutton(f"5 ✅" if current_warning_limit == 5 else "5", callback_data="warn_5")],
                [inlinekeyboardbutton("back", callback_data="back"), inlinekeyboardbutton("close", callback_data="close")]
            ])
            await callback_query.message.edit_text(
                "<b>select number of warnings before punishment:</b>",
                reply_markup=keyboard,
                parse_mode=enums.parsemode.html
            )
            return

        if data in ["mute", "ban"]:
            punishment[chat_id] = ("warn", punishment.get(chat_id, default_punishment_set)[1], data)
            keyboard = inlinekeyboardmarkup([
                [inlinekeyboardbutton("warn", callback_data="warn")],
                [inlinekeyboardbutton(f"mute ✅" if data == "mute" else "mute", callback_data="mute"),
                 inlinekeyboardbutton(f"ban ✅" if data == "ban" else "ban", callback_data="ban")],
                [inlinekeyboardbutton("close", callback_data="close")]
            ])
            await callback_query.message.edit_text(
                f"<b>punishment set to {data}</b>",
                reply_markup=keyboard,
                parse_mode=enums.parsemode.html
            )
            await callback_query.answer(f"punishment updated to {data}")
            logger.info(f"punishment for chat {chat_id} set to {data}")
            return

        if data.startswith("warn_"):
            try:
                num_warnings = int(data.split("_")[1])
                if num_warnings not in [3, 4, 5]:
                    raise valueerror("invalid warning count")
                punishment[chat_id] = ("warn", num_warnings, punishment.get(chat_id, default_punishment_set)[2])
                keyboard = inlinekeyboardmarkup([
                    [inlinekeyboardbutton(f"3 ✅" if num_warnings == 3 else "3", callback_data="warn_3"),
                     inlinekeyboardbutton(f"4 ✅" if num_warnings == 4 else "4", callback_data="warn_4"),
                     inlinekeyboardbutton(f"5 ✅" if num_warnings == 5 else "5", callback_data="warn_5")],
                    [inlinekeyboardbutton("back", callback_data="back"), inlinekeyboardbutton("close", callback_data="close")]
                ])
                await callback_query.message.edit_text(
                    f"<b>warning limit set to {num_warnings}</b>",
                    reply_markup=keyboard,
                    parse_mode=enums.parsemode.html
                )
                await callback_query.answer(f"warning limit set to {num_warnings}")
                logger.info(f"warning limit for chat {chat_id} set to {num_warnings}")
            except valueerror:
                await callback_query.answer("invalid warning selection", show_alert=true)
            return

        if data.startswith("unmute_"):
            try:
                target_user_id = int(data.split("_")[1])
                user_name = await get_user_name(client, target_user_id)
                await client.restrict_chat_member(chat_id, target_user_id, chatpermissions(can_send_messages=true))
                await callback_query.message.edit(
                    f"{user_name} has been unmuted",
                    parse_mode=enums.parsemode.html
                )
                logger.info(f"user {target_user_id} unmuted in chat {chat_id}")
            except errors.chatadminrequired:
                await callback_query.message.edit("i don't have permission to unmute users.")
            except valueerror:
                await callback_query.answer("invalid user id", show_alert=true)
            return

        if data.startswith("unban_"):
            try:
                target_user_id = int(data.split("_")[1])
                user_name = await get_user_name(client, target_user_id)
                await client.unban_chat_member(chat_id, target_user_id)
                await callback_query.message.edit(
                    f"{user_name} has been unbanned",
                    parse_mode=enums.parsemode.html
                )
                logger.info(f"user {target_user_id} unbanned in chat {chat_id}")
            except errors.chatadminrequired:
                await callback_query.message.edit("i don't have permission to unban users.")
            except valueerror:
                await callback_query.answer("invalid user id", show_alert=true)
            return

    except exception as e:
        logger.error(f"error in callback handler: {e}")
        await callback_query.answer("an error occurred, please try again.", show_alert=true)

@app.on_message(filters.group)
async def check_bio(client, message):
    """check user bio for links and apply punishments."""
    chat_id = message.chat.id
    user_id = message.from_user.id

    try:
        user_full = await client.get_chat(user_id)
        bio = user_full.bio or ""
        user_name = await get_user_name(client, user_id)

        if re.search(url_pattern, bio):
            try:
                await message.delete()
            except errors.messagedeleteforbidden:
                await message.reply_text("please grant me delete permission.")
                return

            action = punishment.get(chat_id, default_punishment_set)
            if action[0] == "warn":
                warnings[user_id] = warnings.get(user_id, 0) + 1
                sent_msg = await message.reply_text(
                    f"{user_name} please remove links from your bio. warned {warnings[user_id]}/{action[1]}",
                    parse_mode=enums.parsemode.html
                )
                if warnings[user_id] >= action[1]:
                    try:
                        if action[2] == "mute":
                            await client.restrict_chat_member(chat_id, user_id, chatpermissions())
                            keyboard = inlinekeyboardmarkup([
                                [inlinekeyboardbutton("unmute ✅", callback_data=f"unmute_{user_id}")]
                            ])
                            await sent_msg.edit(
                                f"{user_name} has been 🔇 muted for [link in bio].",
                                reply_markup=keyboard,
                                parse_mode=enums.parsemode.html
                            )
                            logger.info(f"user {user_id} muted in chat {chat_id}")
                        elif action[2] == "ban":
                            await client.ban_chat_member(chat_id, user_id)
                            keyboard = inlinekeyboardmarkup([
                                [inlinekeyboardbutton("unban ✅", callback_data=f"unban_{user_id}")]
                            ])
                            await sent_msg.edit(
                                f"{user_name} has been 🔨 banned for [link in bio].",
                                reply_markup=keyboard,
                                parse_mode=enums.parsemode.html
                            )
                            logger.info(f"user {user_id} banned in chat {chat_id}")
                    except errors.chatadminrequired:
                        await sent_msg.edit(f"i don't have permission to {action[2]} users.")
            elif action[0] in ["mute", "ban"]:
                try:
                    if action[0] == "mute":
                        await client.restrict_chat_member(chat_id, user_id, chatpermissions())
                        keyboard = inlinekeyboardmarkup([
                            [inlinekeyboardbutton("unmute", callback_data=f"unmute_{user_id}")]
                        ])
                        await message.reply_text(
                            f"{user_name} has been 🔇 muted for [link in bio].",
                            reply_markup=keyboard,
                            parse_mode=enums.parsemode.html
                        )
                        logger.info(f"user {user_id} muted in chat {chat_id}")
                    else:
                        await client.ban_chat_member(chat_id, user_id)
                        keyboard = inlinekeyboardmarkup([
                            [inlinekeyboardbutton("unban", callback_data=f"unban_{user_id}")]
                        ])
                        await message.reply_text(
                            f"{user_name} has been 🔨 banned for [link in bio].",
                            reply_markup=keyboard,
                            parse_mode=enums.parsemode.html
                        )
                        logger.info(f"user {user_id} banned in chat {chat_id}")
                except errors.chatadminrequired:
                    await message.reply_text(f"i don't have permission to {action[0]} users.")
        else:
            if user_id in warnings:
                del warnings[user_id]
                logger.info(f"warnings reset for user {user_id} in chat {chat_id}")

    except errors.floodwait as e:
        logger.warning(f"flood wait error in check_bio: {e}")
    except exception as e:
        logger.error(f"error in check_bio: {e}")

if __name__ == "__main__":
    logger.info("starting bot...")
    app.run()
