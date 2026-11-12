# Data Model & State Transitions: Agent Loop Architecture

**Feature ID**: `064-agent-loop-architecture`  
**Ngày cập nhật**: 2026-11-12  

---

## 1. Entities & Value Objects

### 1.1. `AgentLoopState` (Trạng thái nội tại của một chu kỳ Agent Loop)
```python
@dataclass
class AgentLoopState:
    iteration: int = 0
    max_iterations: int = 5
    accumulated_content: str = ""
    accumulated_reasoning: str = ""
    executed_tools: list[ToolCallRecord] = field(default_factory=list)
    call_signatures: set[str] = field(default_factory=set)
    is_completed: bool = False

    def add_call_signature(self, tool_name: str, args: dict[str, Any]) -> bool:
        """Returns True if new, False if duplicate call detected."""
        import json
        sig = f"{tool_name}:{json.dumps(args, sort_keys=True)}"
        if sig in self.call_signatures:
            return False
        self.call_signatures.add(sig)
        return True
```

### 1.2. `ToolCallRecord` (Domain Value Object đã có, tăng cường thông tin chu kỳ)
```python
@dataclass(frozen=True)
class ToolCallRecord:
    tool_name: str
    arguments: dict[str, Any]
    execution_status: str  # "success" | "error" | "duplicate_skipped"
    iteration_index: int = 1
```

---

## 2. Giao Thức SSE Payload (SSE Message Contract)

Hệ thống bổ sung sự kiện `tool_call` để thông báo cho Client hiển thị `ToolTrace` ngay lập tức:

```json
// Khi Tool bắt đầu thực thi
data: {"type": "tool_call_start", "data": {"name": "admin_get_unsubmitted_homeworks", "iteration": 1}}

// Khi Tool hoàn thành
data: {"type": "tool_call_end", "data": {"name": "admin_get_unsubmitted_homeworks", "status": "success", "iteration": 1}}

// Chuyển sang vòng lặp tiếp theo
data: {"type": "iteration_step", "data": {"iteration": 2, "max_iterations": 5}}

// Nội dung suy luận / văn bản như cũ
data: {"type": "reasoning", "data": "Dựa trên danh sách chưa nộp bài, tôi sẽ tiếp tục kiểm tra..."}
data: {"type": "content", "data": "Dưới đây là kết quả..."}
data: {"type": "done", "data": "..."}
data: [DONE]
```
