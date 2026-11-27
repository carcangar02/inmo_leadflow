from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import os
import json
import sqlite3

from app.database import init_db, get_db
from app.lead_qualifier import LeadQualifier

app = FastAPI(title="InmoLeadFlow - Consulting Villaviciosa Demo", version="1.2.0")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

qualifier = LeadQualifier()

@app.on_event("startup")
def startup_event():
    # Only seed if properties table is empty
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM properties")
    count = cursor.fetchone()[0]
    conn.close()
    if count == 0:
        init_db()

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ValuationRequest(BaseModel):
    zone: str
    property_type: str
    area_m2: int
    condition: str
    name: str
    phone: str
    email: Optional[str] = None

class VisitRequest(BaseModel):
    property_id: int
    property_title: str
    name: str
    phone: str
    email: Optional[str] = None
    preferred_date: Optional[str] = None
    has_house_to_sell: Optional[str] = "No"
    message: Optional[str] = None

class OwnerLeadRequest(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    operation: str # 'Venta' or 'Alquiler'
    zone: str
    address: Optional[str] = ""
    property_type: str
    area_m2: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    condition: Optional[str] = "Buen estado"
    comments: Optional[str] = ""

class ContactRequest(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    subject: Optional[str] = "Consulta General"
    message: str

# ----------------- WEB PAGES -----------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM properties ORDER BY price DESC")
    properties = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return templates.TemplateResponse(request=request, name="index.html", context={"properties": properties})

@app.get("/propiedad/{property_id}", response_class=HTMLResponse)
async def property_detail(request: Request, property_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM properties WHERE id = ?", (property_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Inmueble no encontrado")
    
    prop = dict(row)
    prop['gallery'] = json.loads(prop.get('gallery_images') or '[]')
    prop['features_list'] = json.loads(prop.get('features') or '[]')
    prop['distribution_dict'] = json.loads(prop.get('distribution') or '{}')
    
    # 3 similar properties for bottom carousel
    cursor.execute("SELECT * FROM properties WHERE id != ? ORDER BY RANDOM() LIMIT 3", (property_id,))
    similar = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    return templates.TemplateResponse(
        request=request, 
        name="property_detail.html", 
        context={"prop": prop, "similar": similar}
    )

@app.get("/vender", response_class=HTMLResponse)
async def vender_page(request: Request):
    return templates.TemplateResponse(request=request, name="vender.html", context={})

@app.get("/alquilar", response_class=HTMLResponse)
async def alquilar_page(request: Request):
    return templates.TemplateResponse(request=request, name="alquilar.html", context={})

@app.get("/quienes-somos", response_class=HTMLResponse)
async def quienes_somos_page(request: Request):
    return templates.TemplateResponse(request=request, name="quienes_somos.html", context={})

@app.get("/contacto", response_class=HTMLResponse)
async def contacto_page(request: Request):
    return templates.TemplateResponse(request=request, name="contacto.html", context={})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads ORDER BY score DESC, created_at DESC")
    leads = [dict(r) for r in cursor.fetchall()]
    
    total_leads = len(leads)
    hot_leads = len([l for l in leads if l['category'] == 'CALIENTE'])
    warm_leads = len([l for l in leads if l['category'] == 'TEMPLADO'])
    cold_leads = len([l for l in leads if l['category'] == 'FRIO'])
    scheduled_visits = len([l for l in leads if l['appointment_date']])
    total_pipeline = sum(l['budget'] for l in leads if l['budget'])
    
    conn.close()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "leads": leads,
            "stats": {
                "total_leads": total_leads,
                "hot_leads": hot_leads,
                "warm_leads": warm_leads,
                "cold_leads": cold_leads,
                "scheduled_visits": scheduled_visits,
                "total_pipeline": total_pipeline
            }
        }
    )

# ----------------- APIS & LEAD CAPTURE -----------------

