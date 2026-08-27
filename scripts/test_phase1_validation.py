#!/usr/bin/env python3
"""
Phase 1 Validation Test Suite — Database, RLS, Procedures & SQL Logic
Database: bd_santiago_munoz_nakamoto
"""
import os
import sys
import asyncio
import asyncpg
from datetime import datetime, timezone

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5433"))
DB_NAME = os.getenv("DB_NAME", "bd_santiago_munoz_nakamoto")
DB_ADMIN_USER = os.getenv("DB_ADMIN_USER", "postgres")
DB_ADMIN_PASSWORD = os.getenv("DB_ADMIN_PASSWORD", "postgres")
DB_APP_USER = os.getenv("DB_APP_USER", "rw_app_role")
DB_APP_PASSWORD = os.getenv("DB_APP_PASSWORD", "rw_app_secure_pass_2026")

# Test user IDs
SANTIAGO_ID = "11111111-1111-4111-8111-111111111111"  # Admin, member of #general, #backend-dev, #devops-infra
CAMILA_ID   = "22222222-2222-4222-8222-222222222222"  # Member, member of #general, #frontend-design
NESTOR_ID   = "33333333-3333-4333-8333-333333333333"  # Member, member of #general, #backend-dev
VALENTINA_ID= "44444444-4444-4444-8444-444444444444"  # Member, member of #general, #frontend-design

# Channels
GENERAL_ID  = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BACKEND_ID  = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
FRONTEND_ID = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
DEVOPS_ID   = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"

report_lines = []

def log_test(test_name: str, passed: bool, details: str = ""):
    status = "✅ PASS" if passed else "❌ FAIL"
    msg = f"[{status}] {test_name}: {details}"
    print(msg)
    report_lines.append(f"- **{status}** {test_name} — {details}")
    if not passed:
        raise AssertionError(f"Test failed: {test_name} - {details}")

