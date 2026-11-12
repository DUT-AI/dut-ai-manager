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
import {
  CodeBlock,
  CodeBlockContent,
  CodeBlockHeader,
  CodeBlockTitle,
} from "@/components/ui/code-block";
import { WrenchIcon, Loader2Icon, CheckCircle2Icon, AlertTriangleIcon } from "lucide-react";
import type { ToolCallRecord } from "../../types/chatbot.types";

interface ToolTraceProps {
  tools?: ToolCallRecord[];
  isExecuting?: boolean;
}

const TOOL_NAME_LABELS: Record<string, string> = {
  get_my_violations: "Tra cứu hồ sơ vi phạm cá nhân",
  get_my_homework_status: "Tra cứu tiến độ bài tập cá nhân",
  inspect_entity_records: "Khảo sát thực thể học vụ",
  get_all_violations_analytics: "Tổng hợp thống kê vi phạm toàn CLB",
  get_homework_turn_in_status: "Tổng hợp danh sách nộp bài tập",
};

export const ToolTrace: React.FC<ToolTraceProps> = ({ tools, isExecuting }) => {
  if (isExecuting) {
    return (
      <Trace className="w-fit my-1.5 select-none">
        <TraceLine status="running">
          <TraceIcon>
            <Loader2Icon className="size-3.5 animate-spin text-primary" />
          </TraceIcon>
          <TraceTitle className="text-xs text-muted-foreground font-mono">
            Đang gọi công cụ hệ thống...
          </TraceTitle>
        </TraceLine>
      </Trace>
    );
  }

  if (!tools || tools.length === 0) return null;

  return (
    <div className="flex flex-col gap-1.5 my-1.5 w-full max-w-2xl">
      {tools.map((t, idx) => {
        const friendlyName = TOOL_NAME_LABELS[t.tool_name] || t.tool_name;
        const isSuccess = t.execution_status === "success";

        return (
          <Trace key={idx} className="w-fit">
            <TraceCollapsible defaultOpen={false}>
              <TraceCollapsibleTrigger className="cursor-pointer group">
                <TraceLine status={!isSuccess ? "error" : undefined}>
                  <TraceIcon>
                    {isSuccess ? (
                      <CheckCircle2Icon className="size-3.5 text-emerald-600 dark:text-emerald-400" />
                    ) : (
                      <AlertTriangleIcon className="size-3.5 text-destructive" />
                    )}
                  </TraceIcon>
                  <TraceTitle className="text-xs font-medium text-muted-foreground group-hover:text-foreground transition-colors flex items-center gap-1.5">
                    <WrenchIcon className="size-3 text-muted-foreground/70" />
                    <span>{friendlyName}</span>
                  </TraceTitle>
                  <TraceDescription className="text-[11px] font-mono text-muted-foreground/60">
                    ({t.tool_name})
                  </TraceDescription>
                </TraceLine>
              </TraceCollapsibleTrigger>

              {t.arguments && Object.keys(t.arguments).length > 0 && (
                <TraceCollapsibleContent className="pl-6 pt-1.5 max-w-xl">
                  <CodeBlock className="rounded-lg border border-border/60 bg-muted/20">
                    <CodeBlockHeader className="py-1 px-2.5 bg-muted/40 text-[11px]">
                      <CodeBlockTitle className="font-mono text-[11px] text-muted-foreground">
                        Tham số đầu vào (arguments)
                      </CodeBlockTitle>
                    </CodeBlockHeader>
                    <CodeBlockContent className="p-2 text-[11px] font-mono">
                      {JSON.stringify(t.arguments, null, 2)}
                    </CodeBlockContent>
                  </CodeBlock>
                </TraceCollapsibleContent>
              )}
            </TraceCollapsible>
          </Trace>
        );
      })}
    </div>
  );
};
