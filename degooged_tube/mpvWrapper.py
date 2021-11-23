import mpv

player = mpv.MPV(ytdl=True, input_default_bindings=True, input_vo_keyboard=True, osc=True)
#player['ytdl-format'] = "bestvideo[height<=?1080][vcodec!=vp9]+bestaudio/best"
#player['vo'] = 'gpu'
#player['stream-buffer-size']='1MiB'

def playVideo(url):
    try:
        player.play(url)
        player.wait_for_playback()
    except mpv.ShutdownError:
        return


if __name__ == '__main__':
    playVideo('https://www.youtube.com/watch?v=j-FHbHoiwNk&ab_channel=AppliedScience')
    print("hello")
