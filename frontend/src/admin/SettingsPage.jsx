import { useState,useEffect } from 'react';
import { Save,Loader2,Phone,Building2,Mail,BarChart3,ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import { api,errorText } from '../lib/api';
import { Input } from '../components/ui/input';
import { AdminHeading } from './Dashboard';
import { SeoSettings } from './SeoSettings';

export default function SettingsPage(){
 const [form,setForm]=useState(null);const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 useEffect(()=>{api.get('/admin/settings').then(r=>setForm(r.data)).catch(e=>setError(errorText(e)))},[]);
 const set=(k,v)=>setForm(f=>({...f,[k]:v}));
 const field=(k,label,placeholder='',type='text')=>(
  <label className="form-field" key={k}><span>{label}</span><Input data-testid={`settings-${k}`} value={form[k]??''} type={type} placeholder={placeholder} onChange={e=>set(k,type==='number'?Number(e.target.value):e.target.value)}/></label>
 );
 const save=async e=>{
  e.preventDefault();setBusy(true);setError('');
  try{const data={...form};['email','admin_email','privacy_contact'].forEach(k=>{if(!data[k])data[k]=null});await api.put('/admin/settings',data);toast.success('Configurações guardadas');window.dispatchEvent(new Event('site-updated'))}
  catch(err){setError(errorText(err))}finally{setBusy(false)}
 };
 if(!form)return error?<p className="form-error" data-testid="settings-load-error">{error}</p>:<Loader2 className="spin"/>;
 return <>
  <AdminHeading title="O essencial, bem definido." description="Contactos reais, dados do negócio e integrações."/>
  <form className="settings-form" onSubmit={save}>
   <section className="admin-section">
    <div className="admin-section-title"><h2><Building2 size={19}/>Identidade do negócio</h2></div>
    <div className="settings-grid">{field('business_name','Nome comercial')}{field('legal_name','Nome da entidade legal')}{field('tax_id','NIF')}{field('address','Morada oficial')}{field('business_hours','Horário de funcionamento')}</div>
    <label className="settings-check"><input data-testid="settings-verified_business" type="checkbox" checked={form.verified_business} onChange={e=>set('verified_business',e.target.checked)}/><span>Confirmei a identidade e os dados reais do negócio.<small>Permite indexar páginas elegíveis. As verificações de cada serviço/localização mantêm-se obrigatórias.</small></span></label>
   </section>
   <section className="admin-section">
    <div className="admin-section-title"><h2><Phone size={19}/>Contactos do website</h2></div>
    <div className="settings-grid">{field('phone','Telefone internacional','+351…')}{field('whatsapp','WhatsApp internacional','+351…')}{field('email','Email público','', 'email')}{field('google_reviews_url','Página de avaliações Google (HTTPS)')}</div>
    <p className="admin-note">Os números aparecem automaticamente nos botões e nas mensagens de WhatsApp. Não são apresentados números fictícios.</p>
   </section>
   <section className="admin-section">
    <div className="admin-section-title"><h2><Mail size={19}/>Notificações de pedidos</h2></div>
    <div className="settings-grid">{field('admin_email','Email destinatário (seu endereço real)','', 'email')}</div>
    <label className="settings-check"><input data-testid="settings-email_notifications" type="checkbox" checked={form.email_notifications} onChange={e=>set('email_notifications',e.target.checked)}/><span>Enviar um email quando chega um novo pedido.<small>Envio transacional gerido. O pedido é sempre guardado, mesmo que o envio de email falhe.</small></span></label>
   </section>
   <section className="admin-section">
    <div className="admin-section-title"><h2><BarChart3 size={19}/>Análise e campanhas</h2></div>
    <div className="settings-grid">{field('ga4_id','Google Analytics 4','G-…')}{field('gtm_id','Google Tag Manager','GTM-…')}{field('ads_id','Google Ads','AW-…')}{field('ads_conversion_label','Etiqueta de conversão Google Ads')}{field('meta_pixel_id','Meta Pixel ID')}{field('search_console','Código de verificação Search Console')}</div>
    <div className="info-note">Os rastreadores só carregam após consentimento. O Tag Manager exige análise e marketing aceites; configure os seus tags para respeitar o consentimento. Evite instalar o mesmo rastreador diretamente e no Tag Manager.</div>
   </section>
   <SeoSettings value={form.static_seo||{}} onChange={value=>set('static_seo',value)}/>
   <section className="admin-section">
    <div className="admin-section-title"><h2><ShieldCheck size={19}/>Privacidade e conservação</h2></div>
    <div className="settings-grid">{field('privacy_contact','Email para assuntos de privacidade','', 'email')}{field('retention_months','Conservação de pedidos sem contrato (meses)','', 'number')}</div>
    <p className="admin-note">Reveja e elimine pedidos antigos no painel. A conservação não configura uma eliminação automática. Complete a entidade legal e confirme os textos de privacidade antes de abrir ao público.</p>
   </section>
   {error&&<p className="form-error" data-testid="settings-error">{error}</p>}
   <div className="settings-save-bar"><span>As alterações aplicam-se a todo o website.</span><button className="btn btn-primary" data-testid="settings-save" disabled={busy}>{busy?<Loader2 className="spin" size={16}/>:<Save size={16}/>}Guardar configurações</button></div>
  </form>
 </>
}