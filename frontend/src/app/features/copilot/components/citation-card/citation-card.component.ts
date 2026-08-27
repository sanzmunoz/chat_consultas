import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CopilotCitation } from '../../../../core/models/copilot.model';

@Component({
  selector: 'app-citation-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="citation-box">
      <div class="citation-header">
        <span class="badge badge-mint">{{ citation.msg_ref }}</span>
        <span class="citation-channel">{{ citation.channel_name }}</span>
        <span class="citation-author">{{ citation.author_name }}</span>
        <span class="citation-score">{{ (citation.similarity_score * 100).toFixed(1) }}% sim</span>
      </div>
      <p class="citation-snippet">"{{ citation.content_snippet }}"</p>
    </div>
  `,
  styles: [`
    .citation-box {
      background-color: var(--mint-surface);
      border: 1px solid var(--mint-green);
      padding: 8px 12px;
      margin-top: 6px;
    }
    .citation-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;
      font-size: 11px;
    }
    .citation-channel {
      font-weight: 700;
      color: var(--mint-dark);
    }
    .citation-author {
      font-weight: 600;
      color: var(--text-main);
    }
    .citation-score {
      margin-left: auto;
      font-size: 10px;
      color: var(--text-muted);
    }
    .citation-snippet {
      margin: 0;
      font-size: 12px;
      color: var(--text-main);
      font-style: italic;
      line-height: 1.35;
    }
  `]
})
export class CitationCardComponent {
  @Input({ required: true }) citation!: CopilotCitation;
}
