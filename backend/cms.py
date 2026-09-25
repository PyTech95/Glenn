import uuid, re, unicodedata
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError
from db import db,now
from auth import admin
from models import PageInput,SettingsInput
from seed import DISTRICTS,FAQ

router=APIRouter(prefix='/api')

@router.get('/site')
async def public_site():
    settings=await db.settings.find_one({'id':'business'},{'_id':0,'admin_email':0,'email_notifications':0})
    pages=await db.pages.find({'status':'published'},{'_id':0,'content':0,'content_en':0,'faqs':0}).sort('created_at',1).to_list(2000)
    reviews=await db.pages.find({'status':'published','kind':'review','verified':True},{'_id':0}).to_list(200)
    reviews_by_id={p['id']:p for p in reviews}
    pages=[reviews_by_id.get(p['id'],p) for p in pages]
    import os
    faq_pages=await db.pages.find({'kind':'faq','status':'published'},{'_id':0,'faqs':1}).to_list(100)
    global_faqs=[f for p in faq_pages for f in p.get('faqs',[]) if f.get('q') and f.get('a')]
    return {'settings':{**settings,'site_url':os.environ['SITE_URL']},'pages':pages,'districts':DISTRICTS,'faqs':global_faqs or FAQ}

@router.get('/pages/{slug:path}')
async def public_page(slug:str):
    page=await db.pages.find_one({'slug':slug.strip('/'),'status':'published'},{'_id':0})
    if not page:raise HTTPException(404,'Página não encontrada')
    return page

@router.get('/locations/search')
async def search_locations(q:str=''):
    q=q.strip()[:100]
    if len(q)<2:return {'results':[]}
    normalized=unicodedata.normalize('NFKD',q).encode('ascii','ignore').decode().lower()
    candidates=await db.geography.find({},{'_id':0}).to_list(1000)
    matches=[g for g in candidates if normalized in unicodedata.normalize('NFKD',g['city']).encode('ascii','ignore').decode().lower() or any(q.startswith(prefix) for prefix in g.get('postal_prefixes',[]))]
    results=[]
    for item in matches[:12]:
        page=await db.pages.find_one({'status':'published','verified':True,'municipality':item['city'],'kind':{'$in':['municipality','service_area','location','service_location']}},{'_id':0,'slug':1,'kind':1,'physical':1})
        results.append({**item,'page':page})
    return {'results':results}

@router.get('/admin/settings')
async def get_settings(user=Depends(admin)):
    return await db.settings.find_one({'id':'business'},{'_id':0,'id':0})

@router.put('/admin/settings')
async def update_settings(body:SettingsInput,user=Depends(admin)):
    if body.google_reviews_url and not body.google_reviews_url.startswith('https://'):
        raise HTTPException(422,'Use um endereço HTTPS para as avaliações')
    await db.settings.update_one({'id':'business'},{'$set':body.model_dump(mode='json')})
    return {'ok':True}

@router.get('/admin/pages')
async def list_pages(kind:str='',status:str='',search:str='',user=Depends(admin)):
    query={}
    if kind:query['kind']=kind
    if status:query['status']=status
    if search:query['title']={'$regex':re.escape(search[:100]),'$options':'i'}
    return await db.pages.find(query,{'_id':0}).sort('updated_at',-1).to_list(5000)

