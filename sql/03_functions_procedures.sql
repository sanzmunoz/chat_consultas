-- =============================================================================
-- Riwi Co. Internal Messaging Platform — Functions, Triggers & Procedures (Phase 1)
-- Database: bd_santiago_munoz_nakamoto
-- Atomic transaction safety & business logic encapsulated in PostgreSQL
-- =============================================================================

-- 1. Trigger function: Maintains full-text search tsvector and edit metadata
CREATE OR REPLACE FUNCTION rw_fn_sync_message_search() 
RETURNS TRIGGER 
LANGUAGE plpgsql 
AS $$
BEGIN
    -- Synchronize Spanish full-text search vector
    NEW.search_vector := to_tsvector('spanish', COALESCE(NEW.content, ''));
    NEW.updated_at := CURRENT_TIMESTAMP;

    -- Track message modifications while preserving original content
    IF TG_OP = 'UPDATE' THEN
        IF NEW.content IS DISTINCT FROM OLD.content THEN
            NEW.is_edited := TRUE;
            NEW.edited_at := CURRENT_TIMESTAMP;
            -- Preserve initial unedited content on first edit
            IF OLD.original_content IS NULL THEN
                NEW.original_content := OLD.content;
            ELSE
                NEW.original_content := OLD.original_content;
            END IF;
        END IF;

        -- Soft delete tracking
        IF NEW.is_deleted = TRUE AND OLD.is_deleted = FALSE THEN
            NEW.deleted_at := CURRENT_TIMESTAMP;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS rw_trg_message_search ON rw_messages;
CREATE TRIGGER rw_trg_message_search
BEFORE INSERT OR UPDATE OF content, is_deleted ON rw_messages
FOR EACH ROW
EXECUTE FUNCTION rw_fn_sync_message_search();

-- 2. Atomic Transaction Function: Send message with membership check and read receipt
CREATE OR REPLACE FUNCTION rw_fn_send_message(
    p_channel_id UUID,
    p_content TEXT,
    p_embedding vector(1536) DEFAULT NULL,
    p_status VARCHAR DEFAULT 'sent',
    p_msg_ref VARCHAR DEFAULT NULL
) 
RETURNS UUID 
LANGUAGE plpgsql 
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_actor_id UUID;
    v_channel_archived BOOLEAN;
    v_new_message_id UUID;
    v_ref VARCHAR(50);
BEGIN
    -- 1. Validate authenticated session
    v_actor_id := rw_get_current_user_id();
    IF v_actor_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: No active actor authenticated in transaction.'
            USING ERRCODE = '28000';
    END IF;

    -- 2. Validate channel existence and state
    SELECT is_archived INTO v_channel_archived
    FROM rw_channels
    WHERE id = p_channel_id;

    IF v_channel_archived IS NULL THEN
        RAISE EXCEPTION 'Channel % does not exist.', p_channel_id
            USING ERRCODE = '23503';
    ELSIF v_channel_archived = TRUE THEN
        RAISE EXCEPTION 'Cannot send message to an archived channel.'
            USING ERRCODE = '22023';
    END IF;

    -- 3. Validate channel membership
    IF NOT rw_is_channel_member(p_channel_id) THEN
        RAISE EXCEPTION 'Access denied: Actor % is not a member of channel %.', v_actor_id, p_channel_id
            USING ERRCODE = '42501';
    END IF;

    -- 4. Validate content
    IF p_content IS NULL OR trim(p_content) = '' THEN
        IF p_status != 'failed' THEN
            RAISE EXCEPTION 'Message content cannot be empty for successful messages.'
                USING ERRCODE = '23514';
        END IF;
    END IF;

    -- 5. Generate message reference if not provided
    v_ref := COALESCE(p_msg_ref, 'msg-' || substr(md5(random()::text || clock_timestamp()::text), 1, 8));

    -- 6. Insert message
    INSERT INTO rw_messages (
        msg_ref,
        channel_id,
        author_id,
        content,
        embedding,
        status,
        created_at,
        updated_at
    ) VALUES (
        v_ref,
        p_channel_id,
        v_actor_id,
        COALESCE(p_content, ''),
        p_embedding,
        COALESCE(p_status, 'sent'),
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ) RETURNING id INTO v_new_message_id;

    -- 7. Automatically record read receipt for the author
    INSERT INTO rw_read_receipts (message_id, user_id, read_at)
    VALUES (v_new_message_id, v_actor_id, CURRENT_TIMESTAMP)
    ON CONFLICT (message_id, user_id) DO NOTHING;

    RETURN v_new_message_id;
