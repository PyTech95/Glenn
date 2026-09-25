import re
from typing import Literal
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator

class LeadInput(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=7, max_length=24)
    email: EmailStr | None = None
    whatsapp: str = Field(default='', max_length=24)
    district: str = Field(default='', max_length=80)
    municipality: str = Field(default='', max_length=100)
    postal_code: str = Field(default='', max_length=8)
    device: str = Field(min_length=2, max_length=80)
    brand: str = Field(default='', max_length=80)
    model: str = Field(default='', max_length=100)
    issue: str = Field(min_length=2, max_length=150)
    description: str = Field(default='', max_length=4000)
    preferred_contact: Literal['whatsapp','phone','email'] = 'whatsapp'
    consent: bool
    marketing_consent: bool = False
    website: str = Field(default='', max_length=200)
    language: Literal['pt','en'] = 'pt'
    context: dict[str, str] = Field(default_factory=dict)

    @field_validator('phone','whatsapp')
    @classmethod
    def phone_valid(cls, v):
        if v and not re.fullmatch(r'\+?[\d\s()\-]{7,24}', v):
            raise ValueError('Número de telefone inválido')
        return v.strip()

    @field_validator('postal_code')
    @classmethod
    def postal_valid(cls, v):
        if v and not re.fullmatch(r'\d{4}-\d{3}', v):
            raise ValueError('Use o formato 0000-000')
        return v

    @model_validator(mode='after')
    def check_consent(self):
        if not self.consent:
            raise ValueError('É necessário aceitar a política de privacidade')
        if self.preferred_contact == 'email' and not self.email:
            raise ValueError('Indique o email para este método de contacto')
        if len(self.context) > 20 or any(len(v) > 2000 for v in self.context.values()):
            raise ValueError('Contexto inválido')
        return self

class LeadUpdate(BaseModel):
    status: Literal['new','contacted','quote_sent','booked','completed','lost']
    notes: str = Field(default='', max_length=10000)

class PageInput(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    title_en: str = Field(default='', max_length=180)
    slug: str = Field(min_length=1, max_length=220, pattern=r'^[a-z0-9]+(?:[\-/][a-z0-9]+)*$')
    kind: Literal['service','repair','brand','model','device','district','municipality','location','service_area','service_location','blog','campaign','faq','review']
    status: Literal['draft','published'] = 'draft'
    noindex: bool = True
    verified: bool = False
    intro: str = Field(default='', max_length=3000)
    intro_en: str = Field(default='', max_length=3000)
    content: str = Field(default='', max_length=30000)
    content_en: str = Field(default='', max_length=30000)
    seo_title: str = Field(default='', max_length=180)
    seo_description: str = Field(default='', max_length=350)
    seo_title_en: str = Field(default='', max_length=180)
    seo_description_en: str = Field(default='', max_length=350)
    service: str = Field(default='', max_length=100)
    device: str = Field(default='', max_length=100)
    brand: str = Field(default='', max_length=100)
    model: str = Field(default='', max_length=100)
    district: str = Field(default='', max_length=100)
    municipality: str = Field(default='', max_length=100)
    category: str = Field(default='', max_length=100)
    coverage: str = Field(default='', max_length=3000)
    service_method: str = Field(default='', max_length=1000)
    nearby: list[str] = Field(default_factory=list, max_length=30)
    faqs: list[dict[str,str]] = Field(default_factory=list, max_length=30)
    physical: bool = False
    address: str = Field(default='', max_length=300)
    hours: str = Field(default='', max_length=500)
    maps_url: str = Field(default='', max_length=500)
    phone: str = Field(default='', max_length=30)
    image: str = Field(default='', max_length=1000)
    campaign_type: Literal['','google','meta'] = ''
    postal_prefixes: list[str] = Field(default_factory=list, max_length=100)
    review_author: str = Field(default='', max_length=100)
    rating: int | None = Field(default=None, ge=1, le=5)
    source_url: str = Field(default='', max_length=1000)

    @field_validator('image','maps_url','source_url')
    @classmethod
    def safe_url(cls, v):
        if v and not (v.startswith('https://') or (v.startswith('/images/') and '..' not in v)):
            raise ValueError('Use um endereço HTTPS válido')
        return v

class SettingsInput(BaseModel):
    business_name: str = Field(default='GlennTek', min_length=2, max_length=100)
    legal_name: str = Field(default='', max_length=150)
    tax_id: str = Field(default='', max_length=30)
    phone: str = Field(default='', max_length=24)
    whatsapp: str = Field(default='', max_length=24)
    email: EmailStr | None = None
    admin_email: EmailStr | None = None
    address: str = Field(default='', max_length=300)
    business_hours: str = Field(default='', max_length=500)
    verified_business: bool = False
    ga4_id: str = Field(default='', pattern=r'^(G-[A-Z0-9]+)?$')
    gtm_id: str = Field(default='', pattern=r'^(GTM-[A-Z0-9]+)?$')
    ads_id: str = Field(default='', pattern=r'^(AW-\d+)?$')
    ads_conversion_label: str = Field(default='', max_length=100, pattern=r'^[a-zA-Z0-9_-]*$')
    meta_pixel_id: str = Field(default='', pattern=r'^\d*$')
    search_console: str = Field(default='', max_length=200, pattern=r'^[a-zA-Z0-9_-]*$')
    google_reviews_url: str = Field(default='', max_length=500)
    privacy_contact: EmailStr | None = None
    retention_months: int = Field(default=12, ge=1, le=120)
    email_notifications: bool = False
    static_seo: dict[str, dict[str,str]] = Field(default_factory=dict)

    @field_validator('static_seo')
    @classmethod
    def seo_limits(cls, v):
        if len(v)>20 or any(len(key)>100 or len(fields)>4 or any(len(text)>500 for text in fields.values()) for key,fields in v.items()):
            raise ValueError('Métadados SEO inválidos')
        return v

    @field_validator('phone','whatsapp')
    @classmethod
    def contact_valid(cls,v):
        if v and not re.fullmatch(r'\+[1-9]\d{7,14}',v):
            raise ValueError('Use o formato internacional, por exemplo +351 seguido do número')
        return v

    @model_validator(mode='after')
    def email_ready(self):
        if self.email_notifications and not self.admin_email:
            raise ValueError('Indique o email destinatário das notificações')
        return self