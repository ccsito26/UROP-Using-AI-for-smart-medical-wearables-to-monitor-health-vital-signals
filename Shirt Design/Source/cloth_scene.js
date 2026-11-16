// ---------- scene (cloth-simulated shirt on a moving mannequin) ----------
const stage=document.getElementById('stage');
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true}); renderer.setPixelRatio(Math.min(devicePixelRatio,2)); stage.prepend(renderer.domElement);
const scene=new THREE.Scene(); const camera=new THREE.PerspectiveCamera(32,1,5,8000);
const controls=new THREE.OrbitControls(camera,renderer.domElement); controls.enableDamping=true; controls.target.set(0,430,0);
scene.add(new THREE.HemisphereLight(0xffffff,0x9a9a90,0.85)); const L1=new THREE.DirectionalLight(0xffffff,0.55); L1.position.set(600,1400,-1200); scene.add(L1); const L2=new THREE.DirectionalLight(0xffffff,0.45); L2.position.set(-800,900,1200); scene.add(L2);
const BASE=[86,96,70], RIB=[52,60,42];
const SIM={fit:'compression',motion:'still',wind:false,on:true,t:0,mouse:'sensors',pose:bodyPose(0,'still')};
let CL=makeCloth(SIM.fit);
// torso mesh bound to the particle grid
const tIdx=[]; for(let i=0;i<CNTH;i++){ const i2=(i+1)%CNTH; for(let j=0;j<CNZ-1;j++){ const a=i*CNZ+j,b=i2*CNZ+j,c=i2*CNZ+j+1,d=i*CNZ+j+1; tIdx.push(a,b,c,a,c,d);} }
const tGeo=new THREE.BufferGeometry(); const tPosAttr=new THREE.BufferAttribute(new Float32Array(CL.nT*3),3); tPosAttr.setUsage(THREE.DynamicDrawUsage);
tGeo.setAttribute('position',tPosAttr); tGeo.setIndex(tIdx); const tCol=new Float32Array(CL.nT*3); tGeo.setAttribute('color',new THREE.BufferAttribute(tCol,3));
const shirtMat=new THREE.MeshStandardMaterial({vertexColors:true,side:THREE.DoubleSide,roughness:.9,transparent:true,opacity:.92});
const torso=new THREE.Mesh(tGeo,shirtMat); torso.frustumCulled=false; scene.add(torso);
const sleeves=[]; for(let si=0;si<2;si++){ const idx=[]; for(let a=0;a<SNA;a++){ const a2=(a+1)%SNA; for(let t=0;t<SNT-1;t++){ const A=a*SNT+t,B=a2*SNT+t,Cc=a2*SNT+t+1,D=a*SNT+t+1; idx.push(A,B,Cc,A,Cc,D);} }
  const g=new THREE.BufferGeometry(); const pa=new THREE.BufferAttribute(new Float32Array(SNA*SNT*3),3); pa.setUsage(THREE.DynamicDrawUsage); g.setAttribute('position',pa); g.setIndex(idx);
  g.setAttribute('color',new THREE.BufferAttribute(new Float32Array(SNA*SNT*3),3)); const m=new THREE.Mesh(g,shirtMat); m.frustumCulled=false; m.userData={si,side:si===0?1:-1,off:CL.nT+si*SNA*SNT}; scene.add(m); sleeves.push(m); }
function syncMeshes(){ tPosAttr.array.set(CL.pos.subarray(0,CL.nT*3)); tPosAttr.needsUpdate=true; tGeo.computeVertexNormals(); tGeo.computeBoundingSphere();
  for(const m of sleeves){ const o=m.userData.off*3, pa=m.geometry.attributes.position; pa.array.set(CL.pos.subarray(o,o+SNA*SNT*3)); pa.needsUpdate=true; m.geometry.computeVertexNormals(); m.geometry.computeBoundingSphere(); } }
