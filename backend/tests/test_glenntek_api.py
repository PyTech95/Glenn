import os
import time
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient


# Auth, leads, CMS and SEO critical-path API regression tests
load_dotenv(Path('/app/frontend/.env'))
load_dotenv(Path('/app/backend/.env'))

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
FRONTEND_ORIGIN = os.environ.get('FRONTEND_ORIGIN', '')
ADMIN_SETUP_TOKEN = os.environ.get('ADMIN_SETUP_TOKEN', '')
MONGO_URL = os.environ.get('MONGO_URL', '')
DB_NAME = os.environ.get('DB_NAME', '')

TEST_ADMIN_EMAIL = 'admin@glenntek.com'
TEST_ADMIN_PASSWORD = 'GlennTek@2026!'
TEST_IDS = {'lead_id': None, 'page_id': None, 'generated_page_id': None}


@pytest.fixture(scope='session', autouse=True)
def _validate_env():
    assert BASE_URL, 'REACT_APP_BACKEND_URL is required'
    assert FRONTEND_ORIGIN, 'FRONTEND_ORIGIN is required'
    assert ADMIN_SETUP_TOKEN, 'ADMIN_SETUP_TOKEN is required'


@pytest.fixture(scope='session')
def anon_client():
    s = requests.Session()
    s.headers.update({'Content-Type': 'application/json'})
    return s


@pytest.fixture(scope='session')
def admin_client():
    s = requests.Session()
    s.headers.update({'Content-Type': 'application/json', 'Origin': FRONTEND_ORIGIN})
    return s


@pytest.fixture(scope='session', autouse=True)
def cleanup_test_data():
    yield
    if not MONGO_URL or not DB_NAME:
        return
    mongo = MongoClient(MONGO_URL)
    db = mongo[DB_NAME]
    db.leads.delete_many({'name': {'$regex': '^TEST_'}})
    db.pages.delete_many({'slug': {'$regex': '^test-'}})
    db.pages.delete_many({'title': {'$regex': '^TEST_'}})
    db.sessions.delete_many({'admin_id': 'owner'})
    mongo.close()


def test_01_public_health_and_site(anon_client):
    health = anon_client.get(f'{BASE_URL}/api/health', timeout=20)
    assert health.status_code == 200
    assert health.json().get('status') == 'ok'

    site = anon_client.get(f'{BASE_URL}/api/site', timeout=20)
    assert site.status_code == 200
    data = site.json()
    assert isinstance(data.get('pages'), list)
    assert 'settings' in data


def test_02_admin_status_and_password_policy(anon_client):
    status = anon_client.get(f'{BASE_URL}/api/auth/status', timeout=20)
    assert status.status_code == 200
    assert 'setup_required' in status.json()

    short_pass = {
        'email': TEST_ADMIN_EMAIL,
        'password': 'shortpass',
        'setup_token': ADMIN_SETUP_TOKEN,
    }
    r = anon_client.post(
        f'{BASE_URL}/api/auth/setup',
        json=short_pass,
        headers={'Origin': FRONTEND_ORIGIN},
        timeout=20,
    )
    assert r.status_code == 422


def test_03_admin_setup_login_logout_and_me(admin_client):
    payload = {
        'email': TEST_ADMIN_EMAIL,
        'password': TEST_ADMIN_PASSWORD,
        'setup_token': ADMIN_SETUP_TOKEN,
    }
    setup = admin_client.post(f'{BASE_URL}/api/auth/setup', json=payload, timeout=20)
    assert setup.status_code in (200, 409)

    second_setup = admin_client.post(f'{BASE_URL}/api/auth/setup', json=payload, timeout=20)
    assert second_setup.status_code == 409

    login = admin_client.post(f'{BASE_URL}/api/auth/login', json=payload, timeout=20)
    assert login.status_code == 200
    body = login.json()
    assert body.get('email') == TEST_ADMIN_EMAIL
    assert isinstance(body.get('csrf'), str) and len(body['csrf']) > 10
    admin_client.headers['X-CSRF-Token'] = body['csrf']

    me = admin_client.get(f'{BASE_URL}/api/auth/me', timeout=20)
    assert me.status_code == 200
    assert me.json().get('email') == TEST_ADMIN_EMAIL

    logout = admin_client.post(f'{BASE_URL}/api/auth/logout', timeout=20)
    assert logout.status_code == 200
    me_after = admin_client.get(f'{BASE_URL}/api/auth/me', timeout=20)
    assert me_after.status_code == 401

    relogin = admin_client.post(f'{BASE_URL}/api/auth/login', json=payload, timeout=20)
    assert relogin.status_code == 200
    admin_client.headers['X-CSRF-Token'] = relogin.json()['csrf']


