import os, json
from html import escape
from urllib.parse import quote
from fastapi import APIRouter
from fastapi.responses import Response
from db import db

router=APIRouter(prefix='/api/seo')
STATIC={
 '':('Reparação de Telemóveis, Tablets e Computadores em Portugal','Phone, Tablet and Computer Repair in Portugal','Dê uma nova vida ao seu equipamento. Peça uma avaliação à Glenntek para telemóveis, tablets e computadores.','Give your device a second life. Request a Glenntek assessment for phones, tablets and computers.'),
 'reparacoes':('Todas as reparações','All repairs','Escolha o seu dispositivo e descreva o problema. Peça um orçamento antes de decidir.','Choose your device and describe the issue. Request a quote before deciding.'),
 'marcas':('Marcas e equipamentos','Brands and devices','Consulte a disponibilidade de assistência para a marca e modelo do seu equipamento.','Check repair availability for your device brand and model.'),
 'localizacoes':('Onde precisa de ajuda?','Where do you need help?','Pesquise por cidade ou código postal. A cobertura e a forma de atendimento são confirmadas individualmente.','Search by city or postcode. Coverage and service arrangements are confirmed individually.'),
 'como-funciona':('Da primeira mensagem ao próximo capítulo.','From the first message to the next chapter.','Escolha o dispositivo, descreva o problema e receba uma avaliação antes de autorizar qualquer reparação.','Choose your device, describe the problem and get an assessment before authorising any repair.'),
 'sobre-nos':('Mais vida para a sua tecnologia.','More life for your technology.','Na Glenntek, acreditamos numa decisão informada antes de substituir um equipamento.','At Glenntek, we believe in making an informed decision before replacing a device.'),
 'contactos':('Vamos conversar.','Let’s talk.','Conte-nos o que aconteceu ao seu dispositivo e indique como prefere ser contactado.','Tell us what happened to your device and how you prefer to be contacted.'),
 'blog':('Mais conhecimento. Melhor tecnologia.','More knowledge. Better technology.','Conselhos práticos sobre baterias, ecrãs, líquidos e manutenção dos seus equipamentos.','Practical advice on batteries, screens, liquid damage and caring for your devices.'),
 'faq':('Perguntas frequentes','Frequently asked questions','Respostas sobre avaliação, orçamento, dados e disponibilidade de reparação.','Answers about assessments, quotes, data and repair availability.'),
 'orcamento':('Peça o seu orçamento','Request a quote','Descreva o dispositivo, o problema e a localização. Pedido sem compromisso de reparação.','Describe the device, issue and location. No commitment to repair.'),
 'privacidade':('Política de Privacidade','Privacy Policy','Informação sobre os dados recolhidos, finalidades, conservação e direitos.','Information about collected data, purposes, retention and your rights.'),
 'cookies':('Política de Cookies','Cookie Policy','Cookies essenciais e preferências de análise e marketing.','Essential cookies and analytics and marketing preferences.'),
 'termos':('Termos e Condições','Terms and Conditions','Condições de utilização do website e dos pedidos de orçamento.','Terms for website use and repair enquiries.')}

def translated(page,key,en):
    return page.get(key+'_en') or page.get(key,'') if en else page.get(key,'')