// mannequin
const bodyMat=new THREE.MeshStandardMaterial({color:0xb7ada0,roughness:.85});
const bodyGroup=new THREE.Group(); scene.add(bodyGroup); const bodyInner=new THREE.Group(); bodyInner.position.y=-430; bodyGroup.add(bodyInner);
{ const NA=72,NZb=40,pos=[],idx=[]; for(let i=0;i<NA;i++){ const th=2*Math.PI*i/NA, c=Math.cos(th), s=Math.sin(th), e=2/NEXP; for(let j=0;j<NZb;j++){ const z=-60+(BNP+150)*j/(NZb-1); const ux=Math.sign(c)*Math.pow(Math.abs(c),e), uy=Math.sign(s)*Math.pow(Math.abs(s),e); pos.push(bodyA(Math.max(0,z))*ux*0.995, z, bodyB(Math.max(0,z))*uy*0.995); } }
  for(let i=0;i<NA;i++){ const i2=(i+1)%NA; for(let j=0;j<NZb-1;j++){ const a=i*NZb+j,b=i2*NZb+j,c=i2*NZb+j+1,d=i*NZb+j+1; idx.push(a,c,b,a,d,c);} }
  const g=new THREE.BufferGeometry(); g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3)); g.setIndex(idx); g.computeVertexNormals(); bodyInner.add(new THREE.Mesh(g,bodyMat)); }
const armMeshes=[1,-1].map(()=>{ const m=new THREE.Mesh(new THREE.CylinderGeometry(ARM.r-1,ARM.r-6,ARM.len,24,1,false),bodyMat); scene.add(m); return m; });
function syncBody(P){ bodyGroup.position.set(P.tx,430+P.ty,P.tz); bodyGroup.rotation.set(0,P.yaw,P.roll,'YZX');
  [1,-1].forEach((side,k)=>{ const [A,B]=armSeg(P,side); const a=new THREE.Vector3(...A), b=new THREE.Vector3(...B); armMeshes[k].position.copy(a).add(b).multiplyScalar(.5); armMeshes[k].quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), b.clone().sub(a).normalize()); }); }

// cloth lookups: (s,z) on the torso and (side,t,ang) on a sleeve -> current position and frame
const _v=(i)=>new THREE.Vector3(CL.pos[i*3],CL.pos[i*3+1],CL.pos[i*3+2]);
function gridPt(fi,fj){ const i0=Math.floor(fi), j0=Math.max(0,Math.min(CNZ-2,Math.floor(fj))), u=fi-i0, v=Math.max(0,Math.min(1,fj-j0)); const I=(i)=>((i%CNTH)+CNTH)%CNTH;
  const p00=_v(I(i0)*CNZ+j0), p10=_v(I(i0+1)*CNZ+j0), p01=_v(I(i0)*CNZ+j0+1), p11=_v(I(i0+1)*CNZ+j0+1);
  return p00.multiplyScalar((1-u)*(1-v)).addScaledVector(p10,u*(1-v)).addScaledVector(p01,(1-u)*v).addScaledVector(p11,u*v); }
function clothAt(s,z){ const th=sToTh(s,z); const fi=(th+Math.PI/2)/(2*Math.PI)*CNTH, fj=z/BNP*(CNZ-1); return {fi,fj,o:gridPt(fi,fj)}; }
function clothFrame(s,z){ const c=clothAt(s,z); const ts=gridPt(c.fi+0.5,c.fj).sub(gridPt(c.fi-0.5,c.fj)).normalize(); const tzv=gridPt(c.fi,Math.min(CNZ-1.01,c.fj+0.5)).sub(gridPt(c.fi,Math.max(0,c.fj-0.5))).normalize();
  const n=new THREE.Vector3().crossVectors(ts,tzv).normalize(); const rad=c.o.clone().sub(new THREE.Vector3(SIM.pose.tx,c.o.y,SIM.pose.tz)); if(n.dot(rad)<0) n.negate();
  const tz2=new THREE.Vector3().crossVectors(n,ts).normalize(); return {o:c.o,ts,tz:tz2,n}; }
function sleevePt(si,fa,ft){ const off=CL.nT+si*SNA*SNT; const a0=Math.floor(fa), t0=Math.max(0,Math.min(SNT-2,Math.floor(ft))), u=fa-a0, v=Math.max(0,Math.min(1,ft-t0)); const A=(a)=>((a%SNA)+SNA)%SNA;
  const q=(a,t)=>_v(off+A(a)*SNT+t); return q(a0,t0).multiplyScalar((1-u)*(1-v)).addScaledVector(q(a0+1,t0),u*(1-v)).addScaledVector(q(a0,t0+1),(1-u)*v).addScaledVector(q(a0+1,t0+1),u*v); }
