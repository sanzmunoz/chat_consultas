export interface ChannelSummary {
  channel_id: string;
  channel_name: string;
  channel_description?: string;
  channel_type: 'public' | 'private';
  is_archived: boolean;
  user_channel_role: 'owner' | 'member';
  member_count: number;
  unread_count: number;
  last_message_id?: string;
  last_message_content?: string;
  last_message_created_at?: string;
  last_message_author_name?: string;
}

export interface ChannelMember {
  membership_id: string;
  user_id: string;
  display_name: string;
  username: string;
  email: string;
  position: string;
  role: 'owner' | 'member';
  joined_at: string;
}
