import { useState, useEffect } from 'react';
import { 
  Box, 
  Button, 
  Group, 
  Progress, 
  Text, 
  Title, 
  Paper, 
  Switch, 
  Select, 
  Alert, 
  Code,
  Divider,
  NumberInput
} from '@mantine/core';
import { IconBrain, IconRefresh, IconAlertCircle, IconInfoCircle } from '@tabler/icons-react';
import useEmbeddingGeneration from '@/hooks/useEmbeddingGeneration';
import axios from 'axios';

export const EmbeddingGeneration = () => {
  const [model, setModel] = useState('qodo');
  const [force, setForce] = useState(false);
  const [useGpu, setUseGpu] = useState(false);
  const [batchSize, setBatchSize] = useState(8);
  const [structuresExist, setStructuresExist] = useState(true);
  
  const { 
    status, 
    loading, 
    error, 
    startGeneration, 
    reset, 
    isRunning,
    isCompleted,
    isFailed
  } = useEmbeddingGeneration();
  
  // Check if structures.json exists
  useEffect(() => {
    const checkStructures = async () => {
      try {
        // Make a simple HEAD request to check if data/structures.json exists
        // This is a simplified approach - ideally the backend would have an endpoint for this
        await axios.head('/data/structures.json');
        setStructuresExist(true);
      } catch (err) {
        setStructuresExist(false);
      }
    };
    
    checkStructures();
  }, []);
  
  const handleGenerateEmbeddings = () => {
    startGeneration({
      model,
      force,
      use_gpu: useGpu,
      batch_size: batchSize
    });
  };
  
  // Calculate time elapsed
  const getElapsedTime = () => {
    if (!status.start_time) return '0s';
    
    const endTime = status.end_time || Date.now() / 1000;
    const elapsed = Math.floor(endTime - status.start_time);
    
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    
    return minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
  };
  
  // Calculate estimated time remaining
  const getEstimatedTimeRemaining = () => {
    if (!status.start_time || !status.total || !status.processed || status.progress >= 100) {
      return null;
    }
    
    const elapsed = (Date.now() / 1000) - status.start_time;
    const processed = status.processed || 0;
    const remaining = status.total - processed;
    
    // Calculate time per item
    const timePerItem = processed > 0 ? elapsed / processed : 0;
    
    // Estimate remaining time
    const estimatedRemaining = timePerItem * remaining;
    if (estimatedRemaining <= 0) return null;
    
    const minutes = Math.floor(estimatedRemaining / 60);
    const seconds = Math.floor(estimatedRemaining % 60);
    
    return minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
  };
  
  return (
    <Paper p="md" withBorder radius="md" mb="xl">
      <Title order={3} mb="md">Embedding Generation</Title>
      
      {!structuresExist && (
        <Alert
          icon={<IconInfoCircle size={16} />}
          title="No Code Structures Found"
          color="yellow"
          mb="md"
        >
          You need to generate code structures first before creating embeddings.
          Please go to the "Structure Generation" tab and generate code structures.
        </Alert>
      )}
      
      {error && (
        <Alert 
          icon={<IconAlertCircle size={16} />} 
          title="Error" 
          color="red" 
          mb="md"
          withCloseButton
          onClose={reset}
        >
          {error}
        </Alert>
      )}
      
      {(isRunning || isCompleted) && (
        <Box mb="lg">
          <Group justify="apart" mb={5}>
            <Text size="sm" fw={500}>
              {status.status === 'running' ? 'Generating embeddings...' : 'Embedding generation complete'}
            </Text>
            <Text size="xs" c="dimmed">
              {status.status === 'running' && status.progress === 100 
                ? 'Processing... (This may take several minutes)' 
                : `${status.progress}%`}
            </Text>
          </Group>
          
          <Progress 
            value={status.progress} 
            size="lg" 
            radius="md" 
            color={isCompleted ? 'green' : 'blue'} 
            striped={isRunning}
            animated={isRunning}
          />
          
          <Group justify="apart" mt={5}>
            <Text size="xs" c="dimmed">Time elapsed: {getElapsedTime()}</Text>
            {status.total && (
              <Text size="xs" c="dimmed">
                {status.processed && status.processed < status.total 
                  ? `Processing ${status.processed}/${status.total} code structures` 
                  : `Processing ${status.total} code structures`}
              </Text>
            )}
          </Group>
          
          {getEstimatedTimeRemaining() && (
            <Text size="xs" c="dimmed" mt={5}>
              Estimated time remaining: {getEstimatedTimeRemaining()}
            </Text>
          )}
          
          <Text size="sm" mt="md" c="dimmed">
            <Code>{status.message}</Code>
          </Text>
        </Box>
      )}
      
      <Group align="flex-end">
        <Select
          label="Embedding Model"
          description="Select the model to use for generation"
          data={[
            { value: 'qodo', label: 'Qodo Embed' },
            { value: 'nomic', label: 'Nomic Embed' },
            { value: 'jina', label: 'Jina Embeddings v2' }
          ]}
          value={model}
          onChange={(value) => setModel(value || 'qodo')}
          disabled={isRunning || !structuresExist}
        />
        
        <NumberInput
          label="Batch Size"
          description="Smaller values use less memory"
          value={batchSize}
          onChange={(value) => setBatchSize(Number(value) || 8)}
          min={1}
          max={32}
          disabled={isRunning || !structuresExist}
          w={120}
        />
        
        <Switch
          label="Force regeneration"
          description="Regenerate all embeddings"
          checked={force}
          onChange={(event) => setForce(event.currentTarget.checked)}
          disabled={isRunning || !structuresExist}
        />
        
        <Switch
          label="Use GPU"
          description="Use GPU for faster generation"
          checked={useGpu}
          onChange={(event) => setUseGpu(event.currentTarget.checked)}
          disabled={isRunning || !structuresExist}
        />
      </Group>
      
      <Group mt="md">
        <Button
          leftSection={<IconBrain size={16} />}
          onClick={handleGenerateEmbeddings}
          loading={loading}
          disabled={isRunning || !structuresExist}
          color="blue"
        >
          Generate Embeddings
        </Button>
        
        {(isCompleted || isFailed) && (
          <Button
            leftSection={<IconRefresh size={16} />}
            variant="light"
            onClick={reset}
          >
            Reset
          </Button>
        )}
      </Group>
      
      <Divider my="md" />
      
      <Text size="sm" c="dimmed">
        <IconInfoCircle size={16} style={{ verticalAlign: 'middle', marginRight: '5px' }} />
        Embedding generation creates vector representations of your code structures 
        that enable semantic search capabilities. Make sure to generate code structures first.
      </Text>
    </Paper>
  );
};

export default EmbeddingGeneration; 