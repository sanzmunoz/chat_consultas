-- =============================================================================
-- Riwi Co. Internal Messaging Platform — Security & RLS Policies (Phase 1)
-- Role: rw_app_role (NOBYPASSRLS)
-- Session context: app.current_user_id (via SET LOCAL)
-- =============================================================================

-- 1. Create dedicated application role without administrative bypasses
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rw_app_role') THEN
        CREATE ROLE rw_app_role WITH LOGIN PASSWORD 'rw_app_secure_pass_2026';
    END IF;
    ALTER ROLE rw_app_role NOBYPASSRLS NOSUPERUSER NOCREATEDB NOCREATEROLE;
END $$;

-- 2. Helper function: retrieves current transaction actor ID
CREATE OR REPLACE FUNCTION rw_get_current_user_id() 
RETURNS UUID 
LANGUAGE plpgsql 
STABLE
AS $$
DECLARE
    v_user_text TEXT;
BEGIN
    v_user_text := current_setting('app.current_user_id', TRUE);
    IF v_user_text IS NULL OR v_user_text = '' THEN
        RETURN NULL;
    END IF;
    RETURN v_user_text::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$;

COMMENT ON FUNCTION rw_get_current_user_id IS 'Returns the active user UUID from transaction session parameter app.current_user_id';

-- 3. Helper function: checks if active actor is a member of the given channel
CREATE OR REPLACE FUNCTION rw_is_channel_member(p_channel_id UUID) 
RETURNS BOOLEAN 
LANGUAGE plpgsql 
STABLE
AS $$
DECLARE
    v_actor_id UUID;
BEGIN
    v_actor_id := rw_get_current_user_id();
    IF v_actor_id IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Return true if user has an explicit membership record in the channel
    RETURN EXISTS (
        SELECT 1 
        FROM rw_channel_members 
        WHERE channel_id = p_channel_id 
          AND user_id = v_actor_id
    );
END;
$$;

COMMENT ON FUNCTION rw_is_channel_member IS 'Validates whether the active actor belongs to a specific channel';

-- 4. Helper function: checks if active actor has administrator role
CREATE OR REPLACE FUNCTION rw_is_admin() 
RETURNS BOOLEAN 
LANGUAGE plpgsql 
STABLE
AS $$
DECLARE
    v_actor_id UUID;
    v_role VARCHAR(20);
BEGIN
    v_actor_id := rw_get_current_user_id();
    IF v_actor_id IS NULL THEN
        RETURN FALSE;
    END IF;

    SELECT role INTO v_role 
    FROM rw_users 
    WHERE id = v_actor_id AND is_active = TRUE;

    RETURN COALESCE(v_role = 'admin', FALSE);
END;
$$;

COMMENT ON FUNCTION rw_is_admin IS 'Checks if the authenticated actor possesses system admin privileges';

-- 5. Enable and enforce RLS across core tables
ALTER TABLE rw_channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE rw_channels FORCE ROW LEVEL SECURITY;

ALTER TABLE rw_channel_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE rw_channel_members FORCE ROW LEVEL SECURITY;

ALTER TABLE rw_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE rw_messages FORCE ROW LEVEL SECURITY;

ALTER TABLE rw_read_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE rw_read_receipts FORCE ROW LEVEL SECURITY;

ALTER TABLE rw_copilot_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE rw_copilot_logs FORCE ROW LEVEL SECURITY;

ALTER TABLE rw_refresh_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE rw_refresh_tokens FORCE ROW LEVEL SECURITY;

-- 6. Drop previous policies for clean idempotency
DROP POLICY IF EXISTS rw_pol_channels_select ON rw_channels;
DROP POLICY IF EXISTS rw_pol_channels_insert ON rw_channels;
DROP POLICY IF EXISTS rw_pol_channels_update ON rw_channels;

DROP POLICY IF EXISTS rw_pol_channel_members_select ON rw_channel_members;
DROP POLICY IF EXISTS rw_pol_channel_members_insert ON rw_channel_members;

DROP POLICY IF EXISTS rw_pol_messages_select ON rw_messages;
DROP POLICY IF EXISTS rw_pol_messages_insert ON rw_messages;
DROP POLICY IF EXISTS rw_pol_messages_update ON rw_messages;

DROP POLICY IF EXISTS rw_pol_read_receipts_select ON rw_read_receipts;
DROP POLICY IF EXISTS rw_pol_read_receipts_insert ON rw_read_receipts;

DROP POLICY IF EXISTS rw_pol_copilot_logs_select ON rw_copilot_logs;
DROP POLICY IF EXISTS rw_pol_copilot_logs_insert ON rw_copilot_logs;

DROP POLICY IF EXISTS rw_pol_refresh_tokens_all ON rw_refresh_tokens;

-- 7. Policies for rw_channels:
-- Users can view channels where they are members OR public channels
CREATE POLICY rw_pol_channels_select ON rw_channels
FOR SELECT
USING (
    type = 'public' 
    OR created_by = rw_get_current_user_id() 
    OR rw_is_channel_member(id)
    OR rw_is_admin()
);