function sleeveClothFrame(side,t,ang){ const si=side>0?0:1, fa=(((ang%(2*Math.PI))+2*Math.PI)%(2*Math.PI))/(2*Math.PI)*SNA, ft=t*(SNT-1);
  const o=sleevePt(si,fa,ft); const ts=sleevePt(si,fa,Math.min(SNT-1.01,ft+0.4)).sub(sleevePt(si,fa,Math.max(0,ft-0.4))).normalize();
  const [A,B]=armSeg(SIM.pose,side); const a=new THREE.Vector3(...A), ab=new THREE.Vector3(...B).sub(a); const u=Math.max(0,Math.min(1,o.clone().sub(a).dot(ab)/ab.lengthSq()));
  const n=o.clone().sub(a.clone().addScaledVector(ab,u)).normalize(); const tzv=new THREE.Vector3().crossVectors(n,ts).normalize(); return {o,ts,tz:tzv,n}; }

// ---------- modules ----------
const KEYS=['m1','temp','imu','sweat','hub','ecgR','ecgL','hr'];
const NAMES={m1:'M1 back patch (temp + IMU + sweat)',temp:'Skin-temperature sensor',imu:'Gait IMU',sweat:'Sweat / wetness sensor',hub:'Hub pod',ecgR:'ECG electrode, right',ecgL:'ECG electrode, left',hr:'Optical HR pod (arm)'};
const DIMS={m1:[84,104,6.6,'#2a2d31'],temp:[50,50,6.6,'#2563eb'],imu:[30,26,8,'#c2410c'],sweat:[40,40,3,'#0891b2'],hub:[64,34,13,'#111827'],ecgR:[42,78,0.8,'#cbd5e1'],ecgL:[42,78,0.8,'#cbd5e1'],hr:[36,36,10,'#374151']};
const MASS={m1:30,temp:20,imu:10,sweat:8,hub:35,ecgR:4,ecgL:4,hr:15};       // grams (targets from drawing set)
const CONTACT_NEEDED={temp:'skin',sweat:'skin',ecgR:'skin',ecgL:'skin',imu:'coupling',m1:'skin',hr:'skin'};
const state={bundle:true,mirror:true,place:{}};
const gearOn={rucksack:true,vest:false};
const meshes={}, foot={}, contact={};
function rrShape(w,h,r){ const s=new THREE.Shape(), x=-w/2,y=-h/2; s.moveTo(x+r,y); s.lineTo(x+w-r,y); s.quadraticCurveTo(x+w,y,x+w,y+r); s.lineTo(x+w,y+h-r); s.quadraticCurveTo(x+w,y+h,x+w-r,y+h); s.lineTo(x+r,y+h); s.quadraticCurveTo(x,y+h,x,y+h-r); s.lineTo(x,y+r); s.quadraticCurveTo(x,y,x+r,y); return s; }
for(const k of KEYS){ const [w,h,t,col]=DIMS[k]; const geo=new THREE.ExtrudeGeometry(rrShape(w,h,Math.min(w,h)*0.2),{depth:t,bevelEnabled:true,bevelThickness:Math.min(1.5,t/3),bevelSize:1.2,bevelSegments:2,curveSegments:8});
  const mat=new THREE.MeshStandardMaterial({color:col,roughness:k.startsWith('ecg')?.35:.5,metalness:k.startsWith('ecg')?.6:.05});
  const m=new THREE.Mesh(geo,mat); m.userData.key=k; scene.add(m); meshes[k]=m; }
const traceGroup=new THREE.Group(); scene.add(traceGroup);
const selRing=new THREE.Mesh(new THREE.RingGeometry(0.93,1,64),new THREE.MeshBasicMaterial({color:0x1d4ed8,side:THREE.DoubleSide,depthTest:false,transparent:true})); selRing.renderOrder=10; scene.add(selRing);
function visibleKey(k){ return k==='m1'? state.bundle : (['temp','imu','sweat'].includes(k)? !state.bundle : true); }
function placeMesh(k){ const m=meshes[k], p=state.place[k]; if(!p){m.visible=false;return;} const vis=visibleKey(k); m.visible=vis; if(!vis)return;
  const f= p.kind==='sleeve'? sleeveClothFrame(p.side,p.t,p.ang) : clothFrame(p.s,p.z);
  const inside=k.startsWith('ecg'); const off= inside? -(DIMS[k][2]+1.6) : 1.0;
  m.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(f.ts,f.tz,f.n)); m.position.copy(f.o).addScaledVector(f.n,off); }
