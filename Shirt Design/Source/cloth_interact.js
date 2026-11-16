// ---------- shirt colouring (evidence heatmap + gear stripes on the moving cloth) ----------
function colorShirt(){ const k=heatSel.value, show=heat.checked; const S=sensorRules(k);
  for(let v=0;v<CL.nT;v++){ const s=CL.sz[v*2], z=CL.sz[v*2+1], j=v%CNZ; let c=BASE;
    if(show){ c=ramp(scoreAt(k,{kind:'torso',s,z}).score); }
    const g=gearAt(s,z); if(g.length){ const stripe=(Math.floor((z+s*0.6)/14)%2===0); if(stripe) c=c.map((x,i)=>Math.round(x*.45+[90,110,140][i]*.55)); }
    if(j===0||j===CNZ-1) c=RIB;
    tCol[v*3]=c[0]/255; tCol[v*3+1]=c[1]/255; tCol[v*3+2]=c[2]/255; }
  tGeo.attributes.color.needsUpdate=true;
  for(const m of sleeves){ const col=m.geometry.attributes.color; for(let v=0;v<SNA*SNT;v++){ const q=(m.userData.off-CL.nT+v)*3, side=CL.sl[q], t=CL.sl[q+1], ang=CL.sl[q+2];
      let c=BASE; if(show) c=ramp(scoreAt(k,{kind:'sleeve',side,t,ang}).score); if(v%SNT===SNT-1) c=RIB; col.setXYZ(v,c[0]/255,c[1]/255,c[2]/255); } col.needsUpdate=true; }
  document.getElementById('legendFor').textContent=S.name; document.getElementById('gearKey').style.display=(gearOn.rucksack||gearOn.vest)?'block':'none'; }

// ---------- interaction ----------
const ray=new THREE.Raycaster(), mouse=new THREE.Vector2(); let dragging=null, grabPlane=null;
function setMouse(ev){ const r=renderer.domElement.getBoundingClientRect(); mouse.x=((ev.clientX-r.left)/r.width)*2-1; mouse.y=-((ev.clientY-r.top)/r.height)*2+1; ray.setFromCamera(mouse,camera); }
function hitToSZ(hit){ const f=hit.face, A=_v(f.a), B=_v(f.b), Cc=_v(f.c), bc=new THREE.Vector3(); THREE.Triangle.getBarycoord(hit.point,A,B,Cc,bc);
  const za=CL.sz[f.a*2+1], zb=CL.sz[f.b*2+1], zc=CL.sz[f.c*2+1], z=za*bc.x+zb*bc.y+zc*bc.z; const Cz=arc(z).C; const sa=CL.sz[f.a*2]; const un=(s)=>{ let d=s-sa; if(d>Cz/2)d-=Cz; if(d<-Cz/2)d+=Cz; return sa+d; };
  let s=sa*bc.x+un(CL.sz[f.b*2])*bc.y+un(CL.sz[f.c*2])*bc.z; if(s>Cz/2)s-=Cz; if(s<-Cz/2)s+=Cz; return {s,z}; }
function hitToSleeve(hit,m){ const f=hit.face, o=m.userData.off-CL.nT, bc=new THREE.Vector3(); const off=m.userData.off;
  THREE.Triangle.getBarycoord(hit.point,_v(off+f.a),_v(off+f.b),_v(off+f.c),bc); const g=(v,k)=>CL.sl[(o+v)*3+k];
  const t=g(f.a,1)*bc.x+g(f.b,1)*bc.y+g(f.c,1)*bc.z; const a0=g(f.a,2); const un=(x)=>{ let d=x-a0; d=Math.atan2(Math.sin(d),Math.cos(d)); return a0+d; };
  const ang=a0*bc.x+un(g(f.b,2))*bc.y+un(g(f.c,2))*bc.z; return {side:m.userData.side,t:Math.max(.12,Math.min(.88,t)),ang}; }
renderer.domElement.addEventListener('pointerdown',ev=>{ setMouse(ev);
  if(SIM.mouse==='fabric'){ const hits=ray.intersectObjects([torso,...sleeves],false); const h=hits[0]; if(!h)return;
    const off= h.object===torso? 0 : h.object.userData.off; const cand=[h.face.a,h.face.b,h.face.c].map(v=>v+off); let best=cand[0],bd=1e9; for(const p of cand){ const d=_v(p).distanceToSquared(h.point); if(d<bd){bd=d;best=p;} }
    CL.grab=best; CL.grabT=[h.point.x,h.point.y,h.point.z]; grabPlane=new THREE.Plane().setFromNormalAndCoplanarPoint(camera.getWorldDirection(new THREE.Vector3()).negate(),h.point);
    controls.enabled=false; renderer.domElement.setPointerCapture(ev.pointerId); return; }
  const vis=Object.values(meshes).filter(m=>m.visible); const hit=ray.intersectObjects(vis,false)[0];
  if(hit){ dragging=hit.object.userData.key; controls.enabled=false; renderer.domElement.setPointerCapture(ev.pointerId); select(dragging); } });
renderer.domElement.addEventListener('pointermove',ev=>{ setMouse(ev);
  if(CL.grab>=0&&grabPlane){ const p=new THREE.Vector3(); if(ray.ray.intersectPlane(grabPlane,p)) CL.grabT=[p.x,p.y,p.z]; return; }
  if(!dragging)return; const k=dragging;
  if(k==='hr'){ const hit=ray.intersectObjects(sleeves,false)[0]; if(!hit)return; const q=hitToSleeve(hit,hit.object); state.place.hr={kind:'sleeve',...q}; }
  else { const hit=ray.intersectObject(torso,false)[0]; if(!hit)return; const q=hitToSZ(hit); q.z=Math.max(20,Math.min(690,q.z)); state.place[k]={kind:'torso',s:q.s,z:q.z};
    if(state.mirror&&(k==='ecgR'||k==='ecgL')){ const o=k==='ecgR'?'ecgL':'ecgR'; state.place[o]={kind:'torso',s:-q.s,z:q.z}; } }
  placementChanged(true); });
