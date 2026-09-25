import { createContext, useContext } from 'react';
export const SiteContext=createContext({settings:{},pages:[],districts:[],lang:'pt'});
export const useSite=()=>useContext(SiteContext);
export const useText=()=>{const {lang}=useSite();return (pt,en)=>lang==='en'?en:pt;};
export const localPath=(path,lang)=>`${lang==='en'?'/en':''}${path==='/'?'/':path}`;
export const pageText=(page,key,lang)=>lang==='en'?(page[key+'_en']||page[key]):page[key];