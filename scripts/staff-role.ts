import 'reflect-metadata';
import {Database} from '../apps/api/src/database.js';
import {validateConfig} from '../apps/api/src/config.js';
const [email,role]=process.argv.slice(2);if(!email||!['student','counsellor','expert','admin'].includes(role)){console.error('Usage: npm run staff:role -- email@example.com admin|counsellor|expert|student');process.exit(1);}
validateConfig();const db=new Database();try{await db.init();const rows=await db.q('update profiles set role=$2 where email=$1 returning email,role',[email.toLowerCase(),role]);if(!rows.length)throw new Error('Account not found. Register and sign in once before assigning its role.');console.log(rows[0]);}finally{await db.close();}
