#!/usr/bin/env python3
"""SaniyeLab: offline Shorts proof-of-concept, no upload without explicit --upload."""
import argparse, json, math, os, random, shutil, subprocess, tempfile, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pydub import AudioSegment

ROOT=Path(__file__).resolve().parent
CONF=json.loads((ROOT/'config.json').read_text(encoding='utf8'))
W,H=CONF['size']
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
if not Path(FONT).exists(): FONT='DejaVuSans-Bold.ttf'; FONT_REG='DejaVuSans.ttf'

def font(sz,bold=True):
    try: return ImageFont.truetype(FONT if bold else FONT_REG,sz)
    except: return ImageFont.load_default()

def call(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)

def wrapped(text,max_width, ft, draw):
    lines=[]; cur=''
    for word in text.split():
        cand=(cur+' '+word).strip()
        if draw.textbbox((0,0),cand,font=ft)[2]>max_width and cur:
            lines.append(cur);cur=word
        else: cur=cand
    if cur:lines.append(cur)
    return lines

def star_field(dr, seed):
    rng=random.Random(seed)
    for i in range(105):
        x=rng.randint(20,W-20); y=rng.randint(80,810);r=rng.choice([1,1,1,2,2,3])
        a=rng.choice([90,135,180,225])
        dr.ellipse((x-r,y-r,x+r,y+r),fill=(a,a,min(255,a+25)))

def ellipse_ring(dr, center, rx, ry, color, width=6):
    cx,cy=center
    dr.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),outline=color,width=width)

def art(img,dr,theme,idx):
    cx=W//2; cy=490
    if theme in ('space','moon','gps'):
        star_field(dr, idx+5)
        dr.ellipse((cx-178,cy-165,cx+178,cy+191),fill=(23,74,127),outline=(86,208,250),width=7)
        for rr in [115,170]:
            dr.arc((cx-rr,cy-rr,cx+rr,cy+rr),15+idx*13,150+idx*13,fill=(73,176,216),width=3)
        if theme=='moon':
            dr.ellipse((cx+107,cy-214,cx+228,cy-93),fill=(215,217,223),outline=(242,245,250),width=4)
            for x,y,r in [(cx+145,cy-174,14),(cx+185,cy-133,9),(cx+171,cy-191,8)]:dr.ellipse((x-r,y-r,x+r,y+r),fill=(165,173,189))
            dr.arc((cx-235,cy-255,cx+255,cy+245),-60,200,fill=(85,199,226),width=6)
        if theme=='space':
            for i in range(3):
                yy=cy-165+i*63+idx*8
                dr.ellipse((cx+156+i*22,yy,cx+178+i*22,yy+26),fill=(147,226,255),outline='white',width=2)
        if theme=='gps':
            dr.line((cx-230,cy-220,cx-80,cy-85),fill=(93,224,235),width=6)
            dr.polygon([(cx-245,cy-270),(cx-189,cy-280),(cx-174,cy-226),(cx-232,cy-207)],fill=(210,213,224))
            dr.rectangle((cx-300,cy-292,cx-252,cy-229),fill=(40,98,188),outline=(130,211,255),width=3)
            dr.rectangle((cx-173,cy-292,cx-125,cy-229),fill=(40,98,188),outline=(130,211,255),width=3)
    elif theme=='saturn':
        ellipse_ring(dr,(cx,cy),290,105,(153,190,215),12)
        dr.ellipse((cx-180,cy-177,cx+180,cy+183),fill=(221,180,118),outline=(255,223,162),width=7)
        for i in range(5): dr.arc((cx-175,cy-165,cx+175,cy+165),25+i*17,145+i*17,fill=(163,117,86),width=9)
        dr.arc((cx-290,cy-105,cx+290,cy+105),7,170,fill=(235,212,173),width=16)
    elif theme=='glass':
        dr.rounded_rectangle((cx-194,cy-222,cx+194,cy+210),radius=22,fill=(39,101,143),outline=(178,234,252),width=9)
        dr.line((cx-182,cy-218,cx+130,cy+192),fill=(90,188,227),width=18)
        dr.line((cx-90,cy-207,cx+208,cy+130),fill=(145,217,244),width=8)
        for i in range(18):
            x=random.Random(i+11).randint(cx-130,cx+130); y=random.Random(i+51).randint(cy-150,cy+140)
            dr.ellipse((x-4,y-4,x+4,y+4),fill=(191,238,250))
    elif theme=='ocean':
        dr.rectangle((0,340,W,890),fill=(5,31,72))
        for i in range(7):
            yy=385+i*73
            dr.arc((-100,yy-18,W+130,yy+70),170,360,fill=(21+i*3,102+i*6,170+i*4),width=7)
        dr.ellipse((cx-90,cy-90,cx+90,cy+90),fill=(7,83,126),outline=(97,210,233),width=4)
        dr.polygon([(cx-80,cy),(cx-153,cy-49),(cx-150,cy+49)],fill=(27,180,217))
        dr.ellipse((cx+40,cy-22,cx+53,cy-9),fill=(241,250,255))