async def validate_publication(data,page_id=None):
    reserved={'reparacoes','marcas','localizacoes','como-funciona','sobre-nos','contactos','blog','faq','orcamento','privacidade','cookies','termos','en','admin','api'}
    if data['slug'] in reserved or data['slug'].split('/')[0] in {'admin','api','en'}:
        raise HTTPException(422,'Este endereço está reservado pelo website. Escolha outro.')
    if data['status']!='published':return
    if any(not f.get('q','').strip() or not f.get('a','').strip() for f in data['faqs']):
        raise HTTPException(422,'Preencha a pergunta e a resposta de cada FAQ antes de publicar.')
    if data['kind'] in ['brand','model','location','service_area','municipality','district','service_location','review'] and not data['verified']:
        raise HTTPException(422,'Confirme os dados e a cobertura antes de publicar este conteúdo.')
    if not data['intro'] and data['kind']!='review':raise HTTPException(422,'Preencha a introdução antes de publicar.')
    if not data['noindex']:
        if not data['verified']:raise HTTPException(422,'Confirme a informação antes de permitir indexação.')
        if not data['seo_title'] or not data['seo_description']:raise HTTPException(422,'Preencha o título SEO e a descrição para indexar.')
    if data['physical'] and (data['kind']!='location' or not data['address'] or not data['phone'] or not data['hours']):
        raise HTTPException(422,'Uma loja física precisa de morada, telefone e horário verificados.')
    if data['kind']=='review' and (not data['source_url'] or not data['review_author'] or not data['rating'] or not data['content']):
        raise HTTPException(422,'Uma avaliação requer autor, texto, classificação e fonte verificável.')
    if data['kind'] in ['service_location','service_area','municipality','district','location'] and not data['noindex']:
        if len((data['intro']+' '+data['content']).split())<180 or not data['coverage'] or not data['service_method'] or len(data['faqs'])<2:
            raise HTTPException(422,'Para indexar: 180 palavras úteis, cobertura real, método de atendimento e pelo menos 2 perguntas locais.')
        words=set(re.findall(r'\w+',data['content'].lower()))
        existing=await db.pages.find({'kind':{'$in':['service_location','service_area','municipality','district','location']},'noindex':False,'status':'published'},{'_id':0,'id':1,'content':1}).to_list(5000)
        for page in existing:
            other=set(re.findall(r'\w+',page.get('content','').lower()))
            if page['id']!=page_id and words and len(words & other)/len(words | other)>.85:
                raise HTTPException(422,'O conteúdo é demasiado semelhante a outra página local. Acrescente informação específica e útil.')

@router.post('/admin/pages',status_code=201)
async def create_page(body:PageInput,user=Depends(admin)):
    data=body.model_dump();await validate_publication(data)
    data.update(id=str(uuid.uuid4()),created_at=now(),updated_at=now())
    try:await db.pages.insert_one(dict(data))
    except DuplicateKeyError:raise HTTPException(409,'Já existe uma página com este endereço.')
    return data

@router.put('/admin/pages/{page_id}')
async def update_page(page_id:str,body:PageInput,user=Depends(admin)):
    data=body.model_dump();await validate_publication(data,page_id)
    data['updated_at']=now()
    try:result=await db.pages.update_one({'id':page_id},{'$set':data})
    except DuplicateKeyError:raise HTTPException(409,'Já existe uma página com este endereço.')
    if not result.matched_count:raise HTTPException(404,'Página não encontrada')
    return {'ok':True}

@router.delete('/admin/pages/{page_id}')
async def delete_page(page_id:str,user=Depends(admin)):
    result=await db.pages.delete_one({'id':page_id})
    if not result.deleted_count:raise HTTPException(404,'Página não encontrada')
    return {'ok':True}

class GenerateInput(BaseModel):
    service_id:str
    location_id:str

@router.post('/admin/generate',status_code=201)
async def generate_page(body:GenerateInput,user=Depends(admin)):
    service=await db.pages.find_one({'id':body.service_id,'kind':'service'},{'_id':0})
    location=await db.pages.find_one({'id':body.location_id,'kind':{'$in':['municipality','location','service_area']}},{'_id':0})
    if not service or not location:raise HTTPException(422,'Selecione um serviço e uma localização válidos.')
    city=location.get('municipality') or location['title']
    city_slug=unicodedata.normalize('NFKD',city).encode('ascii','ignore').decode().lower().replace(' ','-')
    page=PageInput(title=f'{service["title"]} em {city}',title_en=f'{service.get("title_en",service["title"])} in {city}',slug=f'{city_slug}/{service["slug"]}',kind='service_location',service=service.get('service',''),device=service.get('device',''),municipality=city,district=location.get('district',''),coverage=location.get('coverage',''),service_method=location.get('service_method',''),nearby=location.get('nearby',[]))
    return await create_page(page,user)