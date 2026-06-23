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

const REFRESH_INTERVAL = 30 * 1000; // 30 seconds

export const CapacityProvider = ({ children }: { children: ReactNode }) => {
  const [capacity, setCapacity] = useState<CapacityStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const fetchRef = useRef(false);

  const fetchCapacity = useCallback(async () => {
    if (fetchRef.current) return; // prevent concurrent fetches
    fetchRef.current = true;
    setLoading(true);
    try {

      // MỞ COMMENT ĐOẠN NÀY ĐỂ MOCK DỮ LIỆU UI (NHỚ NHẤN F5 ĐỂ ÁP DỤNG)
      // setCapacity({
      //   current_count: 15,
      //   incoming_count: 5,
      //   outgoing_count: 0,
      //   future_count: 20,
      //   status: 'warning', // thay đ1ổi: 'safe' | 'warning' | 'overload'
      //   max_capacity: 20
      // });
      // return;


      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
      const response = await fetch(`${apiUrl}/meetings/capacity/forecast`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
        }
      });
      const result = await response.json();
      if (result.is_success || result.success) {
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
    const timer = setInterval(fetchCapacity, 30 * 1000); // 30s

    return () => clearInterval(timer);
  }, [fetchCapacity]);

  const capacityStatus = capacity?.status?.toLowerCase() ?? null;

  return (
    <CapacityContext.Provider value={{ capacity, capacityStatus, loading }}>
      {children}
    </CapacityContext.Provider>
  );
};
