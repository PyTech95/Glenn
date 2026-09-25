import { useEffect,useState,lazy,Suspense } from 'react';
import { BrowserRouter,Routes,Route,useLocation,Link } from 'react-router-dom';
import { Toaster } from './components/ui/sonner';
import { Loader2 } from 'lucide-react';
import { SiteContext } from './lib/context';
import { api,saveCampaign } from './lib/api';
import { Header,Footer,MobileBar,Logo } from './components/Layout';
import { CookieConsent } from './components/CookieConsent';
import { ContactActions } from './components/ContactActions';
import { SEO } from './components/SEO';
import Home from './pages/Home';
import './App.css';
import './refinements.css';
const StaticPages=lazy(()=>import('./pages/StaticPages'));
const ContentPage=lazy(()=>import('./pages/ContentPage'));
const AdminApp=lazy(()=>import('./admin/AdminApp'));
const Loading=()=> <div className="page-loading" data-testid="page-loading"><Loader2 size={28} className="spin"/></div>;
function Site(){
 const location=useLocation();const lang=location.pathname==='/en'||location.pathname.startsWith('/en/')?'en':'pt';const [site,setSite]=useState(null);const [error,setError]=useState(false);const isAdmin=location.pathname.startsWith('/admin');const campaign=location.pathname.includes('/campanhas/');
 useEffect(()=>{const load=()=>api.get('/site').then(r=>setSite(r.data)).catch(()=>setError(true));load();window.addEventListener('site-updated',load);return()=>window.removeEventListener('site-updated',load)},[]);
 useEffect(()=>{window.scrollTo(0,0);saveCampaign()},[location.pathname,location.search]);
 if(error&&!site)return <div className="error-page"><h1 data-testid="site-load-error">Glenntek</h1><p>Não foi possível carregar o website. / Unable to load the website.</p><button className="btn btn-primary" data-testid="site-retry" onClick={()=>window.location.reload()}>Tentar novamente / Retry</button></div>;
 if(!site)return <Loading/>;
 const staticRoutes=['reparacoes','marcas','localizacoes','como-funciona','sobre-nos','blog','faq','contactos','orcamento','privacidade','cookies','termos'];
 const currentPage=site.pages.find(p=>'/'+p.slug===location.pathname.replace(/^\/en/,'').replace(/\/$/,''));
 const contactContext=Object.fromEntries(['service','device','brand','model','district','municipality'].map(k=>[k,currentPage?.[k]||'']));
 return (
   <SiteContext.Provider value={{...site,lang}}>
     <SEO/>
     {!isAdmin && (campaign ? (
       <div className="container campaign-header">
         <Link to={lang==='en'?'/en/':'/'} data-testid="campaign-logo"><Logo/></Link>
         <ContactActions id="campaign-header" quote={false}/>
       </div>
     ) : <Header/>)}
     <main id="main-content">
       <Suspense fallback={<Loading/>}>
         <Routes>
           <Route path="/admin/*" element={<AdminApp/>}/>
           {['','/en'].flatMap(prefix=>[
             <Route path={prefix+'/'} key={prefix+'home'} element={<Home/>}/>,
             ...staticRoutes.map(type=>(
               <Route path={`${prefix}/${type}`} key={`${prefix}/${type}`} element={<StaticPages type={type}/>}/>
             ))
           ])}
           <Route path="*" element={<ContentPage/>}/>
         </Routes>
       </Suspense>
     </main>
     {!isAdmin && <><Footer/><MobileBar context={contactContext}/><CookieConsent/></>}
     <Toaster position="top-right" richColors closeButton/>
   </SiteContext.Provider>
 );
}
export default function App(){return <BrowserRouter><Site/></BrowserRouter>}