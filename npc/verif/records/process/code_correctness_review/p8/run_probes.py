#!/usr/bin/env python3
"""Compile unchanged production units in a fresh /tmp tree; archive all commands."""
from pathlib import Path
import json,subprocess,tempfile,shutil,os
ROOT=Path(__file__).resolve().parents[6]; HERE=Path(__file__).resolve().parent
WORK=Path(tempfile.mkdtemp(prefix='ccr-p8-')); OUT=HERE/'probes-fixed';OUT.mkdir(exist_ok=True)
results=[]
def run(name,args,expected=0):
    p=subprocess.run([str(a) for a in args],cwd=WORK,env={**os.environ,'CCACHE_DISABLE':'1'},text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=45)
    (OUT/(name+'.log')).write_text(p.stdout)
    results.append(dict(name=name,argv=[str(a) for a in args],cwd=str(WORK),exit_code=p.returncode,expected_exit=expected,matched=p.returncode==expected))
    (OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(name,p.returncode,'expected',expected,flush=True)
    return p.returncode
inc=['-I'+str(ROOT/'navy-apps/libs'/d) for d in ['libminiSDL/include','libndl/include','libvorbis/include','libSDL_mixer/include','libfixedptc/include','libSDL_image/include','libSDL_ttf/include','libbdf/include','libbmp/include']]
units=[ROOT/'navy-apps/libs/libndl/NDL.c',*sorted((ROOT/'navy-apps/libs/libminiSDL/src').glob('*.c'))]
units += [ROOT/'navy-apps/libs'/d/f for d,f in [('libSDL_image','src/image.c'),('libSDL_ttf','src/ttf.c'),('libSDL_mixer','src/mixer.c'),('libbmp','src/BMP.c'),('libbmp','src/SDL_bmp.c')]]
for i,u in enumerate(units):
    run('rv64-'+u.parent.parent.name+'-'+u.stem,['riscv64-linux-gnu-gcc','-O2','-c','-ffreestanding','-march=rv64g','-mabi=lp64d',*inc,'-I'+str(ROOT/'navy-apps/libs/libc/include'),u,'-o',WORK/(str(i)+'.o')])
src=[ROOT/'navy-apps/libs/libminiSDL/src'/f for f in ['file.c','video.c','event.c','timer.c','audio.c']]
common=['gcc','-O1','-g','-ffunction-sections','-fdata-sections',*inc,HERE/'service-probe.c',*src,'-Wl,--gc-sections']
if run('service-build',[*common,'-o',WORK/'service'])==0:
    for mode in ['video','rw','timer','close']: run(mode,[WORK/'service',mode])
if run('bounds-build',[*common,'-fsanitize=address,undefined','-fno-sanitize-recover=all','-o',WORK/'bounds'])==0:
    run('keys',[WORK/'bounds','keys'],1);run('oddmix',[WORK/'bounds','oddmix'],1)
if run('mixer-build',['gcc','-O1','-ffunction-sections','-fdata-sections',*inc,'-I'+str(ROOT/'navy-apps/libs/libSDL_mixer/src'),HERE/'mixer-probe.c','-Wl,--gc-sections','-o',WORK/'mixer'])==0:run('mixer-wrap',[WORK/'mixer'])
run('gcc-version',['gcc','--version']);run('rv64-version',['riscv64-linux-gnu-gcc','--version'])
print('Archived',OUT)
