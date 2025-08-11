import asyncio
from os import sep
from pathlib import Path
from signal import signal as signal_fn, SIGINT, SIGTERM, SIGABRT
from sys import path, platform, exit

from pyrogram.errors import AuthKeyUnregistered

from pagermaid.common.reload import load_all
from pagermaid.config import Config
from pagermaid.dependence import scheduler
from pagermaid.services import bot
from pagermaid.static import working_dir
from pagermaid.utils import lang, logs, SessionFileManager
from pagermaid.utils.listener import process_exit
from pagermaid.web import web
from pagermaid.web.api.web_login import web_login
from pyromod.methods.sign_in_qrcode import start_client

bot.PARENT_DIR = Path(working_dir)
path.insert(1, f"{working_dir}{sep}plugins")


async def idle():
    task = None

    def signal_handler(_, __):
        if web.web_server_task:
            web.web_server_task.cancel()
        task.cancel()

    for s in (SIGINT, SIGTERM, SIGABRT):
        signal_fn(s, signal_handler)

    while True:
        task = asyncio.create_task(asyncio.sleep(600))
        web.bot_main_task = task
        try:
            await task
        except asyncio.CancelledError:
            break


async def console_bot():
    try:
        await start_client(bot)
    except AuthKeyUnregistered:
        SessionFileManager.safe_remove_session()
        exit()
    me = await bot.get_me()
    await bot.storage.user_id(me.id)
    if me.is_bot:
        SessionFileManager.safe_remove_session()
        exit()
    logs.info(f"{lang('save_id')} {me.first_name}({me.id})")
    await load_all()
    await process_exit(start=True, _client=bot)


async def web_bot():
    try:
        await web_login.init()
    except AuthKeyUnregistered:
        SessionFileManager.safe_remove_session()
        exit()
    if bot.me is not None:
        me = await bot.get_me()
        await bot.storage.user_id(me.id)
        if me.is_bot:
            SessionFileManager.safe_remove_session()
            exit()
    else:
        logs.info("Please use web to login, path: web_login .")


async def main():
    logs.info(lang("platform") + platform + lang("platform_load"))
    if not scheduler.running:
        scheduler.start()
    await web.start()
    if not (Config.WEB_ENABLE and Config.WEB_LOGIN):
        await console_bot()
        logs.info(lang("start"))
    else:
        await web_bot()

    try:
        await idle()
    finally:
        if scheduler.running:
            scheduler.shutdown()
        try:
            await bot.stop()
        except ConnectionError:
            pass
        if web.web_server:
            try:
                await web.web_server.shutdown()
            except AttributeError:
                pass


bot.run(main())
