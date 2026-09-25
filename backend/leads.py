import os, uuid, csv, io, logging
import httpx
from html import escape
from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from db import db, now
from models import LeadInput, LeadUpdate
from auth import admin, rate_limit
from email_guard import _assert_safe_email

router=APIRouter(prefix='/api')
EMAIL_BASE_URL='https://integrations.emergentagent.com'

async def notify(lead_id):
    settings=await db.settings.find_one({'id':'business'},{'_id':0})
    status='not_configured'
    if settings.get('email_notifications') and settings.get('admin_email'):
        subject='Glenntek — novo pedido de orçamento'
        html=f'<table role="presentation" width="100%"><tr><td style="padding:24px;font-family:Arial,sans-serif"><h2>Novo pedido de orçamento</h2><p>Foi recebido um novo pedido no website Glenntek.</p><p>Referência: {escape(lead_id[:8].upper())}</p><p><a href="{escape(os.environ["FRONTEND_ORIGIN"])}/admin/leads">Consultar o pedido no painel Glenntek</a></p><p style="font-size:12px;color:#666">Enviado por Glenntek. Não responda a este email com palavras-passe ou dados de pagamento.</p></td></tr></table>'
        try:
            _assert_safe_email(subject,html)
            async with httpx.AsyncClient(timeout=25) as client:
                result=await client.post(f'{EMAIL_BASE_URL}/api/v1/email/send',headers={'X-Email-Key':os.environ['EMERGENT_EMAIL_KEY']},json={'to':[settings['admin_email']],'subject':subject,'html':html,'from_name':os.environ['EMAIL_FROM_NAME']})
                result.raise_for_status()
            status='sent'
        except Exception:
            logging.exception('Lead notification failed; lead retained')
            status='failed'
    await db.leads.update_one({'id':lead_id},{'$set':{'notification_status':status}})

class LeadReceipt(BaseModel):
    id:str
    reference:str
    status:str

@router.post('/leads',response_model=LeadReceipt,status_code=201)
async def create_lead(body:LeadInput,request:Request,background:BackgroundTasks):
    await rate_limit(request,'enquiry',5,600)
    if body.website:raise HTTPException(422,'Não foi possível validar o pedido')
    lead_id=str(uuid.uuid4())
    doc={**body.model_dump(mode='json',exclude={'website'}),'id':lead_id,'status':'new','notes':'','created_at':now(),'updated_at':now(),'notification_status':'pending','consent_version':'2026-01'}
    allowed={'url','service','device','brand','model','district','municipality','source','utm_source','utm_medium','utm_campaign','utm_content','utm_term','gclid','fbclid'}
    doc['context']={k:v for k,v in doc['context'].items() if k in allowed}
    await db.leads.insert_one(doc)
    background.add_task(notify,lead_id)
    return LeadReceipt(id=lead_id,reference=lead_id[:8].upper(),status='received')

def lead_filter(status='',search=''):
    import re
    query={}
    if status:query['status']=status
    if search:
        pattern={'$regex':re.escape(search[:100]),'$options':'i'}
        query['$or']=[{k:pattern} for k in ['name','email','phone','device','municipality']]
    return query

@router.get('/admin/leads')
async def list_leads(status:str='',search:str='',page:int=1,user=Depends(admin)):
    query=lead_filter(status,search)
    total=await db.leads.count_documents(query)
    items=await db.leads.find(query,{'_id':0}).sort('created_at',-1).skip((max(1,page)-1)*30).limit(30).to_list(30)
    return {'items':items,'total':total,'page':max(1,page)}

@router.get('/admin/leads/export')
async def export_leads(status:str='',search:str='',user=Depends(admin)):
    fields=['id','name','phone','whatsapp','email','device','brand','model','issue','description','district','municipality','postal_code','preferred_contact','status','notes','created_at','notification_status','url','source','utm_source','utm_medium','utm_campaign','utm_content','gclid']
    def safe(value):
        v=str(value or '')
        return "'"+v if v.lstrip().startswith(('=','+','-','@','\t','\r')) else v
    async def rows():
        buffer=io.StringIO();writer=csv.DictWriter(buffer,fieldnames=fields);writer.writeheader();yield '\ufeff'+buffer.getvalue();buffer.seek(0);buffer.truncate(0)
        async for lead in db.leads.find(lead_filter(status,search),{'_id':0}).sort('created_at',-1):
            flat={**lead,**lead.get('context',{})};writer.writerow({key:safe(flat.get(key)) for key in fields});yield buffer.getvalue();buffer.seek(0);buffer.truncate(0)
    return StreamingResponse(rows(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="glenntek-pedidos.csv"'})

@router.patch('/admin/leads/{lead_id}')
async def update_lead(lead_id:str,body:LeadUpdate,user=Depends(admin)):
    result=await db.leads.update_one({'id':lead_id},{'$set':{**body.model_dump(),'updated_at':now()}})
    if not result.matched_count:raise HTTPException(404,'Pedido não encontrado')
    return {'ok':True}

@router.delete('/admin/leads/{lead_id}')
async def delete_lead(lead_id:str,user=Depends(admin)):
    result=await db.leads.delete_one({'id':lead_id})
    if not result.deleted_count:raise HTTPException(404,'Pedido não encontrado')
    return {'ok':True}

@router.post('/admin/leads/{lead_id}/notify')
async def retry_notification(lead_id:str,request:Request,background:BackgroundTasks,user=Depends(admin)):
    await rate_limit(request,'notify',10,600)
    if not await db.leads.find_one({'id':lead_id}):raise HTTPException(404,'Pedido não encontrado')
    background.add_task(notify,lead_id)
    return {'status':'queued'}

@router.get('/admin/stats')
async def stats(user=Depends(admin)):
    counts=await db.leads.aggregate([{'$group':{'_id':'$status','count':{'$sum':1}}},{'$project':{'_id':0,'status':'$_id','count':1}}]).to_list(10)
    return {'total_leads':await db.leads.count_documents({}),'statuses':counts,'published_pages':await db.pages.count_documents({'status':'published'}),'draft_pages':await db.pages.count_documents({'status':'draft'}),'recent_leads':await db.leads.find({},{'_id':0}).sort('created_at',-1).limit(5).to_list(5),'notifications_pending':await db.leads.count_documents({'notification_status':{'$in':['failed','pending','not_configured']}})}