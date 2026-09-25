import { Search } from 'lucide-react';
import { useState } from 'react';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';

export const SeoSettings=({value={},onChange})=>{
 const [page,setPage]=useState('home');
 const routes={home:'Página inicial',reparacoes:'Todas as reparações',marcas:'Marcas',localizacoes:'Localizações','como-funciona':'Como funciona','sobre-nos':'Sobre nós',contactos:'Contactos',blog:'Blog',faq:'Perguntas frequentes',orcamento:'Orçamento',privacidade:'Privacidade',cookies:'Cookies',termos:'Termos'};
 const current=value[page]||{};
 const change=(key,text)=>onChange({...value,[page]:{...current,[key]:text}});
 return <section className="admin-section"><div className="admin-section-title"><h2><Search size={19}/>SEO das páginas principais</h2></div><label className="form-field"><span>Página</span><select data-testid="settings-seo-page" value={page} onChange={e=>setPage(e.target.value)}>{Object.entries(routes).map(([slug,label])=><option key={slug} value={slug}>{label}</option>)}</select></label><div className="settings-grid seo-settings-fields">{[['title','Título SEO (PT)'],['title_en','SEO title (EN)'],['description','Descrição SEO (PT)'],['description_en','SEO description (EN)']].map(([key,label])=><label className="form-field" key={key}><span>{label}</span>{key.startsWith('description')?<Textarea data-testid={`settings-seo-${key}`} value={current[key]||''} onChange={e=>change(key,e.target.value)} maxLength={350} rows={3} placeholder="Deixe vazio para utilizar o texto da página"/>:<Input data-testid={`settings-seo-${key}`} value={current[key]||''} onChange={e=>change(key,e.target.value)} maxLength={180}/>}</label>)}</div><p className="admin-note">Canonicals e hreflang são calculados automaticamente. Os metadados também são incluídos no HTML inicial.</p></section>
};