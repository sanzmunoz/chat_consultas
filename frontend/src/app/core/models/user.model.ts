export interface User {
  id: string;
  username: string;
  email: string;
  display_name: string;
  role: 'admin' | 'member';
  position: string;
  is_active?: boolean;
  created_at?: string;
  channels_count?: number;
  messages_count?: number;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user?: User;
}