function effective(k){ if(['temp','imu','sweat'].includes(k)&&state.bundle) return state.place.m1; return state.place[k]; }
function updateMasses(){ const items=[]; for(const k of KEYS){ const p=state.place[k]; if(!p||!visibleKey(k)){ foot[k]=[]; continue; }
    foot[k]= p.kind==='sleeve'? sleeveFootprint(CL,p.side,p.t,p.ang) : footprint(CL,p.s,p.z,DIMS[k][0],DIMS[k][1]); items.push({idx:foot[k],mass:MASS[k]}); }
  applyMasses(CL,items); }
function measureContact(){ for(const k of KEYS){ const idx=foot[k]||[]; if(!idx.length){ contact[k]=null; continue; } let s=0,lift=0; for(const p of idx){ const g=Math.max(0,CL.gap[p]-0.6); s+=g; if(g>2)lift++; }
    const g=s/idx.length, lf=lift/idx.length, c=contact[k]||{gap:g,lift:lf,peak:g}; c.gap=c.gap*0.9+g*0.1; c.lift=c.lift*0.9+lf*0.1; c.peak=Math.max(c.peak*0.995,g); contact[k]=c; } }
function contactFor(k){ return contact[k==='temp'||k==='imu'||k==='sweat'? (state.bundle?'m1':k) : k]; }
// traces in (s,z), drawn on the moving cloth
function laneFor(k,hub){ return k==='ecgR'? hub.s+70 : k==='ecgL'? hub.s-70 : null; }
function traceLen(a,b,lane){ const C=arc(a.z).C; const tg= lane==null? b.s : lane; let ds=Math.abs(a.s-tg); ds=Math.min(ds,C-ds); return ds+Math.abs(a.z-b.z)+(lane==null?0:Math.abs(lane-b.s)); }
function tracePathSZ(a,b,lane){ const pts=[]; const C=arc(a.z).C; const tg= lane==null? b.s : lane; let ds=tg-a.s; if(ds>C/2)ds-=C; if(ds<-C/2)ds+=C; const n1=Math.max(2,Math.ceil(Math.abs(ds)/10));
  for(let i=0;i<=n1;i++) pts.push([a.s+ds*i/n1,a.z]); const dz=b.z-a.z, n2=Math.max(2,Math.ceil(Math.abs(dz)/10)); for(let i=1;i<=n2;i++) pts.push([a.s+ds,a.z+dz*i/n2]);
  if(lane!=null){ const d2=b.s-(a.s+ds), n3=Math.max(2,Math.ceil(Math.abs(d2)/10)); for(let i=1;i<=n3;i++) pts.push([a.s+ds+d2*i/n3,b.z]); } return pts; }
let traceSZ=[];
function buildTraces(){ traceGroup.clear(); traceSZ=[]; const hub=state.place.hub; const mat=new THREE.LineBasicMaterial({color:0xc2410c});
  const wired= state.bundle? ['m1','ecgR','ecgL'] : ['temp','imu','sweat','ecgR','ecgL'];
  for(const k of wired){ const p=state.place[k]; if(!p||p.kind!=='torso')continue; const sz=tracePathSZ(p,hub,laneFor(k,hub)); const g=new THREE.BufferGeometry(); g.setAttribute('position',new THREE.BufferAttribute(new Float32Array(sz.length*3),3)); const line=new THREE.Line(g,mat); line.frustumCulled=false; traceGroup.add(line); traceSZ.push([line,sz]); } }
function syncTraces(){ for(const [line,sz] of traceSZ){ const a=line.geometry.attributes.position; sz.forEach(([s,z],i)=>{ const f=clothFrame(s,z); const p=f.o.addScaledVector(f.n,1.5); a.setXYZ(i,p.x,p.y,p.z); }); a.needsUpdate=true; } }
function drawTraces(){ buildTraces(); syncTraces(); }
