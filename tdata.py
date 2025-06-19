from opentele.td import TDesktop
from opentele.tl import TelegramClient
from opentele.api import API, CreateNewSession, UseCurrentSession
import asyncio
import os


async def convert_all_tdata(us_dir='./us'):
    api = API.TelegramIOS.Generate()
    for subdir in os.listdir(us_dir):
        tdata_path = os.path.join(us_dir, subdir, 'tdata')
        if os.path.isdir(tdata_path):
            session_file = os.path.join('sessions', f'{subdir}.session')
            print(f'Converting {tdata_path} -> {session_file}')
            tdesk = TDesktop(tdata_path)
            try:
                await tdesk.ToTelethon(session_file, CreateNewSession, api)
                print(f'Success: {session_file}')
            except Exception as e:
                print(f'Failed: {tdata_path} - {e}')

if __name__ == '__main__':
    asyncio.run(convert_all_tdata())
