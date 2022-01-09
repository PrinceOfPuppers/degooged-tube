from yt_dlp import YoutubeDL
fps = [
    '30', '60', 'highest'
]

qualities = [
        '144',
        '240',
        '360',
        '480',
        '720',
        '1080',
        'best'
]

def _getFormat(maxQuality: str, maxFps: str):
    if maxFps != 'highest':
        fpsStr = f'[fps <= {maxFps}]'
    else:
        fpsStr= ''

    if maxQuality == 'best':
        return f'best{fpsStr}'

    if maxQuality == '144' or maxQuality == '240':
        backup = 'worst'
    else:
        backup = 'best'

    
    return f'bestvideo[height <= {maxQuality}]{fpsStr}/{backup}'


def getStreamLink(maxQuality:str, maxFps:str):
    format = _getFormat(maxQuality, maxFps)
    ydl_opts = {'writeinfojson': True, 'quiet': True, 'format': format}
    with YoutubeDL(ydl_opts) as ydl:
        x = ydl.extract_info('https://youtu.be/mI85lQ44Zfc', False)
        return x['url']

# print(getStreamLink('720', '60'))
