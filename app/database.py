import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "inmo.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Leads table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE,
        name TEXT,
        phone TEXT,
        email TEXT,
        intent TEXT,
        property_type TEXT,
        zone TEXT,
        budget REAL,
        financing TEXT,
        timeframe TEXT,
        score INTEGER DEFAULT 0,
        category TEXT DEFAULT 'FRIO',
        appointment_date TEXT,
        summary TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Drop and recreate properties table to ensure all new rich columns exist
    cursor.execute("DROP TABLE IF EXISTS properties")
    cursor.execute("""
    CREATE TABLE properties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        zone TEXT NOT NULL,
        property_type TEXT NOT NULL,
        price REAL NOT NULL,
        bedrooms INTEGER,
        bathrooms INTEGER,
        area_m2 INTEGER,
        plot_m2 INTEGER DEFAULT 0,
        year_built INTEGER DEFAULT 2020,
        energy_rating TEXT DEFAULT 'A',
        energy_kwh TEXT DEFAULT '45.2 kWh/m² año',
        garage_spaces INTEGER DEFAULT 2,
        orientation TEXT DEFAULT 'Sur',
        description TEXT,
        image_url TEXT,
        gallery_images TEXT,
        features TEXT,
        distribution TEXT,
        location_info TEXT,
        featured BOOLEAN DEFAULT 1
    );
    """)
    
    # Messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        sender TEXT NOT NULL,
        text TEXT NOT NULL,
        buttons TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    conn.commit()
    seed_properties(cursor, conn)
    conn.close()

