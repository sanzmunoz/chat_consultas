export interface CopilotCitation {
  msg_ref: string;
  channel_name: string;
  author_name: string;
  content_snippet: string;
  similarity_score: number;
}

export interface CopilotQueryResponse {
  query: string;
  response: string;
  citations: CopilotCitation[];
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  model: string;
  prompt_version: string;
}

export interface CopilotUsage {
  user_id: string;
  display_name: string;
  email: string;
  total_queries: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens_used: number;
  last_query_at?: string;
}
