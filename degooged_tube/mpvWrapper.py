import mpv




import subprocess
import degooged_tube.config as cfg

#player['ytdl-format'] = "bestvideo[height<=?1080][vcodec!=vp9]+bestaudio/best"
#player['vo'] = 'gpu'
#player['stream-buffer-size']='1MiB'

def playVideo(url:str):
    cfg.logger.info("\nMPV Player \nPress (q) or Close Window to Stop:")
    subprocess.call((f'mpv', '--ytdl-format=bestvideo[height<=?1080]+bestaudio/best', url))
    return

#    player = mpv.MPV(ytdl=True, input_default_bindings=True, input_vo_keyboard=True, osc=True)
#    try:
#        player.play(url)
#        player.wait_for_playback()
#    except mpv.ShutdownError:
#        player.terminate()
#    try:
#        player.wait_for_shutdown()
#    except mpv.ShutdownError:
#        return

if __name__ == '__main__':
    playVideo('https://www.youtube.com/watch?v=j-FHbHoiwNk&ab_channel=AppliedScience')
    playVideo('https://www.youtube.com/watch?v=j-FHbHoiwNk&ab_channel=AppliedScience')

