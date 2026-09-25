import os, secrets, hashlib, hmac, asyncio
from datetime import datetime, timezone, timedelta
import bcrypt
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from pydantic import BaseModel, EmailStr, Field
from pymongo.errors import DuplicateKeyError
from db import db, now

router=APIRouter(prefix='/api/auth')

async def rate_limit(request, scope, limit=10, seconds=900):
    ip=request.headers.get('x-forwarded-for','').split(',')[0].strip() or request.client.host
    key=hashlib.sha256(f'{scope}:{ip}:{int(datetime.now(timezone.utc).timestamp())//seconds}'.encode()).hexdigest()
    item=await db.rate_limits.find_one_and_update({'_id':key},{'$inc':{'count':1},'$setOnInsert':{'expires':datetime.now(timezone.utc)+timedelta(seconds=seconds*2)}},upsert=True,return_document=True,projection={'_id':0})
    if item['count']>limit:
        raise HTTPException(429,'Demasiadas tentativas. Aguarde alguns minutos.')

def check_origin(request):
    origin=request.headers.get('origin')
    if origin != os.environ['FRONTEND_ORIGIN']:
        import logging
        logging.warning('Origin rejection: actual=%r expected=%r host=%r forwarded_host=%r',origin,os.environ['FRONTEND_ORIGIN'],request.headers.get('host'),request.headers.get('x-forwarded-host'))
        raise HTTPException(403,'Origem do pedido não autorizada')

async def admin(request:Request):
    raw=request.cookies.get('gt_session','')
    session=await db.sessions.find_one({'token_hash':hashlib.sha256(raw.encode()).hexdigest(),'expires':{'$gt':datetime.now(timezone.utc)}},{'_id':0}) if raw else None
    if not session:
        raise HTTPException(401,'Inicie sessão para continuar')
    user=await db.admins.find_one({'id':session['admin_id'],'active':True},{'_id':0,'password_hash':0})
    if not user:
        raise HTTPException(401,'Sessão inválida')
    if request.method not in ('GET','HEAD','OPTIONS'):
        check_origin(request)
        if not hmac.compare_digest(request.headers.get('X-CSRF-Token',''),session['csrf']):
            raise HTTPException(403,'Pedido inválido. Atualize a página.')
    return {**user,'csrf':session['csrf']}

class Credentials(BaseModel):
    email:EmailStr
    password:str=Field(min_length=12,max_length=72)
    setup_token:str=Field(default='',max_length=200)

async def create_session(response,user):
    token=secrets.token_urlsafe(40);csrf=secrets.token_urlsafe(32)
    await db.sessions.insert_one({'admin_id':user['id'],'token_hash':hashlib.sha256(token.encode()).hexdigest(),'csrf':csrf,'expires':datetime.now(timezone.utc)+timedelta(hours=12)})
    response.set_cookie('gt_session',token,httponly=True,secure=True,samesite='strict',max_age=43200,path='/api')
    return {'email':user['email'],'csrf':csrf}

@router.get('/status')
async def auth_status():
    return {'setup_required':not bool(await db.admins.find_one({'id':'owner'}))}

@router.post('/setup')
async def setup(body:Credentials,request:Request,response:Response):
    check_origin(request);await rate_limit(request,'setup',5)
    if not hmac.compare_digest(body.setup_token,os.environ['ADMIN_SETUP_TOKEN']):
        raise HTTPException(403,'Código de configuração inválido')
    if await db.admins.find_one({'id':'owner'}):
        raise HTTPException(409,'A administração já foi configurada')
    password_hash=await asyncio.to_thread(bcrypt.hashpw,body.password.encode(),bcrypt.gensalt())
    user={'id':'owner','email':str(body.email).lower(),'password_hash':password_hash.decode(),'active':True,'created_at':now()}
    try:await db.admins.insert_one(user)
    except DuplicateKeyError:raise HTTPException(409,'A administração já foi configurada')
    return await create_session(response,user)

@router.post('/login')
async def login(body:Credentials,request:Request,response:Response):
    check_origin(request);await rate_limit(request,'login',8)
    user=await db.admins.find_one({'email':str(body.email).lower(),'active':True},{'_id':0})
    valid=await asyncio.to_thread(bcrypt.checkpw,body.password.encode(),user['password_hash'].encode()) if user else False
    if not valid:raise HTTPException(401,'Email ou palavra-passe incorretos')
    return await create_session(response,user)

@router.get('/me')
async def me(user=Depends(admin)):
    return {'email':user['email'],'csrf':user['csrf']}

@router.post('/logout')
async def logout(request:Request,response:Response,user=Depends(admin)):
    await db.sessions.delete_one({'token_hash':hashlib.sha256(request.cookies.get('gt_session','').encode()).hexdigest()})
    response.delete_cookie('gt_session',path='/api',secure=True,httponly=True,samesite='strict')
    return {'ok':True}