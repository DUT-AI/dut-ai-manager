import { NavigateFunction } from 'react-router-dom';
import { TAB_PATHS } from '@/constants/paths';

export type TabKey = 'home' | 'calendar' | 'profile';

const TAB_ORDER: Record<TabKey, number> = {
  home: 0,
  calendar: 1,
  profile: 2,
};

// Module-level direction store — allows navigate(-1) to carry direction without state
let _direction: 'forward' | 'backward' = 'forward';
export const getNavigationDirection = (): 'forward' | 'backward' => _direction;

export function navigateForward(
  navigate: NavigateFunction,
  path: string,
  state?: Record<string, unknown>
): void {
  _direction = 'forward';
  navigate(path, state ? { state } : undefined);
}

export function navigateBack(navigate: NavigateFunction): void {
  _direction = 'backward';
  navigate(-1);
}

export function navigateTab(
  navigate: NavigateFunction,
  currentTab: string,
  targetTab: string
): void {
  if (currentTab === targetTab) return;

  const path = TAB_PATHS[targetTab];
  if (!path) return;

  const currentIdx = TAB_ORDER[currentTab as TabKey] ?? 0;
  const targetIdx = TAB_ORDER[targetTab as TabKey] ?? 0;
  _direction = targetIdx > currentIdx ? 'forward' : 'backward';

  navigate(path, { replace: true });
}
