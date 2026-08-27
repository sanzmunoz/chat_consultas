# Reporte de Validación — Fase 1: Modelo y Base de Datos
**Fecha y Hora:** 2026-08-27T13:25:19.060041+00:00
**Base de datos:** `bd_santiago_munoz_nakamoto`

## Resultados de las Pruebas de Validación

- **✅ PASS** 1.1 Existencia de Tablas rw_* — Tablas encontradas: 8/7
- **✅ PASS** 1.2 Aislamiento RLS de Lectura (Néstor) — Canales accesibles por Néstor: 2 (sin fugas de canales privados ajenos)
- **✅ PASS** 1.3 Rechazo de Mensaje Privado Ajeno (msg-1007) — Mensaje de #frontend-design totalmente inaccesible para Néstor
- **✅ PASS** 1.4 Aislamiento RLS de Lectura (Camila) — Camila ve #frontend-design (msg-1007) pero RLS bloquea #backend-dev (msg-1004)
- **✅ PASS** 1.5 Rechazo Transaccional de Inserción No Autorizada — rw_fn_send_message bloqueó envío a canal sin membresía
- **✅ PASS** 1.6 Envío Atómico de Mensaje Autorizado — Mensaje insertado exitosamente con ID a6f5dfb8-0a77-43b5-859e-c90b1f6bdb7e
- **✅ PASS** 1.7 Trigger tsvector Automático — Trigger rw_trg_message_search generó search_vector en español
- **✅ PASS** 1.8 Recibo de Lectura Automático para Autor — Registro insertado en rw_read_receipts para el autor
- **✅ PASS** 1.9 Edición con Preservación de Estado Original — Original preservado: 'Mensaje de prueba validación Fase 1' | Actual: 'Mensaje editado con éxito'
- **✅ PASS** 1.10 Soft-Delete y Ocultamiento RLS — Mensaje marcado como is_deleted y filtrado automáticamente por política RLS
- **✅ PASS** 1.11 Consulta 1: Keyset Pagination sin OFFSET — Página 1: 3 msgs, Página 2: 3 msgs navegados con cursor compuesto
- **✅ PASS** 1.12 Consulta 2: Búsqueda con Resaltado (ts_headline) — Resultados encontrados: 1 con etiquetas <mark>...
- **✅ PASS** 1.13 Consulta 3: Recuperación Vectorial RAG con Permisos — Resultados retornados: 5 (0 canales privados ajenos para Valentina)
- **✅ PASS** 1.14 Consulta 4: Consumo Acumulado de Tokens Copiloto — Santiago: 2 consultas, 1040 tokens consumidos
- **✅ PASS** 1.15 Procedimiento 1: Consulta de Usuarios con Métricas — Usuario encontrado: Camila Rojas, Canales: 2
- **✅ PASS** 1.16 Procedimiento 2: Edición de Perfil de Usuario — Nombre actualizado: Camila Rojas Senior (Senior Frontend Dev)