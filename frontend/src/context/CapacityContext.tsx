import { createContext, useContext, useState, useEffect, useRef, useCallback, type ReactNode } from 'react';

export interface CapacityStatus {
  current_count: number;
  incoming_count: number;
  outgoing_count: number;
  future_count: number;
  status: 'safe' | 'warning' | 'overload';
  max_capacity: number;
}

interface CapacityContextType {
  capacity: CapacityStatus | null;
  capacityStatus: 'safe' | 'warning' | 'overload' | null;
  loading: boolean;
}

const CapacityContext = createContext<CapacityContextType>({
  capacity: null,
  capacityStatus: null,
  loading: false,
});

export const useCapacity = () => useContext(CapacityContext);

const REFRESH_INTERVAL = 15 * 60 * 1000; // 15 minutes

export const CapacityProvider = ({ children }: { children: ReactNode }) => {
  const [capacity, setCapacity] = useState<CapacityStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const fetchRef = useRef(false);

  const fetchCapacity = useCallback(async () => {
    if (fetchRef.current) return; // prevent concurrent fetches
    fetchRef.current = true;
    setLoading(true);
    try {
      /* 
      // MỞ COMMENT ĐOẠN NÀY ĐỂ MOCK DỮ LIỆU UI (NHỚ NHẤN F5 ĐỂ ÁP DỤNG)
      setCapacity({
        current_count: 55,
        incoming_count: 10,
        outgoing_count: 2,
        future_count: 63,
        status: 'overload', // thay đổi: 'safe' | 'warning' | 'overload'
        max_capacity: 50
      });
      return;
      */

      const response = await fetch('/api/v1/capacity/forecast');
      const result = await response.json();
      if (result.success) {
        setCapacity(result.data);
      }
    } catch (error) {
      console.error('Failed to fetch capacity:', error);
    } finally {
      setLoading(false);
      fetchRef.current = false;
    }
  }, []);

  useEffect(() => {
    fetchCapacity();
    const interval = setInterval(fetchCapacity, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchCapacity]);

  const capacityStatus = capacity?.status ?? null;

  return (
    <CapacityContext.Provider value={{ capacity, capacityStatus, loading }}>
      {children}
    </CapacityContext.Provider>
  );
};
