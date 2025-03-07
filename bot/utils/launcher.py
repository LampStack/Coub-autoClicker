import os
import glob
import asyncio
import argparse
from itertools import cycle

from pyrogram import Client
from better_proxy import Proxy

from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper, run_tapper1
from bot.core.registrator import register_sessions


start_text = """
██████╗  ██████╗ ██╗    ██╗███████╗██████╗  ██████╗ ██████╗ ██████╗ ███████╗███████╗
██╔══██╗██╔═══██╗██║    ██║██╔════╝██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝
██████╔╝██║   ██║██║ █╗ ██║█████╗  ██████╔╝██║     ██║   ██║██║  ██║█████╗  ███████╗
██╔═══╝ ██║   ██║██║███╗██║██╔══╝  ██╔══██╗██║     ██║   ██║██║  ██║██╔══╝  ╚════██║
██║     ╚██████╔╝╚███╔███╔╝███████╗██║  ██║╚██████╗╚██████╔╝██████╔╝███████╗███████║
╚═╝      ╚═════╝  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚══════╝
                                                                                    
 ██████╗ ██████╗ ██╗   ██╗██████╗                                                   
██╔════╝██╔═══██╗██║   ██║██╔══██╗                                                  
██║     ██║   ██║██║   ██║██████╔╝                                                  
██║     ██║   ██║██║   ██║██╔══██╗                                                  
╚██████╗╚██████╔╝╚██████╔╝██████╔╝                                                  
 ╚═════╝ ╚═════╝  ╚═════╝ ╚═════╝     by: osClub
                                                                                                                                                                                                         
Select an action:

    1. Run clicker (Session)
    2. Create session
"""

global tg_clients

def get_session_names() -> list[str]:
    session_names = sorted(glob.glob("sessions/*.session"))
    session_names = [
        os.path.splitext(os.path.basename(file))[0] for file in session_names
    ]

    return session_names


def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file="bot/config/proxies.txt", encoding="utf-8-sig") as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies


async def get_tg_clients() -> list[Client]:
    global tg_clients

    session_names = get_session_names()

    if not session_names:
        raise FileNotFoundError("Not found session files")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [
        Client(
            name=session_name,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            workdir="sessions/",
            plugins=dict(root="bot/plugins"),
        )
        for session_name in session_names
    ]

    return tg_clients


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")
    parser.add_argument("-m", "--multithread", type=str, help="Enable multi-threading")

    action = parser.parse_args().action
    ans = parser.parse_args().multithread
    logger.info(f"Detected {len(get_session_names())} sessions | {len(get_proxies())} proxies")

    if not action:
        print(start_text)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be number")
            elif action not in ["1", "2"]:
                logger.warning("Action must be 1 or 2")
            else:
                action = int(action)
                break

    if action == 2:
        await register_sessions()
    elif action == 1:
        if ans is None:
            while True:
                ans = input("> Do you want to run the bot with multi-thread? (y/n) ")
                if ans not in ["y", "n"]:
                    logger.warning("Answer must be y or n")
                else:
                    break

        if ans == "y":
            tg_clients = await get_tg_clients()

            await run_tasks(tg_clients=tg_clients)
        else:
            tg_clients = await get_tg_clients()
            proxies = get_proxies()
            await run_tapper1(tg_clients=tg_clients, proxies=proxies)

async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None
    tasks = [
        asyncio.create_task(
            run_tapper(
                tg_client=tg_client,
                proxy=next(proxies_cycle) if proxies_cycle else None,
            )
        )
        for tg_client in tg_clients
    ]

    await asyncio.gather(*tasks)
