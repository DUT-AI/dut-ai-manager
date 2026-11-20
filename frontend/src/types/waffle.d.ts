import type React from 'react';

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'dutai-waffle': React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement> & {
          current?: 'manage' | 'lms' | 'meetly' | 'data' | string;
        },
        HTMLElement
      >;
    }
  }
  namespace React.JSX {
    interface IntrinsicElements {
      'dutai-waffle': React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement> & {
          current?: 'manage' | 'lms' | 'meetly' | 'data' | string;
        },
        HTMLElement
      >;
    }
  }
}