END;
$$;

COMMENT ON FUNCTION rw_fn_send_message IS 'Atomic transactional message creation verifying channel membership and marking self-read';

-- 3. Atomic Function: Edit message preserving previous state
CREATE OR REPLACE FUNCTION rw_fn_edit_message(
    p_message_id UUID,
    p_new_content TEXT
) 
RETURNS BOOLEAN 
LANGUAGE plpgsql 
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_actor_id UUID;
    v_author_id UUID;
    v_is_deleted BOOLEAN;
BEGIN
    v_actor_id := rw_get_current_user_id();
    IF v_actor_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: No active actor.' USING ERRCODE = '28000';
    END IF;

    SELECT author_id, is_deleted INTO v_author_id, v_is_deleted
    FROM rw_messages 
    WHERE id = p_message_id;

    IF v_author_id IS NULL THEN
        RAISE EXCEPTION 'Message % not found.', p_message_id USING ERRCODE = '02000';
    END IF;

    IF v_is_deleted = TRUE THEN
        RAISE EXCEPTION 'Cannot edit a deleted message.' USING ERRCODE = '22023';
    END IF;

    IF v_author_id != v_actor_id AND NOT rw_is_admin() THEN
        RAISE EXCEPTION 'Permission denied: Only the author can edit this message.' USING ERRCODE = '42501';
    END IF;

    UPDATE rw_messages 
    SET content = p_new_content
    WHERE id = p_message_id;

    RETURN TRUE;
END;
$$;

-- 4. Atomic Function: Logical soft-delete of message
CREATE OR REPLACE FUNCTION rw_fn_delete_message(
    p_message_id UUID
) 
RETURNS BOOLEAN 
LANGUAGE plpgsql 
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_actor_id UUID;
    v_author_id UUID;
BEGIN
    v_actor_id := rw_get_current_user_id();
    IF v_actor_id IS NULL THEN
        RAISE EXCEPTION 'Unauthorized: No active actor.' USING ERRCODE = '28000';
    END IF;

    SELECT author_id INTO v_author_id
    FROM rw_messages 
    WHERE id = p_message_id AND is_deleted = FALSE;

    IF v_author_id IS NULL THEN
        RAISE EXCEPTION 'Message % not found or already deleted.', p_message_id USING ERRCODE = '02000';
    END IF;

    IF v_author_id != v_actor_id AND NOT rw_is_admin() THEN
        RAISE EXCEPTION 'Permission denied: Only the author or an admin can delete this message.' USING ERRCODE = '42501';
    END IF;

    UPDATE rw_messages 
    SET is_deleted = TRUE,
        deleted_at = CURRENT_TIMESTAMP
    WHERE id = p_message_id;

    RETURN TRUE;
END;
$$;

