import json
import hashlib
import numpy as np

# Users definition
users = [
    {
        "id": "11111111-1111-4111-8111-111111111111",
        "username": "smunoz",
        "email": "santiago.munoz@riwi.co",
        "display_name": "Santiago Muñoz",
        "role": "admin",
        "position": "Tech Lead"
    },
    {
        "id": "22222222-2222-4222-8222-222222222222",
        "username": "crojas",
        "email": "camila.rojas@riwi.co",
        "display_name": "Camila Rojas",
        "role": "member",
        "position": "Frontend Developer"
    },
    {
        "id": "33333333-3333-4333-8333-333333333333",
        "username": "nvega",
        "email": "nestor.vega@riwi.co",
        "display_name": "Néstor Vega",
        "role": "member",
        "position": "Backend Developer"
    },
    {
        "id": "44444444-4444-4444-8444-444444444444",
        "username": "vcastro",
        "email": "valentina.castro@riwi.co",
        "display_name": "Valentina Castro",
        "role": "member",
        "position": "QA Engineer"
    },
    {
        "id": "55555555-5555-4555-8555-555555555555",
        "username": "alopez",
        "email": "andres.lopez@riwi.co",
        "display_name": "Andrés López",
        "role": "member",
        "position": "DevOps Engineer"
    }
]

email_to_id = {u["email"]: u["id"] for u in users}

channels = [
    {
        "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        "name": "#general",
        "type": "public",
        "description": "Canal general de comunicación para todo el equipo de Riwi Co.",
        "created_by": email_to_id["santiago.munoz@riwi.co"]
    },
    {
        "id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        "name": "#backend-dev",
        "type": "private",
        "description": "Discusiones técnicas del equipo backend. Temas de arquitectura, base de datos y API.",
        "created_by": email_to_id["santiago.munoz@riwi.co"]
    },
    {
        "id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        "name": "#frontend-design",
        "type": "private",
        "description": "Diseño de interfaces y componentes del frontend. UX, Material Design y responsive.",
        "created_by": email_to_id["camila.rojas@riwi.co"]
    },
    {
        "id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
        "name": "#devops-infra",
        "type": "private",
        "description": "Infraestructura, CI/CD, Docker y despliegue. Solo equipo de operaciones.",
        "created_by": email_to_id["andres.lopez@riwi.co"]
    }
]

channel_name_to_id = {c["name"]: c["id"] for c in channels}

memberships = [
    # #general (all)
    ("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", email_to_id["santiago.munoz@riwi.co"], "owner"),
    ("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", email_to_id["camila.rojas@riwi.co"], "member"),
    ("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", email_to_id["nestor.vega@riwi.co"], "member"),
    ("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", email_to_id["valentina.castro@riwi.co"], "member"),
    ("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", email_to_id["andres.lopez@riwi.co"], "member"),
    # #backend-dev
    ("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", email_to_id["santiago.munoz@riwi.co"], "owner"),
    ("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", email_to_id["nestor.vega@riwi.co"], "member"),
    # #frontend-design
    ("cccccccc-cccc-4ccc-8ccc-cccccccccccc", email_to_id["camila.rojas@riwi.co"], "owner"),
    ("cccccccc-cccc-4ccc-8ccc-cccccccccccc", email_to_id["valentina.castro@riwi.co"], "member"),
    # #devops-infra
    ("dddddddd-dddd-4ddd-8ddd-dddddddddddd", email_to_id["andres.lopez@riwi.co"], "owner"),
    ("dddddddd-dddd-4ddd-8ddd-dddddddddddd", email_to_id["santiago.munoz@riwi.co"], "member"),
]

