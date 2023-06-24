FROM gorialis/discord.py:3.10.10-master-minimal

WORKDIR /

RUN pip install discord asyncio yt_dlp python-dotenv

COPY . . 

CMD python main.py 