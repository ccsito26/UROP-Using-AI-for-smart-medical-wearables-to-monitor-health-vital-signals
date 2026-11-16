import base64, os
HERE = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(HERE, 'viewer_template.html'), encoding='utf-8').read()
b = base64.b64encode(open(os.path.join(HERE, 'out', 'RSAF_HeatStrain_Shirt_Assembly.glb'), 'rb').read()).decode()
open(os.path.join(HERE, 'out', 'RSAF_HeatStrain_Shirt_3D_Viewer.html'), 'w', encoding='utf-8').write(t.replace('__GLB__', b))
print('viewer written')
