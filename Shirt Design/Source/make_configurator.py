"""Build the Sensor Placement Configurator page.
Assembles configurator_template.html + cloth_core.js (PBD cloth solver) + cloth_scene.js (three.js scene,
cloth-bound meshes, modules, skin-contact measurement) + cloth_interact.js (UI, dragging, animation loop),
and injects placement_rules.json + references_apa.json."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
rd = lambda f: open(os.path.join(HERE, f), encoding='utf-8').read()
rules = json.loads(rd('placement_rules.json')); refs = json.loads(rd('references_apa.json'))
page = (rd('configurator_template.html')
        .replace('/*__CLOTH_CORE__*/', rd('cloth_core.js'))
        .replace('/*__CLOTH_SCENE__*/', rd('cloth_scene.js'))
        .replace('/*__CLOTH_INTERACT__*/', rd('cloth_interact.js'))
        .replace('__RULES__', json.dumps(rules)).replace('__REFS__', json.dumps(refs)))
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
open(os.path.join(HERE, 'out', 'configurator_artifact.html'), 'w', encoding='utf-8').write(page)
doc = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body>\n' + page + '\n</body></html>'
open(os.path.join(HERE, 'out', 'RSAF_Sensor_Placement_Configurator.html'), 'w', encoding='utf-8').write(doc)
print('configurator written')
