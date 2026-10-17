#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,tempfile,os,struct
ROOT=Path(__file__).resolve().parents[6]; HERE=Path(__file__).resolve().parent
WORK=Path(tempfile.mkdtemp(prefix='ccr-p8-extra-'));OUT=HERE/'supplement';OUT.mkdir(exist_ok=True)
records=[]
def run(name,args,expect=0):
 p=subprocess.run(list(map(str,args)),cwd=WORK,env={**os.environ,'CCACHE_DISABLE':'1'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=45)
 (OUT/(name+'.log')).write_bytes(p.stdout);records.append(dict(name=name,argv=list(map(str,args)),cwd=str(WORK),exit_code=p.returncode,expected_exit=expect,matched=p.returncode==expect));(OUT/'results.json').write_text(json.dumps(records,indent=2)+'\n');print(name,p.returncode,flush=True);return p.returncode
inc=['-I'+str(ROOT/'navy-apps/libs'/d/'include') for d in ['libminiSDL','libndl','libvorbis','libSDL_mixer','libSDL_image','libSDL_ttf','libfixedptc','libbdf','libbmp']]
fmt=b'fmt '+struct.pack('<IHHIIHH',16,1,2,44100,176400,4,16)
chunks=fmt+b'JUNK'+struct.pack('<I',1)+b'x\0'+b'data'+struct.pack('<I',4)+b'\0'*4
for name,ch in [('odd',chunks),('nofmt',b'data'+struct.pack('<I',4)+b'\0'*4)]:
 (WORK/(name+'.wav')).write_bytes(b'RIFF'+struct.pack('<I',len(ch)+4)+b'WAVE'+ch)
src=ROOT/'navy-apps/libs/libminiSDL/src'
if run('wav-build',['gcc','-O1','-ffunction-sections','-fdata-sections',*inc,'-I'+str(ROOT/'navy-apps/libs/libSDL_mixer/src'),HERE/'wav-probe.c',src/'file.c',src/'audio.c','-Wl,--gc-sections','-o',WORK/'wav'])==0:
 run('wav-sdl-odd',[WORK/'wav','s',WORK/'odd.wav']);run('wav-mix-odd',[WORK/'wav','m',WORK/'odd.wav']);run('wav-nofmt',[WORK/'wav','n',WORK/'nofmt.wav'])
# Only compilation: never invoke the original Makefiles (parse-time clones).
sources=[]
for d in ['nterm','nwm','menu','nslider','nplayer','bird']:
 folder=ROOT/'navy-apps/apps'/d
 sources += [(d,f) for f in folder.rglob('*') if f.suffix in ['.c','.cpp'] and '/build/' not in str(f) and '/.git/' not in str(f)]
sources += [('test',ROOT/'navy-apps/tests'/d/'main.c') for d in ['audiotest','bmp-test','event-test','timer-test']]
for i,(app,f) in enumerate(sources):
 cc='/usr/bin/riscv64-linux-gnu-g++' if f.suffix=='.cpp' else '/usr/bin/riscv64-linux-gnu-gcc'
 ai=ROOT/'navy-apps/apps'/app
 run('rv64-'+app+'-'+f.stem,[cc,'-O2','-D__NAVY__','-D__ISA_RISCV64__','-march=rv64g','-ffreestanding',*(['-fno-exceptions','-fno-rtti'] if f.suffix=='.cpp' else []),*inc,'-I'+str(ROOT/'navy-apps/libs/libc/include'),'-I'+str(ai/'include'),'-I'+str(ai/'repo/include'),'-c',f,'-o',WORK/(str(i)+'.o')])
for d,f in [('libvorbis','src/stb_vorbis.c'),('libbdf','src/BDF.cpp'),('libbdf','src/SDL_bdf.cpp')]:
 cc='/usr/bin/riscv64-linux-gnu-g++' if f.endswith('.cpp') else '/usr/bin/riscv64-linux-gnu-gcc'
 run('rv64-'+d+'-'+Path(f).stem,[cc,'-O2','-D__NAVY__','-march=rv64g','-ffreestanding',*inc,'-I'+str(ROOT/'navy-apps/libs/libc/include'),'-c',ROOT/'navy-apps/libs'/d/f,'-o',WORK/(d+Path(f).stem+'.o')])