def test_04_admin_endpoints_reject_anonymous(anon_client):
    endpoints = [
        ('GET', '/api/admin/settings', None),
        ('PUT', '/api/admin/settings', {'business_name': 'GlennTek'}),
        ('GET', '/api/admin/pages', None),
        ('POST', '/api/admin/pages', {'title': 'x'}),
        ('POST', '/api/admin/generate', {'service_id': 'x', 'location_id': 'y'}),
        ('GET', '/api/admin/leads', None),
        ('GET', '/api/admin/leads/export', None),
        ('PATCH', '/api/admin/leads/non-existing', {'status': 'new', 'notes': ''}),
        ('DELETE', '/api/admin/leads/non-existing', None),
        ('POST', '/api/admin/leads/non-existing/notify', None),
        ('GET', '/api/admin/stats', None),
    ]
    for method, path, payload in endpoints:
        r = anon_client.request(method, f'{BASE_URL}{path}', json=payload, timeout=20)
        assert r.status_code == 401


def test_05_csrf_and_origin_protection_for_mutations(admin_client):
    current = admin_client.get(f'{BASE_URL}/api/admin/settings', timeout=20)
    assert current.status_code == 200
    settings = current.json()

    without_csrf = admin_client.put(
        f'{BASE_URL}/api/admin/settings',
        json=settings,
        headers={'Origin': FRONTEND_ORIGIN, 'X-CSRF-Token': ''},
        timeout=20,
    )
    assert without_csrf.status_code == 403

    wrong_origin = admin_client.put(
        f'{BASE_URL}/api/admin/settings',
        json=settings,
        headers={'Origin': 'https://invalid-origin.example', 'X-CSRF-Token': admin_client.headers['X-CSRF-Token']},
        timeout=20,
    )
    assert wrong_origin.status_code == 403


def test_06_settings_validation(admin_client):
    settings = admin_client.get(f'{BASE_URL}/api/admin/settings', timeout=20)
    assert settings.status_code == 200
    body = settings.json()

    bad_phone = {**body, 'phone': '912345678'}
    bad_phone_res = admin_client.put(f'{BASE_URL}/api/admin/settings', json=bad_phone, timeout=20)
    assert bad_phone_res.status_code == 422

    bad_email_notify = {**body, 'email_notifications': True, 'admin_email': None}
    bad_notify_res = admin_client.put(f'{BASE_URL}/api/admin/settings', json=bad_email_notify, timeout=20)
    assert bad_notify_res.status_code == 422