CREATE POLICY rw_pol_channels_insert ON rw_channels
FOR INSERT
WITH CHECK (
    created_by = rw_get_current_user_id()
);

CREATE POLICY rw_pol_channels_update ON rw_channels
FOR UPDATE
USING (
    created_by = rw_get_current_user_id() OR rw_is_admin()
);

-- 8. Policies for rw_channel_members:
CREATE POLICY rw_pol_channel_members_select ON rw_channel_members
FOR SELECT
USING (
    user_id = rw_get_current_user_id()
    OR rw_is_channel_member(channel_id)
    OR rw_is_admin()
);

CREATE POLICY rw_pol_channel_members_insert ON rw_channel_members
FOR INSERT
WITH CHECK (
    user_id = rw_get_current_user_id()
    OR rw_is_channel_member(channel_id)
    OR rw_is_admin()
);

-- 9. Policies for rw_messages:
-- Critical Requirement: Actor CANNOT view or search messages from channels where they are not a member
CREATE POLICY rw_pol_messages_select ON rw_messages
FOR SELECT
USING (
    is_deleted = FALSE 
    AND rw_is_channel_member(channel_id)
);

CREATE POLICY rw_pol_messages_insert ON rw_messages
FOR INSERT
WITH CHECK (
    author_id = rw_get_current_user_id() 
    AND rw_is_channel_member(channel_id)
);

CREATE POLICY rw_pol_messages_update ON rw_messages
FOR UPDATE
USING (
    author_id = rw_get_current_user_id() OR rw_is_admin()
)
WITH CHECK (
    author_id = rw_get_current_user_id() OR rw_is_admin()
);

-- 10. Policies for rw_read_receipts:
CREATE POLICY rw_pol_read_receipts_select ON rw_read_receipts
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM rw_messages m 
        WHERE m.id = rw_read_receipts.message_id 
          AND rw_is_channel_member(m.channel_id)
    )
);

CREATE POLICY rw_pol_read_receipts_insert ON rw_read_receipts
FOR INSERT
WITH CHECK (
    user_id = rw_get_current_user_id()
);

-- 11. Policies for rw_copilot_logs:
CREATE POLICY rw_pol_copilot_logs_select ON rw_copilot_logs
FOR SELECT
USING (
    user_id = rw_get_current_user_id() OR rw_is_admin()
);

CREATE POLICY rw_pol_copilot_logs_insert ON rw_copilot_logs
FOR INSERT
WITH CHECK (
    user_id = rw_get_current_user_id()
);

-- 12. Policies for rw_refresh_tokens:
CREATE POLICY rw_pol_refresh_tokens_all ON rw_refresh_tokens
FOR ALL
USING (
    user_id = rw_get_current_user_id()
)
WITH CHECK (
    user_id = rw_get_current_user_id()
);

-- 13. Vista: rw_v_user_conversations
-- Summarizes accessible channels, participant counts, unread counters, and last message info
CREATE OR REPLACE VIEW rw_v_user_conversations AS
SELECT 
    c.id AS channel_id,
    c.name AS channel_name,
    c.description AS channel_description,
    c.type AS channel_type,
    c.is_archived,
    cm.role AS user_channel_role,
    cm.joined_at,
    (
        SELECT COUNT(DISTINCT m_all.user_id) 
        FROM rw_channel_members m_all 
        WHERE m_all.channel_id = c.id
    ) AS member_count,
    (
        SELECT COUNT(msg.id) 
        FROM rw_messages msg
        WHERE msg.channel_id = c.id 
          AND msg.is_deleted = FALSE 
          AND msg.author_id != rw_get_current_user_id()
          AND NOT EXISTS (
              SELECT 1 FROM rw_read_receipts rr 
              WHERE rr.message_id = msg.id 
                AND rr.user_id = rw_get_current_user_id()
          )
    ) AS unread_count,
    last_msg.id AS last_message_id,
    last_msg.content AS last_message_content,
    last_msg.created_at AS last_message_created_at,
    last_author.display_name AS last_message_author_name
FROM rw_channels c
JOIN rw_channel_members cm ON c.id = cm.channel_id AND cm.user_id = rw_get_current_user_id()
LEFT JOIN LATERAL (
    SELECT lm.id, lm.content, lm.created_at, lm.author_id
    FROM rw_messages lm
    WHERE lm.channel_id = c.id AND lm.is_deleted = FALSE
    ORDER BY lm.created_at DESC, lm.id DESC
    LIMIT 1
) last_msg ON TRUE
LEFT JOIN rw_users last_author ON last_msg.author_id = last_author.id
WHERE c.is_archived = FALSE;

COMMENT ON VIEW rw_v_user_conversations IS 'Dynamic view computing active channels, unread messages count, and latest message preview per actor';

-- 14. Grant table and sequence permissions to application role
GRANT USAGE ON SCHEMA public TO rw_app_role;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO rw_app_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO rw_app_role;
-- Explicitly revoke physical DELETE permissions from application role
REVOKE DELETE ON rw_users, rw_channels, rw_channel_members, rw_messages, rw_read_receipts FROM rw_app_role;
