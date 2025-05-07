import { useState, useEffect, useCallback } from 'react';
import { generateStructures, getStructureStatus } from '@/api/search';

type StructureStatus = {
  status: 'idle' | 'running' | 'completed' | 'failed';
  progress: number;
  message: string;
  start_time: number | null;
  end_time: number | null;
  total?: number;
  processed?: number;
};

type StructureOptions = {
  target_dir: string;
  pattern: string;
  max_lines: number;
  force: boolean;
};

export const useStructureGeneration = () => {
  const [status, setStatus] = useState<StructureStatus>({
    status: 'idle',
    progress: 0,
    message: '',
    start_time: null,
    end_time: null
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  
  // Fetch current status
  const fetchStatus = useCallback(async () => {
    try {
      const response = await getStructureStatus();
      if (response.data) {
        setStatus(response.data);
        
        // Stop polling when completed or failed
        if (response.data.status === 'completed' || response.data.status === 'failed') {
          setIsPolling(false);
        }
      }
    } catch (err) {
      console.error('Error fetching structure status:', err);
      setError('Failed to fetch structure status');
      setIsPolling(false);
    }
  }, []);
  
  // Start structure generation
  const startGeneration = useCallback(async (options: StructureOptions) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await generateStructures(options);
      
      if (response.data.status === 'started') {
        setIsPolling(true);
        await fetchStatus(); // Fetch initial status
      } else if (response.data.status === 'error') {
        setError(response.data.message);
      }
    } catch (err) {
      console.error('Error starting structure generation:', err);
      setError('Failed to start structure generation');
    } finally {
      setLoading(false);
    }
  }, [fetchStatus]);
  
  // Reset the state
  const reset = useCallback(() => {
    setStatus({
      status: 'idle',
      progress: 0,
      message: '',
      start_time: null,
      end_time: null
    });
    setError(null);
    setIsPolling(false);
  }, []);
  
  // Poll for status updates
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;
    
    if (isPolling) {
      intervalId = setInterval(() => {
        fetchStatus();
      }, 1000); // Poll every second
    }
    
    // Cleanup
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isPolling, fetchStatus]);
  
  // Check status on initial mount
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);
  
  return {
    status,
    loading,
    error,
    startGeneration,
    reset,
    isRunning: status.status === 'running',
    isCompleted: status.status === 'completed',
    isFailed: status.status === 'failed'
  };
};

export default useStructureGeneration; 