import React from "react";
import { Badge } from "@/components/ui/badge";
import { SparklesIcon, ShieldAlertIcon } from "lucide-react";
import type { QuickPromptItem } from "../../types/chatbot.types";

interface SuggestionProps {
  prompts: QuickPromptItem[];
  onSelectPrompt: (promptText: string) => void;
  disabled?: boolean;
}

export const Suggestion: React.FC<SuggestionProps> = ({
  prompts,
  onSelectPrompt,
  disabled,
}) => {
  if (!prompts || prompts.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-1.5 py-1">
      {prompts.map((item, index) => {
        const isAdmin = item.category === "administrative";
        return (
          <button
            key={index}
            type="button"
            disabled={disabled}
            onClick={() => onSelectPrompt(item.prompt)}
            className="group cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-full"
            title={item.prompt}
          >
            <Badge
              variant="outline"
              className={`px-3 py-1.5 text-xs font-normal rounded-full gap-1.5 transition-all shadow-2xs ${
                isAdmin
                  ? "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30 hover:bg-amber-500/20"
                  : "bg-muted/50 text-muted-foreground hover:text-foreground hover:bg-muted border-border/70"
              }`}
            >
              {isAdmin ? (
                <ShieldAlertIcon className="size-3 text-amber-600 dark:text-amber-400" />
              ) : (
                <SparklesIcon className="size-3 text-primary/80 group-hover:text-primary transition-colors" />
              )}
              <span className="truncate max-w-[240px] sm:max-w-none">{item.label}</span>
            </Badge>
          </button>
        );
      })}
    </div>
  );
};
