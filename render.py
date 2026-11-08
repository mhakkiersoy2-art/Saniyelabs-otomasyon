import argparse, asyncio, json, math, random, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
ROOT=Path(__file__).parent
W,H=1080,1920

def run(args): subprocess.run(args,check=True)
def backdrop(path,seed):
    rng=random.Random(seed); im=Image.new('RGB',(W,H)); p=im.load()
    for y in range(H):
        t=y/H
        c=(int(3+8*t),int(10+19*t),int(28+31*t))
        for x in range(W):p[x,y]=c
    d=ImageDraw.Draw(im,'RGBA')
    for _ in range(230):
        x=rng.randrange(W); y=rng.randrange(1400); r=rng.choice([1,1,2,3]);d.ellipse((x-r,y-r,x+r,y+r),fill=(170,215,255,rng.randrange(90,220)))
    x=540+rng.randrange(-110,110);y=760+rng.randrange(-90,90)
    for r in range(410,140,-12):d.ellipse((x-r,y-r,x+r,y+r),fill=(25,95,160,5))
    d.ellipse((x-270,y-270,x+270,y+270),fill=(15,62,114,255),outline=(97,187,240,220),width=9)
    for i in range(8):
        yy=y-220+i*58;d.arc((x-265,yy-70,x+265,yy+95),10,175,fill=(80,174,225,65),width=5)
    im=im.filter(ImageFilter.GaussianBlur(0.6)); im.save(path)

def duration(file):
    p=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(file)],capture_output=True,text=True,check=True)
    return float(p.stdout.strip())

async def voice(text,path):
    import edge_tts
    await edge_tts.Communicate(text,'tr-TR-AhmetNeural',rate='+12%').save(str(path))

def make(topic,out):
    out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td); clips=[]
        for i,scene in enumerate(topic['scenes']):
            audio=tmp/f'{i}.mp3'
            try:asyncio.run(voice(scene['narration'],audio))
            except Exception as e:raise RuntimeError('Doğal Türkçe ses için internet erişimi gerekli: '+str(e))
            bg=tmp/f'{i}.png';backdrop(bg,i+11)
            sec=duration(audio)+0.12
            text=scene['headline'].upper()
            # drawtext supports Turkish via DejaVu; escape FFmpeg text and use a separate textfile
            txt=tmp/f'{i}.txt';txt.write_text(text,encoding='utf-8')
            font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
            filt=(f"scale=1200:2134,crop=1080:1920:x='60+20*sin(t*0.7)':y='100+20*cos(t*0.5)',"
                  f"drawbox=x=60:y=1400:w=960:h=350:color=black@0.72:t=fill,"
                  f"drawtext=fontfile={font}:textfile={txt}:fontcolor=white:fontsize=51:"
                  f"x=(w-text_w)/2:y=1510:box=0,"
                  f"drawtext=fontfile={font}:text='SANIYELABS':fontcolor=0x7fdcff:fontsize=37:x=70:y=85,"
                  f"format=yuv420p")
            clip=tmp/f'{i}.mp4'
            run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate','30','-i',str(bg),'-i',str(audio),'-vf',filt,'-t',str(sec),'-r','30','-c:v','libx264','-preset','veryfast','-crf','23','-c:a','aac','-b:a','160k','-pix_fmt','yuv420p','-shortest',str(clip)])
            clips.append(clip)
        listing=tmp/'clips.txt';listing.write_text(''.join(f"file '{c}'\n" for c in clips))
        final=out/(topic['slug']+'.mp4')
        run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(final)])
        print('Üretildi:',final)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--topic',default='uzayda-aglamak');a=ap.parse_args()
    topics=json.loads((ROOT/'topics.json').read_text(encoding='utf-8'))
    t=next((x for x in topics if x['slug']==a.topic),None)
    if not t:raise SystemExit('Konu bulunamadı: '+a.topic)
    make(t,ROOT/'output')
