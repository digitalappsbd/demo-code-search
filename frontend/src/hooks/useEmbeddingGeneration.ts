import { useState, useEffect, useCallback } from 'react';
import { generateEmbeddings, getEmbeddingStatus } from '@/api/search';

type EmbeddingStatus = {
  status: 'idle' | 'running' | 'completed' | 'failed';
  progress: number;
  message: string;
  start_time: number | null;
  end_time: number | null;
  total?: number;
  processed?: number;
};

type EmbeddingOptions = {
  model: string;
  force: boolean;
  use_gpu: boolean;
  batch_size?: number;
};

export const useEmbeddingGeneration = () => {
  const [status, setStatus] = useState<EmbeddingStatus>({
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
      const response = await getEmbeddingStatus();
      if (response.data) {
        setStatus(prevStatus => ({ ...prevStatus, ...response.data }));
        
        // Stop polling when completed or failed
        if (response.data.status === 'completed' || response.data.status === 'failed') {
          setIsPolling(false);
        }
      }
    } catch (err) {
      console.error('Error fetching embedding status:', err);
      // Keep polling even if one request fails, but log an error
      // setError('Failed to fetch embedding status'); 
      // setIsPolling(false);
    }
  }, []); // No dependencies needed for fetchStatus itself, as setStatus/setIsPolling are stable
  
  // Start embedding generation
  const startGeneration = useCallback(async (options: EmbeddingOptions) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await generateEmbeddings(options);
      
      if (response.data.status === 'started') {
        setIsPolling(true);
        await fetchStatus(); // Fetch initial status
      } else if (response.data.status === 'error') {
        setError(response.data.message);
      }
    } catch (err) {
      console.error('Error starting embedding generation:', err);
      setError('Failed to start embedding generation');
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
      // Fetch immediately when polling starts
      fetchStatus(); 
      intervalId = setInterval(fetchStatus, 500); // Poll every 500ms
    }
    
    // Cleanup
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isPolling, fetchStatus]); // fetchStatus is stable due to useCallback with empty deps
  
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

export default useEmbeddingGeneration; 