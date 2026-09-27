// Only allowlisted public artifacts are exposed; no user credentials or arbitrary upstreams.
import SNAPSHOT from './config-snapshot.js';
export const PUBLIC_OWNER = 'HiiragiNemu/ProgettoMagius-1';
export const LEGACY_OWNER = 'HiiragiNemu/magireco-cn-patch';
export const HEADER_BUDGET_MS = 2000;
const PUBLIC_RAW = 'https://raw.githubusercontent.com/' + PUBLIC_OWNER + '/main/';
const LEGACY_RAW = 'https://raw.githubusercontent.com/' + LEGACY_OWNER + '/main/';
const PUBLIC_RELEASE = 'https://github.com/' + PUBLIC_OWNER + '/releases/download/latest/';
const LEGACY_RELEASE = 'https://github.com/' + LEGACY_OWNER + '/releases/download/latest/';
const ASSETS = new Set([
  'apk-overlay-atlas.zip','apk-overlay-atlas-e34fdda8.zip',
  'cn_base_00_db.zip','cn_base_01_json.zip','cn_base_02.zip','cn_base_03.zip',
  'cn_base_04.zip','cn_base_05.zip','cn_base_06.zip','cn_js_update.zip',
  'cn_js_update_manifest.json','cn_magica_resource.zip','cn_scenario_img.zip',
  'cn_scenario_update.zip','cn_scenario_update_manifest.json','cn_voice_01.zip',
  'cn_voice_02_done.zip','magireco-latest-legacy-client.apk',
  'magireco-latest-legacy-client.version.json','manifest.json','movie.zip','movie2.zip',
  'cn_js_delta.zip','cn_js_delta_manifest.json','version_js_delta.json',
  'version_js.json','version_scenario.json'
]);
export function routes(path) {
  if (path === '/legacy/config.json') return [PUBLIC_RAW+'legacy/config.json',LEGACY_RAW+'configures/personal-online-config.json'];
  return ASSETS.has(path.slice(1)) ? [PUBLIC_RELEASE+path.slice(1),LEGACY_RELEASE+path.slice(1)] : [];
}
export function route(path) { return routes(path)[0] || null; }
function headersFor(upstream, authority) {
  const out = new Headers();
  for (const name of ['Content-Type','Content-Length','Content-Range','Accept-Ranges','ETag','Last-Modified','Content-Disposition']) {
    const value = upstream.headers.get(name); if (value) out.set(name,value);
  }
  out.set('Cache-Control','no-store');
  out.set('Access-Control-Allow-Origin','*');
  out.set('Access-Control-Expose-Headers','Content-Length, Content-Range, Accept-Ranges, ETag, X-Release-Authority');
  out.set('X-Release-Authority',authority);
  return out;
}
function allowedRedirect(url) {
  return url.protocol === 'https:' && !url.username && !url.password &&
    (url.hostname === 'github.com' || url.hostname === 'raw.githubusercontent.com' ||
     url.hostname.endsWith('.githubusercontent.com'));
}
async function fetchPublic(target, options) {
  const seen = new Set();
  for (let redirects=0;redirects<=5;redirects++) {
    const url = new URL(target);
    if (!allowedRedirect(url) || seen.has(url.href)) throw new Error('Invalid redirect chain');
    seen.add(url.href);
    const r = await fetch(url.href,{...options,redirect:'manual',cf:{cacheTtl:0}});
    if (![301,302,303,307,308].includes(r.status)) return r;
    const location=r.headers.get('Location');
    if (r.body) await r.body.cancel();
    if (!location) throw new Error('Missing redirect target');
    target = new URL(location,url).href;
  }
  throw new Error('Redirect budget exhausted');
}
async function readJson(response) {
  const reader=response.body?.getReader(); if(!reader) throw new Error('Missing JSON body');
  const chunks=[]; let length=0;
  try {
    for (;;) {
      const next=await reader.read(); if(next.done) break;
      length+=next.value.byteLength;
      if(length>2*1024*1024) throw new Error('Metadata exceeds limit');
      chunks.push(next.value);
    }
  } catch(error) { await reader.cancel().catch(()=>{}); throw error; }
  finally { reader.releaseLock(); }
  const bytes=new Uint8Array(length); let offset=0;
  for(const chunk of chunks) {bytes.set(chunk,offset);offset+=chunk.length;}
  const value=JSON.parse(new TextDecoder().decode(bytes));
  if(!value || typeof value!=='object') throw new Error('Invalid metadata');
  return value;
}
function versionCompare(a,b) {
  const x=a.split('.').map(Number), y=b.split('.').map(Number);
  for(let i=0;i<Math.max(x.length,y.length);i++) if((x[i]||0)!==(y[i]||0)) return (x[i]||0)>(y[i]||0)?1:-1;
  return 0;
}
function verifiedConfig(c) {
  const m=c?.client, floor=SNAPSHOT.client;
  if(!m || !/^\d+(\.\d+){1,3}$/.test(m.version) || !Number.isSafeInteger(m.size) || m.size<=0 ||
     !/^[a-f0-9]{64}$/i.test(m.sha256) || !Array.isArray(c.mirrors) || !m.apk_url?.startsWith('https://')) return false;
  const cmp=versionCompare(m.version,floor.version);
  return cmp>0 || (cmp===0 && m.size===floor.size && m.sha256.toLowerCase()===floor.sha256.toLowerCase());
}
export function validRange(requested, response) {
  if(!requested) return response.status!==206;
  if(response.status===416) return /^bytes \*\/\d+$/.test(response.headers.get('Content-Range')||'');
  if(response.status!==206) return false;
  const asked=/^bytes=(\d*)-(\d*)$/.exec(requested), got=/^bytes (\d+)-(\d+)\/(\d+)$/.exec(response.headers.get('Content-Range')||'');
  if(!asked || !got || (!asked[1]&&!asked[2])) return false;
  const [start,end,total]=got.slice(1).map(Number);
  if(!Number.isSafeInteger(total) || start>end || end>=total) return false;
  const wantedStart=asked[1]?Number(asked[1]):Math.max(0,total-Number(asked[2]));
  const wantedEnd=asked[1]&&asked[2]?Math.min(total-1,Number(asked[2])):total-1;
  const size=response.headers.get('Content-Length');
  return start===wantedStart && end===wantedEnd && (size===null || Number(size)===end-start+1);
}
function jsonResponse(value, method, authority) {
  const body=JSON.stringify(value);
  return new Response(method==='HEAD'?null:body,{headers:{'Content-Type':'application/json; charset=utf-8',
    'Content-Length':String(new TextEncoder().encode(body).length),'Cache-Control':'no-store',
    'Access-Control-Allow-Origin':'*','X-Release-Authority':authority}});
}
export default {
  async fetch(request) {
    const url=new URL(request.url);
    if(request.method==='OPTIONS') return new Response(null,{status:204,headers:{
      'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET, HEAD, OPTIONS',
      'Access-Control-Allow-Headers':'Range, If-Range, If-None-Match'}});
    if(!['GET','HEAD'].includes(request.method)) return new Response('Method not allowed',{status:405,headers:{Allow:'GET, HEAD, OPTIONS'}});
    if(url.pathname==='/health.json') return jsonResponse({status:'ok',revision:'private-ready-196',authority:PUBLIC_OWNER,
      emergencyAuthority:LEGACY_OWNER,configurationSnapshot:SNAPSHOT.client.version,
      upstreamHeaderBudgetMs:HEADER_BUDGET_MS,maximumUpstreams:2,organizationCredentialsRequired:false},request.method,'deployment');
    if(url.pathname==='/') return new Response('<!doctype html><meta charset="utf-8"><title>MadeInMagius 更新入口</title><h1>MadeInMagius 更新入口</h1><p><a href="/magireco-latest-legacy-client.apk">下载客户端</a> · <a href="/legacy/config.json">在线配置</a></p>',{headers:{'Content-Type':'text/html; charset=utf-8'}});
    const targets=routes(url.pathname);
    if(!targets.length) return new Response('Not found',{status:404});
    const config=url.pathname==='/legacy/config.json';
    const metadata=url.pathname.endsWith('.json');
    const headers=new Headers({'User-Agent':'MadeInMagius-Public-Distribution','Accept-Encoding':'identity'});
    if(!config) for(const name of ['Range','If-Range','If-None-Match']) {
      const value=request.headers.get(name); if(value) headers.set(name,value);
    }
    for(let i=0;i<targets.length;i++) {
      const controller=new AbortController();
      // Metadata includes body time; healthy large binary streams have no total-time limit.
      const timer=setTimeout(()=>controller.abort(),HEADER_BUDGET_MS);
      try {
        const target=targets[i]+(metadata?'?fresh='+Math.floor(Date.now()/15000):'');
        const upstream=await fetchPublic(target,{method:config?'GET':request.method,headers,signal:controller.signal});
        if(!upstream.ok && upstream.status!==304 && upstream.status!==416) {
          if(upstream.body) await upstream.body.cancel(); continue;
        }
        const authority=i===0?PUBLIC_OWNER:LEGACY_OWNER;
        if(config) {
          const value=await readJson(upstream);
          if(!verifiedConfig(value)) continue;
          return jsonResponse(value,request.method,authority);
        }
        if(request.method==='GET' && upstream.status!==304 && !validRange(headers.get('Range'),upstream)) {
          if(upstream.body) await upstream.body.cancel(); continue;
        }
        if(metadata && request.method==='GET' && !headers.has('Range') && upstream.status===200) {
          const value=await readJson(upstream);
          return jsonResponse(value,request.method,authority);
        }
        clearTimeout(timer);
        return new Response(request.method==='HEAD'||upstream.status===304?null:upstream.body,
          {status:upstream.status,headers:headersFor(upstream,authority)});
      } catch (_) { /* This public source failed; attempt the one remaining source only. */ }
      finally { clearTimeout(timer); }
    }
    if(config) return jsonResponse(SNAPSHOT,request.method,'verified-independent-snapshot');
    return new Response('Download sources temporarily unavailable; please retry later',{
      status:502,headers:{'Cache-Control':'no-store','Access-Control-Allow-Origin':'*','Retry-After':'30'}});
  }
};
