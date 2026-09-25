import os, logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from db import client
from seed import seed
from auth import router as auth_router
from leads import router as leads_router
from cms import router as cms_router
from seo import router as seo_router

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app):
    await seed()
    yield
    client.close()

app=FastAPI(title='GlennTek',docs_url=None,redoc_url=None,lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=[os.environ['FRONTEND_ORIGIN']],allow_credentials=True,allow_methods=['GET','POST','PUT','PATCH','DELETE','OPTIONS'],allow_headers=['Content-Type','X-CSRF-Token'])

@app.middleware('http')
async def security_headers(request:Request,call_next):
    try:
        length=int(request.headers.get('content-length','0'))
    except ValueError:
        return JSONResponse({'detail':'Pedido inválido'},status_code=400)
    if length>100000 or (request.method in {'POST','PUT','PATCH'} and len(await request.body())>100000):
        return JSONResponse({'detail':'Pedido demasiado grande'},status_code=413)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    response.headers['X-Frame-Options']='DENY'
    if request.url.path.startswith(('/api/admin','/api/auth')):
        response.headers['Cache-Control']='no-store'
        response.headers['X-Robots-Tag']='noindex, nofollow'
    return response

@app.get('/api/health')
async def health():return {'status':'ok','brand':'GlennTek'}

app.include_router(auth_router)
app.include_router(leads_router)
app.include_router(cms_router)
app.include_router(seo_router)