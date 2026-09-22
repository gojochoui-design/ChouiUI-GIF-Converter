from pathlib import Path
from PIL import Image
src=Image.open('/home/ubuntu/repo_update/assets/choui_icon_adapted.png').convert('RGB')
src.save('/home/ubuntu/repo_update/assets/choui_icon.ico',sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])
for folder,size in [('mdpi',48),('hdpi',72),('xhdpi',96),('xxhdpi',144),('xxxhdpi',192)]:
    out=Path('/home/ubuntu/repo_update/android/app/src/main/res/mipmap-'+folder);out.mkdir(parents=True,exist_ok=True)
    src.resize((size,size),Image.Resampling.LANCZOS).save(out/'ic_launcher.png',optimize=True)