async def document_data(path):
    clean=path.split('?')[0].strip('/')
    en=clean=='en' or clean.startswith('en/')
    slug=clean[3:] if clean.startswith('en/') else '' if clean=='en' else clean
    settings=await db.settings.find_one({'id':'business'},{'_id':0})
    base=os.environ['SITE_URL'].rstrip('/')
    canonical=base+('/en' if en else '')+('/'+slug+'/' if slug else '/')
    page=None;status=200;noindex=not settings.get('verified_business')
    if slug in STATIC:
        pt,eng,desc,desc_en=STATIC[slug];title=eng if en else pt;description=desc_en if en else desc
        override=settings.get('static_seo',{}).get(slug or 'home',{})
        title=override.get('title_en' if en else 'title') or title
        description=override.get('description_en' if en else 'description') or description
        content='';faqs=[];kind='website'
        if slug in ['privacidade','cookies','termos','orcamento']:noindex=True
    elif slug.startswith('admin'):
        title='Administração Glenntek';description='Área reservada';content='';faqs=[];kind='website';noindex=True
    else:
        page=await db.pages.find_one({'slug':slug,'status':'published'},{'_id':0})
        if not page:
            status=404;title='Page not found' if en else 'Página não encontrada';description='';content='';faqs=[];kind='website';noindex=True
        else:
            title=translated(page,'seo_title',en) or translated(page,'title',en)
            description=translated(page,'seo_description',en) or translated(page,'intro',en)
            content=translated(page,'content',en);faqs=page.get('faqs',[]);kind=page['kind']
            noindex=page.get('noindex',True) or not page.get('verified') or (not settings.get('verified_business') and kind!='blog')
            if en and not page.get('content_en'):noindex=True
    title=title if 'Glenntek' in title else title+' | Glenntek'
    graph=[{'@type':'Organization','@id':base+'/#organization','name':settings['business_name'],'url':base+'/'},{'@type':'WebSite','@id':base+'/#website','name':'Glenntek','url':base+'/','inLanguage':['pt-PT','en']}]
    if settings.get('phone'):graph[0]['telephone']=settings['phone']
    if settings.get('email'):graph[0]['email']=settings['email']
    if page:
        graph.append({'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Home' if en else 'Início','item':base+('/en/' if en else '/')},{'@type':'ListItem','position':2,'name':translated(page,'title',en),'item':canonical}]})
        if kind=='blog':graph.append({'@type':'Article','headline':translated(page,'title',en),'description':description,'datePublished':page['created_at'],'dateModified':page['updated_at'],'author':{'@type':'Organization','name':'Glenntek'},'mainEntityOfPage':canonical,'inLanguage':'en' if en else 'pt-PT'})
        elif kind in ['service','repair','service_location'] and page.get('verified'):
            graph.append({'@type':'Service','name':translated(page,'title',en),'description':description,'provider':{'@id':base+'/#organization'},'url':canonical})
        if kind=='location' and page.get('physical') and page.get('verified') and page.get('address'):
            graph.append({'@type':'LocalBusiness','name':'Glenntek — '+page['title'],'address':{'@type':'PostalAddress','streetAddress':page['address'],'addressLocality':page.get('municipality',''),'addressCountry':'PT'},'telephone':page.get('phone',''),'url':canonical})
        if faqs and page.get('verified'):
            graph.append({'@type':'FAQPage','mainEntity':[{'@type':'Question','name':f.get('q_en',f['q']) if en else f['q'],'acceptedAnswer':{'@type':'Answer','text':f.get('a_en',f['a']) if en else f['a']}} for f in faqs if f.get('q') and f.get('a')]})
    image=base+'/images/repair-hero.webp'
    meta={'title':title,'description':description[:350],'canonical':canonical,'robots':'noindex, follow' if noindex else 'index, follow','lang':'en' if en else 'pt-PT','image':image,'type':'article' if kind=='blog' else 'website','graph':{'@context':'https://schema.org','@graph':graph},'alternates':[]}
    if status==200 and (not page or (page.get('title_en') and page.get('content_en'))):
        for code,prefix in [('pt-PT',''),('en','/en'),('x-default','')]:meta['alternates'].append({'lang':code,'href':base+prefix+('/'+slug+'/' if slug else '/')})
    head=f'<title>{escape(title)}</title><meta name="description" content="{escape(meta["description"])}"><meta name="robots" content="{meta["robots"]}"><link rel="canonical" href="{escape(canonical)}">'
    for prop,value in [('og:title',title),('og:description',description[:350]),('og:url',canonical),('og:image',image),('og:type',meta['type']),('og:locale','en_GB' if en else 'pt_PT')]:head+=f'<meta property="{prop}" content="{escape(value)}">'
    for name,value in [('twitter:card','summary_large_image'),('twitter:title',title),('twitter:description',description[:350]),('twitter:image',image)]:head+=f'<meta name="{name}" content="{escape(value)}">'
    for alt in meta['alternates']:head+=f'<link rel="alternate" hreflang="{alt["lang"]}" href="{escape(alt["href"])}">'
    if settings.get('search_console'):head+=f'<meta name="google-site-verification" content="{escape(settings["search_console"])}">'
    head+='<script type="application/ld+json" id="gt-schema">'+json.dumps(meta['graph'],ensure_ascii=False).replace('<','\\u003c')+'</script>'
    prefix='/en' if en else ''
    body=f'<header><a href="{prefix}/">Glenntek</a><nav><a href="{prefix}/reparacoes/">'+('Repairs' if en else 'Reparações')+f'</a> · <a href="{prefix}/localizacoes/">'+('Locations' if en else 'Localizações')+f'</a> · <a href="{prefix}/blog/">Blog</a></nav></header><main><h1>{escape(title.replace(" | Glenntek",""))}</h1><p>{escape(description)}</p>'
    for para in content.split('\n\n'):
        if para:body+=f'<{"h2" if len(para)<90 else "p"}>{escape(para)}</{"h2" if len(para)<90 else "p"}>'
    if page and page.get('coverage'):body+='<h2>'+('Service area' if en else 'Área de atendimento')+'</h2><p>'+escape(page['coverage'])+'</p><p>'+escape(page.get('service_method',''))+'</p>'
    if faqs:
        body+='<section><h2>'+('Frequently asked questions' if en else 'Perguntas frequentes')+'</h2>'
        for f in faqs:body+=f'<h3>{escape(f.get("q_en",f.get("q","")) if en else f.get("q",""))}</h3><p>{escape(f.get("a_en",f.get("a","")) if en else f.get("a",""))}</p>'
        body+='</section>'
    if slug in ('','reparacoes','blog','marcas','localizacoes'):
        kinds={'':['service','blog'],'reparacoes':['service','repair'],'blog':['blog'],'marcas':['brand'],'localizacoes':['location','service_area','municipality']}[slug]
        entries=await db.pages.find({'status':'published','kind':{'$in':kinds}},{'_id':0,'slug':1,'title':1,'title_en':1,'intro':1,'intro_en':1}).to_list(2000)
        body+='<section>'
        for entry in entries:body+=f'<article><h2><a href="{prefix}/{escape(entry["slug"])}/">{escape(translated(entry,"title",en))}</a></h2><p>{escape(translated(entry,"intro",en))}</p></article>'
        body+='</section>'
    body+=f'<a href="{prefix}/orcamento/">'+('Request a quote' if en else 'Pedir orçamento')+'</a></main>'
    return {'meta':meta,'head':head,'body':body,'status':status}

