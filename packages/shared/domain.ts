export const types = ['R','I','A','S','E','C'] as const;
export type Interest = typeof types[number];
export type Role = 'student'|'counsellor'|'admin'|'expert';
export type Vector = Record<Interest,number>;
export type Skills = Record<string,number>;
export type Weights = {interest:number;skills:number;degree:number};
export interface User {id:string;email:string;name:string;role:Role;degree:string|null;semester:number|null;cgpa:number|null;bio:string;specialty:string;}
export interface Career {id:string;title:string;category:string;summary:string;interests:Vector;skills:Skills;degrees:string[];active:boolean;source:string;reviewStatus:string;}
export interface Assessment {id:string;user_id:string;answers:number[];scores:Vector;skills:Skills;created_at:string;}
export interface Match {career:Career;score:number;factors:{label:string;value:number;contribution:number;detail:string}[];gaps:{skill:string;current:number;required:number;resource:string;url:string}[];}
export const interestInfo:Record<Interest,{name:string;color:string;description:string}> = {
 R:{name:'Realistic',color:'#f4ae75',description:'Building, fixing and working with practical systems'},
 I:{name:'Investigative',color:'#a69aff',description:'Exploring ideas, analysing evidence and solving problems'},
 A:{name:'Artistic',color:'#e997cf',description:'Creating, designing and expressing original ideas'},
 S:{name:'Social',color:'#7acbea',description:'Teaching, supporting and connecting with people'},
 E:{name:'Enterprising',color:'#e8c56f',description:'Leading, persuading and starting new initiatives'},
 C:{name:'Conventional',color:'#9be2bd',description:'Organising information and following reliable processes'}
};
// Original educational items. These are not the licensed O*NET instrument or a validated psychometric scale.
const activities:Record<Interest,string[]> = {
 R:['Assemble a small electronic device','Repair a tool or piece of equipment','Build a working prototype','Work outdoors on a practical task','Set up a computer network','Test how a machine works','Use tools to make a useful object','Install and configure hardware'],
 I:['Investigate why a system failed','Analyse a dataset for patterns','Design an experiment to test an idea','Solve a challenging logic problem','Read about a scientific discovery','Compare evidence before reaching a conclusion','Research a technical question in depth','Develop a mathematical model'],
 A:['Design a visual identity for a project','Write a story or a creative article','Create an illustration or animation','Experiment with colours and layouts','Make a short film or audio project','Develop a new concept from a blank page','Design an engaging digital experience','Express an idea through an original artwork'],
 S:['Explain a difficult topic to a classmate','Support someone who is facing a problem','Teach a small group a new skill','Listen carefully to another person’s concerns','Organise a community learning activity','Help someone identify their strengths','Work with people from different backgrounds','Guide a newcomer through an unfamiliar process'],
 E:['Pitch a new idea to a group','Lead a team toward a shared goal','Negotiate an agreement','Start a small project or business','Persuade others to support an initiative','Take responsibility for a team decision','Present a proposal to decision makers','Identify an opportunity for a new service'],
 C:['Organise records so they are easy to find','Check a report for errors','Maintain an accurate project schedule','Follow a clear process to complete a task','Track spending in a spreadsheet','Document how a system is configured','Classify information using consistent rules','Review details before submitting work']
};
export const questions = Array.from({length:8},(_,n)=>types.map(type=>({id:`${type}${n+1}`,type,text:activities[type][n]}))).flat();
export const skillCatalog = [
 ['programming','Programming','MDN JavaScript Guide','https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide'],
 ['data','Data analysis','Kaggle Learn','https://www.kaggle.com/learn'],
 ['design','Design and prototyping','Figma Learn','https://help.figma.com/hc/en-us/categories/360002051613'],
 ['communication','Communication','OpenLearn communication courses','https://www.open.edu/openlearn/'],
 ['research','Research and critical thinking','OpenLearn research courses','https://www.open.edu/openlearn/'],
 ['math','Mathematics','Khan Academy mathematics','https://www.khanacademy.org/math'],
 ['leadership','Leadership','OpenLearn leadership courses','https://www.open.edu/openlearn/'],
 ['writing','Writing and documentation','Google technical writing','https://developers.google.com/tech-writing'],
 ['business','Business fundamentals','HP LIFE business courses','https://www.life-global.org/'],
 ['systems','Systems and networking','Cisco Skills for All','https://skillsforall.com/'],
 ['security','Security fundamentals','PortSwigger Web Security Academy','https://portswigger.net/web-security'],
 ['project','Project organisation','Atlassian project management','https://www.atlassian.com/work-management/project-management'],
 ['empathy','Listening and empathy','OpenLearn psychology courses','https://www.open.edu/openlearn/'],
 ['finance','Financial literacy','Khan Academy financial literacy','https://www.khanacademy.org/college-careers-more/financial-literacy'],
 ['science','Scientific reasoning','Khan Academy science','https://www.khanacademy.org/science'],
 ['practical','Practical problem solving','Arduino tutorials','https://docs.arduino.cc/tutorials/']
].map(([id,name,resource,url])=>({id,name,resource,url}));
export const skillName = (id:string)=>skillCatalog.find(s=>s.id===id)?.name??id;
export const defaultWeights:Weights = {interest:0.5,skills:0.35,degree:0.15};
export function scoreInterests(answers:number[]):Vector {
 if(answers.length!==48 || answers.some(x=>!Number.isInteger(x)||x<1||x>5)) throw new Error('Answer all 48 activities using a rating from 1 to 5.');
 return Object.fromEntries(types.map(type=>[type, Math.round(questions.reduce((sum,q,i)=>sum+(q.type===type?answers[i]-1:0),0)/32*100)])) as Vector;
}
export function cosine(a:Vector,b:Vector) {
 const dot=types.reduce((s,k)=>s+a[k]*b[k],0);
 const denom=Math.sqrt(types.reduce((s,k)=>s+a[k]**2,0))*Math.sqrt(types.reduce((s,k)=>s+b[k]**2,0));
 return denom?dot/denom:0;
}
export function rankCareers(scores:Vector,skills:Skills,degree:string|null,careers:Career[],weights:Weights=defaultWeights):Match[] {
 return careers.filter(c=>c.active).map(career=>{
 const interest=cosine(scores,career.interests);
 const required=Object.entries(career.skills);
 const coverage=required.length?required.reduce((sum,[s,n])=>sum+Math.min((skills[s]??1)/n,1),0)/required.length:0;
 const eligibility=!degree?0.5:career.degrees.length===0||career.degrees.some(d=>d.toLowerCase()===degree.toLowerCase())?1:0.25;
 const factors=[
 {label:'Interest alignment',value:Math.round(interest*100),contribution:interest*weights.interest*100,detail:'Cosine similarity between your six interest scores and this career profile.'},
 {label:'Skill readiness',value:Math.round(coverage*100),contribution:coverage*weights.skills*100,detail:'Average fraction of each required skill level that you currently meet.'},
 {label:'Academic fit',value:Math.round(eligibility*100),contribution:eligibility*weights.degree*100,detail:!degree?'No degree supplied. A neutral academic value of 50% is used.':eligibility===1?'Your degree matches the starter profile.':'Your degree is outside the starter list. This reduces the score, but does not rule out the career.'}
 ].sort((a,b)=>b.contribution-a.contribution);
 const gaps=required.filter(([s,n])=>(skills[s]??1)<n).sort((a,b)=>(b[1]-(skills[b[0]]??1))-(a[1]-(skills[a[0]]??1))||a[0].localeCompare(b[0])).map(([skill,n])=>{const r=skillCatalog.find(s=>s.id===skill)!;return {skill,current:skills[skill]??1,required:n,resource:r.resource,url:r.url};});
 return {career,score:Math.round(factors.reduce((s,f)=>s+f.contribution,0)*10)/10,factors,gaps};
 }).sort((a,b)=>b.score-a.score||a.career.title.localeCompare(b.career.title));
}
export function precisionAtK(ids:string[],ratings:Record<string,number>,k=5){return ids.slice(0,k).filter(id=>(ratings[id]??0)>=4).length/k;}
export function ndcgAtK(ids:string[],ratings:Record<string,number>,k=5){const dcg=(v:number[])=>v.slice(0,k).reduce((s,r,i)=>s+(2**r-1)/Math.log2(i+2),0);const ideal=dcg(Object.values(ratings).sort((a,b)=>b-a));return ideal?dcg(ids.map(id=>ratings[id]??0))/ideal:0;}
