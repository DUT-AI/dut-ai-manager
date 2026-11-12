import React from "react";
import {
  Trace,
  TraceCollapsible,
  TraceCollapsibleContent,
  TraceCollapsibleTrigger,
  TraceDescription,
  TraceIcon,
  TraceLine,
  TraceTitle,
} from "@/components/ui/trace";
import { CircleCheckIcon, Loader2Icon, BrainCircuitIcon } from "lucide-react";

interface ReasoningProps {
  content: string;
  isStreaming?: boolean;
}

export const Reasoning: React.FC<ReasoningProps> = ({ content, isStreaming }) => {
  if (!content) return null;

  return (
    <Trace className="w-fit my-1.5 select-none">
      <TraceCollapsible defaultOpen={false}>
        <TraceCollapsibleTrigger className="cursor-pointer group">
          <TraceLine status={isStreaming ? "running" : undefined}>
            <TraceIcon>
              {isStreaming ? (
                <Loader2Icon className="size-3.5 animate-spin text-primary" />
              ) : (
                <CircleCheckIcon className="size-3.5 text-muted-foreground group-hover:text-foreground transition-colors" />
              )}
            </TraceIcon>
            <TraceTitle className="text-xs text-muted-foreground font-medium group-hover:text-foreground transition-colors flex items-center gap-1.5">
              <BrainCircuitIcon className="size-3 text-muted-foreground/70" />
              <span>{isStreaming ? "Thinking..." : "Thought"}</span>
            </TraceTitle>
            {!isStreaming && (
              <TraceDescription className="text-[11px] text-muted-foreground/60">
                (nhấp để xem)
              </TraceDescription>
            )}
          </TraceLine>
        </TraceCollapsibleTrigger>
        <TraceCollapsibleContent className="whitespace-pre-wrap font-sans text-xs text-muted-foreground/90 leading-relaxed pl-6 pt-1.5 max-w-2xl border-l-2 border-border/40 ml-2 mt-1">
          <div className="rounded-lg bg-muted/30 p-2.5 text-xs text-muted-foreground">
            {content}
          </div>
        </TraceCollapsibleContent>
      </TraceCollapsible>
    </Trace>
  );
};