def test_07_lead_create_persistence_and_validation(admin_client, anon_client):
    lead = {
        'name': 'TEST_Lead User',
        'phone': '+351912345678',
        'email': 'test.lead@example.com',
        'whatsapp': '+351912345678',
        'district': 'Lisboa',
        'municipality': 'Lisboa',
        'postal_code': '1000-100',
        'device': 'iPhone',
        'brand': 'Apple',
        'model': 'iPhone 15',
        'issue': 'Ecrã',
        'description': 'TEST_ cracked screen',
        'preferred_contact': 'email',
        'consent': True,
        'marketing_consent': False,
        'website': '',
        'language': 'pt',
        'context': {
            'service': 'Ecrã',
            'device': 'iPhone',
            'district': 'Lisboa',
            'municipality': 'Lisboa',
            'utm_source': 'google',
            'utm_medium': 'cpc',
            'utm_campaign': 'test_campaign',
            'gclid': 'TEST_GCLID_123',
            'random_key_should_be_removed': 'x',
        },
    }
    created = anon_client.post(f'{BASE_URL}/api/leads', json=lead, timeout=20)
    assert created.status_code == 201
    receipt = created.json()
    assert receipt.get('status') == 'received'
    TEST_IDS['lead_id'] = receipt['id']

    time.sleep(0.7)
    leads = admin_client.get(f'{BASE_URL}/api/admin/leads', params={'search': 'TEST_Lead User'}, timeout=20)
    assert leads.status_code == 200
    items = leads.json().get('items', [])
    assert any(i.get('id') == TEST_IDS['lead_id'] for i in items)
    selected = next(i for i in items if i['id'] == TEST_IDS['lead_id'])
    assert selected.get('context', {}).get('gclid') == 'TEST_GCLID_123'
    assert 'random_key_should_be_removed' not in selected.get('context', {})

    invalid = {**lead, 'email': None, 'context': {}, 'name': 'TEST_Invalid Lead'}
    bad = anon_client.post(f'{BASE_URL}/api/leads', json=invalid, timeout=20)
    assert bad.status_code == 422


def test_08_leads_update_export_delete(admin_client):
    assert TEST_IDS['lead_id'], 'Lead should be created first'
    update = admin_client.patch(
        f"{BASE_URL}/api/admin/leads/{TEST_IDS['lead_id']}",
        json={'status': 'quote_sent', 'notes': 'TEST_note'},
        timeout=20,
    )
    assert update.status_code == 200

    listing = admin_client.get(f'{BASE_URL}/api/admin/leads', params={'search': 'TEST_Lead User'}, timeout=20)
    assert listing.status_code == 200
    lead = next(i for i in listing.json().get('items', []) if i['id'] == TEST_IDS['lead_id'])
    assert lead.get('status') == 'quote_sent'
    assert lead.get('notes') == 'TEST_note'

    export_res = admin_client.get(f'{BASE_URL}/api/admin/leads/export', timeout=20)
    assert export_res.status_code == 200
    assert 'text/csv' in export_res.headers.get('content-type', '')
    assert 'id,name,phone' in export_res.text

    delete = admin_client.delete(f"{BASE_URL}/api/admin/leads/{TEST_IDS['lead_id']}", timeout=20)
    assert delete.status_code == 200


def test_09_location_search_api(anon_client):
    lisboa = anon_client.get(f'{BASE_URL}/api/locations/search', params={'q': 'Lisboa'}, timeout=20)
    assert lisboa.status_code == 200
    assert any(r.get('city') == 'Lisboa' for r in lisboa.json().get('results', []))

    porto = anon_client.get(f'{BASE_URL}/api/locations/search', params={'q': 'Porto'}, timeout=20)
    assert porto.status_code == 200
    assert any('Porto' in (r.get('city') or '') for r in porto.json().get('results', []))

    postcode = anon_client.get(f'{BASE_URL}/api/locations/search', params={'q': '1000'}, timeout=20)
    assert postcode.status_code == 200
    assert len(postcode.json().get('results', [])) > 0

    unknown = anon_client.get(f'{BASE_URL}/api/locations/search', params={'q': 'ZZZZUnknownCity'}, timeout=20)
    assert unknown.status_code == 200
    assert unknown.json().get('results') == []


