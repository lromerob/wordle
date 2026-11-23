"use strict";
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {validateContext,allowedURL}=require('./capture_policy.cjs');
const base=()=>({mode:'aks',action:'capture',environment:'azure-aks',target_verified:true,release_sha:'a'.repeat(40),release_id:'b'.repeat(64),runtime_images:[{image:'example@sha256:'+'c'.repeat(64),imageID:'containerd://sha256:'+'c'.repeat(64)}],namespaces:['wordle-demo','wordle-observability'],stage:'stable-blue',owned_ports:[1234,1235],public_port:1234,ports:{grafana:1235}});
test('kind isolated context accepted',()=>validateContext({prefix:['kubectl','--context','kind-wordle-fin1015-synthetic']}));
test('AKS rejected by local mode',()=>assert.throws(()=>validateContext({prefix:['kubectl','--context','aks-wordle']})));
test('explicit complete AKS accepted',()=>validateContext(base()));
test('no mutation action accepted',()=>assert.throws(()=>validateContext({...base(),action:'delete'})));
test('unowned port rejected',()=>assert.throws(()=>validateContext({...base(),public_port:9999})));
test('external navigation rejected',()=>assert.equal(allowedURL('http://example.com:1234',base()),false));
test('wrong loopback port rejected',()=>assert.equal(allowedURL('http://127.0.0.1:9999',base()),false));
test('owned loopback accepted',()=>assert.equal(allowedURL('http://127.0.0.1:1234',base()),true));

test('incomplete runtime metadata rejected',()=>assert.throws(()=>validateContext({...base(),runtime_images:[{}]})));
