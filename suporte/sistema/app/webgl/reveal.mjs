// Revelação de APRESENTAÇÃO: não modifica posição, tráfego, geometria ou cota física.
import * as THREE from '../vendor/three/build/three.module.js';
export function validateReveal(r){if(r==null)return r;if(!Number.isInteger(r.size)||r.size<2||r.size>256||!Array.isArray(r.bounds)||r.bounds.length!==4||!r.bounds.every(Number.isFinite)||r.bounds[2]<=r.bounds[0]||r.bounds[3]<=r.bounds[1]||!Array.isArray(r.stations)||r.stations.length!==r.size*r.size||!r.stations.every(x=>Number.isInteger(x)&&x>=0&&x<=65534)||!['initial','progressive'].includes(r.existing))throw Error('Campo de revelação 3D inválido. Reconstrua a cena.');return r}
export class ProjectReveal{
 constructor(viewer,data,ground){this.viewer=viewer;this.data=validateReveal(data);this.sprites=[];if(!data)return;
  const bytes=new Uint8Array(data.size*data.size*4);data.stations.forEach((s,i)=>{bytes[i*4]=s>>8;bytes[i*4+1]=s&255;bytes[i*4+3]=255});
  const texture=new THREE.DataTexture(bytes,data.size,data.size,THREE.RGBAFormat);texture.minFilter=texture.magFilter=THREE.LinearFilter;texture.needsUpdate=true;viewer.textures.add(texture);
  this.enabled={value:0};this.front={value:1};const bounds={value:new THREE.Vector4(...data.bounds)},field={value:texture};
  viewer.scene.traverse(object=>{if(object===ground||object.parent===viewer.technical||object.isInstancedMesh)return;if(object.isSprite){this.sprites.push(object);return}if(!object.geometry||!object.material)return;
   let state=object.userData?.presentation_state;for(let parent=object.parent;!state&&parent;parent=parent.parent)state=parent.userData?.presentation_state;const always=state==='existing'&&data.existing==='initial';
   for(const material of (Array.isArray(object.material)?object.material:[object.material])){const old=material.onBeforeCompile;
    material.onBeforeCompile=shader=>{old?.(shader,viewer.renderer);Object.assign(shader.uniforms,{rsRevealEnabled:this.enabled,rsRevealFront:this.front,rsRevealBounds:bounds,rsRevealField:field,rsRevealAlways:{value:always?1:0}});
     shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nvarying vec2 rsRevealXZ;').replace('#include <begin_vertex>','#include <begin_vertex>\nrsRevealXZ=(modelMatrix*vec4(transformed,1.0)).xz;');
     shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nvarying vec2 rsRevealXZ;uniform float rsRevealEnabled;uniform float rsRevealFront;uniform float rsRevealAlways;uniform vec4 rsRevealBounds;uniform sampler2D rsRevealField;').replace('#include <clipping_planes_fragment>','#include <clipping_planes_fragment>\nif(rsRevealEnabled>0.5&&rsRevealAlways<0.5){vec2 uv=clamp((rsRevealXZ-rsRevealBounds.xy)/(rsRevealBounds.zw-rsRevealBounds.xy),0.0,1.0);vec2 st=texture2D(rsRevealField,uv).rg;float fraction=(st.r*65280.0+st.g*255.0)/65534.0;if(fraction>rsRevealFront)discard;}');};
    material.customProgramCacheKey=()=>`rodovia-reveal-270`;material.needsUpdate=true;
   }
  });
 }
 fraction(x,z){const r=this.data;if(!r)return 0;const u=Math.max(0,Math.min(1,(x-r.bounds[0])/(r.bounds[2]-r.bounds[0]))),v=Math.max(0,Math.min(1,(z-r.bounds[1])/(r.bounds[3]-r.bounds[1])));return r.stations[Math.round(v*(r.size-1))*r.size+Math.round(u*(r.size-1))]/65534}
 sync(){if(!this.data)return;this.enabled.value=this.viewer.capturing?1:0;this.front.value=Math.max(0,Math.min(1,this.viewer.time/Math.max(.001,this.viewer.captureDuration??this.viewer.data.duration_s)))}
 visible(x,z){return !this.data||!this.viewer.capturing||this.fraction(x,z)<=this.front.value+1e-5}
 draw(callback){this.sync();if(!this.data||!this.viewer.capturing)return callback();this.viewer.scene.updateMatrixWorld(true);const changed=[];for(const sprite of this.sprites){const p=sprite.getWorldPosition(new THREE.Vector3());let state=sprite.userData?.presentation_state;for(let parent=sprite.parent;!state&&parent;parent=parent.parent)state=parent.userData?.presentation_state;if(!(state==='existing'&&this.data.existing==='initial')&&!this.visible(p.x,p.z)){changed.push([sprite,sprite.visible]);sprite.visible=false}}try{return callback()}finally{for(const [sprite,visible] of changed)sprite.visible=visible}}
}