-- 5. Stored Function & Procedure 1: rw_fn_query_users / rw_sp_query_users
-- Queries users with filter parameters, keyset pagination, and aggregated activity metrics
CREATE OR REPLACE FUNCTION rw_fn_query_users(
    p_search TEXT DEFAULT NULL,
    p_role VARCHAR DEFAULT NULL,
    p_cursor_created_at TIMESTAMPTZ DEFAULT NULL,
    p_cursor_id UUID DEFAULT NULL,
    p_limit INT DEFAULT 20
) 
RETURNS TABLE (
    id UUID,
    username VARCHAR,
    email VARCHAR,
    display_name VARCHAR,
    role VARCHAR,
    "position" VARCHAR,
    is_active BOOLEAN,
    created_at TIMESTAMPTZ,
    channels_count BIGINT,
    messages_count BIGINT
) 
LANGUAGE sql 
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT 
        u.id,
        u.username,
        u.email,
        u.display_name,
        u.role,
        u.position,
        u.is_active,
        u.created_at,
        (
            SELECT COUNT(cm.id) 
            FROM rw_channel_members cm 
            WHERE cm.user_id = u.id
        ) AS channels_count,
        (
            SELECT COUNT(m.id) 
            FROM rw_messages m 
            WHERE m.author_id = u.id AND m.is_deleted = FALSE
        ) AS messages_count
    FROM rw_users u
    WHERE (
        p_search IS NULL 
        OR u.display_name ILIKE '%' || p_search || '%' 
        OR u.username ILIKE '%' || p_search || '%' 
        OR u.email ILIKE '%' || p_search || '%'
        OR u.position ILIKE '%' || p_search || '%'
    )
    AND (p_role IS NULL OR u.role = p_role)
    AND (
        p_cursor_created_at IS NULL 
        OR (u.created_at, u.id) < (p_cursor_created_at, p_cursor_id)
    )
    ORDER BY u.created_at DESC, u.id DESC
    LIMIT LEAST(COALESCE(p_limit, 20), 100);
$$;

DROP PROCEDURE IF EXISTS rw_sp_query_users;
CREATE OR REPLACE PROCEDURE rw_sp_query_users(
    IN p_search TEXT,
    IN p_role VARCHAR,
    IN p_cursor_created_at TIMESTAMPTZ,
    IN p_cursor_id UUID,
    IN p_limit INT,
    INOUT p_result_cursor REFCURSOR DEFAULT 'users_cursor'
) 
LANGUAGE plpgsql 
AS $$
BEGIN
    OPEN p_result_cursor FOR 
        SELECT * FROM rw_fn_query_users(p_search, p_role, p_cursor_created_at, p_cursor_id, p_limit);
END;
$$;

-- 6. Stored Procedure 2: rw_sp_edit_or_delete_user
-- Encapsulates profile updates and safe logical deactivations with session invalidation
DROP PROCEDURE IF EXISTS rw_sp_edit_or_delete_user;
CREATE OR REPLACE PROCEDURE rw_sp_edit_or_delete_user(
    IN p_target_user_id UUID,
    IN p_action VARCHAR,
    IN p_display_name VARCHAR,
    IN p_position VARCHAR,
    IN p_role VARCHAR,
    INOUT p_success BOOLEAN DEFAULT FALSE,
    INOUT p_message TEXT DEFAULT ''
) 
LANGUAGE plpgsql 
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_actor_id UUID;
    v_is_admin BOOLEAN;
    v_user_exists BOOLEAN;
