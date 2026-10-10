#!/usr/bin/env python3
"""Use OpenSBI's bundled Kconfiglib; no source edits or installed packages."""
import os
from pathlib import Path
import subprocess
import sys
src, out = map(lambda x: Path(x).resolve(), sys.argv[1:])
kdir = out / 'platform/generic/kconfig'
kdir.mkdir(parents=True, exist_ok=True)
os.environ.update(OPENSBI_SRC_DIR=str(src), OPENSBI_PLATFORM='generic',
                  OPENSBI_PLATFORM_SRC_DIR=str(src / 'platform/generic'),
                  KCONFIG_CONFIG=str(kdir / '.config'), PYTHONDONTWRITEBYTECODE='1')
sys.dont_write_bytecode = True
sys.path.insert(0, str(src / 'scripts/Kconfiglib'))
import kconfiglib
conf = kconfiglib.Kconfig(str(src / 'Kconfig'))
conf.load_config(str(src / 'platform/generic/configs/defconfig'))
# This platform uses the DT UART, not a debugger semihosting console. The
# optional semihost probe executes ebreak, reserved by legacy NEMU for halt.
conf.syms['SERIAL_SEMIHOSTING'].set_value(0)
conf.write_config(str(kdir / '.config'))
subprocess.run([sys.executable, str(src / 'scripts/Kconfiglib/genconfig.py'),
                '--header-path', str(kdir / 'autoconf.h'), '--sync-deps', str(kdir),
                '--file-list', str(kdir / 'auto.list'), str(src / 'Kconfig')], check=True)
