import 'reflect-metadata';
import {NestFactory,APP_GUARD} from '@nestjs/core';
import {Module,Controller,Get,Post,Put,Patch,Delete,Body,Param,Req,Res,Inject,Catch,HttpException,type ExceptionFilter,type ArgumentsHost} from '@nestjs/common';
import type {Request,Response,NextFunction} from 'express';
import cookieParser from 'cookie-parser';
import helmet from 'helmet';
import {ZodError} from 'zod';
import {pathToFileURL} from 'node:url';
import {join} from 'node:path';
import {existsSync} from 'node:fs';
import {Database} from './database.js';
import {CareerService} from './service.js';
import {AuthService,AccessGuard,Public,Roles,type AuthRequest} from './auth.js';
import {config,validateConfig} from './config.js';
import {questions,skillCatalog,interestInfo} from '../../../packages/shared/domain.js';
@Catch()
class Errors implements ExceptionFilter {
 catch(error:any,host:ArgumentsHost){const res=host.switchToHttp().getResponse<Response>();if(error instanceof ZodError){res.status(400).json({message:error.issues.map(x=>`${x.path.join('.')||'Input'}: ${x.message}`).join(' ')});return;}
 const code=error instanceof HttpException?error.getStatus():error.code==='23505'?409:error.code==='23503'?400:500;
 if(code===500)console.error('Request failed:',error.code??error.name);
 res.status(code).json({message:error instanceof HttpException?error.message:code===409?'This record already exists or this slot was just booked.':code===400?'A referenced record is unavailable.':'The server could not complete this request.'});}
}
@Controller('api')
class ApiController {
 constructor(@Inject(AuthService)private auth:AuthService,@Inject(CareerService)private service:CareerService){}
 @Public() @Get('meta') meta(){return {mode:config.mode,questions,skillCatalog,interestInfo};}
 @Public() @Get('health') async health(){await this.service.db.q('select 1');return {status:'ok',mode:config.mode};}
 @Public() @Post('auth/register') register(@Body()p:unknown,@Res({passthrough:true})res:Response){return this.auth.register(p,res);}
 @Public() @Post('auth/login') login(@Body()p:unknown,@Res({passthrough:true})res:Response){return this.auth.login(p,res);}
 @Public() @Post('auth/refresh') refresh(@Req()r:Request,@Res({passthrough:true})res:Response){return this.auth.refresh(r,res);}
 @Public() @Post('auth/logout') logout(@Req()r:Request,@Res({passthrough:true})res:Response){return this.auth.logout(r,res);}
 @Get('me') me(@Req()r:AuthRequest){return r.user;}
 @Put('me') profile(@Req()r:AuthRequest,@Body()p:unknown){return this.service.profile(r.user,p);}
 @Roles('student') @Delete('me') remove(@Req()r:AuthRequest,@Body()p:unknown,@Res({passthrough:true})res:Response){return this.auth.remove(r.user,p,res);}
 @Get('dashboard') dashboard(@Req()r:AuthRequest){return this.service.dashboard(r.user);}
 @Get('careers') async careers(@Req()r:AuthRequest){const list=await this.service.careers();return ['admin','expert'].includes(r.user.role)?list:list.filter(c=>c.active);}
 @Roles('student') @Get('recommendations') recommendations(@Req()r:AuthRequest){return this.service.recommendations(r.user);}
 @Roles('student') @Post('assessments') assessment(@Req()r:AuthRequest,@Body()p:unknown){return this.service.assessment(r.user,p);}
 @Roles('student') @Put('assessment-draft') draft(@Req()r:AuthRequest,@Body()p:unknown){return this.service.draft(r.user,p);}
 @Roles('student') @Put('careers/:id/feedback') feedback(@Req()r:AuthRequest,@Param('id')id:string,@Body()p:unknown){return this.service.feedback(r.user,id,p);}
 @Roles('student') @Get('careers/:id/roadmap') roadmap(@Req()r:AuthRequest,@Param('id')id:string){return this.service.roadmap(r.user,id);}
 @Roles('student') @Put('careers/:id/milestones/:skill') milestone(@Req()r:AuthRequest,@Param('id')id:string,@Param('skill')skill:string,@Body()p:unknown){return this.service.milestone(r.user,id,skill,p);}
 @Get('counsellors') counsellors(){return this.service.counsellors();}
 @Roles('student') @Get('slots') available(){return this.service.available();}
 @Roles('counsellor') @Post('slots') addSlot(@Req()r:AuthRequest,@Body()p:unknown){return this.service.addSlot(r.user,p);}
 @Roles('counsellor') @Delete('slots/:id') removeSlot(@Req()r:AuthRequest,@Param('id')id:string){return this.service.removeSlot(r.user,id);}
 @Roles('student') @Post('bookings') book(@Req()r:AuthRequest,@Body()p:unknown){return this.service.book(r.user,p);}
 @Roles('student','counsellor') @Patch('bookings/:id') updateBooking(@Req()r:AuthRequest,@Param('id')id:string,@Body()p:unknown){return this.service.updateBooking(r.user,id,p);}
 @Roles('counsellor') @Get('bookings/:id/context') context(@Req()r:AuthRequest,@Param('id')id:string){return this.service.context(r.user,id);}
 @Roles('counsellor') @Get('bookings/:id/note') note(@Req()r:AuthRequest,@Param('id')id:string){return this.service.note(r.user,id);}
 @Roles('counsellor') @Put('bookings/:id/note') saveNote(@Req()r:AuthRequest,@Param('id')id:string,@Body()p:unknown){return this.service.note(r.user,id,p);}
 @Put('notifications/read') read(@Req()r:AuthRequest){return this.service.readNotifications(r.user);}
 @Roles('admin') @Post('admin/careers') createCareer(@Body()p:unknown){return this.service.saveCareer(p);}
 @Roles('admin') @Put('admin/careers/:id') saveCareer(@Param('id')id:string,@Body()p:unknown){return this.service.saveCareer(p,id);}
 @Roles('admin') @Put('admin/weights') setWeights(@Body()p:unknown){return this.service.setWeights(p);}
 @Roles('admin') @Patch('admin/users/:id/role') setRole(@Req()r:AuthRequest,@Param('id')id:string,@Body()p:unknown){return this.service.setRole(r.user,id,p);}
 @Roles('expert') @Post('proposals') propose(@Req()r:AuthRequest,@Body()p:unknown){return this.service.propose(r.user,p);}
 @Roles('admin') @Patch('admin/proposals/:id') review(@Req()r:AuthRequest,@Param('id')id:string,@Body()p:unknown){return this.service.review(r.user,id,p);}
}
@Module({controllers:[ApiController],providers:[Database,AuthService,CareerService,{provide:APP_GUARD,useClass:AccessGuard}]})
class AppModule{}
export async function createApp(){
 validateConfig();const app=await NestFactory.create(AppModule,{logger:process.env.NODE_ENV==='test'?false:['error','warn','log']});
 await app.get(Database).init();
 app.use(helmet({contentSecurityPolicy:{directives:{defaultSrc:["'self'"],scriptSrc:["'self'"],styleSrc:["'self'","'unsafe-inline'"],imgSrc:["'self'",'data:'],connectSrc:["'self'"],fontSrc:["'self'"]}}}));
 const origins=!config.production&&config.mode==='demo'?[config.origin,'http://localhost:5174','http://127.0.0.1:5174']:[config.origin];
 app.use(cookieParser());app.enableCors({origin:origins,credentials:true,allowedHeaders:['Content-Type','X-CareerCompass'],methods:['GET','POST','PUT','PATCH','DELETE','OPTIONS']});
 const buckets=new Map<string,{n:number;until:number}>();
 app.use('/api',(req:Request,res:Response,next:NextFunction)=>{
  if(!['GET','HEAD','OPTIONS'].includes(req.method)&&(req.get('X-CareerCompass')!=='1'||(req.get('Origin')&&!origins.includes(req.get('Origin')!))))return res.status(403).json({message:'Request origin could not be verified.'});
  if(buckets.size>10000){for(const [k,v] of buckets)if(v.until<Date.now())buckets.delete(k);if(buckets.size>10000)return res.status(429).json({message:'Too many requests. Try again later.'});}
  const auth=/\/auth\/(login|register|refresh)/.test(req.path);const key=`${req.ip}:${auth?'auth':'api'}`;const now=Date.now();let b=buckets.get(key);if(!b||b.until<now){b={n:0,until:now+60000};buckets.set(key,b);}b.n++;if(process.env.NODE_ENV!=='test'&&b.n>(auth?20:300))return res.status(429).json({message:'Too many requests. Wait a minute before trying again.'});next();
 });
 app.useGlobalFilters(new Errors());
 if(config.production&&existsSync('dist/web/index.html')){const express=await import('express');app.use(express.default.static(join(process.cwd(),'dist/web')));}
 app.enableShutdownHooks();await app.init();return app;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){try{const app=await createApp();await app.listen(config.port,process.env.HOST??(config.production?'0.0.0.0':'127.0.0.1'));console.log(`CareerCompass API http://localhost:${config.port} (${config.mode})`);}catch(e){console.error('CareerCompass startup failed:',(e as Error).message);process.exit(1);}}
