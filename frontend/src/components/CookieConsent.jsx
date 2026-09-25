import { useState,useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, X } from 'lucide-react';
import { useSite,useText,localPath } from '../lib/context';

const read=()=>{try{return JSON.parse(localStorage.getItem('gt-consent'))}catch{return null}};
export const CookieConsent=()=>{
 const {settings,lang}=useSite();const t=useText();const [consent,setConsent]=useState(read);const [open,setOpen]=useState(!read());const [details,setDetails]=useState(false);const [analytics,setAnalytics]=useState(consent?.analytics||false);const [marketing,setMarketing]=useState(consent?.marketing||false);
 useEffect(()=>{const handle=()=>{setOpen(true);setDetails(true)};window.addEventListener('open-cookie-settings',handle);return()=>window.removeEventListener('open-cookie-settings',handle)},[]);
 useEffect(()=>{
  if(!consent)return;
  const script=(id,src)=>{if(document.getElementById(id))return;const el=document.createElement('script');el.id=id;el.src=src;el.async=true;document.head.appendChild(el)};
  window.dataLayer=window.dataLayer||[];
  window.gtag=window.gtag||function(){window.dataLayer.push(arguments)};
  window.gtag('consent','default',{analytics_storage:'denied',ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied'});
  window.gtag('consent','update',{analytics_storage:consent.analytics?'granted':'denied',ad_storage:consent.marketing?'granted':'denied',ad_user_data:consent.marketing?'granted':'denied',ad_personalization:consent.marketing?'granted':'denied'});
  const googleId=(consent.analytics&&settings.ga4_id)||(consent.marketing&&settings.ads_id);
  if(googleId){script('gt-google-tag',`https://www.googletagmanager.com/gtag/js?id=${googleId}`);window.gtag('js',new Date());if(consent.analytics&&settings.ga4_id)window.gtag('config',settings.ga4_id);if(consent.marketing&&settings.ads_id)window.gtag('config',settings.ads_id)}
  if(consent.analytics&&consent.marketing&&settings.gtm_id){window.dataLayer.push({'gtm.start':Date.now(),event:'gtm.js'});script('gt-tag-manager',`https://www.googletagmanager.com/gtm.js?id=${settings.gtm_id}`)}
  if(consent.marketing&&settings.meta_pixel_id){if(!window.fbq){const f=function(){f.callMethod?f.callMethod.apply(f,arguments):f.queue.push(arguments)};f.queue=[];f.loaded=true;f.version='2.0';window.fbq=f;script('gt-meta-pixel','https://connect.facebook.net/en_US/fbevents.js');f('init',settings.meta_pixel_id);f('track','PageView')}}
 },[consent,settings]);
 const save=(a,m)=>{const previous=consent;const value={necessary:true,analytics:a,marketing:m,date:new Date().toISOString(),version:1};localStorage.setItem('gt-consent',JSON.stringify(value));setConsent(value);setOpen(false);if((previous?.analytics&&!a)||(previous?.marketing&&!m)){document.cookie.split(';').forEach(c=>{const name=c.split('=')[0].trim();if(/^(_ga|_gid|_gcl|_fbp|_fbc)/.test(name)){document.cookie=`${name}=; Max-Age=0; path=/`;document.cookie=`${name}=; Max-Age=0; path=/; domain=.${window.location.hostname}`}});window.location.reload()}};
 if(!open)return null;
 return <aside className="cookie-consent" data-testid="cookie-banner" aria-label={t('Preferências de cookies','Cookie preferences')}><div className="cookie-heading"><ShieldCheck size={21}/><strong>{t('A sua privacidade importa.','Your privacy matters.')}</strong>{consent&&<button aria-label="Fechar" data-testid="cookie-close" onClick={()=>setOpen(false)}><X size={18}/></button>}</div><p>{t('Usamos cookies essenciais. Os de análise e marketing só são ativados com a sua autorização.','We use essential cookies. Analytics and marketing only activate with your permission.')} <Link data-testid="cookie-policy-link" to={localPath('/cookies',lang)}>{t('Saber mais','Learn more')}</Link></p>{details&&<div className="cookie-toggles"><label><input data-testid="cookie-analytics-toggle" type="checkbox" checked={analytics} onChange={e=>setAnalytics(e.target.checked)}/>{t('Análise de utilização','Usage analytics')}</label><label><input data-testid="cookie-marketing-toggle" type="checkbox" checked={marketing} onChange={e=>setMarketing(e.target.checked)}/>{t('Marketing','Marketing')}</label></div>}<div className="cookie-buttons"><button className="btn btn-outline" data-testid="cookie-reject" onClick={()=>save(false,false)}>{t('Só essenciais','Essential only')}</button><button className="btn btn-primary" data-testid="cookie-accept" onClick={()=>details?save(analytics,marketing):save(true,true)}>{details?t('Guardar escolhas','Save choices'):t('Aceitar todos','Accept all')}</button></div>{!details&&<button className="cookie-customize" data-testid="cookie-customize" onClick={()=>setDetails(true)}>{t('Personalizar preferências','Customise preferences')}</button>}</aside>
};