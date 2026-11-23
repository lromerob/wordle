"use strict";
function validateContext(c){
 const kind=Array.isArray(c.prefix)&&c.prefix.some(x=>String(x).startsWith('kind-wordle-fin1015-'));
 if(c.mode!=='aks'){if(!kind||c.mode&&c.mode!=='kind')throw Error('Isolated kind context required');return;}
 if(c.action!=='capture'||c.environment!=='azure-aks'||c.target_verified!==true||
    !/^[a-f0-9]{40}$/.test(c.release_sha||'')||!/^[a-f0-9]{64}$/.test(c.release_id||'')||
    !Array.isArray(c.runtime_images)||!c.runtime_images.length||c.runtime_images.some(r=>!/@sha256:[a-f0-9]{64}$/.test(r.image||'')||!/sha256:[a-f0-9]{64}$/.test(r.imageID||''))||
    JSON.stringify(c.namespaces)!==JSON.stringify(['wordle-demo','wordle-observability'])||
    !['stable-blue','promoted-green','rollback-green','signals'].includes(c.stage))throw Error('Incomplete authorized AKS provenance');
 if(!Array.isArray(c.owned_ports)||c.owned_ports.some(p=>!Number.isInteger(p)||p<1024||p>65535)||
    new Set(c.owned_ports).size!==c.owned_ports.length||!c.owned_ports.includes(c.public_port)||
    Object.values(c.ports||{}).some(p=>!c.owned_ports.includes(p)))throw Error('Unowned port-forward');
}
function allowedURL(url,c){
 const u=new URL(url);
 return u.protocol==='http:'&&!u.username&&!u.password&&['127.0.0.1','localhost','wordle.test'].includes(u.hostname)&&
   (c.mode!=='aks'||c.owned_ports.includes(Number(u.port)));
}
module.exports={validateContext,allowedURL};
