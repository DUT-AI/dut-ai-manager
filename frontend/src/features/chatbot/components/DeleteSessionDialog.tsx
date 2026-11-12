import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Loader2Icon, AlertTriangleIcon } from "lucide-react";

interface DeleteSessionDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isDeleting: boolean;
}

export const DeleteSessionDialog: React.FC<DeleteSessionDialogProps> = ({
  isOpen,
  onOpenChange,
  onConfirm,
  isDeleting,
}) => {
  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader className="gap-2">
          <div className="size-10 rounded-full bg-destructive/10 text-destructive flex items-center justify-center mb-1">
            <AlertTriangleIcon className="size-5" />
          </div>
          <DialogTitle className="text-base font-semibold">
            Xóa cuộc trò chuyện?
          </DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground leading-relaxed">
            Hành động này sẽ xóa vĩnh viễn toàn bộ tin nhắn trong phiên hội thoại này khỏi lịch sử của bạn. Bạn không thể hoàn tác hành động này.
          </DialogDescription>
        </DialogHeader>

        <DialogFooter className="mt-4 flex gap-2 sm:justify-end">
          <DialogClose render={<Button variant="outline" size="sm" disabled={isDeleting} />}>
            Hủy
          </DialogClose>
          <Button
            type="button"
            variant="destructive"
            size="sm"
            onClick={onConfirm}
            disabled={isDeleting}
            className="gap-1.5"
          >
            {isDeleting && <Loader2Icon className="size-3.5 animate-spin" />}
            Xóa vĩnh viễn
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