async def run_phase1_validation():
    print(f"=== INICIANDO VALIDACIÓN DE FASE 1: BASE DE DATOS Y LÓGICA SQL ===")
    report_lines.append("# Reporte de Validación — Fase 1: Modelo y Base de Datos")
    report_lines.append(f"**Fecha y Hora:** {datetime.now(timezone.utc).isoformat()}")
    report_lines.append(f"**Base de datos:** `{DB_NAME}`\n")
    report_lines.append("## Resultados de las Pruebas de Validación\n")

    # Connect as App Role (rw_app_role) to test true RLS
    conn = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, user=DB_APP_USER, password=DB_APP_PASSWORD, database=DB_NAME
    )

    try:
        # TEST 1: Schema Structure & Table Existence
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name LIKE 'rw_%'
            ORDER BY table_name;
        """)
        tbl_names = {r["table_name"] for r in tables}
        expected_tables = {
            "rw_users", "rw_channels", "rw_channel_members", "rw_messages", 
            "rw_read_receipts", "rw_copilot_logs", "rw_refresh_tokens"
        }
        log_test("1.1 Existencia de Tablas rw_*", expected_tables.issubset(tbl_names),
                 f"Tablas encontradas: {len(tbl_names)}/{len(expected_tables)}")

        # TEST 2: RLS Isolation — Nestor cannot view #frontend-design or #devops-infra messages
        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{NESTOR_ID}';")
            visible_msgs = await conn.fetch("SELECT msg_ref, channel_id FROM rw_messages;")
            visible_channels = {str(r["channel_id"]) for r in visible_msgs}
            
            # Nestor should only see messages from #general and #backend-dev
            invalid_channels = visible_channels - {GENERAL_ID, BACKEND_ID}
            log_test("1.2 Aislamiento RLS de Lectura (Néstor)", len(invalid_channels) == 0,
                     f"Canales accesibles por Néstor: {len(visible_channels)} (sin fugas de canales privados ajenos)")

            # Check specific private messages from #frontend-design are NOT visible
            frontend_msg = await conn.fetchval("SELECT COUNT(*) FROM rw_messages WHERE msg_ref = 'msg-1007';")
            log_test("1.3 Rechazo de Mensaje Privado Ajeno (msg-1007)", frontend_msg == 0,
                     "Mensaje de #frontend-design totalmente inaccesible para Néstor")

        # TEST 3: RLS Isolation — Camila can view #frontend-design but NOT #backend-dev
        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{CAMILA_ID}';")
            backend_msg = await conn.fetchval("SELECT COUNT(*) FROM rw_messages WHERE msg_ref = 'msg-1004';")
            frontend_msg = await conn.fetchval("SELECT COUNT(*) FROM rw_messages WHERE msg_ref = 'msg-1007';")
            log_test("1.4 Aislamiento RLS de Lectura (Camila)", backend_msg == 0 and frontend_msg == 1,
                     "Camila ve #frontend-design (msg-1007) pero RLS bloquea #backend-dev (msg-1004)")

        # TEST 4: Atomic Function rw_fn_send_message with Membership Validation (Negative test)
        rejected = False
        try:
            async with conn.transaction():
                await conn.execute(f"SET LOCAL app.current_user_id = '{NESTOR_ID}';")
                await conn.execute(f"SELECT rw_fn_send_message('{FRONTEND_ID}', 'Hola intruso');")
        except asyncpg.PostgresError as e:
            rejected = True
        log_test("1.5 Rechazo Transaccional de Inserción No Autorizada", rejected,
                 "rw_fn_send_message bloqueó envío a canal sin membresía")

        # TEST 5: Atomic Function rw_fn_send_message with Membership Validation (Positive test)
        new_msg_id = None
        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{NESTOR_ID}';")
            new_msg_id = await conn.fetchval(
                f"SELECT rw_fn_send_message('{BACKEND_ID}', 'Mensaje de prueba validación Fase 1');"
            )
        log_test("1.6 Envío Atómico de Mensaje Autorizado", new_msg_id is not None,
                 f"Mensaje insertado exitosamente con ID {new_msg_id}")

        # TEST 6: Verify trigger and read receipt
        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{NESTOR_ID}';")
            tsv = await conn.fetchval(f"SELECT search_vector IS NOT NULL FROM rw_messages WHERE id = '{new_msg_id}';")
            log_test("1.7 Trigger tsvector Automático", tsv is True,
                     "Trigger rw_trg_message_search generó search_vector en español")

            receipt_exists = await conn.fetchval(
                f"SELECT 1 FROM rw_read_receipts WHERE message_id = '{new_msg_id}' AND user_id = '{NESTOR_ID}';"
            )
            log_test("1.8 Recibo de Lectura Automático para Autor", receipt_exists == 1,
                     "Registro insertado en rw_read_receipts para el autor")

        # TEST 7: Message Edit Preserving Original Content
        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{NESTOR_ID}';")
            await conn.execute(f"SELECT rw_fn_edit_message('{new_msg_id}', 'Mensaje editado con éxito');")
            row = await conn.fetchrow(f"SELECT content, original_content, is_edited FROM rw_messages WHERE id = '{new_msg_id}';")
            log_test("1.9 Edición con Preservación de Estado Original",
                     row["is_edited"] is True and row["original_content"] == "Mensaje de prueba validación Fase 1",
                     f"Original preservado: '{row['original_content']}' | Actual: '{row['content']}'")

        # TEST 8: Message Soft-Delete
        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{NESTOR_ID}';")
            await conn.execute(f"SELECT rw_fn_delete_message('{new_msg_id}');")
            del_visible = await conn.fetchval(f"SELECT COUNT(*) FROM rw_messages WHERE id = '{new_msg_id}';")
            log_test("1.10 Soft-Delete y Ocultamiento RLS",
                     del_visible == 0,
                     "Mensaje marcado como is_deleted y filtrado automáticamente por política RLS")

        # TEST 9: Required Query 1 — Keyset Pagination
        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{SANTIAGO_ID}';")
            page1 = await conn.fetch("""
                SELECT id, msg_ref, content, created_at
                FROM rw_messages
                WHERE channel_id = $1 AND is_deleted = FALSE AND rw_is_channel_member(channel_id)
                ORDER BY created_at DESC, id DESC
                LIMIT 3;
            """, GENERAL_ID)
            cursor_at = page1[-1]["created_at"]
            cursor_id = page1[-1]["id"]

            page2 = await conn.fetch("""
                SELECT id, msg_ref, content, created_at
                FROM rw_messages
                WHERE channel_id = $1 AND is_deleted = FALSE AND rw_is_channel_member(channel_id)
                  AND (created_at, id) < ($2, $3)
                ORDER BY created_at DESC, id DESC
                LIMIT 3;
            """, GENERAL_ID, cursor_at, cursor_id)
            log_test("1.11 Consulta 1: Keyset Pagination sin OFFSET", len(page1) == 3 and len(page2) > 0,
                     f"Página 1: {len(page1)} msgs, Página 2: {len(page2)} msgs navegados con cursor compuesto")

        # TEST 10: Required Query 2 — Full-Text Search with Highlighting (ts_headline)
        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{SANTIAGO_ID}';")
            search_results = await conn.fetch("""
                SELECT msg_ref, ts_headline('spanish', content, websearch_to_tsquery('spanish', 'asyncpg pool'), 'StartSel=<mark>,StopSel=</mark>') AS hl
                FROM rw_messages
                WHERE is_deleted = FALSE AND rw_is_channel_member(channel_id)
                  AND search_vector @@ websearch_to_tsquery('spanish', 'asyncpg pool');
            """)
            has_mark = any("<mark>" in r["hl"] for r in search_results)
            log_test("1.12 Consulta 2: Búsqueda con Resaltado (ts_headline)", len(search_results) > 0 and has_mark,
                     f"Resultados encontrados: {len(search_results)} con etiquetas <mark>...")

        # TEST 11: Required Query 3 — Copilot Vector Retrieval with Permissions
        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{VALENTINA_ID}';")
            dummy_vec = [0.05] * 1536
            vec_str = "[" + ",".join(str(x) for x in dummy_vec) + "]"
            v_results = await conn.fetch(f"""
                SELECT m.msg_ref, c.name as channel_name, (1 - (m.embedding <=> '{vec_str}'::vector)) as sim
                FROM rw_messages m
                JOIN rw_channels c ON m.channel_id = c.id
                WHERE m.is_deleted = FALSE AND m.embedding IS NOT NULL AND rw_is_channel_member(m.channel_id)
                ORDER BY m.embedding <=> '{vec_str}'::vector ASC
                LIMIT 5;
            """)
            has_backend = any(r["channel_name"] == "#backend-dev" for r in v_results)
            log_test("1.13 Consulta 3: Recuperación Vectorial RAG con Permisos", not has_backend,
                     f"Resultados retornados: {len(v_results)} (0 canales privados ajenos para Valentina)")

        # TEST 12: Required Query 4 — Copilot Token Usage Aggregation
        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{SANTIAGO_ID}';")
            usage = await conn.fetchrow("""
                SELECT COUNT(l.id) as total_queries, SUM(l.total_tokens) as total_tokens
                FROM rw_users u
                JOIN rw_copilot_logs l ON u.id = l.user_id
                WHERE u.id = $1
                GROUP BY u.id;
            """, SANTIAGO_ID)
            log_test("1.14 Consulta 4: Consumo Acumulado de Tokens Copiloto",
                     usage is not None and usage["total_queries"] >= 2,
                     f"Santiago: {usage['total_queries']} consultas, {usage['total_tokens']} tokens consumidos")

        # TEST 13: Stored Procedures (rw_sp_query_users & rw_sp_edit_or_delete_user)
        async with conn.transaction():
            await conn.execute(f"SET LOCAL app.current_user_id = '{SANTIAGO_ID}';")
            users_list = await conn.fetch("SELECT * FROM rw_fn_query_users('Camila', NULL, NULL, NULL, 5);")
            log_test("1.15 Procedimiento 1: Consulta de Usuarios con Métricas",
                     len(users_list) == 1 and users_list[0]["username"] == "crojas",
                     f"Usuario encontrado: {users_list[0]['display_name']}, Canales: {users_list[0]['channels_count']}")

            # Edit user profile via procedure
            await conn.execute("""
                CALL rw_sp_edit_or_delete_user($1, 'EDIT', 'Camila Rojas Senior', 'Senior Frontend Dev', NULL, NULL, NULL);
            """, CAMILA_ID)
            upd_user = await conn.fetchrow(f"SELECT display_name, position FROM rw_users WHERE id = '{CAMILA_ID}';")
            log_test("1.16 Procedimiento 2: Edición de Perfil de Usuario",
                     upd_user["display_name"] == "Camila Rojas Senior",
                     f"Nombre actualizado: {upd_user['display_name']} ({upd_user['position']})")

    finally:
        await conn.close()

    print("\n=== TODAS LAS 16 PRUEBAS DE FASE 1 COMPLETADAS EXITOSAMENTE (16/16) ===")
    
    # Write report
    report_text = "\n".join(report_lines)
    with open("/home/cohorte5/Documentos/san_mz/chat_consultas_riwi/docs/phase1_validation.md", "w", encoding="utf-8") as f:
        f.write(report_text)
    print("Reporte guardado en docs/phase1_validation.md")

if __name__ == "__main__":
    asyncio.run(run_phase1_validation())
