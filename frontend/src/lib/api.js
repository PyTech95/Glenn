import axios from 'axios';
export const API_URL = process.env.REACT_APP_BACKEND_URL;
export const api = axios.create({baseURL: `${API_URL}/api`,withCredentials:true});
let csrf = '';
export const setCsrf = value => {csrf=value || '';};
api.interceptors.request.use(config=>{if(csrf)config.headers['X-CSRF-Token']=csrf;return config;});
export const errorText = error => {const d=error.response?.data?.detail;return typeof d==='string'?d:Array.isArray(d)?d.map(x=>x.msg.replace('Value error, ','')).join(' · '):'Não foi possível concluir. Tente novamente.';};
export const saveCampaign = () => {
 const params=new URLSearchParams(window.location.search); const data={};
 ['utm_source','utm_medium','utm_campaign','utm_content','utm_term','gclid','fbclid'].forEach(k=>{if(params.get(k))data[k]=params.get(k).slice(0,1000)});
 if(Object.keys(data).length)sessionStorage.setItem('gt-campaign',JSON.stringify(data));
};
export const track = (event,data={}) => {
 let consent={};try{consent=JSON.parse(localStorage.getItem('gt-consent')||'{}')}catch{}
 if(!consent.analytics && !consent.marketing)return;
 window.dataLayer=window.dataLayer||[];window.dataLayer.push({event,...data});
 if(consent.analytics && window.gtag)window.gtag('event',event,data);
 if(consent.marketing && window.fbq)window.fbq('trackCustom',event,data);
};