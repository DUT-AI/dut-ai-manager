import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button, Icon } from 'zmp-ui';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error caught by ErrorBoundary:', error, errorInfo);
  }

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen p-6 bg-slate-50 text-center">
          <div className="w-16 h-16 rounded-3xl bg-rose-100 text-rose-600 flex items-center justify-center mb-4 shadow-sm">
            <Icon icon="zi-warning-circle" size={32} />
          </div>
          <h2 className="text-base font-bold text-gray-900 mb-1">Đã xảy ra sự cố hiển thị</h2>
          <p className="text-xs text-gray-500 mb-5 max-w-xs leading-relaxed">
            Hệ thống vừa gặp lỗi khi tải trang. Vui lòng bấm nút bên dưới để thử lại.
          </p>

          <Button
            className="rounded-2xl bg-blue-600 text-white font-bold text-xs px-6 py-2 shadow-xs"
            onClick={this.handleReload}
          >
            Tải lại trang
          </Button>

          {this.state.error && (
            <div className="mt-6 p-3 bg-white rounded-xl border border-gray-200 text-left w-full max-w-xs text-[11px] text-gray-400 font-mono overflow-auto max-h-24">
              {this.state.error.message || String(this.state.error)}
            </div>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
