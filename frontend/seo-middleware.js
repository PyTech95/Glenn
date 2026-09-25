const path = require('path');
const fs = require('fs');
const backend = process.env.REACT_APP_BACKEND_URL;

function inject(template, data) {
 return template.replace(/<title>[\s\S]*?<\/title>/i,'').replace(/<meta\s+name="description"[^>]*>/gi,'').replace(/<html lang="[^"]*"/,'<html lang="'+data.meta.lang+'"').replace('</head>',data.head+'</head>').replace('<div id="root"></div>','<div id="root">'+data.body+'</div>');
}
function seoMiddleware(getTemplate) {
 return async (req,res,next)=>{
  const pathname=req.url.split('?')[0];
  if(req.method!=='GET'||pathname.startsWith('/api/')||pathname.startsWith('/static/')||pathname.startsWith('/__'))return next();
  const file=pathname.match(/^\/(robots\.txt|sitemap(?:-(?:services|locations|service-locations|blog))?\.xml)$/);
  try {
   if(file){const r=await fetch(backend+'/api/seo/'+file[1],{signal:AbortSignal.timeout(10000)});res.statusCode=r.status;res.setHeader('Content-Type',file[1].endsWith('.txt')?'text/plain; charset=utf-8':'application/xml; charset=utf-8');return res.end(await r.text());}
   if(path.extname(pathname))return next();
   const r=await fetch(backend+'/api/seo/document?path='+encodeURIComponent(pathname),{signal:AbortSignal.timeout(10000)});
   if(!r.ok)return next();
   const data=await r.json();const template=await getTemplate();
   if(!template)return next();
   res.statusCode=data.status;res.setHeader('Content-Type','text/html; charset=utf-8');res.setHeader('Cache-Control','no-cache');res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','strict-origin-when-cross-origin');res.setHeader('X-Frame-Options','DENY');
   return res.end(inject(template,data));
  }catch(error){console.warn('SEO response unavailable:',error.message);return next();}
 };
}
module.exports={seoMiddleware,inject};