def scene_image(theme,idx,title,headline,subtitle,out):
    top=(7,14,34);bot=(7,49,83)
    im=Image.new('RGB',(W,H)); p=im.load()
    for y in range(H):
        t=y/(H-1)
        rr=int(top[0]*(1-t)+bot[0]*t);gg=int(top[1]*(1-t)+bot[1]*t);bb=int(top[2]*(1-t)+bot[2]*t)
        for x in range(W):p[x,y]=(rr,gg,bb)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((44,55,278,113),radius=17,fill=(21,76,107),outline=(90,183,218),width=2)
    d.text((61,70),'S A N İ Y E L A B',font=font(22),fill=(227,247,255))
    d.text((W-147,77),f'{idx+1:02d} / 05',font=font(21),fill=(145,199,219))
    art(im,d,theme,idx)
    d.rounded_rectangle((34,851,W-34,1204),radius=32,fill=(6,19,39),outline=(37,105,149),width=3)
    ft=font(37)
    hlines=wrapped(headline,W-118,ft,d)
    yy=889
    for line in hlines[:2]:
        d.text((W//2,yy),line,font=ft,anchor='mt',fill=(106,232,248),stroke_width=0)
        yy+=49
    yy+=12
    subft=font(32,False)
    for line in wrapped(subtitle,W-124,subft,d)[:5]:
        d.text((W//2,yy),line,font=subft,anchor='mt',fill=(248,250,255))
        yy+=45
    # a 5-segment progress bar
    for i in range(5):
        x=34+i*(W-68)/5
        d.rounded_rectangle((x,1232,x+(W-68)/5-10,1242),radius=4,fill=(54,199,226) if i<=idx else (34,71,101))
    im.save(out,optimize=True)

def speak(text,wav_path,mode='offline'):
    if mode=='edge':
        try:
            import edge_tts,asyncio
            mp3=str(wav_path)+'.mp3'
            asyncio.run(edge_tts.Communicate(text,voice=CONF.get('voice','tr-TR-AhmetNeural'),rate='+10%').save(mp3))
            call(['ffmpeg','-loglevel','error','-y','-i',mp3,'-ar','22050','-ac','1',str(wav_path)])
            return
        except Exception as e:
            print('Edge ses mevcut değil, espeak kullanılıyor:',str(e)[:200])
    if not shutil.which('espeak'):
        raise RuntimeError('espeak bulunamadı. Linux: sudo apt install espeak; veya pip install edge-tts ve --voice edge kullanın.')
    call(['espeak','-v','tr','-s','170','-p','47','-a','185','-w',str(wav_path),text])

def render(topic,voice='offline',outdir=None):
    outdir=Path(outdir or ROOT/'output');outdir.mkdir(parents=True,exist_ok=True)
    movie=outdir/(topic['slug']+'.mp4')
    with tempfile.TemporaryDirectory() as temp:
        tmp=Path(temp)
        aud=AudioSegment.silent(duration=0,frame_rate=22050)
        durations=[]; images=[]
        for i,s in enumerate(topic['scenes']):
            wav=tmp/f'v{i}.wav'
            speak(s['narration'],wav,voice)
            seg=AudioSegment.from_file(wav).set_frame_rate(22050).set_channels(1)
            pause=AudioSegment.silent(duration=140,frame_rate=22050).set_channels(1)
            aud+=seg+pause
            duration=(len(seg)+len(pause))/1000.0
            durations.append(duration)
            png=tmp/f'scene{i:02}.png'
            scene_image(topic['theme'],i,topic['title'],s['headline'],s['narration'],png)
            images.append(png)
        audiofile=tmp/'speech.wav';aud.export(audiofile,format='wav')
        cmd=['ffmpeg','-loglevel','error','-y'];n=len(images)
        for d,img in zip(durations,images):cmd+=['-loop','1','-framerate',str(CONF['fps']),'-t',f'{d:.3f}','-i',str(img)]
        cmd+=['-i',str(audiofile)]
        steps=[]
        for i in range(n): steps.append(f'[{i}:v]format=yuv420p,setsar=1,setpts=PTS-STARTPTS[v{i}]')
        steps.append(''.join(f'[v{i}]' for i in range(n))+f'concat=n={n}:v=1:a=0[video]')
        cmd+=['-filter_complex',';'.join(steps),'-map','[video]','-map',f'{n}:a',
              '-t',f'{len(aud)/1000:.3f}','-c:v','libx264','-preset','veryfast','-crf','23',
              '-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',str(movie)]
        call(cmd)
    metadata={'title':topic['title']+' #shorts','description':CONF['channel_description']+'\n\n#shorts #bilim #teknoloji',
              'tags':topic['tags'],'file':str(movie),'duration_seconds':round(len(aud)/1000,1)}
    (outdir/(topic['slug']+'.json')).write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf8')
    return movie,metadata

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--topic',default='uzayda-aglamak',help='topics.json içindeki slug; tümü için all')
    parser.add_argument('--voice',default='offline',choices=['offline','edge'])
    args=parser.parse_args()
    topics=json.loads((ROOT/'topics.json').read_text(encoding='utf8'))
    choices=topics if args.topic=='all' else [next(t for t in topics if t['slug']==args.topic)]
    for topic in choices:
        file,meta=render(topic,args.voice)
        print('Video üretildi:',file,'süre:',meta['duration_seconds'],'sn')
