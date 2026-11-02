import 'dotenv/config';
import {randomBytes} from 'node:crypto';
export const config={
 mode:process.env.APP_MODE??'demo',port:Number(process.env.PORT??4001),origin:process.env.WEB_ORIGIN??'http://localhost:5174',
 secret:process.env.JWT_SECRET||randomBytes(48).toString('hex'),dataDir:process.env.DEMO_DATA_DIR??'.data/demo',
 supabaseUrl:process.env.SUPABASE_URL??'',anonKey:process.env.SUPABASE_ANON_KEY??'',serviceKey:process.env.SUPABASE_SERVICE_ROLE_KEY??'',
 databaseUrl:process.env.DATABASE_URL??'',secure:process.env.COOKIE_SECURE==='true',production:process.env.NODE_ENV==='production'
};
export function validateConfig(){
 if(!['demo','supabase'].includes(config.mode))throw new Error('APP_MODE must be demo or supabase.');
 if(config.production&&(config.mode==='demo'||!config.secure))throw new Error('Production requires Supabase mode and secure cookies over HTTPS.');
 if(config.mode==='supabase'&&(!config.supabaseUrl.startsWith('https://')||!config.anonKey||!config.serviceKey||!config.databaseUrl))throw new Error('Configure Supabase URL, anon key, service-role key and DATABASE_URL.');
}