BEGIN
    v_actor_id := rw_get_current_user_id();
    IF v_actor_id IS NULL THEN
        p_success := FALSE;
        p_message := 'Unauthorized: No active actor session.';
        RETURN;
    END IF;

    v_is_admin := rw_is_admin();

    -- Verify target user existence
    SELECT EXISTS (SELECT 1 FROM rw_users WHERE id = p_target_user_id) 
    INTO v_user_exists;

    IF NOT v_user_exists THEN
        p_success := FALSE;
        p_message := 'User not found.';
        RETURN;
    END IF;

    -- Action 1: EDIT Profile
    IF upper(p_action) = 'EDIT' THEN
        -- Permission: User can edit own profile, or Admin can edit anyone
        IF v_actor_id != p_target_user_id AND NOT v_is_admin THEN
            p_success := FALSE;
            p_message := 'Permission denied: Cannot edit another user profile without admin privileges.';
            RETURN;
        END IF;

        -- Only admin can alter system roles
        IF p_role IS NOT NULL AND p_role != '' AND NOT v_is_admin THEN
            p_success := FALSE;
            p_message := 'Permission denied: Only administrators can modify user roles.';
            RETURN;
        END IF;

        UPDATE rw_users 
        SET 
            display_name = COALESCE(NULLIF(p_display_name, ''), display_name),
            position = COALESCE(NULLIF(p_position, ''), position),
            role = CASE 
                WHEN v_is_admin AND p_role IN ('admin', 'member') THEN p_role 
                ELSE role 
            END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = p_target_user_id;

        p_success := TRUE;
        p_message := 'User profile successfully updated.';
        RETURN;

    -- Action 2: DELETE / Deactivate User
    ELSIF upper(p_action) = 'DELETE' THEN
        -- Only admin can deactivate users
        IF NOT v_is_admin THEN
            p_success := FALSE;
            p_message := 'Permission denied: Only administrators can deactivate users.';
            RETURN;
        END IF;

        -- Prevent admin self-deactivation lockout
        IF v_actor_id = p_target_user_id THEN
            p_success := FALSE;
            p_message := 'Operation rejected: Cannot deactivate own administrator account.';
            RETURN;
        END IF;

        -- 1. Logical soft-deactivation (preserves history and foreign key constraints)
        UPDATE rw_users 
        SET is_active = FALSE,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = p_target_user_id;

        -- 2. Revoke all active refresh tokens for immediate session invalidation
        UPDATE rw_refresh_tokens 
        SET is_revoked = TRUE 
        WHERE user_id = p_target_user_id AND is_revoked = FALSE;

        p_success := TRUE;
        p_message := 'User deactivated and active sessions revoked.';
        RETURN;

    ELSE
        p_success := FALSE;
        p_message := 'Invalid action. Must be EDIT or DELETE.';
        RETURN;
    END IF;
END;
$$;

-- 7. Functions for Refresh Token Management (SECURITY DEFINER for pre-authentication operations)
CREATE OR REPLACE FUNCTION rw_fn_save_refresh_token(
    p_user_id UUID,
    p_token_hash VARCHAR,
    p_expires_at TIMESTAMPTZ
) 
RETURNS VOID 
LANGUAGE plpgsql 
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO rw_refresh_tokens (user_id, token_hash, expires_at, is_revoked)
    VALUES (p_user_id, p_token_hash, p_expires_at, FALSE);
END;
$$;

CREATE OR REPLACE FUNCTION rw_fn_rotate_refresh_token(
    p_old_token_hash VARCHAR,
    p_new_token_hash VARCHAR,
    p_new_expires_at TIMESTAMPTZ
) 
RETURNS UUID 
LANGUAGE plpgsql 
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_token_id UUID;
    v_user_id UUID;
    v_expires_at TIMESTAMPTZ;
    v_is_revoked BOOLEAN;
BEGIN
    -- Look up old token
    SELECT id, user_id, expires_at, is_revoked 
    INTO v_token_id, v_user_id, v_expires_at, v_is_revoked
    FROM rw_refresh_tokens
    WHERE token_hash = p_old_token_hash
    FOR UPDATE;

    IF v_token_id IS NULL OR v_is_revoked = TRUE OR v_expires_at < CURRENT_TIMESTAMP THEN
        RETURN NULL;
    END IF;

    -- Revoke old token
    UPDATE rw_refresh_tokens 
    SET is_revoked = TRUE 
    WHERE id = v_token_id;

    -- Save new token
    INSERT INTO rw_refresh_tokens (user_id, token_hash, expires_at, is_revoked)
    VALUES (v_user_id, p_new_token_hash, p_new_expires_at, FALSE);

    RETURN v_user_id;
END;
$$;
