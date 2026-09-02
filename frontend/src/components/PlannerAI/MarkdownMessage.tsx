import { type FC } from 'react';

/**
 * Lightweight markdown-to-HTML renderer for AI chat messages.
 * Handles headings, bold, italic, bullet lists, numbered lists, and line breaks.
 * No external dependencies.
 */

interface MarkdownMessageProps {
  content: string;
}

export const MarkdownMessage: FC<MarkdownMessageProps> = ({ content }) => {
  const html = renderMarkdown(content);
  return (
    <div
      className="ai-markdown text-sm text-zinc-800 leading-relaxed"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};

function renderMarkdown(md: string): string {
  const lines = md.split('\n');
  const result: string[] = [];
  let inList = false;
  let listType: 'ul' | 'ol' | null = null;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    // Headings
    const h3Match = line.match(/^###\s+(.*)/);
    const h2Match = line.match(/^##\s+(.*)/);
    const h1Match = line.match(/^#\s+(.*)/);

    if (h3Match) {
      closeList();
      result.push(`<h4 class="text-sm font-semibold text-zinc-700 mt-3 mb-1">${inlineFormat(h3Match[1])}</h4>`);
      continue;
    }
    if (h2Match) {
      closeList();
      result.push(`<h3 class="text-sm font-bold text-zinc-800 mt-4 mb-1">${inlineFormat(h2Match[1])}</h3>`);
      continue;
    }
    if (h1Match) {
      closeList();
      result.push(`<h2 class="text-base font-bold text-zinc-900 mt-4 mb-2">${inlineFormat(h1Match[1])}</h2>`);
      continue;
    }

    // Unordered list items
    const ulMatch = line.match(/^\s*[-*]\s+(.*)/);
    if (ulMatch) {
      if (listType !== 'ul') {
        closeList();
        result.push('<ul class="ml-3 space-y-0.5 my-1">');
        inList = true;
        listType = 'ul';
      }
      result.push(`<li class="flex gap-1.5 items-start"><span class="text-orange-400 mt-0.5 shrink-0">•</span><span>${inlineFormat(ulMatch[1])}</span></li>`);
      continue;
    }

    // Ordered list items
    const olMatch = line.match(/^\s*(\d+)[.)]\s+(.*)/);
    if (olMatch) {
      if (listType !== 'ol') {
        closeList();
        result.push('<ol class="ml-3 space-y-0.5 my-1">');
        inList = true;
        listType = 'ol';
      }
      result.push(`<li class="flex gap-1.5 items-start"><span class="text-orange-400 font-medium shrink-0">${olMatch[1]}.</span><span>${inlineFormat(olMatch[2])}</span></li>`);
      continue;
    }

    // Horizontal rule
    if (/^---+$/.test(line.trim())) {
      closeList();
      result.push('<hr class="my-2 border-zinc-200" />');
      continue;
    }

    // Empty line
    if (line.trim() === '') {
      closeList();
      result.push('<div class="h-1.5"></div>');
      continue;
    }

    // Regular paragraph
    closeList();
    result.push(`<p class="my-0.5">${inlineFormat(line)}</p>`);
  }

  closeList();
  return result.join('\n');

  function closeList() {
    if (inList) {
      result.push(listType === 'ol' ? '</ol>' : '</ul>');
      inList = false;
      listType = null;
    }
  }
}

function inlineFormat(text: string): string {
  // Bold + italic
  text = text.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
  // Bold
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-zinc-900">$1</strong>');
  // Italic
  text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // Inline code
  text = text.replace(/`(.*?)`/g, '<code class="bg-zinc-100 text-orange-700 px-1 py-0.5 rounded text-xs font-mono">$1</code>');
  return text;
}
