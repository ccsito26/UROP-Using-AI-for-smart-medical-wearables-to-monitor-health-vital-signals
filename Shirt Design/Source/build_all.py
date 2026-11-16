"""Regenerate every output from placement.json (exported by the Sensor Placement Configurator).
Usage:  python build_all.py            -> uses Source/placement.json (created with the Rev A layout if missing)
        python build_all.py my.json    -> copies my.json to placement.json first"""
import sys, os, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) > 1:
    shutil.copy(sys.argv[1], os.path.join(HERE, 'placement.json'))
for step in ('build3d.py', 'parts.py', 'drawings.py', 'dxf.py', 'make_viewer.py', 'make_configurator.py'):
    print('running', step); subprocess.run([sys.executable, os.path.join(HERE, step)], check=True, cwd=HERE)
print('done: see the out/ folder')
