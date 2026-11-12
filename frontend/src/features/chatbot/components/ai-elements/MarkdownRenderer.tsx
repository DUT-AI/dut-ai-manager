import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  CodeBlock,
  CodeBlockHeader,
  CodeBlockTitle,
  CodeBlockActions,
  CodeBlockCopyButton,
  CodeBlockContent,
} from "@/components/ui/code-block";
import { Code2Icon } from "lucide-react";

interface MarkdownRendererProps {
  content: string;
}

/**
 * Preprocesses markdown text to fix common LLM formatting glitches:
 * 1. Splits table rows concatenated on the same line (`| col | | next row |` -> `| col |\n| next row |`).
 * 2. Ensures table blocks have preceding and trailing blank lines so GFM parser recognizes them.
 */
function preprocessMarkdown(text: string): string {
  if (!text) return "";
  let fixed = text;

  // Split table rows glued together with `| |` instead of `|\n|`
  fixed = fixed.replace(/\|\s*\|\s*/g, "|\n|");

  // Ensure there is a blank line before a table starts if preceded by regular text
  fixed = fixed.replace(/([^\n|])\n\s*(\|)/g, "$1\n\n$2");

  // Ensure there is a blank line after a table ends before subsequent text
  fixed = fixed.replace(/(\|[^\n]*)\n([^\n|])/g, "$1\n\n$2");

  return fixed;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  const processedContent = preprocessMarkdown(content);

  return (
    <div className="prose prose-sm dark:prose-invert max-w-none text-foreground/90 leading-relaxed break-words">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const isInline = !match && !String(children).includes("\n");

            if (isInline) {
              return (
                <code
                  className="rounded-md bg-muted px-1.5 py-0.5 font-mono text-xs text-foreground font-medium"
                  {...props}
                >
                  {children}
                </code>
              );
            }

            const codeString = String(children).replace(/\n$/, "");
            const language = match ? match[1] : "plaintext";

            return (
              <CodeBlock className="my-3 overflow-hidden rounded-xl border border-border/80 shadow-2xs">
                <CodeBlockHeader className="border-b border-border/60 bg-muted/40 px-3 py-1.5">
                  <CodeBlockTitle className="flex items-center gap-1.5 text-xs font-mono text-muted-foreground uppercase">
                    <Code2Icon className="size-3.5" />
                    <span>{language}</span>
                  </CodeBlockTitle>
                  <CodeBlockActions>
                    <CodeBlockCopyButton value={codeString} />
                  </CodeBlockActions>
                </CodeBlockHeader>
                <CodeBlockContent className="bg-muted/15 p-3 text-xs font-mono">
                  {codeString}
                </CodeBlockContent>
              </CodeBlock>
            );
          },
          p({ children }) {
            return <p className="mb-2.5 last:mb-0 leading-relaxed">{children}</p>;
          },
          ul({ children }) {
            return <ul className="my-2.5 list-disc pl-5 space-y-1">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="my-2.5 list-decimal pl-5 space-y-1">{children}</ol>;
          },
          li({ children }) {
            return <li className="leading-relaxed">{children}</li>;
          },
          table({ children }) {
            return (
              <div className="my-3.5 w-full overflow-x-auto rounded-xl border border-border/70 shadow-2xs bg-card">
                <table className="w-full text-xs border-collapse text-left">
                  {children}
                </table>
              </div>
            );
          },
          thead({ children }) {
            return (
              <thead className="bg-muted/60 border-b border-border/70 text-foreground font-semibold">
                {children}
              </thead>
            );
          },
          tbody({ children }) {
            return (
              <tbody className="divide-y divide-border/40 bg-card">
                {children}
              </tbody>
            );
          },
          tr({ children }) {
            return (
              <tr className="hover:bg-muted/30 transition-colors">
                {children}
              </tr>
            );
          },
          th({ children }) {
            return (
              <th className="px-3.5 py-2.5 font-semibold text-foreground whitespace-nowrap text-xs">
                {children}
              </th>
            );
          },
          td({ children }) {
            return (
              <td className="px-3.5 py-2 text-foreground/85 leading-normal text-xs">
                {children}
              </td>
            );
          },
        }}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
};