def generate_pseudo_embedding(text: str, dim: int = 1536) -> str:
    """Generates a deterministic normalized unit vector based on text hash for offline testing."""
    if not text:
        return None
    # Create deterministic seed from text
    seed = int(hashlib.sha256(text.encode('utf-8')).hexdigest()[:8], 16)
    rng = np.random.RandomState(seed)
    vec = rng.randn(dim).astype(np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return "[" + ",".join(f"{x:.6f}" for x in vec[:1536]) + "]"

with open("/home/cohorte5/Documentos/san_mz/chat_consultas_riwi/seed.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# Bcrypt hash for password 'riwi2026!'
# Verified standard passlib bcrypt format:
# $2a$10$D9ZPcsAov6yLiRrhr8GVMekkdjBQZ6OetYjTRmXL9GINjwT5UiqCC
BCRYPT_HASH = "$2a$10$D9ZPcsAov6yLiRrhr8GVMekkdjBQZ6OetYjTRmXL9GINjwT5UiqCC"

sql_lines = [
    "-- =============================================================================",
    "-- Riwi Co. Internal Messaging Platform — Normalized Seed Data (Phase 1)",
    "-- Database: bd_santiago_munoz_nakamoto",
    "-- Default password for all users: 'riwi2026!'",
    "-- =============================================================================",
    "",
    "-- 1. Seed Users",
    "INSERT INTO rw_users (id, username, email, password_hash, display_name, role, position, is_active)",
    "VALUES"
]

user_values = []
for u in users:
    val = f"  ('{u['id']}', '{u['username']}', '{u['email']}', '{BCRYPT_HASH}', '{u['display_name']}', '{u['role']}', '{u['position']}', TRUE)"
    user_values.append(val)
sql_lines.append(",\n".join(user_values))
sql_lines.append("""ON CONFLICT (email) DO UPDATE 
SET display_name = EXCLUDED.display_name,
    role = EXCLUDED.role,
    position = EXCLUDED.position,
    password_hash = EXCLUDED.password_hash;
""")

sql_lines.append("-- 2. Seed Channels")
sql_lines.append("INSERT INTO rw_channels (id, name, description, type, created_by)")
sql_lines.append("VALUES")
chan_values = []
for c in channels:
    desc = c['description'].replace("'", "''")
    val = f"  ('{c['id']}', '{c['name']}', '{desc}', '{c['type']}', '{c['created_by']}')"
    chan_values.append(val)
sql_lines.append(",\n".join(chan_values))
sql_lines.append("""ON CONFLICT (name) DO UPDATE 
SET description = EXCLUDED.description,
    type = EXCLUDED.type;
""")

sql_lines.append("-- 3. Seed Channel Memberships")
sql_lines.append("INSERT INTO rw_channel_members (channel_id, user_id, role)")
sql_lines.append("VALUES")
mem_values = []
for cid, uid, r in memberships:
    val = f"  ('{cid}', '{uid}', '{r}')"
    mem_values.append(val)
sql_lines.append(",\n".join(mem_values))
sql_lines.append("ON CONFLICT (channel_id, user_id) DO NOTHING;\n")

sql_lines.append("-- 4. Seed Messages")
msg_values = []
receipt_values = []

for idx, m in enumerate(raw_data["mensajes"], start=1):
    m_id = f"10000000-0000-0000-0000-{idx:012d}"
    c_id = channel_name_to_id[m["canal_nombre"]]
    a_id = email_to_id[m["autor_email"]]
    ref = m["msg_ref"]
    content = m["contenido"].replace("'", "''")
    orig_content = f"'{m['contenido_original'].replace("'", "''")}'" if m["contenido_original"] else "NULL"
    is_edited = "TRUE" if m["editado"] else "FALSE"
    edited_at = f"'{m['editado_en']}'" if m.get("editado_en") else "NULL"
    is_deleted = "TRUE" if m["eliminado"] else "FALSE"
    deleted_at = f"'{m['eliminado_en']}'" if m.get("eliminado_en") else "NULL"
    status = m["estado"]
    created_at = m["creado_en"]
    
    # Vector embedding
    emb = generate_pseudo_embedding(m["contenido"])
    emb_str = f"'{emb}'::vector" if emb else "NULL"
    
    val = f"  ('{m_id}', '{ref}', '{c_id}', '{a_id}', '{content}', {orig_content}, {emb_str}, {is_edited}, {edited_at}, {is_deleted}, {deleted_at}, '{status}', '{created_at}')"
    msg_values.append(val)

    # Read receipts
    # Author always marked as read
    receipt_values.append(f"  ('{m_id}', '{a_id}', '{created_at}')")
    for reader_email in m.get("leido_por", []):
        if reader_email in email_to_id:
            r_uid = email_to_id[reader_email]
            if r_uid != a_id:
                receipt_values.append(f"  ('{m_id}', '{r_uid}', '{created_at}')")

sql_lines.append("INSERT INTO rw_messages (id, msg_ref, channel_id, author_id, content, original_content, embedding, is_edited, edited_at, is_deleted, deleted_at, status, created_at)")
sql_lines.append("VALUES")
sql_lines.append(",\n".join(msg_values))
sql_lines.append("""ON CONFLICT (msg_ref) DO UPDATE 
SET content = EXCLUDED.content,
    original_content = EXCLUDED.original_content,
    embedding = EXCLUDED.embedding,
    is_edited = EXCLUDED.is_edited,
    is_deleted = EXCLUDED.is_deleted,
    status = EXCLUDED.status;
""")

sql_lines.append("-- 5. Seed Read Receipts")
sql_lines.append("INSERT INTO rw_read_receipts (message_id, user_id, read_at)")
sql_lines.append("VALUES")
sql_lines.append(",\n".join(receipt_values))
sql_lines.append("ON CONFLICT (message_id, user_id) DO NOTHING;\n")

sql_lines.append("-- 6. Seed Copilot Logs")
sql_lines.append("INSERT INTO rw_copilot_logs (user_id, query, response, prompt_tokens, completion_tokens, total_tokens, model, prompt_version, created_at)")
sql_lines.append("VALUES")
cop_values = []
for log in raw_data.get("consultas_copiloto", []):
    u_id = email_to_id[log["usuario_email"]]
    q = log["pregunta"].replace("'", "''")
    r = log["respuesta"].replace("'", "''")
    val = f"  ('{u_id}', '{q}', '{r}', {log['tokens_prompt']}, {log['tokens_completion']}, {log['tokens_total']}, '{log['modelo']}', '{log['version_prompt']}', '{log['creado_en']}')"
    cop_values.append(val)
sql_lines.append(",\n".join(cop_values))
sql_lines.append(";\n")

sql_text = "\n".join(sql_lines)
with open("/home/cohorte5/Documentos/san_mz/chat_consultas_riwi/sql/05_seed.sql", "w", encoding="utf-8") as f:
    f.write(sql_text)

print("Generated sql/05_seed.sql successfully!")
