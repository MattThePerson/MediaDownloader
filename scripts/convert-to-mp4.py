import sys
import subprocess
import shlex


if __name__ == '__main__':
    pth = sys.argv[1]
    ext = pth.split('.')[-1]
    if ext.lower() not in ['mp4', 'webm']:
        new_pth = pth.replace(f'.{ext}', '.mp4')

        command = f'ffmpeg -hide_banner -loglevel error -stats -i "{pth}" -c copy "{new_pth}" -n'
        subprocess.run(shlex.split(command))
        subprocess.run(shlex.split(f'rm "{pth}"'))