@router.get('/document')
async def document(path:str='/'):
    return await document_data(path[:500])

@router.get('/robots.txt')
async def robots():
    return Response('User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/\nSitemap: '+os.environ['SITE_URL'].rstrip('/')+'/sitemap.xml\n',media_type='text/plain')

@router.get('/{filename}')
async def sitemap(filename:str):
    base=os.environ['SITE_URL'].rstrip('/')
    names=['services','locations','service-locations','blog']
    if filename=='sitemap.xml':
        xml='<?xml version="1.0" encoding="UTF-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<sitemap><loc>{escape(base)}/sitemap-{name}.xml</loc></sitemap>' for name in names)+'</sitemapindex>'
        return Response(xml,media_type='application/xml')
    name=filename.removeprefix('sitemap-').removesuffix('.xml')
    if name not in names:return Response('Not found',status_code=404)
    kinds={'services':['service','repair','brand','model','device'],'locations':['location','service_area','district','municipality'],'service-locations':['service_location'],'blog':['blog']}[name]
    settings=await db.settings.find_one({'id':'business'},{'_id':0})
    entries=await db.pages.find({'kind':{'$in':kinds},'status':'published','noindex':False,'verified':True},{'_id':0}).to_list(50000)
    if name!='blog' and not settings.get('verified_business'):entries=[]
    urls=[]
    for entry in entries:
        urls.append((base+'/'+entry['slug']+'/',entry.get('updated_at','')))
        if entry.get('title_en') and entry.get('content_en'):urls.append((base+'/en/'+entry['slug']+'/',entry.get('updated_at','')))
    if name=='services' and settings.get('verified_business'):
        for path in ['','reparacoes','marcas','localizacoes','como-funciona','sobre-nos','contactos','blog','faq']:
            for prefix in ['', '/en']:urls.append((base+prefix+('/'+path+'/' if path else '/'),''))
    xml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+escape(url)+'</loc>'+('<lastmod>'+escape(date[:10])+'</lastmod>' if date else '')+'</url>' for url,date in urls)+'</urlset>'
    return Response(xml,media_type='application/xml')