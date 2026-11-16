RSAF heat-strain shirt with detachable sensing patches - concept design files (Rev C, 10 Nov 2026, size M)

NEW IN REV C: the shirt is now a cloth simulation (configurator only)
  - Fabric is a particle mesh (position-based dynamics: stretch, shear and bend springs, gravity, friction on skin)
    draped on a moving mannequin. Shoulder yoke rests on the shoulders; nothing else is glued to the body.
  - Fit: compression (3.5% under body girth, sleeves taper onto the arm), regular (5% ease), loose (14% ease).
  - Motion: standing, marching (0.9 Hz stride), running (1.35 Hz stride, 28 mm vertical bounce, arm swing). Optional gusting head wind.
  - Each module's mass (M1 30 g, hub 35 g, HR pod 15 g, IMU 10 g, sweat 8 g, ECG 4 g) loads the fabric under it.
  - Live skin contact per sensor: mean gap, peak gap and % of time lifted >2 mm. The checks warn when a skin-contact
    sensor (temperature, sweat, ECG, HR) averages >2 mm or is lifted >30% of the time, or when the IMU sits >3 mm off the body.
  - "Pull fabric" mouse mode: drag the shirt to see it tent and spring back. "Reset cloth" re-drapes it.
  - Limits: the mannequin is a rigid superellipse torso + arm cylinders (no breathing, no muscle, no sweat-wetted friction);
    fabric stiffness and friction are representative values, not measured from our fabric. Use it to compare
    placements and fits against each other, not as absolute gap predictions.
  Source: cloth_core.js (solver), cloth_scene.js (3D scene + contact measurement), cloth_interact.js (UI);
  make_configurator.py assembles them into the HTML. Evidence scores, checks, flats and JSON export work as in Rev B.

REV B: dynamic sensor placement
  RSAF_Sensor_Placement_Configurator.html  Double-click (needs internet for the 3D library).
      - Drag the skin-temperature sensor, gait IMU, sweat sensor, hub pod, ECG electrodes and arm HR pod on the 3D shirt.
      - Shirt colours = evidence strength for the selected sensor, from the consolidated literature review
        (rules and citations in Source\placement_rules.json). Rucksack / vest contact zones shown as stripes.
      - Live checks: ECG side and spacing, trace lengths, overlaps, gear conflicts.
      - Live front/back flats with dimensions from BNP, CB and CF.
      - "Copy JSON" gives a placement file.

  To regenerate the 3D model, drawing set and DXF at your chosen positions (Python 3 + numpy, matplotlib, scipy):
      1. Paste the copied JSON into Source\placement.json
      2. In the Source folder run:  python build_all.py
         (or: python build_all.py placement_examples\MrLim_shoulder_top_IMU.json)
      3. New files appear in Source\out\ (drawings in Source\out\drawings\).
  Example placements: Rev A review recommendation, Mr Lim shoulder-top IMU, chest IMU (Buller 2022 style), lower-back IMU reference.

OTHER FILES (generated for the Rev A placement)
  RSAF_HeatStrain_Shirt_3D_Viewer.html   3D viewer with explode and module toggles
  Drawings\..._Drawing_Set_UROP-HSS-001-005.pdf   Sheet 001 is now placement-driven with an evidence table
  Drawings\..._Flat_Patterns.dxf          1:1 templates incl. trace routing for the current placement
  3D\RSAF_HeatStrain_Shirt_Assembly.glb   Full assembly (opens in Blender or gltf-viewer.donmccurdy.com)
  3D\Printable\ (unchanged from Rev A)    Printable pod and patch parts
