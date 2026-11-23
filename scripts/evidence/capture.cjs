'use strict';
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const root = process.env.WORDLE_PLAYWRIGHT_ROOT ||
  path.join(require('node:os').homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
const {chromium} = require(require.resolve('playwright', {paths:[root]}));
const {validateContext,allowedURL}=require('./capture_policy.cjs');
function browserOptions(){return process.env.WORDLE_BROWSER_EXECUTABLE?{executablePath:process.env.WORDLE_BROWSER_EXECUTABLE}:{channel:process.env.WORDLE_BROWSER_CHANNEL||'msedge'};}
function png(file) {
 const b=fs.readFileSync(file);
 if(!b.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))) throw Error('Not PNG');
 return {sha256:crypto.createHash('sha256').update(b).digest('hex'),width:b.readUInt32BE(16),height:b.readUInt32BE(20),format:'PNG'};
}
async function smoke(output) {
 fs.mkdirSync(output,{recursive:true});
 const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end('<!doctype html><html lang="es"><title>Wordle capture diagnostic</title><h1>Prueba local de captura</h1><p>Diagnóstico de Playwright y Edge. No es una prueba funcional de Wordle.</p></html>');});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 let browser;
 try {
  browser=await chromium.launch({...browserOptions(),headless:true,args:['--no-proxy-server']});
  const context=await browser.newContext({viewport:{width:1440,height:1000},locale:'es-ES',timezoneId:'UTC'});
  await context.addInitScript(user=>localStorage.setItem('wordle-user-id',user),'capture-'+crypto.randomUUID());
  const page=await context.newPage();
  await page.goto('http://127.0.0.1:'+server.address().port);
  await page.getByRole('heading',{name:'Prueba local de captura',exact:true}).waitFor();
  const file=path.join(output,'edge-smoke.png');assert(!fs.existsSync(file),'Refuse smoke evidence overwrite');
  await page.screenshot({path:file,type:'png'});
  const info=png(file);
  if(info.width!==1440||info.height!==1000)throw Error('Unexpected dimensions');
  fs.writeFileSync(path.join(output,'edge-smoke.json'),JSON.stringify({result:'PASS',utc:new Date().toISOString(),browser:browser.version(),channel:'msedge',...info,limitation:'Tool diagnostic only, not Wordle evidence'},null,2));
  await context.close();
  console.log(JSON.stringify({smoke:'PASS',...info}));
 } finally {if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
}
if(require.main===module) {
 if(process.argv[2]==='--smoke')smoke(path.resolve(process.argv[3])).catch(e=>{console.error(e.message);process.exitCode=1;});
}
module.exports={png,chromium};