const endDrag=()=>{ if(CL.grab>=0){ CL.grab=-1; grabPlane=null; controls.enabled=true; } if(dragging){ dragging=null; controls.enabled=true; placementChanged(false); } };
renderer.domElement.addEventListener('pointerup',endDrag); renderer.domElement.addEventListener('pointercancel',endDrag);
document.querySelectorAll('[data-p]').forEach(b=>b.onclick=()=>preset(b.dataset.p));
document.querySelectorAll('[data-v]').forEach(b=>b.onclick=()=>setView(b.dataset.v));
heat.onchange=colorShirt; heatSel.onchange=colorShirt;
document.getElementById('gearRuck').onchange=e=>{gearOn.rucksack=e.target.checked; colorShirt(); refreshPanels();};
document.getElementById('gearVest').onchange=e=>{gearOn.vest=e.target.checked; colorShirt(); refreshPanels();};
document.getElementById('bundle').onchange=e=>{ state.bundle=e.target.checked; if(state.bundle){ selected='m1'; } else { const m=state.place.m1; state.place.temp={kind:'torso',s:m.s,z:m.z+15}; state.place.imu={kind:'torso',s:m.s-22,z:m.z-40}; state.place.sweat={kind:'torso',s:m.s+22,z:m.z-40}; selected='temp'; } select(selected); };
document.getElementById('mirror').onchange=e=>{ state.mirror=e.target.checked; };
// physics controls
document.getElementById('physOn').onchange=e=>{ SIM.on=e.target.checked; };
document.getElementById('fit').onchange=e=>{ SIM.fit=e.target.value; resetCloth(); };
document.getElementById('motion').onchange=e=>{ SIM.motion=e.target.value; };
document.getElementById('wind').onchange=e=>{ SIM.wind=e.target.checked; };
document.getElementById('dummy').onchange=e=>{ bodyGroup.visible=e.target.checked; armMeshes.forEach(m=>m.visible=e.target.checked); };
document.getElementById('resetCloth').onclick=()=>resetCloth();
document.querySelectorAll('[data-mouse]').forEach(b=>b.onclick=()=>{ SIM.mouse=b.dataset.mouse; document.querySelectorAll('[data-mouse]').forEach(x=>x.classList.toggle('on',x===b)); document.getElementById('mouseHint').textContent= SIM.mouse==='fabric'? 'Drag the shirt to pull the fabric; it springs back when released.' : 'Drag a sensor to move it; drag empty space to rotate.'; });
function resetCloth(){ CL=makeCloth(SIM.fit); for(const k in contact) delete contact[k]; colorShirt(); updateMasses(); }
document.getElementById('copy').onclick=async()=>{ const t=document.getElementById('json'); try{ await navigator.clipboard.writeText(t.value); msg('Copied.'); }catch(_){ t.select(); msg('Text selected; press Ctrl+C.'); } };
document.getElementById('apply').onclick=()=>{ try{ fromJSON(document.getElementById('json').value); selected=state.bundle?'m1':'temp'; select(selected); msg('Applied.'); }catch(err){ msg('That is not valid placement JSON: '+err.message); } };
function msg(t){ document.getElementById('msg').textContent=t; }
function setView(v){ const r=2100, P={back:[0,520,-r],front:[0,520,r],left:[-r,520,0],right:[r,520,0]}[v]; camera.position.set(...P); controls.target.set(0,430,0); controls.update(); }
function refreshPanels(){ listMods(); detail(); checks(); }
function placementChanged(fast){ updateMasses(); buildTraces(); refreshPanels(); if(!fast){ drawFlats(); document.getElementById('json').value=toJSON(); } else { drawFlats(); } }
function refresh(){ placementChanged(false); }
function resize(){ const c=renderer.domElement, w=c.clientWidth||stage.clientWidth, h=c.clientHeight||stage.clientHeight; renderer.setSize(w,h,false); camera.aspect=w/h; camera.updateProjectionMatrix(); }
addEventListener('resize',resize);
document.getElementById('refs').innerHTML=REFS.map(r=>`<li>${r}</li>`).join('');
resize(); setView('back'); preset('revA'); colorShirt();
let frame=0;
// settle the cloth before the first frame so the page opens in a rested state
for(let i=0;i<90;i++){ SIM.t+=1/60; SIM.pose=stepCloth(CL,SIM.t,1/60,'still',false); }
(function loop(){ requestAnimationFrame(loop);
  if(SIM.on){ SIM.t+=1/60; SIM.pose=stepCloth(CL,SIM.t,1/60,SIM.motion,SIM.wind); }
  syncBody(SIM.pose); syncMeshes(); for(const k of KEYS) placeMesh(k); syncTraces();
  const m=meshes[selected]; if(m&&m.visible){ selRing.visible=true; selRing.position.copy(m.position); selRing.quaternion.copy(m.quaternion); const s=Math.max(DIMS[selected][0],DIMS[selected][1])*0.62; selRing.scale.set(s,s,1); selRing.translateZ(DIMS[selected][2]+1.5);} else selRing.visible=false;
  measureContact(); if(++frame%15===0){ detail(); checks(); }
  controls.update(); renderer.render(scene,camera); })();