@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    response = qualifier.process_message(payload.session_id, payload.message)
    return JSONResponse(response)

@app.post("/api/schedule-visit")
async def schedule_visit(payload: VisitRequest):
    """
    Direct visit request from individual property page.
    Automatically classified as HOT lead (CALIENTE).
    """
    session_id = f"vis_{payload.property_id}_{payload.phone.replace(' ', '')[-8:]}"
    has_sale_text = " (Tiene casa que vender antes de comprar)" if payload.has_house_to_sell.lower() in ['si', 'sí', 'yes'] else ""
    summary = (
        f"📅 SOLICITUD DE VISITA PRIVADA para Ref #{payload.property_id} ({payload.property_title}). "
        f"Fecha preferida: {payload.preferred_date or 'Lo antes posible'}.{has_sale_text}"
    )
    
    score = 85 if has_sale_text else 75
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO leads (session_id, name, phone, email, intent, property_type, zone, budget, financing, timeframe, score, category, appointment_date, summary)
    VALUES (?, ?, ?, ?, 'Comprar', 'Inmueble Seleccionado', 'Villaviciosa de Odón', 0, 'Por verificar', ?, ?, 'CALIENTE', ?, ?)
    """, (session_id, payload.name, payload.phone, payload.email, 'Inmediato (< 1 mes)', score, payload.preferred_date or 'Pendiente de confirmación', summary))
    conn.commit()
    conn.close()
    
    return JSONResponse({
        "status": "success",
        "message": "Solicitud de visita agendada correctamente. El equipo comercial de Consulting Inmobiliario te contactará en breve."
    })

@app.post("/api/owner-lead")
async def register_owner_lead(payload: OwnerLeadRequest):
    """
    Captures an owner wanting to sell or rent out their property.
    Highest commercial value (Captación en exclusiva): Score 90-95 (CALIENTE).
    """
    session_id = f"own_{payload.phone.replace(' ', '')[-8:]}"
    summary = (
        f"🔑 CAPTACIÓN DE PROPIETARIO ({payload.operation.upper()}): {payload.property_type} en {payload.zone} ({payload.address}). "
        f"Sup: {payload.area_m2 or 'N/D'} m², Habs: {payload.bedrooms or 'N/D'}, Baños: {payload.bathrooms or 'N/D'}. "
        f"Notas: {payload.comments or 'Sin comentarios adicionales'}"
    )
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO leads (session_id, name, phone, email, intent, property_type, zone, budget, financing, timeframe, score, category, appointment_date, summary)
    VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'Propietario Directo', 'Inmediato (< 1 mes)', 92, 'CALIENTE', 'Visita de Captación Pendiente', ?)
    """, (session_id, payload.name, payload.phone, payload.email, payload.operation, payload.property_type, payload.zone, summary))
    conn.commit()
    conn.close()
    
    return JSONResponse({
        "status": "success",
        "message": "Datos de tu inmueble recibidos. Un asesor experto de Consulting Inmobiliario contactará contigo para preparar tu informe ACM gratuito."
    })