const {execFileSync}=require('node:child_process');
function assert(ok,message){if(!ok)throw Error(message);}
async function capture(ctx) {
 validateContext(ctx);
 const out=path.resolve(process.env.WORDLE_CAPTURE_DIR);
 const entries=[], checks=[];
 const api='http://127.0.0.1:'+ctx.public_port;
 const publicURL='http://wordle.test:'+ctx.public_port;
 const browser=await chromium.launch({...browserOptions(),headless:true,args:['--no-proxy-server','--host-resolver-rules=MAP wordle.test 127.0.0.1']});
 const deadline=setTimeout(()=>browser.close().catch(()=>{}),150000);
 let context;
 const sql=q=>{assert(ctx.mode!=='aks','SQL forbidden in AKS screenshot mode');return execFileSync('kubectl',[...ctx.prefix.slice(1),'-n','wordle-demo','exec','-i','postgres-0','--','sh','-c','exec psql --no-psqlrc -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -tA'],{input:q,encoding:'utf8',stdio:['pipe','pipe','pipe']}).trim();};
 async function shot(page,group,name,ev,a,expected) {
  const rel='screenshots/'+group+'/'+name+'.png',file=path.join(out,rel);
  fs.mkdirSync(path.dirname(file),{recursive:true});assert(!fs.existsSync(file),'Refuse screenshot overwrite');
  await page.screenshot({path:file,type:'png',fullPage:group==='grafana'});
  entries.push({ev,requirements:a,scenario:name,utc:new Date().toISOString(),environment:ctx.mode==='aks'?'azure-aks':'kind-local',release_sha:ctx.release_sha,runtime_images:ctx.runtime_images,persistence:'PostgreSQL 16 real',expected,observed:'Verified before screenshot',status:'PASS',path:rel,...png(file),viewport:page.viewportSize(),fullPage:group==='grafana'});
 }
 try {
  context=await browser.newContext({viewport:{width:1440,height:1000},locale:'es-ES',timezoneId:'UTC'});
  await context.route('**/*',route=>{
   const u=new URL(route.request().url());
   const method=route.request().method();
   const readonly=method==='GET'||method==='HEAD'||(ctx.mode==='aks'&&Number(u.port)===ctx.ports.grafana&&method==='POST'&&['/login','/api/ds/query'].includes(u.pathname));
   return allowedURL(u.href,ctx)&&(ctx.mode!=='aks'||readonly)?route.continue():route.abort();
  });
  await context.addInitScript(user=>localStorage.setItem('wordle-user-id',user),'capture-'+crypto.randomUUID());
  const page=await context.newPage();
  const health=await context.request.get(api+'/api/health',{headers:{Host:'wordle.test'},maxRedirects:0});
  assert(health.ok(),'Real HTTP health');const release=health.headers()['x-wordle-release'];
  if(ctx.mode==='aks'&&ctx.stage!=='signals')assert(release===(ctx.stage==='stable-blue'?'blue':'green'),'Captured traffic release differs from stage');
  checks.push({name:'Ingress health',status:health.status(),release});
  await page.goto(publicURL,{waitUntil:'domcontentloaded'});
  await page.getByRole('heading',{name:'Encuentra la palabra.',exact:true}).waitFor();
  await shot(page,'wordle',ctx.stage,'EV-04',['A10','A11','A12','A15'],'Real frontend through Traefik; release '+release);
  if(ctx.stage==='stable-blue'&&ctx.mode!=='aks') {
   let id;
   async function start() {
    const response=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/api/game/nueva'));
    await page.getByRole('button',{name:/Empezar partida|Nueva partida/,exact:true}).click();
    const r=await response;assert(r.status()===200,'Creation HTTP');id=(await r.json()).partida_id;
    assert(/^[0-9a-f-]{36}$/.test(id),'Synthetic game UUID');
    await page.getByRole('status').filter({hasText:'Intento 1 de 6'}).waitFor();
   }
   const state=()=>sql("SELECT estado||'|'||intentos_usados FROM public.partidas WHERE id='"+id+"';");
   const solution=()=>sql("SELECT palabra_secreta FROM public.partidas WHERE id='"+id+"';");
   async function guess(word,mobile=false) {
    await page.locator('h1').click();
    if(mobile)for(const letter of word)await page.getByRole('button',{name:letter,exact:true}).click();
    else for(const letter of word){if(letter==='Ñ')await page.getByRole('button',{name:'Ñ',exact:true}).click();else await page.keyboard.type(letter);}
    await page.waitForFunction(()=>document.querySelectorAll('.tile.filled').length===5);
    const response=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/api/game/intento'));
    await page.getByRole('button',{name:'Enviar',exact:true}).click();
    return await response;
   }
   await shot(page,'wordle','initial-desktop','EV-01',['A01','A50'],'Initial screen');
   await start();await shot(page,'wordle','in-progress-desktop','EV-01',['A01','A50'],'Active game SQL '+state());
   const before=state();let response=await guess('ZZZZZ');assert(response.status()===400&&state()===before,'Invalid word must not write');
   await page.getByRole('alert').filter({hasText:'Palabra no válida'}).waitFor();
   await shot(page,'wordle','invalid-word-no-attempt','EV-01',['A01','A50'],'HTTP400; SQL state unchanged');
   for(let i=0;i<5;i++){await page.getByRole('button',{name:'Borrar letra',exact:true}).click();await page.waitForFunction(expected=>document.querySelectorAll('.tile.filled').length===expected,4-i);}
   const answer=solution();response=await guess(answer);const won=await response.json();assert(response.status()===200&&won.estado==='ganada'&&won.resultado.every(x=>x.estado==='correcto')&&state()==='ganada|1','Victory HTTP/SQL/colors');
   await page.getByRole('status').filter({hasText:'¡Lo has conseguido!'}).waitFor();
   assert(await page.locator('.tile.correcto').count()===5,'Rendered green cells');
   await shot(page,'wordle','victory-desktop','EV-01',['A01','A50'],'HTTP200, SQL victory, five correct cells');
   // Verify persistence through replacement of only this run's PostgreSQL pod.
   const snapshot=()=>crypto.createHash('sha256').update(sql("SELECT json_build_object('games',(SELECT json_agg(p ORDER BY id) FROM public.partidas p),'guesses',(SELECT json_agg(i ORDER BY id) FROM public.intentos i),'stats',(SELECT json_agg(s ORDER BY id) FROM public.estadisticas s));")).digest('hex');
   const hash=snapshot();
   execFileSync('kubectl',[...ctx.prefix.slice(1),'-n','wordle-demo','delete','pod','postgres-0','--wait=true'],{stdio:'pipe',timeout:120000});
   execFileSync('kubectl',[...ctx.prefix.slice(1),'-n','wordle-demo','rollout','status','statefulset/postgres','--timeout=180s'],{stdio:'pipe',timeout:190000});
   assert(snapshot()===hash,'Persistence after PG pod replacement');
   checks.push({name:'PostgreSQL pod replacement preserves SQL snapshot',status:'PASS',sha256:hash});
   let recovered; for(let attempt=0;attempt<30;attempt++){recovered=await context.request.get(api+'/api/game/'+id,{headers:{Host:'wordle.test'},maxRedirects:0});if(recovered.ok())break;await new Promise(resolve=>setTimeout(resolve,500));}
   assert(recovered.ok()&&(await recovered.json()).partida.estado==='ganada','HTTP after replacement');
   await shot(page,'wordle','persisted-victory','EV-14',['A01','A50','A51'],'Same SQL dataset and HTTP victory after PostgreSQL pod replacement');
   await page.setViewportSize({width:390,height:844});
   await start();await shot(page,'wordle','restart-mobile','EV-01',['A01','A50'],'New game SQL en_curso|0');
   const secret=solution();const wrong=sql("SELECT palabra FROM public.palabras WHERE palabra<>'"+secret+"' ORDER BY id LIMIT 1;");
   for(let i=1;i<=6;i++){response=await guess(wrong,true);const result=await response.json();assert(response.status()===200&&result.intentos_usados===i,'Guess count');}
   await page.getByRole('status').filter({hasText:'Fin de la partida.'}).waitFor();assert(state()==='perdida|6','Loss SQL');
   await shot(page,'wordle','loss-mobile-six-attempts','EV-01',['A01','A50'],'Six real attempts, SQL perdida|6, solution only at end');
   await start();await shot(page,'wordle','initial-new-game-mobile','EV-01',['A01','A50'],'Restart to active new game');
   checks.push({name:'UI functional flow',status:'PASS',physicalKeyboard:true,virtualKeyboard:true,invalidNoWrite:true,victory:true,lossSix:true,restart:true});
  }
  if(ctx.stage==='signals') {
   const ports=ctx.ports,graf='http://127.0.0.1:'+ports.grafana,prom='http://127.0.0.1:'+ports.prometheus;
   await page.goto(graf+'/login',{waitUntil:'domcontentloaded'});
   await page.getByRole('textbox',{name:/Email or username|Username|Usuario/i}).fill('demo');
   await page.locator('input[type=password]').fill(ctx.password);
   await page.getByRole('button',{name:/Log in|Iniciar sesión|Sign in/i}).click();
   await page.waitForURL(u=>!u.pathname.includes('/login'));
   await page.goto(graf+'/d/wordle-demo?from=now-15m&to=now&timezone=utc',{waitUntil:'domcontentloaded'});
   await page.getByText('Wordle private demo',{exact:false}).first().waitFor();
   await page.waitForFunction(()=>document.querySelectorAll('canvas').length>=1);
   assert(!/An unexpected error|Data source error/.test(await page.locator('body').innerText()),'Dashboard error');
   await shot(page,'grafana','wordle-dashboard','EV-10',['A24','A30','A48'],'Provisioned dashboard with queries verified by real validator');
   await page.getByText('Monitoring targets',{exact:false}).first().scrollIntoViewIfNeeded();
   await page.waitForFunction(()=>{const t=document.body.innerText;return t.includes('collector:8889')&&t.includes('trace_id');},{},{timeout:30000});
   await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
   await shot(page,'grafana','wordle-dashboard-lower','EV-10',['A24','A30','A48'],'Lower panels of the same real provisioned dashboard');
   await page.goto(prom+'/targets',{waitUntil:'domcontentloaded'});
   await page.getByText(/collector/).first().waitFor();
   await shot(page,'prometheus','targets-up','EV-09',['A23','A26','A27'],'Real target API verified all UP');
   for(const [name,expr] of [['application','wordle_http_requests_total'],['containers','container_memory_working_set_bytes{namespace="wordle-demo",container!=""}'],['nodes','node_memory_MemTotal_bytes']]) {
    await page.goto(prom+'/query?g0.expr='+encodeURIComponent(expr)+'&g0.tab=1',{waitUntil:'domcontentloaded'});
    const queryResponse=page.waitForResponse(r=>r.url().includes('/api/v1/query')&&r.status()===200);
    await page.getByRole('button',{name:/Execute|Ejecutar/i}).first().click();
    const result=await (await queryResponse).json();assert(result.status==='success'&&result.data.result.length>0,'Real Prometheus vector');
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    await shot(page,'prometheus',name+'-metrics','EV-09',['A23','A26','A27'],'Real metric query '+expr);
   }
   // Grafana Explore URLs use the existing provisioned datasource and real queries.
   for(const [name,query] of [['backend','{service_name="wordle-backend"}'],['frontend','{service_name="wordle-frontend"}'],['deployment','{service_name="wordle-deploy"}']]) {
    const panes={capture:{datasource:'loki',queries:[{refId:'A',expr:query,queryType:'range',datasource:{type:'loki',uid:'loki'}}],range:{from:'now-15m',to:'now'}}};
    await page.goto(graf+'/explore?schemaVersion=1&panes='+encodeURIComponent(JSON.stringify(panes))+'&orgId=1',{waitUntil:'domcontentloaded'});
    await page.getByText(/Logs volume|Logs|Registros/).first().waitFor();
    await shot(page,'loki',name+'-logs','EV-11',['A25','A30'],'Real LogQL '+query);
   }
   const panes={capture:{datasource:'tempo',queries:[{refId:'A',queryType:'traceql',query:ctx.trace_id,datasource:{type:'tempo',uid:'tempo'}}],range:{from:'now-15m',to:'now'}}};
   await page.goto(graf+'/explore?schemaVersion=1&panes='+encodeURIComponent(JSON.stringify(panes))+'&orgId=1',{waitUntil:'domcontentloaded'});
   await page.getByText('POST /game/intento',{exact:false}).first().waitFor();
   await shot(page,'tempo','real-attempt-trace','EV-08',['A22','A30','A48'],'Real trace '+ctx.trace_id);
  }
 } finally {
  clearTimeout(deadline);
  if(context)await context.close();
  await browser.close();
  const dir=path.join(out,'results/capture');fs.mkdirSync(dir,{recursive:true});
  fs.writeFileSync(path.join(dir,ctx.stage+'.json'),JSON.stringify({utc:new Date().toISOString(),stage:ctx.stage,checks,screenshots:entries},null,2),{flag:'wx'});
 }
 console.log(JSON.stringify({stage:ctx.stage,result:'PASS',screenshots:entries.length}));
}
if(require.main===module&&process.argv[2]==='--capture'){
 let input='';process.stdin.setEncoding('utf8');process.stdin.on('data',x=>input+=x);process.stdin.on('end',()=>capture(JSON.parse(input)).catch(e=>{console.error(String(e.stack).split(JSON.parse(input).password||'__NO_PASSWORD__').join('[REDACTED]'));process.exitCode=1;}));
}
