import { Link } from 'react-router-dom';
import { ArrowUpRight, Phone, MessageCircle } from 'lucide-react';
import { toast } from 'sonner';
import { useSite, useText, localPath } from '../lib/context';
import { track } from '../lib/api';

export const ContactActions=({context={},id='contact',compact=false,quote=true})=>{
 const {settings,lang}=useSite();const t=useText();
 const message=lang==='en'?`Hello GlennTek, I would like information about ${context.service||context.device||'device repair'}${context.municipality?' in '+context.municipality:''}.`:`Olá GlennTek, gostaria de pedir informações sobre ${context.service||context.device||'reparação do meu equipamento'}${context.municipality?' em '+context.municipality:''}.`;
 const wa=settings.whatsapp?`https://wa.me/${settings.whatsapp.replace(/\D/g,'')}?text=${encodeURIComponent(message+'\n'+window.location.href)}`:null;
 const missing=(e)=>{e.preventDefault();toast.info(t('Este contacto ainda não está disponível. Envie o seu pedido pelo formulário.','This contact is not available yet. Please use the enquiry form.'));document.getElementById('orcamento')?.scrollIntoView({behavior:'smooth'});};
 return <div className={`contact-actions ${compact?'compact':''}`}>
 {quote&&<Link className="btn btn-primary" data-testid={`${id}-quote`} to={localPath('/orcamento',lang)} state={{context}}>{t('Pedir orçamento','Get a quote')}<ArrowUpRight size={17}/></Link>}
 <a className="btn btn-whatsapp" data-testid={`${id}-whatsapp`} href={wa||'#orcamento'} onClick={wa?()=>track('whatsapp_click',context):missing} target={wa?'_blank':undefined} rel="noopener noreferrer"><MessageCircle size={17}/><span>WhatsApp</span></a>
 <a className="btn btn-call" data-testid={`${id}-phone`} href={settings.phone?`tel:${settings.phone}`:'#orcamento'} onClick={settings.phone?()=>track('phone_click',context):missing}><Phone size={16}/><span>{t('Ligar agora','Call now')}</span></a>
 </div>
};