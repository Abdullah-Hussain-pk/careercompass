import {Injectable} from '@nestjs/common';
import {Pool} from 'pg';
import {readFile,mkdir,writeFile,rename} from 'node:fs/promises';
import {dirname} from 'node:path';
import {randomUUID} from 'node:crypto';
import bcrypt from 'bcryptjs';
import {config} from './config.js';
import {starterCareers} from '../../../packages/shared/careers.js';
import {scoreInterests,rankCareers,defaultWeights,skillCatalog,type Career,type User} from '../../../packages/shared/domain.js';
export type Query = (sql:string,values?:unknown[])=>Promise<any[]>;
export const asCareer=(r:any):Career=>({id:r.id,title:r.title,category:r.category,summary:r.summary,interests:r.interests,skills:r.skills,degrees:r.degrees,active:r.active,source:r.source,reviewStatus:r.review_status});
export const asUser=(r:any):User=>({id:r.id,email:r.email,name:r.name,role:r.role,degree:r.degree,semester:r.semester,cgpa:r.cgpa===null?null:Number(r.cgpa),bio:r.bio,specialty:r.specialty});
@Injectable()
export class Database {
 private pool?:Pool;private local:any;private queue:Promise<unknown>=Promise.resolve();private snapshotTimer?:ReturnType<typeof setTimeout>;private dirty=false;
 async init(){
  if(config.mode==='demo') {
   let loadDataDir:Blob|undefined;
   if(!config.dataDir.startsWith('memory://')){await mkdir(dirname(config.dataDir),{recursive:true});try{loadDataDir=new Blob([new Uint8Array(await readFile(`${config.dataDir}.snapshot.gz`))]);}catch(e){if((e as NodeJS.ErrnoException).code!=='ENOENT')throw e;}}
   const {PGlite}=await import('@electric-sql/pglite');this.local=new PGlite({loadDataDir});await this.local.waitReady;await this.migrate();await this.seed(true);
  }
  else this.pool=new Pool({connectionString:config.databaseUrl,max:10,ssl:process.env.DATABASE_SSL==='false'?false:{rejectUnauthorized:true}});
 }
 private serial<T>(fn:()=>Promise<T>):Promise<T>{const p=this.queue.then(fn);this.queue=p.catch(()=>{});return p;}
 private changed(){if(config.dataDir.startsWith('memory://'))return;this.dirty=true;clearTimeout(this.snapshotTimer);this.snapshotTimer=setTimeout(()=>{this.snapshotTimer=undefined;this.persist().catch(()=>console.error('Demo snapshot could not be saved. Check disk access and close gracefully.'));},1000);this.snapshotTimer.unref();}
 private async persist(){if(!this.dirty||!this.local)return;await this.serial(async()=>{const blob=await this.local.dumpDataDir('gzip');await writeFile(`${config.dataDir}.snapshot.gz.tmp`,new Uint8Array(await blob.arrayBuffer()));await rename(`${config.dataDir}.snapshot.gz.tmp`,`${config.dataDir}.snapshot.gz`);this.dirty=false;});}
 q:Query=async(sql,values=[])=>{if(this.pool)return (await this.pool.query(sql,values)).rows;const rows=await this.serial(async()=> (await this.local.query(sql,values)).rows);if(!/^\s*(select|show)/i.test(sql))this.changed();return rows;};
 async tx<T>(fn:(q:Query)=>Promise<T>):Promise<T>{
  if(this.pool){const c=await this.pool.connect();try {await c.query('begin');const result=await fn(async(s,v)=>(await c.query(s,v)).rows);await c.query('commit');return result;}catch(e){await c.query('rollback');throw e;}finally{c.release();}}
  const result=await this.serial(()=>this.local.transaction((tx:any)=>fn(async(s,v)=>(await tx.query(s,v)).rows)));this.changed();return result;
 }
 async migrate(){const sql=await readFile('supabase/migrations/001_initial.sql','utf8');if(this.local)await this.local.exec(sql);else await this.pool!.query(sql);}
 async seed(demo=false){
  await this.tx(async q=>{for(const c of starterCareers)await q('insert into careers(id,title,category,summary,interests,skills,degrees,active,source,review_status) values($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) on conflict do nothing',[c.id,c.title,c.category,c.summary,JSON.stringify(c.interests),JSON.stringify(c.skills),JSON.stringify(c.degrees),true,c.source,c.reviewStatus]);});
  if(!demo)return;
  const hash=await bcrypt.hash('CompassDemo!2026',12);
  for(const [email,name,role,specialty,bio] of [
   ['student@careercompass.demo','Abdullah Hussain','student','',''],
   ['counsellor@careercompass.demo','Sara Ahmed','counsellor','Technology and early careers','Demo counsellor profile. Helps students explore strengths and plan practical next steps.'],
   ['admin@careercompass.demo','System Administrator','admin','',''],
   ['expert@careercompass.demo','Hamza Ali','expert','Software and product','']
  ]) await this.q('insert into profiles(id,email,name,role,password_hash,degree,semester,cgpa,specialty,bio) values($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) on conflict do nothing',[randomUUID(),email,name,role,hash,role==='student'?'BS Software Engineering':null,role==='student'?5:null,role==='student'?3.4:null,specialty,bio]);
  const [student]=await this.q("select * from profiles where email='student@careercompass.demo'");
  if(!(await this.q('select id from assessments where user_id=$1',[student.id])).length){
   const answers=Array.from({length:48},(_,i)=>[3,5,4,3,3,4][i%6]);const scores=scoreInterests(answers);const skills=Object.fromEntries(skillCatalog.map(s=>[s.id,['programming','design','research'].includes(s.id)?3:2]));
   const matches=rankCareers(scores,skills,student.degree,starterCareers);
   await this.q('insert into assessments(id,user_id,answers,scores,skills,recommendation_ids,weights) values($1,$2,$3,$4,$5,$6,$7)',[randomUUID(),student.id,JSON.stringify(answers),JSON.stringify(scores),JSON.stringify(skills),JSON.stringify(matches.slice(0,10).map(m=>m.career.id)),JSON.stringify(defaultWeights)]);
  }
  const [counsellor]=await this.q("select id from profiles where role='counsellor' limit 1");
  for(let day=1;day<=7;day++)for(const hour of [9,10,14]){const d=new Date();d.setUTCDate(d.getUTCDate()+day);d.setUTCHours(hour,0,0,0);await this.q('insert into slots(id,counsellor_id,starts_at) values($1,$2,$3) on conflict do nothing',[randomUUID(),counsellor.id,d.toISOString()]);}
 }
 async close(){clearTimeout(this.snapshotTimer);if(this.pool)await this.pool.end();if(this.local){await this.persist();await this.local.close();}}
 async onModuleDestroy(){await this.close();}
}
