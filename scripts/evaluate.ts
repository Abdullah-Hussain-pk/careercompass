import {readFile} from 'node:fs/promises';
import {rankCareers,precisionAtK,ndcgAtK,type Vector,type Skills,type Weights} from '../packages/shared/domain.js';
import {starterCareers} from '../packages/shared/careers.js';
// Supply de-identified pilot judgements. Unrated candidates are treated as irrelevant.
const path=process.argv[2];if(!path){console.log('Usage: npm run evaluate -- pilot.json\nJSON array: [{scores:{R:50,I:80,A:60,S:40,E:30,C:50},skills:{programming:3,...},degree:"BS Software Engineering",ratings:{"frontend-developer":5,...}}]\nRate a common pooled candidate set from all variants. No pilot results are fabricated.');process.exit(0);}
const pilots: {scores:Vector;skills:Skills;degree:string|null;ratings:Record<string,number>}[]=JSON.parse(await readFile(path,'utf8'));if(!pilots.length)throw new Error('Provide at least one participant.');
const variants:Record<string,Weights>={interest:{interest:1,skills:0,degree:0},skills:{interest:0,skills:1,degree:0},hybrid:{interest:0.5,skills:0.35,degree:0.15}};
for(const [name,weights]of Object.entries(variants)){const results=pilots.map(p=>{const ids=rankCareers(p.scores,p.skills,p.degree,starterCareers,weights).slice(0,5).map(m=>m.career.id);return {precision:precisionAtK(ids,p.ratings),ndcg:ndcgAtK(ids,p.ratings)};});console.log(JSON.stringify({variant:name,participants:pilots.length,precisionAt5:results.reduce((s,r)=>s+r.precision,0)/pilots.length,ndcgAt5:results.reduce((s,r)=>s+r.ndcg,0)/pilots.length}));}