@app.post("/api/contact-message")
async def register_contact_message(payload: ContactRequest):
    session_id = f"cnt_{payload.phone.replace(' ', '')[-8:]}"
    summary = f"📩 MENSAJE WEB [{payload.subject}]: {payload.message}"
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO leads (session_id, name, phone, email, intent, property_type, zone, budget, financing, timeframe, score, category, appointment_date, summary)
    VALUES (?, ?, ?, ?, 'Consulta', 'General', 'Villaviciosa de Odón', 0, 'N/D', 'No especificado', 50, 'TEMPLADO', NULL, ?)
    """, (session_id, payload.name, payload.phone, payload.email, summary))
    conn.commit()
    conn.close()
    
    return JSONResponse({
        "status": "success",
        "message": "Mensaje recibido correctamente. Nos pondremos en contacto contigo lo antes posible."
    })

@app.post("/api/valuation")
async def calculate_valuation(payload: ValuationRequest):
    zone_rates = {
        "El Bosque": 2650,
        "Campodón": 2300,
        "Castillo": 2400,
        "Casco Urbano": 2350
    }
    base_rate = zone_rates.get(payload.zone, 2400)
    
    condition_mult = {
        "Excelente / Lujo": 1.18,
        "Buen estado": 1.00,
        "A reformar": 0.82
    }
    mult = condition_mult.get(payload.condition, 1.0)
    
    estimated_val = int(payload.area_m2 * base_rate * mult)
    min_val = int(estimated_val * 0.94)
    max_val = int(estimated_val * 1.06)
    
    session_id = f"val_{payload.phone.replace(' ', '')[-8:]}"
    summary = (
        f"🔥 SOLICITUD DE TASACIÓN OFICIAL: {payload.property_type} de {payload.area_m2}m² en {payload.zone} "
        f"({payload.condition}). Estimación automática: {min_val:,.0f} € - {max_val:,.0f} €."
    )
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO leads (session_id, name, phone, email, intent, property_type, zone, budget, financing, timeframe, score, category, appointment_date, summary)
    VALUES (?, ?, ?, ?, 'Vender', ?, ?, ?, 'Propietario Directo', 'Inmediato (< 1 mes)', 95, 'CALIENTE', 'Visita de Tasación Solicitada', ?)
    """, (session_id, payload.name, payload.phone, payload.email, payload.property_type, payload.zone, estimated_val, summary))
    conn.commit()
    conn.close()
    
    return JSONResponse({
        "status": "success",
        "estimated_val": estimated_val,
        "min_val": min_val,
        "max_val": max_val,
        "rate_m2": int(base_rate * mult)
    })

@app.get("/api/leads")
async def get_leads():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads ORDER BY score DESC")
    leads = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return JSONResponse({"leads": leads})

@app.post("/api/leads/seed-demo")
async def seed_demo_leads():
    conn = get_db()
    cursor = conn.cursor()
    
    demo_leads = [
        ("demo_hot_1", "Álvaro Mendizábal", "+34 612 345 678", "alvaro.m@gmail.com", "Comprar", "Chalet Independiente", "El Bosque", 1200000, "Fondos propios / Al contado", "Inmediato (< 1 mes)", 95, "CALIENTE", "Mañana 18:00h", "🔥 Comprador VIP con fondos propios. Quiere visitar chalet en El Bosque esta semana."),
        ("demo_hot_2", "Dña. Carmen Velasco", "+34 639 881 223", "carmen.velasco@outlook.es", "Vender", "Chalet Pareado", "Campodón", 650000, "Al contado", "Inmediato (< 1 mes)", 90, "CALIENTE", "Jueves 11:30h", "🔥 Propietaria quiere vender chalet en Campodón por traslado. Requiere tasación presencial."),
        ("demo_warm_1", "Marcos Delgado", "+34 655 412 901", "marcos.d@empresa.com", "Comprar", "Ático", "Casco Urbano", 380000, "Hipoteca concedida", "1 a 3 meses", 65, "TEMPLADO", None, "⚡ Comprador con hipoteca preconcedida para ático en centro de Villaviciosa."),
        ("demo_cold_1", "Usuario Curioso", "+34 600 000 000", "test@test.es", "Alquilar", "Piso", "Casco Urbano", 900, "Pendiente", "Solo estoy mirando", 25, "FRIO", None, "❄️ Búsqueda de alquiler para próximo curso.")
    ]
    
    for lead in demo_leads:
        cursor.execute("""
        INSERT OR REPLACE INTO leads (session_id, name, phone, email, intent, property_type, zone, budget, financing, timeframe, score, category, appointment_date, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, lead)
        
    conn.commit()
    conn.close()
    return JSONResponse({"status": "success", "message": "Demo leads seeded!"})
