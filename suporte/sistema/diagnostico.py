import importlib,sys,subprocess
modules=['fastapi','uvicorn','multipart','ezdxf','numpy','scipy','shapely','pyproj','cv2','PIL','imageio_ffmpeg','skimage','tifffile']
failed=[]
for mod in modules:
 try:importlib.import_module(mod)
 except Exception as e:failed.append(f'{mod}: {e}')
if not failed:
 import imageio_ffmpeg
 try:
  result=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-f','lavfi','-i','color=size=32x32:rate=1','-frames:v','1','-c:v','libx264','-f','null','-'],capture_output=True,timeout=30)
  if result.returncode:failed.append(result.stderr.decode(errors='replace'))
 except Exception as e:failed.append(str(e))
if failed:print('\n'.join(failed));sys.exit(1)
print('Python, bibliotecas e codificador H.264 disponiveis.')
