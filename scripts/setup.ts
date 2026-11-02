import 'reflect-metadata';
import {Database} from '../apps/api/src/database.js';
import {config,validateConfig} from '../apps/api/src/config.js';
validateConfig();const db=new Database();try{await db.init();if(config.mode==='supabase'){await db.migrate();await db.seed(false);}console.log('Schema and 42 starter career profiles are ready. No live staff accounts were created.');}finally{await db.close();}
