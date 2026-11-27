import json
import re
from app.database import get_db

class LeadQualifier:
    def __init__(self):
        pass

    def get_or_create_lead(self, session_id: str):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if not row:
            cursor.execute("""
            INSERT INTO leads (session_id, category, score, created_at, updated_at)
            VALUES (?, 'FRIO', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (session_id,))
            conn.commit()
            cursor.execute("SELECT * FROM leads WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
        conn.close()
        return dict(row)

    def update_lead(self, session_id: str, **kwargs):
        conn = get_db()
        cursor = conn.cursor()
        fields = []
        values = []
        for k, v in kwargs.items():
            if v is not None:
                fields.append(f"{k} = ?")
                values.append(v)
        if fields:
            values.append(session_id)
            query = f"UPDATE leads SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?"
            cursor.execute(query, values)
            conn.commit()
        conn.close()

    def find_matching_property(self, text: str):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM properties")
        props = [dict(r) for r in cursor.fetchall()]
        conn.close()

        text_lower = text.lower()
        for p in props:
            title_lower = p['title'].lower()
            zone_lower = p['zone'].lower()
            # Match by specific name or zone
            if "bosque" in text_lower and "bosque" in zone_lower:
                return p
            if "campodón" in text_lower or "campodon" in text_lower:
                if "campodón" in zone_lower or "campodon" in zone_lower:
                    return p
            if ("ático" in text_lower or "atico" in text_lower) and "ático" in title_lower:
                return p
            if "castillo" in text_lower and "castillo" in zone_lower:
                return p
            if p['title'].lower() in text_lower:
                return p
        return None

    def calculate_score_and_category(self, lead: dict) -> tuple[int, str, str]:
        score = 0
        intent = lead.get('intent', '') or ''
        budget = lead.get('budget', 0) or 0
        financing = lead.get('financing', '') or ''
        timeframe = lead.get('timeframe', '') or ''
        zone = lead.get('zone', '') or ''

        if "vender" in intent.lower():
            score += 45
            if any(z in zone.lower() for z in ["bosque", "campodón", "castillo"]):
                score += 20
        elif "comprar" in intent.lower():
            score += 25
            if budget >= 1000000:
                score += 35
            elif budget >= 600000:
                score += 25
            elif budget >= 350000:
                score += 15
            else:
                score += 10

        if any(f in financing.lower() for f in ["fondos propios", "contado", "concedida"]):
            score += 25
        elif "hipoteca" in financing.lower():
            score += 15

        if any(t in timeframe.lower() for t in ["inmediato", "< 1 mes", "lo antes posible"]):
            score += 20
        elif "1 a 3 meses" in timeframe.lower():
            score += 12

        score = min(score, 100)

        if score >= 65:
            category = "CALIENTE"
            summary = f"🔥 Lead VIP Alta Prioridad ({intent} en {zone or 'Villaviciosa'}). Capacidad: {budget or 'Tasación'} € ({financing or 'Liquidez'})."
        elif score >= 40:
            category = "TEMPLADO"
            summary = f"⚡ Lead Cualificado ({intent} en {zone or 'Villaviciosa'}). Seguimiento comercial requerido."
        else:
            category = "FRIO"
            summary = f"❄️ Lead Informativo ({intent or 'Consulta general'})."

        return score, category, summary

    def process_message(self, session_id: str, user_text: str) -> dict:
        conn = get_db()
        cursor = conn.cursor()

        # Save user message
        cursor.execute("INSERT INTO messages (session_id, sender, text) VALUES (?, 'user', ?)", (session_id, user_text))
        conn.commit()

        lead = self.get_or_create_lead(session_id)
        raw_text = user_text.strip()
        lower_text = raw_text.lower()

        # Detect and extract phone numbers (e.g. 612345678, +34 612 345 678, etc.)
        phone_match = re.search(r'(\+?34\s?)?[6789]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}', raw_text)
        if phone_match:
            phone_str = phone_match.group(0).strip()
            self.update_lead(session_id, phone=phone_str)

        # Detect names if user says "Me llamo X" or "Soy X"
        name_match = re.search(r'(?:me llamo|soy|mi nombre es)\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{2,30})', raw_text, re.I)
        if name_match:
            name_str = name_match.group(1).strip()
            self.update_lead(session_id, name=name_str)

        reply_text = ""
        buttons = []

        # ========================================================
        # 1. SPECIFIC PROPERTY INQUIRY
        # ========================================================
        prop = self.find_matching_property(raw_text)
        if prop and ("visitar" in lower_text or "información" in lower_text or "disponibilidad" in lower_text or "interesa" in lower_text or "chalet" in lower_text or "ático" in lower_text):
            self.update_lead(session_id, 
                             intent="Comprar", 
                             property_type=prop['property_type'], 
                             zone=prop['zone'], 
                             budget=prop['price'])
            
            price_formatted = f"{prop['price']:,.0f}".replace(",", ".")
            reply_text = (
                f"🏡 **{prop['title']}**\n\n"
                f"• **Ubicación**: {prop['zone']} (Villaviciosa de Odón)\n"
                f"• **Precio**: **{price_formatted} €**\n"
                f"• **Distribución**: {prop['bedrooms']} habitaciones, {prop['bathrooms']} baños, {prop['area_m2']} m²\n\n"
                f"{prop['description']}\n\n"
                "¿Te gustaría agendar una **visita privada presencial** para conocer la propiedad?"
            )
            buttons = [
                f"📅 Agendar Visita para {prop['zone']}",
                "💰 Consultar Opciones de Hipoteca",
                "📞 Quiero que me llame un Asesor"
            ]

        # ========================================================
        # 2. COMMON REAL ESTATE FAQS (Correlative Answers)
        # ========================================================
        elif any(k in lower_text for k in ["comisión", "comision", "honorarios", "cuánto cobráis", "cuanto cobrais"]):
            reply_text = (
                "ℹ️ **Nuestros Honorarios y Comisiones:**\n\n"
                "• **Para Vendedores**: Aplicamos un 3% (+IVA) a éxito de venta, únicamente tras la firma en notaría. Incluye reportaje fotográfico profesional con dron, tour virtual 3D, filtro de solvencia de compradores y gestión jurídica completa.\n"
                "• **Para Compradores**: Nuestro servicio de asesoramiento, búsqueda y visitas no tiene ningún coste añadido directo.\n\n"
                "¿Tienes una propiedad en Villaviciosa que te gustaría valorar?"
            )
            buttons = ["🔑 Sí, quiero valorar mi casa", "🏡 No, estoy buscando comprar", "📍 Dónde está vuestra oficina"]

        elif any(k in lower_text for k in ["oficina", "dónde estáis", "donde estais", "dirección", "direccion", "ubicación", "horario"]):
            reply_text = (
                "📍 **Nuestra Oficina en Villaviciosa:**\n\n"
                "Estamos en **Calle Carretas, 14** (en pleno casco urbano de Villaviciosa de Odón, junto a la Plaza Mayor).\n\n"
                "• **Horario comercial**: Lunes a Viernes de 9:30 a 20:00 (ininterrumpido) y Sábados de 10:00 a 14:00.\n\n"
                "¿Prefieres que concertemos una reunión en nuestra oficina o prefieres que un asesor visite tu inmueble?"
            )
            buttons = ["📅 Concertar cita en oficina", "🔑 Solicitar valoración en mi casa", "🏡 Ver propiedades en cartera"]

        elif any(k in lower_text for k in ["hipoteca", "financiación", "financiacion", "banco"]):
            reply_text = (
                "🏦 **Servicio Financiero e Hipotecas:**\n\n"
                "Contamos con convenios directos con las principales entidades bancarias para conseguir condiciones preferentes (hasta el 80%-90% de tasación) y estudio de viabilidad gratuito sin compromiso en 24-48 horas.\n\n"
                "¿Para qué rango de precio estás buscando vivienda?"
            )
            buttons = ["Hasta 450.000 €", "450.000 € - 750.000 €", "Más de 750.000 €"]

        # ========================================================
        # 3. EXPLICIT SELLER FLOW
        # ========================================================
        elif any(k in lower_text for k in ["vender", "tasar", "valorar mi chalet", "valorar mi propiedad", "tasación", "tasacion", "🔑 quiero vender"]):
            self.update_lead(session_id, intent="Vender")
            reply_text = (
                "🔑 **Valoración y Venta en Villaviciosa de Odón:**\n\n"
                "Gestionamos chalets y fincas de alto ticket con máxima discreción y cartera propia de compradores solventes con liquidez.\n\n"
                "Para orientarte con exactitud, ¿en qué zona de Villaviciosa se encuentra tu propiedad?"
            )
            buttons = ["Urb. El Bosque", "Urb. Campodón", "Casco Urbano", "Castillo / Cerro de las Nieves"]

        # Zone selection in Seller flow
        elif lead.get('intent') == "Vender" and any(z in lower_text for z in ["bosque", "campodón", "campodon", "casco urbano", "castillo", "centro"]):
            zone_selected = "El Bosque" if "bosque" in lower_text else ("Campodón" if "campod" in lower_text else ("Castillo" if "castillo" in lower_text else "Casco Urbano"))
            self.update_lead(session_id, zone=zone_selected)
            reply_text = (
                f"Perfecto, conocemos cada calle y el precio real del m² en **{zone_selected}**.\n\n"
                "¿Qué tipología de inmueble es?"
            )
            buttons = ["Chalet Independiente", "Chalet Pareado / Adosado", "Ático o Piso", "Parcela / Terreno"]

        elif lead.get('intent') == "Vender" and any(t in lower_text for t in ["independiente", "pareado", "adosado", "piso", "ático", "parcela"]):
            prop_type = raw_text
            self.update_lead(session_id, property_type=prop_type)
            reply_text = (
                f"Anotado: **{prop_type}** en **{lead.get('zone', 'Villaviciosa')}**.\n\n"
                "Para coordinar la **valoración técnica gratuita presencial** y enviarte el informe de mercado, ¿cuál es tu nombre y teléfono móvil de contacto?"
            )
            buttons = ["Enviar teléfono por aquí", "📅 Agendar fecha directamente"]

        # ========================================================
        # 4. EXPLICIT BUYER FLOW
        # ========================================================
        elif any(k in lower_text for k in ["comprar", "quiero comprar", "🏡 quiero comprar", "buscar chalets"]):
            self.update_lead(session_id, intent="Comprar")
            reply_text = (
                "🏡 **Búsqueda de Inmuebles en Villaviciosa:**\n\n"
                "Tenemos propiedades exclusivas tanto publicadas como en cartera privada (*off-market*).\n\n"
                "¿Qué tipo de vivienda encaja con lo que buscas?"
            )
            buttons = ["Chalet Independiente", "Chalet Pareado / Adosado", "Ático con Terraza", "Piso Céntrico"]

        elif lead.get('intent') == "Comprar" and any(t in lower_text for t in ["independiente", "pareado", "adosado", "ático", "atico", "piso céntrico"]):
            prop_type = raw_text
            self.update_lead(session_id, property_type=prop_type)
            reply_text = (
                f"Excelente elección: **{prop_type}**.\n\n"
                "¿Tienes preferencia por alguna zona en concreto de Villaviciosa?"
            )
            buttons = ["Urb. El Bosque", "Urb. Campodón", "Casco Urbano / Centro", "Castillo / Alrededores"]

        elif lead.get('intent') == "Comprar" and any(z in lower_text for z in ["bosque", "campodón", "campodon", "casco", "castillo"]):
            zone = "El Bosque" if "bosque" in lower_text else ("Campodón" if "campod" in lower_text else ("Castillo" if "castillo" in lower_text else "Casco Urbano"))
            self.update_lead(session_id, zone=zone)
            reply_text = (
                f"Anotado en **{zone}**.\n\n"
                "¿En qué rango de presupuesto aproximado te estás moviendo para la adquisición?"
            )
            buttons = ["350.000 € - 550.000 €", "550.000 € - 850.000 €", "850.000 € - 1.300.000 €", "Más de 1.300.000 €"]

        elif lead.get('intent') == "Comprar" and any(b in lower_text for b in ["350.000", "550.000", "850.000", "1.300.000", "hasta"]):
            b_val = 700000
            if "350.000" in lower_text: b_val = 450000
            elif "550.000" in lower_text: b_val = 650000
            elif "850.000" in lower_text: b_val = 1100000
            elif "1.300.000" in lower_text: b_val = 1500000
            self.update_lead(session_id, budget=b_val)
            
            reply_text = (
                "Perfecto. Respecto a la disponibilidad de fondos:\n\n"
                "¿Dispones de fondos propios al contado o requieres financiación hipotecaria?"
            )
            buttons = ["Fondos propios / Al contado", "Hipoteca preconcedida", "Necesito estudio de hipoteca", "Tengo que vender primero"]

        elif lead.get('intent') == "Comprar" and any(f in lower_text for f in ["fondos propios", "contado", "preconcedida", "estudio", "vender primero"]):
            self.update_lead(session_id, financing=raw_text)
            reply_text = (
                "Muy bien. Para organizar la agenda y avisar a los propietarios:\n\n"
                "¿En qué plazo estimas tomar la decisión de compra?"
            )
            buttons = ["Inmediato (< 1 mes)", "1 a 3 meses", "Solo explorando opciones"]

        # ========================================================
        # 5. APPOINTMENT BOOKING & CONTACT CONFIRMATION
        # ========================================================
        elif any(k in lower_text for k in ["agendar", "cita", "visita", "mañana", "tarde", "jueves", "viernes", "lunes", "martes", "miércoles"]):
            # Extract or set appointment
            appt = "Mañana a las 18:00h" if "mañana" in lower_text else ("Esta semana (Pendiente fijar hora)")
            self.update_lead(session_id, appointment_date=appt)
            
            lead = self.get_or_create_lead(session_id)
            score, cat, summary = self.calculate_score_and_category(lead)
            self.update_lead(session_id, score=score, category=cat, summary=summary)

            reply_text = (
                "📅 **¡Cita de Visita Solicitada!**\n\n"
                f"• **Preferencia**: {appt}\n"
                f"• **Interés**: {lead.get('property_type', 'Vivienda')} en {lead.get('zone', 'Villaviciosa')}\n\n"
                "Para enviarte la confirmación por SMS/WhatsApp y reservar la franja en la agenda del asesor, indícanos tu **nombre y teléfono**."
            )
            buttons = ["Dejar mi teléfono aquí", "📞 Llamar a la oficina directamente"]

        elif phone_match or any(k in lower_text for k in ["teléfono", "telefono", "móvil", "movil", "6", "7"]):
            if not lead.get('name'):
                self.update_lead(session_id, name="Cliente Web (" + raw_text[:12] + ")")
            
            score, cat, summary = self.calculate_score_and_category(self.get_or_create_lead(session_id))
            self.update_lead(session_id, score=score, category=cat, summary=summary)

            reply_text = (
                "✅ **¡Contacto Registrado con Éxito!**\n\n"
                "Hemos asignado tu ficha a nuestro especialista de zona en Villaviciosa de Odón.\n\n"
                "Te contactaremos en breve para confirmar los detalles de la visita y enviarte la documentación técnica."
            )
            buttons = ["🏡 Ver más chalets disponibles", "📊 Ver CRM Comercial"]

        # ========================================================
        # 6. WELCOME / DEFAULT GREETING
        # ========================================================
        else:
            reply_text = (
                "👋 ¡Hola! Bienvenido a **Consulting Inmobiliario Odón**.\n\n"
                "Soy Sofía, tu asistente comercial para **Villaviciosa de Odón**. Puedo ayudarte a encontrar chalet en El Bosque o Campodón, valorar tu propiedad o resolver dudas de honorarios y visitas.\n\n"
                "¿En qué podemos ayudarte hoy?"
            )
            buttons = ["🏡 Quiero Comprar", "🔑 Quiero Vender", "ℹ️ ¿Cuánto cobráis de comisión?", "📍 Dónde está vuestra oficina"]

        # Save bot response
        cursor.execute("INSERT INTO messages (session_id, sender, text, buttons) VALUES (?, 'bot', ?, ?)",
                       (session_id, reply_text, json.dumps(buttons)))
        conn.commit()
        conn.close()

        updated_lead = self.get_or_create_lead(session_id)
        return {
            'text': reply_text,
            'buttons': buttons,
            'lead': updated_lead
        }
