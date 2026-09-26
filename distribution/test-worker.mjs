import assert from 'node:assert/strict';
import worker, {route,routes} from './_worker.js';
let seen=[], mode='ok';
globalThis.fetch=async (url,init)=>{
  seen.push({url,init});
  const first=url.includes('magireco-cn-patch/');
  if(mode==='both-down'||(mode==='network-fallback'&&first))throw new Error('network');
  const status=mode==='private'&&first?404:mode==='both-404'?404:mode==='range-ignored'&&first?200:mode==='not-modified'?304:mode==='unsatisfiable'?416:206;
  return new Response(status===304?null:new Uint8Array([80,75,3,4]),{status,headers:{'Content-Range':'bytes 0-3/100','Content-Length':'4','Content-Type':'application/zip','Accept-Ranges':'bytes'}});
};
const call=(path='/cn_js_delta.zip',method='GET',headers={Range:'bytes=0-3'})=>worker.fetch(new Request('https://example.test'+path,{method,headers}));
assert.equal(route('/legacy/config.json'),'https://raw.githubusercontent.com/HiiragiNemu/magireco-cn-patch/main/configures/personal-online-config.json');
assert.equal(routes('/legacy/config.json')[1],'https://raw.githubusercontent.com/HiiragiNemu/ProgettoMagius-1/main/legacy/config.json');
for(const path of ['/secret','/https://evil.example/a','/magica/research/private.json','/../x'])assert.equal((await call(path)).status,404);
assert.equal((await call('/cn_js_delta.zip','POST')).status,405);
assert.equal((await call('/cn_js_delta.zip','OPTIONS')).status,204);
assert.equal((await call('/health.json')).status,200);
seen=[];
let response=await call('/cn_js_delta.zip','GET',{Range:'bytes=0-3',Authorization:'must-not-forward'});
assert.equal(response.status,206);assert.equal(seen.length,1);
assert.deepEqual([...new Uint8Array(await response.arrayBuffer())],[80,75,3,4]);
assert.equal(seen[0].init.headers.get('Authorization'),null);
assert.equal(seen[0].init.headers.get('Range'),'bytes=0-3');
assert.equal(seen[0].init.cf.cacheTtl,0);
for(const fallback of ['private','network-fallback','range-ignored']){
  mode=fallback;seen=[];response=await call();
  assert.equal(response.status,206);assert.equal(seen.length,2);
  assert.equal(response.headers.get('X-Release-Authority'),'HiiragiNemu/ProgettoMagius-1');
  assert.equal(response.headers.get('Content-Range'),'bytes 0-3/100');
}
mode='private';response=await call('/cn_base_03.zip','HEAD',{});assert.equal(response.body,null);
mode='not-modified';assert.equal((await call()).status,304);
mode='unsatisfiable';assert.equal((await call()).status,416);
for(mode of ['both-down','both-404'])assert.equal((await call()).status,502);
console.log('PASS dual transport: old success, private-source 404, network fallback, range fallback, HEAD, 304, 416, allowlist and no credential forwarding');