def seed_properties(cursor, conn):
    cursor.execute("DELETE FROM properties")
    sample_props = [
        (
            1,
            "Chalet Independiente de Lujo con Piscina Climatizada en El Bosque",
            "El Bosque",
            "Chalet Independiente",
            1180000,
            5, 4, 480, 1800, 2021, "A", "28.4 kWh/m² año", 4, "Sureste",
            "Exclusivo chalet independiente ubicado en una de las avenidas más distinguidas de la Urbanización El Bosque. Construido con arquitectura bioclimática de líneas depuradas, grandes ventanales de suelo a techo con rotura de puente térmico y orientación óptima para maximizar la luz solar. Cuenta con una parcela consolidada de 1.800 m² con privacidad absoluta, piscina de cloración salina climatizada por bomba de calor, porche apergolado con barbacoa de diseño y jardín japonés con olivos centenarios. Climatización mediante suelo radiante y refrescante por aerotermia de última generación y sistema domótico integral KNX.",
            "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
            json.dumps([
                "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?auto=format&fit=crop&w=1200&q=80"
            ]),
            json.dumps([
                "Piscina privada climatizada de cloración salina",
                "Climatización por aerotermia con suelo radiante y refrescante",
                "Sistema domótico integral KNX para luces, climatización y persianas",
                "Garaje cerrado en sótano para 4 vehículos grandes",
                "Instalación solar fotovoltaica de 8,5 kW con batería acumuladora",
                "Suite principal con vestidor doble de madera de nogal y baño en mármol",
                "Alarma perimetral conectada con cámaras de visión nocturna",
                "Riego automático zonificado con pozo propio legalizado"
            ]),
            json.dumps({
                "Planta Baja": "Gran hall de recepción a doble altura, salón diáfano de 75 m² con chimenea de bioetanol y salida directa al porche cubierto, comedor independiente, cocina de diseño con isla central y electrodomésticos Miele/Gaggenau, despacho profesional o dormitorio de invitados y baño completo.",
                "Primera Planta": "Master Suite de 45 m² con terraza privada panorámica, amplio vestidor y baño spa con bañera exenta y ducha lluvia; 3 dormitorios dobles adicionales en suite, cada uno con vestidor y baño propio incorporado.",
                "Planta Sótano": "Garaje para 4 vehículos con puerta seccional motorizada, sala polivalente de cine/gimnasio con ventilación natural, bodega climatizada a medida, cuarto de lavandería, sala de máquinas de aerotermia y trastero."
            }),
            "Ubicado en la Urbanización El Bosque de Villaviciosa de Odón. A 3 minutos del Club de Golf El Bosque, a 5 minutos del prestigioso Eurocolegio Casvi y de la Universidad Europea de Madrid (UEM). Acceso inmediato a M-501 y M-50, conectando con Moncloa en 20 minutos.",
            1
        ),
        (
            2,
            "Villa Vanguardista con Piscina Volada y Vistas al Golf en El Bosque",
            "El Bosque",
            "Chalet Independiente",
            1450000,
            6, 5, 620, 2100, 2023, "A", "22.1 kWh/m² año", 4, "Sur",
            "Obra maestra arquitectónica de hormigón visto, acero y vidrio en primera línea del campo de golf de El Bosque. Una propiedad singular concebida para amantes del diseño contemporáneo y la máxima privacidad. La piscina infinity volada parece fundirse con el horizonte verde del campo de golf. Dispone de spa interior con sauna finlandesa, ascensor panorámico de cristal que conecta las tres plantas y bodega de conservación climatizada.",
            "https://images.unsplash.com/photo-1600585154526-990dced4db0d?auto=format&fit=crop&w=1200&q=80",
            json.dumps([
                "https://images.unsplash.com/photo-1600585154526-990dced4db0d?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1587174486073-ae5e5cff23aa?auto=format&fit=crop&w=1200&q=80"
            ]),
            json.dumps([
                "Vistas panorámicas directas al campo de golf",
                "Piscina infinity volada con pared de cristal subacuático",
                "Ascensor privado de cristal OTIS de 6 plazas",
                "Spa wellness con sauna finlandesa, jacuzzi y baño turco",
                "Certificación Passivhaus con consumo energético casi nulo",
                "Cocina italiana Poliform con electrodomésticos Gaggenau",
                "Sistema de seguridad de grado 3 con circuito cerrado de TV",
                "Domótica Lutron con gestión de escenas lumínicas"
            ]),
            json.dumps({
                "Planta Baja": "Salón monumental de triple altura con vistas abiertas al golf, cocina abierta de autor con isla de cuarcita natural, comedor formal acristalado, suite de cortesía y aseo de diseño.",
                "Primera Planta": "Pasarela volada que distribuye la Master Suite principal con dos baños independientes y vestidor boutique, más dos dormitorios juveniles en suite con terraza propia.",
                "Planta Sótano": "Zona wellness con spa completo y sauna, sala de proyecciones acústicamente aislada, apartamento de servicio independiente con dormitorio y cocina, garaje para 4 todoterrenos."
            }),
            "Primera línea de golf en Urb. El Bosque. Entorno rodeado de pinos piñoneros protegidos, máxima tranquilidad y vigilancia de seguridad 24h con patrullas activas.",
            1
        ),
        (
            3,
            "Chalet Pareado Familiar con Jardín Privado y Pádel en Campodón",
            "Campodón",
            "Chalet Pareado",
            645000,
            4, 3, 290, 380, 2018, "B", "58.0 kWh/m² año", 2, "Suroeste",
            "Acogedor chalet pareado de diseño familiar en la cotizada Urbanización Campodón, a caballo entre Villaviciosa de Odón y Alcorcón. Parcela privada con jardín de césped natural, porche techado para cenas al aire libre y barbacoa de obra. Urbanización cerrada con excelentes zonas comunes que incluyen pista de pádel de césped artificial, piscina comunitaria y parque infantil.",
            "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
            json.dumps([
                "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1600573472591-ee6b68d14c68?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1556912172-45b7abe8b7e1?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1616046229478-9901c5536a45?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&w=1200&q=80"
            ]),
            json.dumps([
                "Jardín privado consolidado de 380 m² con porche solado",
                "Placas solares de autoconsumo instaladas (ahorro del 65% en factura)",
                "Zonas comunitarias con pista de pádel y gran piscina",
                "Garaje cubierto con cargador de vehículo eléctrico Wallbox",
                "Buhardilla diáfana acondicionada con tarima flotante y aire acondicionado",
                "Calefacción individual por gas natural con termostatos programables",
                "Excelente conexión con transporte público (autobús 518 a Príncipe Pío)"
            ]),
            json.dumps({
                "Planta Baja": "Vestíbulo de entrada con armario gabanero, amplio salón comedor de 38 m² con chimenea con cassete y salida al porche trasero, cocina office equipada con electrodomésticos Bosch, aseo de cortesía y garaje.",
                "Primera Planta": "Dormitorio principal en suite con baño completo y vestidor empotrado; 3 dormitorios secundarios muy amplios con armarios empotrados lacados en blanco; baño completo adicional.",
                "Buhardilla": "Espacio polivalente de 45 m² iluminado por ventanas Velux con persianas automáticas, ideal como despacho, zona de juegos infantil o quinto dormitorio."
            }),
            "Urbanización Campodón, Villaviciosa de Odón. Parada de autobús directo a Madrid (Moncloa y Príncipe Pío) a 200 metros. Proximidad a centros comerciales, colegios bilingües y supermercados Mercadona y Alcampo.",
            1
        ),
        (
            4,
            "Chalet Pareado de Gran Esquina con Parcela Ampliada en Campodón",
            "Campodón",
            "Chalet Pareado",
            720000,
            5, 4, 340, 420, 2019, "A", "36.5 kWh/m² año", 2, "Sur",
            "Chalet de gran esquina que goza de la mayor parcela de la promoción (420 m²), con orientación sur que garantiza sol durante todo el año. Cuenta con piscina privada de cloración salina con cascada de roca artificial, zona chill-out pergolada y césped artificial de alta gama de bajo mantenimiento. El interior destaca por sus acabados de Porcelanosa y carpintería lacada en blanco.",
            "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
            json.dumps([
                "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1600585152220-90363fe7e115?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1556909212-d5b604d0c90d?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1507652313519-d4e9174996dd?auto=format&fit=crop&w=1200&q=80"
            ]),
            json.dumps([
                "Parcela de esquina extragrande de 420 m² con total intimidad",
                "Piscina privada de sal de diseño con iluminación nocturna LED RGB",
                "Suelo radiante y refrescante con caldera de condensación y aerotermia",
                "Zona chill-out exterior con pérgola bioclimática motorizada",
                "Cocina ampliada con isla desayunadora de Neolith",
                "Buhardilla de 55 m² con baño completo privado",
                "Persianas eléctricas de aluminio extrusionado con cierre centralizado"
            ]),
            json.dumps({
                "Planta Baja": "Salón-comedor esquinero bañado en luz natural con dos salidas al jardín privado, cocina gourmet totalmente equipada, dormitorio o despacho en planta baja, baño con plato de ducha.",
                "Primera Planta": "3 dormitorios dobles, destacando la suite principal con terraza privada, vestidor a medida y baño en mármol blanco; baño secundario completo para los otros dos dormitorios.",
                "Segunda Planta": "Espectacular buhardilla acondicionada como suite de invitados o sala de ocio con baño propio completo y terraza solárium.",
                "Sótano": "Garaje para dos vehículos, lavandería y trastero de 20 m²."
            }),
            "En el corazón residencial de Campodón, a 2 minutos de la salida a la M-50 y M-506. Cercano al polígono Pinares Llanos y a zonas de ocio y restauración de Villaviciosa de Odón.",
            1
        ),
        (
            5,
            "Ático Dúplex Exclusivo con Terraza Panorámica en Casco Urbano",
            "Casco Urbano",
            "Ático",
            365000,
            3, 2, 140, 0, 2020, "B", "62.4 kWh/m² año", 1, "Sur",
            "Magnífico ático dúplex ubicado en el centro neurálgico de Villaviciosa de Odón, a pasos de comercios, restaurantes y transporte. Destaca por su imponente terraza descubierta de 45 m² con vistas abiertas hacia la sierra de Guadarrama, perfecta para barbacoas y atardeceres. Finca moderna con ascensor, plaza de garaje subterránea de acceso directo y amplio trastero.",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
            json.dumps([
                "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1556911073-38141963c9e0?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&w=1200&q=80"
            ]),
            json.dumps([
                "Terraza ático descubierta de 45 m² con pérgola y tomas de agua/luz",
                "Finca seminueva con ascensor y accesibilidad total sin barreras",
                "Plaza de garaje subterránea amplia incluida en el precio",
                "Trastero de 8 m² junto a la plaza de garaje",
                "Climatización frío/calor por conductos en toda la vivienda",
                "Armarios empotrados vestidos y forrados en madera de roble",
                "Ubicación inmejorable: todo a pie en Casco Urbano"
            ]),
            json.dumps({
                "Planta Principal": "Hall distribuidor, salón comedor luminoso con gran ventanal, cocina independiente completamente amueblada con tendedero cerrado, 2 dormitorios con armarios empotrados y un baño completo.",
                "Planta Alta": "Dormitorio principal con baño en suite y salida directa a la majestuosa terraza solárium de 45 m² con vistas despejadas."
            }),
            "Ubicado en el casco urbano de Villaviciosa de Odón, próximo a la calle Carretas y Plaza de la Constitución. A 10 minutos a pie del campus de la Universidad Europea de Madrid (alta rentabilidad garantizada).",
            1
        ),
        (
            6,
            "Piso de Autor Reformado con Gran Balcón Céntrico en Casco Urbano",
            "Casco Urbano",
            "Ático",
            285000,
            2, 2, 95, 0, 2022, "A", "38.0 kWh/m² año", 1, "Este",
            "Vivienda de autor con reforma integral de arquitecto finalizada recientemente. Techos altos con vigas vistas recuperadas, iluminación indirecta LED cálida y cocina abierta integrada al salón con barra americana de madera maciza de roble. Ideal como primera vivienda de diseño o inversión de altísima demanda de alquiler para profesores o directivos de la Universidad Europea.",
            "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
            json.dumps([
                "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1616046229478-9901c5536a45?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&w=1200&q=80"
            ]),
            json.dumps([
                "Reforma integral a estrenar con materiales de primera calidad",
                "Calefacción y agua caliente por aerotermia individual de bajo consumo",
                "Balcón corrido exterior con carpintería de aluminio de triple acristalamiento",
                "Cocina con electrodomésticos integrados panelados",
                "Suelos de tarima vinílica de alta resistencia hidrófuga",
                "Bajos gastos de comunidad (solo 35 €/mes)",
                "Excelente rentabilidad estimada de alquiler (> 6,5% bruto)"
            ]),
            json.dumps({
                "Distribución Diáfana": "Salón-comedor integrado con cocina en concepto abierto de 35 m², balcón exterior a calle arbolada y tranquila, dormitorio principal en suite con vestidor, segundo dormitorio individual o despacho y segundo baño completo para invitados."
            }),
            "En pleno Casco Urbano de Villaviciosa de Odón, en calle tranquila y peatonal. A 300 metros de farmacias, supermercados y parada de autobuses interurbanos a Madrid.",
            1
        ),
        (
            7,
            "Villa Señorial de Piedra junto al Castillo Histórico de Villaviciosa",
            "Castillo",
            "Chalet Independiente",
            920000,
            5, 4, 380, 1100, 2016, "B", "48.2 kWh/m² año", 3, "Sur",
            "Imponente villa señorial de sillería de piedra y teja árabe tradicional situada en el emblemático entorno del Castillo de Villaviciosa de Odón. Parcela privada de 1.100 m² con jardín botánico maduro (cedros, cipreses y enebros), estanque y piscina privada con porche rústico castellano. Una propiedad irrepetible con el sabor de la arquitectura clásica y el confort de las instalaciones contemporáneas.",
            "https://images.unsplash.com/photo-1613490493576-7fde63acd811?auto=format&fit=crop&w=1200&q=80",
            json.dumps([
                "https://images.unsplash.com/photo-1613490493576-7fde63acd811?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1600585154526-990dced4db0d?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?auto=format&fit=crop&w=1200&q=80"
            ]),
            json.dumps([
                "Fachada en piedra natural con aislamiento térmico reforzado",
                "Parcela íntima y arbolada de 1.100 m² con estanque y piscina",
                "Gran bodega subterránea con bóveda y capacidad para 800 botellas",
                "Porche rústico con vigas de madera noble y horno de leña tradicional",
                "Calefacción por suelo radiante con caldera de biomasa y apoyo solar",
                "Garaje cubierto para 3 coches y zona de taller",
                "Vistas directas a la arboleda del Castillo de Villaviciosa"
            ]),
            json.dumps({
                "Planta Principal": "Majestuoso salón con chimenea de piedra tallada, comedor independiente, biblioteca con estanterías a medida, amplia cocina rústica equipada con office, despensa y aseo.",
                "Planta Superior": "4 dormitorios dobles de gran tamaño, destacando la suite nupcial con vestidor y baño en mármol envejecido; 2 baños completos de diseño castellano.",
                "Semisótano": "Bodega histórica abovedada con comedor para catas privadas, dormitorio de invitados con baño propio, zona de lavandería y garaje para 3 vehículos."
            }),
            "Ubicación privilegiada en la zona del Castillo de Villaviciosa de Odón. Un entorno señorial rodeado de historia, naturaleza y tranquilidad a escasos minutos a pie del centro del pueblo.",
            1
        ),
        (
            8,
            "Chalet Bioclimático con Aerotermia en Monte de la Yedra",
            "Castillo",
            "Chalet Independiente",
            830000,
            4, 3, 320, 850, 2022, "A", "19.8 kWh/m² año", 2, "Sureste",
            "Vivienda unifamiliar de arquitectura sostenible y diseño vanguardista en el entorno natural de Monte de la Yedra. Certificación energética de clase A con sistema de aerotermia, ventilación mecánica controlada con recuperador de calor y placas solares. Piscina privada con cloración salina, pérgola bioclimática con lamas orientables y jardín xeriscape de diseño de bajo consumo hídrico.",
            "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1200&q=80",
            json.dumps([
                "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=1200&q=80",
                "https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?auto=format&fit=crop&w=1200&q=80"
            ]),
            json.dumps([
                "Certificación energética A con consumo casi nulo",
                "Aerotermia Saunier Duval con suelo radiante y refrescante",
                "Ventilación mecánica con recuperador de calor (aire puro continuo)",
                "Instalación fotovoltaica de 6 kW con inversor Huawei",
                "Piscina infinity de cloración salina con cascada",
                "Pérgola bioclimática exterior con iluminación perimetral LED",
                "Garaje cerrado para 2 vehículos con cargador tipo 2 Mennekes"
            ]),
            json.dumps({
                "Planta Principal": "Espacio diáfano que integra salón, comedor y cocina con isla de Silestone de 5 metros, lavandería independiente, dormitorio en suite para invitados y aseo de diseño.",
                "Planta Alta": "Suite principal con vestidor exento y baño panorámico con vistas a la sierra; dos dormitorios juveniles con armarios empotrados lacados y baño completo compartido."
            }),
            "En el exclusivo enclave de Monte de la Yedra, junto al parque regional del curso medio del río Guadarrama. Naturaleza pura a solo 3 minutos del centro de Villaviciosa de Odón.",
            1
        )
    ]
    cursor.executemany("""
    INSERT INTO properties (
        id, title, zone, property_type, price, bedrooms, bathrooms, area_m2, plot_m2, 
        year_built, energy_rating, energy_kwh, garage_spaces, orientation, 
        description, image_url, gallery_images, features, distribution, location_info, featured
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_props)
    conn.commit()

if __name__ == "__main__":
    init_db()
    print("Database successfully initialized and seeded with 8 rich properties!")
