-- =============================================================================
-- Riwi Co. Internal Messaging Platform — DDL Schema (Phase 1)
-- Database: bd_santiago_munoz_nakamoto
-- Mandatory prefix: rw_
-- Clean Architecture & 3FN Normalized Relational Model
-- =============================================================================

-- 1. Required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 2. Users table: stores internal organization members and authentication info
CREATE TABLE IF NOT EXISTS rw_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'member')),
    position VARCHAR(80) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE rw_users IS 'Organization users and authentication credentials';
COMMENT ON COLUMN rw_users.role IS 'User system permission role: admin or member';

-- 3. Channels table: communication workspaces (public or private)
CREATE TABLE IF NOT EXISTS rw_channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(80) NOT NULL UNIQUE,
    description TEXT,
    type VARCHAR(20) NOT NULL CHECK (type IN ('public', 'private')),
    created_by UUID NOT NULL REFERENCES rw_users(id) ON DELETE RESTRICT,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE rw_channels IS 'Communication channels for team conversations';
COMMENT ON COLUMN rw_channels.type IS 'Channel access visibility: public or private';

-- 4. Channel Members table: explicit channel membership and channel roles
CREATE TABLE IF NOT EXISTS rw_channel_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_id UUID NOT NULL REFERENCES rw_channels(id) ON DELETE RESTRICT,
    user_id UUID NOT NULL REFERENCES rw_users(id) ON DELETE RESTRICT,
    role VARCHAR(20) NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'member')),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT rw_uk_channel_member UNIQUE (channel_id, user_id)
);

COMMENT ON TABLE rw_channel_members IS 'User memberships and participation roles in channels';

-- 5. Messages table: chat messages with soft-delete, audit and vector embeddings
CREATE TABLE IF NOT EXISTS rw_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    msg_ref VARCHAR(50) UNIQUE,
    channel_id UUID NOT NULL REFERENCES rw_channels(id) ON DELETE RESTRICT,
    author_id UUID NOT NULL REFERENCES rw_users(id) ON DELETE RESTRICT,
    content TEXT NOT NULL,
    original_content TEXT,
    search_vector tsvector,
    embedding vector(1536),
    is_edited BOOLEAN NOT NULL DEFAULT FALSE,
    edited_at TIMESTAMPTZ,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'sent' CHECK (status IN ('pending', 'sent', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE rw_messages IS 'Channel chat messages preserving history and vector representations';
COMMENT ON COLUMN rw_messages.original_content IS 'Preserves message content prior to first modification';
COMMENT ON COLUMN rw_messages.is_deleted IS 'Logical soft-delete flag to avoid physical data loss';

-- 6. Read Receipts table: tracking read state per message and user
CREATE TABLE IF NOT EXISTS rw_read_receipts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID NOT NULL REFERENCES rw_messages(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES rw_users(id) ON DELETE RESTRICT,
    read_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT rw_uk_message_user_read UNIQUE (message_id, user_id)
);

COMMENT ON TABLE rw_read_receipts IS 'Message read receipts per individual user';

-- 7. Copilot Logs table: tracks AI assistant token usage and queries
CREATE TABLE IF NOT EXISTS rw_copilot_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES rw_users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    model VARCHAR(50) NOT NULL,
    prompt_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE rw_copilot_logs IS 'Audit trail for AI Copilot queries and token consumption';

-- 8. Refresh Tokens table: rotates refresh tokens with revocation support
CREATE TABLE IF NOT EXISTS rw_refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES rw_users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE rw_refresh_tokens IS 'Secure refresh token sessions with one-time rotation';

-- 9. Partial Unique Index: ensures active messages have unique msg_ref
CREATE UNIQUE INDEX IF NOT EXISTS rw_idx_uq_active_msg_ref 
ON rw_messages (msg_ref) 
WHERE is_deleted = FALSE;

-- 10. Performance Indexes: Keyset pagination, Full-Text GIN, and HNSW vector index
CREATE INDEX IF NOT EXISTS rw_idx_messages_keyset 
ON rw_messages (channel_id, created_at DESC, id DESC) 
WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS rw_idx_messages_search 
ON rw_messages USING GIN (search_vector);

CREATE INDEX IF NOT EXISTS rw_idx_messages_embedding 
ON rw_messages USING HNSW (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS rw_idx_copilot_user_created 
ON rw_copilot_logs (user_id, created_at DESC);
