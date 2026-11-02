import {it,expect} from 'vitest';
import {mkdtemp,stat} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {randomUUID} from 'node:crypto';
it('restores demo records from a compressed PostgreSQL snapshot',async()=>{
 process.env.APP_MODE='demo';process.env.NODE_ENV='test';const dir=await mkdtemp(join(tmpdir(),'careercompass-storage-'));process.env.DEMO_DATA_DIR=join(dir,'demo');
 const {Database}=await import('../apps/api/src/database.js');const {config}=await import('../apps/api/src/config.js');config.dataDir=join(dir,'demo');
 const first=new Database();await first.init();const id=randomUUID();await first.q('insert into profiles(id,email,name) values($1,$2,$3)',[id,'persistent@example.com','Persisted student']);await first.close();expect((await stat(`${config.dataDir}.snapshot.gz`)).size).toBeGreaterThan(0);
 const second=new Database();await second.init();expect((await second.q('select name from profiles where id=$1',[id]))[0].name).toBe('Persisted student');expect((await second.q('select count(*)::int as n from careers'))[0].n).toBe(42);await second.close();
},60000);
