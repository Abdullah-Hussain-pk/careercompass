import {Injectable,Inject,UnauthorizedException,ForbiddenException,BadRequestException,SetMetadata,type CanActivate,type ExecutionContext} from '@nestjs/common';
import {Reflector} from '@nestjs/core';
import type {Request,Response} from 'express';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import {randomUUID} from 'node:crypto';
import {z} from 'zod';
import {Database,asUser} from './database.js';
import {config} from './config.js';
import type {User,Role} from '../../../packages/shared/domain.js';
export type AuthRequest=Request&{user:User};
export const Roles=(...roles:Role[])=>SetMetadata('roles',roles);
export const Public=()=>SetMetadata('public',true);
const credentials=z.object({email:z.string().email().max(200).transform(x=>x.toLowerCase().trim()),password:z.string().min(8).max(72)});
@Injectable()
export class AuthService {
 constructor(@Inject(Database)private db:Database){}
 private async supa(path:string,body?:unknown,token?:string,admin=false,method?:string){
  const key=admin?config.serviceKey:config.anonKey;
  const response=await fetch(`${config.supabaseUrl}/auth/v1/${path}`,{method:method??(body?'POST':'GET'),headers:{apikey:key,Authorization:`Bearer ${token??key}`,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(12000)});
  const data=await response.json().catch(()=>({}));
  if(!response.ok)throw new UnauthorizedException('Authentication failed. Check your details and confirm your email if required.');
  return data;
 }
 private cookies(res:Response,access:string,refresh?:string){
  const base={httpOnly:true,secure:config.secure,sameSite:'lax' as const,path:'/api'};
  res.cookie('cc_access',access,{...base,maxAge:30*60*1000});
  if(refresh)res.cookie('cc_refresh',refresh,{...base,maxAge:7*24*60*60*1000});
 }
 clear(res:Response){for(const c of ['cc_access','cc_refresh'])res.clearCookie(c,{httpOnly:true,secure:config.secure,sameSite:'lax',path:'/api'});}
 async register(body:unknown,res:Response){
  const p=credentials.extend({name:z.string().trim().min(2).max(80)}).strict().parse(body);
  if(config.mode==='supabase'){
   const result=await this.supa('signup',{email:p.email,password:p.password,data:{name:p.name}});
   if(!result.access_token)return {message:'Check your email to confirm your account, then sign in.'};
   this.cookies(res,result.access_token,result.refresh_token);await this.ensureProfile(result.user);
   return {user:await this.byId(result.user.id)};
  }
  if((await this.db.q('select id from profiles where email=$1',[p.email])).length)throw new BadRequestException('An account with this email already exists.');
  const id=randomUUID();await this.db.q('insert into profiles(id,email,name,password_hash) values($1,$2,$3,$4)',[id,p.email,p.name,await bcrypt.hash(p.password,12)]);
  this.cookies(res,jwt.sign({sub:id},config.secret,{expiresIn:'30m',issuer:'careercompass-demo'}));return {user:await this.byId(id)};
 }
 private async ensureProfile(u:any){await this.db.q('insert into profiles(id,email,name) values($1,$2,$3) on conflict(id) do nothing',[u.id,u.email,(String(u.user_metadata?.name||'Student')).slice(0,80)]);}
 async login(body:unknown,res:Response){
  const p=credentials.strict().parse(body);
  if(config.mode==='supabase'){
   const result=await this.supa('token?grant_type=password',p);await this.ensureProfile(result.user);
   this.cookies(res,result.access_token,result.refresh_token);return {user:await this.byId(result.user.id)};
  }
  const [u]=await this.db.q('select * from profiles where email=$1',[p.email]);
  if(!u?.password_hash||!await bcrypt.compare(p.password,u.password_hash))throw new UnauthorizedException('Email or password is incorrect.');
  this.cookies(res,jwt.sign({sub:u.id},config.secret,{expiresIn:'30m',issuer:'careercompass-demo'}));return {user:asUser(u)};
 }
 async refresh(req:Request,res:Response){
  if(config.mode!=='supabase'||!req.cookies.cc_refresh)throw new UnauthorizedException('Sign in again.');
  const result=await this.supa('token?grant_type=refresh_token',{refresh_token:req.cookies.cc_refresh});this.cookies(res,result.access_token,result.refresh_token);return {ok:true};
 }
 async byId(id:string):Promise<User>{const [u]=await this.db.q('select * from profiles where id=$1',[id]);if(!u)throw new UnauthorizedException('Sign in again.');return asUser(u);}
 async authenticate(req:Request){
  const token=req.cookies?.cc_access;if(!token)throw new UnauthorizedException('Sign in to continue.');
  if(config.mode==='supabase'){const u=await this.supa('user',undefined,token);await this.ensureProfile(u);return this.byId(u.id);}
  try {const value=jwt.verify(token,config.secret,{algorithms:['HS256'],issuer:'careercompass-demo'}) as jwt.JwtPayload;return await this.byId(value.sub!);}catch{throw new UnauthorizedException('Your session expired. Sign in again.');}
 }
 async logout(req:Request,res:Response){
  if(config.mode==='supabase'&&req.cookies?.cc_access)await this.supa('logout',undefined,req.cookies.cc_access,false,'POST').catch(()=>{});
  this.clear(res);return {ok:true};
 }
 async remove(user:User,body:unknown,res:Response){
  if(user.role!=='student')throw new ForbiddenException('Student account deletion is available here. Staff accounts are managed by administrators.');
  const {password}=z.object({password:z.string().min(8).max(72),confirmation:z.literal('DELETE')}).strict().parse(body);
  if(config.mode==='supabase'){
   await this.supa('token?grant_type=password',{email:user.email,password});
   // Foreign key to auth.users cascades to profiles and all student-owned data.
   await this.supa(`admin/users/${user.id}`,undefined,undefined,true,'DELETE');
  }else{
   const [p]=await this.db.q('select password_hash from profiles where id=$1',[user.id]);
   if(!await bcrypt.compare(password,p.password_hash))throw new UnauthorizedException('Password is incorrect.');
   await this.db.q('delete from profiles where id=$1',[user.id]);
  }
  this.clear(res);return {ok:true};
 }
}
@Injectable()
export class AccessGuard implements CanActivate {
 constructor(@Inject(AuthService)private auth:AuthService,@Inject(Reflector)private reflector:Reflector){}
 async canActivate(ctx:ExecutionContext){
  if(this.reflector.getAllAndOverride('public',[ctx.getHandler(),ctx.getClass()]))return true;
  const req=ctx.switchToHttp().getRequest<AuthRequest>();req.user=await this.auth.authenticate(req);
  const roles=this.reflector.getAllAndOverride<Role[]>('roles',[ctx.getHandler(),ctx.getClass()]);
  if(roles&&!roles.includes(req.user.role))throw new ForbiddenException('This action is not available for your role.');
  return true;
 }
}
