import { useState } from 'react';
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
  Code
} from '@mantine/core';
import { IconBrain, IconRefresh, IconAlertCircle } from '@tabler/icons-react';
import useEmbeddingGeneration from '@/hooks/useEmbeddingGeneration';

export const EmbeddingGeneration = () => {
  const [model, setModel] = useState('qodo');
  const [force, setForce] = useState(false);
  const [useGpu, setUseGpu] = useState(false);
  
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
  
  const handleGenerateEmbeddings = () => {
    startGeneration({
      model,
      force,
      use_gpu: useGpu
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
  
  return (
    <Paper p="md" withBorder radius="md" mb="xl">
      <Title order={3} mb="md">Embedding Generation</Title>
      
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
            <Text size="xs" c="dimmed">{status.progress}%</Text>
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
                Processing {status.total} code structures
              </Text>
            )}
          </Group>
          
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
            { value: 'nomic', label: 'Nomic Embed' }
          ]}
          value={model}
          onChange={(value) => setModel(value || 'qodo')}
          disabled={isRunning}
        />
        
        <Switch
          label="Force regeneration"
          description="Regenerate all embeddings"
          checked={force}
          onChange={(event) => setForce(event.currentTarget.checked)}
          disabled={isRunning}
        />
        
        <Switch
          label="Use GPU"
          description="Use GPU for faster generation"
          checked={useGpu}
          onChange={(event) => setUseGpu(event.currentTarget.checked)}
          disabled={isRunning}
        />
      </Group>
      
      <Group mt="md">
        <Button
          leftSection={<IconBrain size={16} />}
          onClick={handleGenerateEmbeddings}
          loading={loading}
          disabled={isRunning}
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
    </Paper>
  );
};

export default EmbeddingGeneration; 