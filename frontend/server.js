// Production entry: build with `yarn build`, then PORT=<platform port> node server.js.
require('dotenv').config();
const http=require('http');const path=require('path');const fs=require('fs');
const {seoMiddleware}=require('./seo-middleware');
const build=path.join(__dirname,'build');
if(!process.env.PORT||!process.env.REACT_APP_BACKEND_URL)throw new Error('PORT and REACT_APP_BACKEND_URL are required');
const middleware=seoMiddleware(async()=>fs.readFileSync(path.join(build,'index.html'),'utf8'));
const types={'.js':'application/javascript','.css':'text/css','.webp':'image/webp','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.json':'application/json','.txt':'text/plain','.woff2':'font/woff2'};
http.createServer((req,res)=>middleware(req,res,()=>{
  let pathname;try{pathname=decodeURIComponent(req.url.split('?')[0]);}catch{res.statusCode=400;return res.end('Invalid URL');}
  const file=path.resolve(build,'.'+pathname);
  if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.statusCode=404;return res.end('Not found');}
  res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');
  res.setHeader('X-Content-Type-Options','nosniff');
  res.setHeader('Cache-Control',pathname.startsWith('/static/')?'public, max-age=31536000, immutable':'public, max-age=3600');
  fs.createReadStream(file).pipe(res);
})).listen(Number(process.env.PORT),'0.0.0.0');