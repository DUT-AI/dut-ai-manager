import { useEffect, useRef } from 'react';

export interface DutaiWaffleProps {
  current?: 'manage' | 'lms' | 'meetly' | 'data' | string;
  className?: string;
}

export function DutaiWaffle({ current = 'manage', className = '' }: DutaiWaffleProps) {
  const waffleRef = useRef<HTMLElement>(null);

  useEffect(() => {
    // 1. Ensure the web component script is loaded safely
    const scriptSrc = 'https://workspace.dutai.io.vn/waffle.js';
    if (typeof window !== 'undefined' && !customElements.get('dutai-waffle')) {
      const existingScript = document.querySelector(`script[src="${scriptSrc}"]`);
      if (!existingScript) {
        const script = document.createElement('script');
        script.src = scriptSrc;
        script.defer = true;
        document.head.appendChild(script);
      }
    }

    // 2. Adjust waffle button style inside shadow DOM to match the dark header aesthetic
    const el = waffleRef.current;
    if (!el) return;

    let observer: MutationObserver | null = null;

    const applyContrastStyle = () => {
      const shadow = el.shadowRoot;
      if (!shadow) return;

      if (!shadow.getElementById('dutai-waffle-header-style')) {
        const style = document.createElement('style');
        style.id = 'dutai-waffle-header-style';
        style.textContent = `
          .waffle-btn {
            color: rgba(255, 255, 255, 0.9) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 9999px !important;
            width: 40px !important;
            height: 40px !important;
            transition: all 0.2s ease !important;
          }
          .waffle-btn:hover {
            color: #ffffff !important;
            background: rgba(255, 255, 255, 0.1) !important;
            border-color: rgba(255, 255, 255, 0.35) !important;
          }
        `;
        shadow.appendChild(style);
      }
    };

    const attachObserver = () => {
      if (el.shadowRoot) {
        applyContrastStyle();
        observer = new MutationObserver(() => {
          applyContrastStyle();
        });
        observer.observe(el.shadowRoot, { childList: true });
      }
    };

    if (customElements.get('dutai-waffle')) {
      attachObserver();
    } else {
      customElements.whenDefined('dutai-waffle').then(() => {
        attachObserver();
      });
    }

    return () => {
      observer?.disconnect();
    };
  }, []);

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <dutai-waffle ref={waffleRef} current={current} />
    </div>
  );
}

export default DutaiWaffle;
