-- =============================================================================
-- Riwi Co. Internal Messaging Platform — Required SQL Queries (Phase 1)
-- Database: bd_santiago_munoz_nakamoto
-- Requirement 11 Implementation with PREPARE statements and functions
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Query 1: Channel Message History with Keyset Pagination
-- (O(1) index-backed pagination without OFFSET, preserving scroll position)
-- Parameters:
--   $1: p_channel_id (UUID)
--   $2: p_cursor_created_at (TIMESTAMPTZ, NULL for first page)
--   $3: p_cursor_id (UUID, NULL for first page)
--   $4: p_limit (INT, default 20)
-- -----------------------------------------------------------------------------
PREPARE rw_qry_channel_messages_keyset(
    UUID,        -- $1: channel_id
    TIMESTAMPTZ, -- $2: cursor_created_at
    UUID,        -- $3: cursor_id
    INT          -- $4: limit
) AS
SELECT 
    m.id,
    m.msg_ref,
    m.channel_id,
    m.author_id,
    u.display_name AS author_name,
    u.username AS author_username,
    u.position AS author_position,
    m.content,
    m.original_content,
    m.status,
    m.is_edited,
    m.edited_at,
    m.created_at,
    (
        SELECT COUNT(rr.id) 
        FROM rw_read_receipts rr 
        WHERE rr.message_id = m.id
    ) AS read_count,
    EXISTS (
        SELECT 1 
        FROM rw_read_receipts rr 
        WHERE rr.message_id = m.id 
          AND rr.user_id = rw_get_current_user_id()
    ) AS is_read_by_me
FROM rw_messages m
JOIN rw_users u ON m.author_id = u.id
WHERE m.channel_id = $1
  AND m.is_deleted = FALSE
  AND rw_is_channel_member(m.channel_id)
  AND (
      $2::TIMESTAMPTZ IS NULL 
      OR (m.created_at, m.id) < ($2, $3::UUID)
  )
ORDER BY m.created_at DESC, m.id DESC
LIMIT LEAST(COALESCE($4, 20), 100);

-- -----------------------------------------------------------------------------
-- Query 2: Message Full-Text Search with Term Highlighting (ts_headline)
-- Parameters:
--   $1: p_search_term (TEXT, e.g. 'asyncpg | pool')
--   $2: p_limit (INT, default 20)
-- -----------------------------------------------------------------------------
PREPARE rw_qry_search_messages_highlight(
    TEXT, -- $1: search_term
    INT   -- $2: limit
) AS
SELECT 
    m.id,
    m.msg_ref,
    m.channel_id,
    c.name AS channel_name,
    c.type AS channel_type,
    m.author_id,
    u.display_name AS author_name,
    u.username AS author_username,
    m.content,
    ts_headline(
        'spanish', 
        m.content, 
        websearch_to_tsquery('spanish', $1),
        'StartSel = <mark>, StopSel = </mark>, MaxWords=40, MinWords=15, HighlightAll=FALSE'
    ) AS highlighted_content,
    ts_rank(m.search_vector, websearch_to_tsquery('spanish', $1)) AS search_rank,
    m.created_at
FROM rw_messages m
JOIN rw_channels c ON m.channel_id = c.id
JOIN rw_users u ON m.author_id = u.id
WHERE m.is_deleted = FALSE
  AND rw_is_channel_member(m.channel_id)
  AND m.search_vector @@ websearch_to_tsquery('spanish', $1)
ORDER BY search_rank DESC, m.created_at DESC
LIMIT LEAST(COALESCE($2, 20), 50);

-- -----------------------------------------------------------------------------
-- Query 3: Copilot Semantic RAG Context Retrieval with SQL Permissions
-- (Cosine distance `<=>` strictly scoped to channels where actor is a member)
-- Parameters:
--   $1: p_query_embedding (vector(1536))
--   $2: p_similarity_threshold (FLOAT, max cosine distance)
--   $3: p_limit (INT, top K results)
-- -----------------------------------------------------------------------------
PREPARE rw_qry_copilot_rag_context(
    vector(1536), -- $1: query embedding
    FLOAT,        -- $2: max cosine distance threshold (e.g. 0.65)
    INT           -- $3: top_k
) AS
SELECT 
    m.id,
    m.msg_ref,
    m.channel_id,
    c.name AS channel_name,
    m.author_id,
    u.display_name AS author_name,
    u.position AS author_position,
    m.content,
    m.created_at,
    (1 - (m.embedding <=> $1)) AS similarity_score
FROM rw_messages m
JOIN rw_channels c ON m.channel_id = c.id
JOIN rw_users u ON m.author_id = u.id
WHERE m.is_deleted = FALSE
  AND m.embedding IS NOT NULL
  AND rw_is_channel_member(m.channel_id)
  AND (m.embedding <=> $1) <= COALESCE($2, 0.70)
ORDER BY m.embedding <=> $1 ASC
LIMIT LEAST(COALESCE($3, 5), 20);

-- -----------------------------------------------------------------------------
-- Query 4: Copilot Token Usage & Consumption Aggregates per User
-- Parameters:
--   $1: p_user_id (UUID, NULL to query current actor)
-- -----------------------------------------------------------------------------
PREPARE rw_qry_copilot_token_usage(
    UUID -- $1: target user_id (NULL for current actor)
) AS
SELECT 
    COALESCE($1, rw_get_current_user_id()) AS user_id,
    u.display_name,
    u.email,
    COUNT(l.id) AS total_queries,
    COALESCE(SUM(l.prompt_tokens), 0)::BIGINT AS total_prompt_tokens,
    COALESCE(SUM(l.completion_tokens), 0)::BIGINT AS total_completion_tokens,
    COALESCE(SUM(l.total_tokens), 0)::BIGINT AS total_tokens_used,
    MAX(l.created_at) AS last_query_at
FROM rw_users u
LEFT JOIN rw_copilot_logs l ON u.id = l.user_id
WHERE u.id = COALESCE($1, rw_get_current_user_id())
GROUP BY u.id, u.display_name, u.email;