def test_10_cms_crud_rules_and_generation(admin_client):
    suffix = str(uuid.uuid4())[:8]
    slug = f'test-service-{suffix}'
    payload = {
        'title': f'TEST_Service {suffix}',
        'title_en': f'TEST_Service EN {suffix}',
        'slug': slug,
        'kind': 'service',
        'status': 'draft',
        'noindex': True,
        'verified': False,
        'intro': 'TEST intro',
        'intro_en': 'TEST intro en',
        'content': 'TEST content',
        'content_en': 'TEST content en',
        'seo_title': 'TEST seo',
        'seo_description': 'TEST seo desc',
        'seo_title_en': 'TEST seo en',
        'seo_description_en': 'TEST seo desc en',
        'service': 'iPhone',
        'device': 'iPhone',
        'brand': 'Apple',
        'model': 'iPhone 15',
        'district': '',
        'municipality': '',
        'category': 'test',
        'coverage': '',
        'service_method': '',
        'nearby': [],
        'faqs': [],
        'physical': False,
        'address': '',
        'hours': '',
        'maps_url': '',
        'phone': '',
        'image': '/images/repair-hero.webp',
        'campaign_type': '',
        'postal_prefixes': [],
        'review_author': '',
        'rating': None,
        'source_url': '',
    }
    created = admin_client.post(f'{BASE_URL}/api/admin/pages', json=payload, timeout=20)
    assert created.status_code == 201
    TEST_IDS['page_id'] = created.json()['id']

    duplicate = admin_client.post(f'{BASE_URL}/api/admin/pages', json=payload, timeout=20)
    assert duplicate.status_code == 409

    draft_public = admin_client.get(f'{BASE_URL}/api/pages/{slug}', timeout=20)
    assert draft_public.status_code == 404

    reserved_slug = {**payload, 'slug': 'admin', 'title': 'TEST reserved'}
    reserved_res = admin_client.post(f'{BASE_URL}/api/admin/pages', json=reserved_slug, timeout=20)
    assert reserved_res.status_code == 422

    bad_brand = {**payload, 'slug': f'test-brand-{suffix}', 'kind': 'brand', 'status': 'published'}
    bad_brand_res = admin_client.post(f'{BASE_URL}/api/admin/pages', json=bad_brand, timeout=20)
    assert bad_brand_res.status_code == 422

    pages = admin_client.get(f'{BASE_URL}/api/admin/pages', timeout=20)
    assert pages.status_code == 200
    all_pages = pages.json()
    service = next((p for p in all_pages if p.get('kind') == 'service'), None)
    location = next((p for p in all_pages if p.get('kind') in ['municipality', 'location', 'service_area']), None)
    assert service and location

    generated = admin_client.post(
        f'{BASE_URL}/api/admin/generate',
        json={'service_id': service['id'], 'location_id': location['id']},
        timeout=20,
    )
    assert generated.status_code == 201
    TEST_IDS['generated_page_id'] = generated.json()['id']
    assert generated.json().get('status') == 'draft'
    assert generated.json().get('noindex') is True


def test_11_admin_stats_and_seo_document(admin_client, anon_client):
    stats = admin_client.get(f'{BASE_URL}/api/admin/stats', timeout=20)
    assert stats.status_code == 200
    data = stats.json()
    assert 'total_leads' in data and 'statuses' in data

    seo_doc = anon_client.get(f'{BASE_URL}/api/seo/document', params={'path': '/reparacao-iphone'}, timeout=20)
    assert seo_doc.status_code == 200
    seo = seo_doc.json().get('meta', {})
    assert isinstance(seo.get('canonical'), str)
    assert seo.get('lang') in ['pt-PT', 'en']


def test_12_raw_html_robots_and_sitemaps(anon_client):
    home = anon_client.get(f'{BASE_URL}/', timeout=20)
    assert home.status_code == 200
    assert '<h1>' in home.text
    assert 'application/ld+json' in home.text

    page = anon_client.get(f'{BASE_URL}/reparacao-iphone/', timeout=20)
    assert page.status_code == 200
    assert '<title>' in page.text and '<meta name="description"' in page.text

    nf = anon_client.get(f'{BASE_URL}/this-page-should-not-exist', timeout=20)
    assert nf.status_code == 404

    robots = anon_client.get(f'{BASE_URL}/robots.txt', timeout=20)
    assert robots.status_code == 200
    assert 'Sitemap:' in robots.text

    sitemap_index = anon_client.get(f'{BASE_URL}/sitemap.xml', timeout=20)
    assert sitemap_index.status_code == 200
    assert '<sitemapindex' in sitemap_index.text

    for name in ['services', 'locations', 'service-locations', 'blog']:
        sm = anon_client.get(f'{BASE_URL}/sitemap-{name}.xml', timeout=20)
        assert sm.status_code == 200
        assert '<urlset' in sm.text
