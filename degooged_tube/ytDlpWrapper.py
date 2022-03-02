from yt_dlp import YoutubeDL
import degooged_tube.config as cfg
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

    
    return f'bestvideo[height <= {maxQuality}]{fpsStr}+audio/{backup}'


def getStreamLink(videoUrl:str):
    format = _getFormat(cfg.maxQuality, cfg.maxFps)
    ydl_opts = {'writeinfojson': True, 'quiet': True, 'format': format}
    with YoutubeDL(ydl_opts) as ydl:
        x = ydl.extract_info(videoUrl, False)
        return x['url']
