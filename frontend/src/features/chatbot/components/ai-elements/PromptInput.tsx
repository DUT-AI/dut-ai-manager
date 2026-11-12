import React, { useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { ArrowUpIcon, Loader2Icon } from "lucide-react";

interface PromptInputProps {
  value: string;
  onChange: (val: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
  placeholder?: string;
}

export const PromptInput: React.FC<PromptInputProps> = ({
  value,
  onChange,
  onSubmit,
  isLoading,
  placeholder = "Hỏi về quy chế, lý do vi phạm, bài tập hoặc lịch họp...",
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        180
      )}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading && value.trim()) {
        onSubmit();
      }
    }
  };

  return (
    <div className="relative flex flex-col gap-1 rounded-2xl bg-muted/30 p-2.5 border border-border/60 transition-all focus-within:border-ring/40 focus-within:bg-background focus-within:ring-2 focus-within:ring-ring/15">
      <textarea
        ref={textareaRef}
        rows={1}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={isLoading}
        className="w-full resize-none bg-transparent px-2.5 py-1 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none leading-relaxed disabled:opacity-60"
      />

      <div className="flex items-center justify-between px-1 pt-1">
        <div className="text-[11px] text-muted-foreground/50 select-none">
          Nhấn <kbd className="font-mono rounded bg-muted px-1 py-0.5 text-[10px]">Enter</kbd> để gửi, <kbd className="font-mono rounded bg-muted px-1 py-0.5 text-[10px]">Shift+Enter</kbd> xuống dòng
        </div>

        <Button
          type="button"
          size="icon"
          onClick={onSubmit}
          disabled={isLoading || !value.trim()}
          className="size-7 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-20 transition-all shadow-none"
          title={isLoading ? "Đang xử lý..." : "Gửi tin nhắn"}
        >
          {isLoading ? (
            <Loader2Icon className="size-3.5 animate-spin" />
          ) : (
            <ArrowUpIcon className="size-3.5" />
          )}
        </Button>
      </div>
    </div>
  );
};
