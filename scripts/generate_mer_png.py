import matplotlib.pyplot as plt
import matplotlib.patches as patches

def generate_mer_diagram():
    fig, ax = plt.subplots(figsize=(16, 12), dpi=300)
    ax.set_facecolor("#0F172A") # Dark slate
    fig.patch.set_facecolor("#0F172A")

    # Title
    plt.title("Modelo Entidad-Relación — Riwi Co. Mensajería (bd_santiago_munoz_nakamoto)", 
              fontsize=18, fontweight='bold', color='#38BDF8', pad=25)

    # Box styles
    def draw_entity_box(ax, x, y, width, height, title, attributes, color='#1E293B', border='#38BDF8', title_bg='#0284C7'):
        # Main body
        rect = patches.FancyBboxPatch((x, y - height), width, height,
                                      boxstyle="round,pad=0.02,rounding_size=0.08",
                                      linewidth=1.5, edgecolor=border, facecolor=color)
        ax.add_patch(rect)
        
        # Title header
        header_height = 0.55
        header_rect = patches.FancyBboxPatch((x, y - header_height), width, header_height,
                                            boxstyle="round,pad=0.02,rounding_size=0.08",
                                            linewidth=1.5, edgecolor=border, facecolor=title_bg)
        ax.add_patch(header_rect)
        
        # Title text
        ax.text(x + width / 2.0, y - header_height / 2.0, title,
                ha='center', va='center', fontsize=11, fontweight='bold', color='#FFFFFF')
        
        # Attributes text
        line_y = y - header_height - 0.28
        for attr in attributes:
            color_txt = "#E2E8F0"
            if "PK" in attr:
                color_txt = "#FACC15" # Yellow for PK
            elif "FK" in attr:
                color_txt = "#38BDF8" # Blue for FK
            elif "UK" in attr:
                color_txt = "#4ADE80" # Green for UK
            
            ax.text(x + 0.15, line_y, attr, ha='left', va='center', fontsize=8.5, color=color_txt, fontfamily='monospace')
            line_y -= 0.32

    # Entities definition
    # 1. rw_users
    users_attrs = [
        "id: UUID (PK)",
        "username: VARCHAR(50) (UK)",
        "email: VARCHAR(120) (UK)",
        "password_hash: VARCHAR(255)",
        "display_name: VARCHAR(100)",
        "role: VARCHAR(20) [admin|member]",
        "position: VARCHAR(80)",
        "is_active: BOOLEAN (DEFAULT TRUE)",
        "created_at: TIMESTAMPTZ (UTC)",
        "updated_at: TIMESTAMPTZ (UTC)"
    ]
    draw_entity_box(ax, 0.5, 10.5, 4.2, 4.0, "rw_users", users_attrs, border='#38BDF8', title_bg='#0284C7')

    # 2. rw_channels
    channels_attrs = [
        "id: UUID (PK)",
        "name: VARCHAR(80) (UK)",
        "description: TEXT",
        "type: VARCHAR(20) [public|private]",
        "created_by: UUID (FK -> rw_users)",
        "is_archived: BOOLEAN",
        "created_at: TIMESTAMPTZ (UTC)",
        "updated_at: TIMESTAMPTZ (UTC)"
    ]
    draw_entity_box(ax, 6.0, 10.5, 4.4, 3.4, "rw_channels", channels_attrs, border='#A855F7', title_bg='#7E22CE')

    # 3. rw_channel_members
    members_attrs = [
        "id: UUID (PK)",
        "channel_id: UUID (FK -> rw_channels)",
        "user_id: UUID (FK -> rw_users)",
        "role: VARCHAR(20) [owner|member]",
        "joined_at: TIMESTAMPTZ (UTC)",
        "UK: (channel_id, user_id)"
    ]
    draw_entity_box(ax, 6.0, 6.0, 4.4, 2.7, "rw_channel_members", members_attrs, border='#EC4899', title_bg='#BE185D')

    # 4. rw_messages
    messages_attrs = [
        "id: UUID (PK)",
        "msg_ref: VARCHAR(50) (UK)",
        "channel_id: UUID (FK -> rw_channels)",
        "author_id: UUID (FK -> rw_users)",
        "content: TEXT (NOT NULL)",
        "original_content: TEXT (Audit)",
        "search_vector: TSVECTOR (GIN idx)",
        "embedding: VECTOR(1536) (HNSW)",
        "is_edited: BOOLEAN",
        "edited_at: TIMESTAMPTZ (UTC)",
        "is_deleted: BOOLEAN (Soft Delete)",
        "deleted_at: TIMESTAMPTZ (UTC)",
        "status: VARCHAR(20) [sent|...]",
        "created_at: TIMESTAMPTZ (UTC)",
        "updated_at: TIMESTAMPTZ (UTC)"
    ]
    draw_entity_box(ax, 11.5, 10.5, 4.2, 5.5, "rw_messages", messages_attrs, border='#10B981', title_bg='#047857')

    # 5. rw_read_receipts
    receipts_attrs = [
        "id: UUID (PK)",
        "message_id: UUID (FK -> rw_messages)",
        "user_id: UUID (FK -> rw_users)",
        "read_at: TIMESTAMPTZ (UTC)",
        "UK: (message_id, user_id)"
    ]
    draw_entity_box(ax, 11.5, 4.2, 4.2, 2.4, "rw_read_receipts", receipts_attrs, border='#F59E0B', title_bg='#B45309')

    # 6. rw_copilot_logs
    copilot_attrs = [
        "id: UUID (PK)",
        "user_id: UUID (FK -> rw_users)",
        "query: TEXT",
        "response: TEXT",
        "prompt_tokens: INT",
        "completion_tokens: INT",
        "total_tokens: INT",
        "model: VARCHAR(50)",
        "prompt_version: VARCHAR(20)",
        "created_at: TIMESTAMPTZ (UTC)"
    ]
    draw_entity_box(ax, 0.5, 5.5, 4.2, 3.9, "rw_copilot_logs", copilot_attrs, border='#06B6D4', title_bg='#0E7490')

    # 7. rw_refresh_tokens
    token_attrs = [
        "id: UUID (PK)",
        "user_id: UUID (FK -> rw_users)",
        "token_hash: VARCHAR(255) (UK)",
        "expires_at: TIMESTAMPTZ (UTC)",
        "is_revoked: BOOLEAN",
        "created_at: TIMESTAMPTZ (UTC)"
    ]
    draw_entity_box(ax, 0.5, 1.0, 4.2, 2.7, "rw_refresh_tokens", token_attrs, border='#6366F1', title_bg='#4338CA')

    # Connecting arrows / relationships
    def draw_relation(ax, start, end, label, color='#94A3B8'):
        ax.annotate('', xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.6, ls='--'))
        mid_x = (start[0] + end[0]) / 2.0
        mid_y = (start[1] + end[1]) / 2.0
        ax.text(mid_x, mid_y, label, fontsize=8, color='#CBD5E1', ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#1E293B", edgecolor=color, lw=0.8))

    # user -> channels (creates)
    draw_relation(ax, (4.7, 9.5), (6.0, 9.5), "creates (1:N)", '#38BDF8')
    # channels -> members
    draw_relation(ax, (8.2, 7.1), (8.2, 6.0), "has (1:N)", '#EC4899')
    # users -> members
    draw_relation(ax, (4.7, 7.5), (6.0, 5.0), "joins (1:N)", '#EC4899')
    # channels -> messages
    draw_relation(ax, (10.4, 9.5), (11.5, 9.5), "hosts (1:N)", '#10B981')
    # users -> messages
    draw_relation(ax, (4.7, 10.0), (11.5, 10.0), "authors (1:N)", '#10B981')
    # messages -> receipts
    draw_relation(ax, (13.6, 5.0), (13.6, 4.2), "tracks (1:N)", '#F59E0B')
    # users -> receipts
    draw_relation(ax, (4.7, 6.8), (11.5, 3.2), "reads (1:N)", '#F59E0B')
    # users -> copilot_logs
    draw_relation(ax, (2.6, 6.5), (2.6, 5.5), "queries (1:N)", '#06B6D4')
    # users -> refresh_tokens
    draw_relation(ax, (2.6, 1.6), (2.6, 1.0), "holds (1:N)", '#6366F1')

    ax.set_xlim(-0.2, 16.2)
    ax.set_ylim(-2.0, 11.5)
    ax.axis('off')

    plt.tight_layout()
    plt.savefig("/home/cohorte5/Documentos/san_mz/chat_consultas_riwi/docs/MER.png", bbox_inches='tight', facecolor='#0F172A')
    plt.close()
    print("MER.png generated successfully!")

if __name__ == "__main__":
    generate_mer_diagram()
