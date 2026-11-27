import sys
import uuid
sys.stdout.reconfigure(encoding='utf-8')
from app.database import init_db, get_db
from app.lead_qualifier import LeadQualifier

init_db()
qualifier = LeadQualifier()
session_id = f"test_{uuid.uuid4().hex[:6]}"

res1 = qualifier.process_message(session_id, "Hola")
print("Turn 1:", res1["text"][:50].replace('\n', ' '))
print("Turn 1 buttons:", res1["buttons"])

res2 = qualifier.process_message(session_id, "🏡 Quiero Comprar")
print("Turn 2:", res2["text"][:50].replace('\n', ' '))
print("Turn 2 buttons:", res2["buttons"])

res3 = qualifier.process_message(session_id, "Chalet Independiente")
print("Turn 3:", res3["text"][:50].replace('\n', ' '))
print("Turn 3 buttons:", res3["buttons"])

res4 = qualifier.process_message(session_id, "Urb. El Bosque")
print("Turn 4:", res4["text"][:50].replace('\n', ' '))
print("Turn 4 buttons:", res4["buttons"])

res5 = qualifier.process_message(session_id, "850.000 € - 1.300.000 €")
print("Turn 5:", res5["text"][:50].replace('\n', ' '))
print("Turn 5 buttons:", res5["buttons"])

res6 = qualifier.process_message(session_id, "Fondos propios / Al contado")
print("Turn 6:", res6["text"][:50].replace('\n', ' '))
print("Turn 6 buttons:", res6["buttons"])

res7 = qualifier.process_message(session_id, "Inmediato (< 1 mes)")
lead = res7["lead"]
print(f"Turn 7 -> Score: {lead['score']}/100 | Categoria: {lead['category']}")
print(f"Summary: {lead['summary']}")
