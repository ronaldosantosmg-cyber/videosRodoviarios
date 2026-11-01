// Pintura com largura em metros: independente do suporte do driver a linhas largas.
export function markingTriangles(markings,width=.15){
 if(!Number.isFinite(width)||width<.05||width>.3)throw Error('Largura de pintura inválida.');
 const result={white:[],yellow:[]};
 for(const record of markings||[]){const p=record.p;if(!Array.isArray(p)||p.length!==6||!p.every(Number.isFinite))throw Error('Segmento de pintura inválido.');
  const [x,y,z,X,Y,Z]=p,dx=X-x,dz=Z-z,L=Math.hypot(dx,dz);if(L<1e-8)continue;
  const nx=-dz/L*width/2,nz=dx/L*width/2,a=[x+nx,y+.004,z+nz],b=[x-nx,y+.004,z-nz],c=[X+nx,Y+.004,Z+nz],d=[X-nx,Y+.004,Z-nz];
  result[record.yellow?'yellow':'white'].push(...a,...c,...b,...b,...c,...d);
 }
 return result;
}
