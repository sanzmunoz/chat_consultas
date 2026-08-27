export interface Message {
  id: string;
  msg_ref?: string;
  channel_id: string;
  author_id: string;
  author_name?: string;
  author_username?: string;
  author_position?: string;
  content: string;
  original_content?: string;
  status: 'pending' | 'sent' | 'failed';
  is_edited: boolean;
  edited_at?: string;
  is_deleted: boolean;
  created_at: string;
  read_count: number;
  is_read_by_me: boolean;
  highlighted_content?: string;
}

export interface KeysetMessageList {
  messages: Message[];
  next_cursor_created_at?: string;
  next_cursor_id?: string;
  has_more: boolean;
}

export interface SearchMessageItem {
  id: string;
  msg_ref?: string;
  channel_id: string;
  channel_name: string;
  author_id: string;
  author_name: string;
  author_username: string;
  content: string;
  highlighted_content?: string;
  search_rank: number;
  created_at: string;
}
