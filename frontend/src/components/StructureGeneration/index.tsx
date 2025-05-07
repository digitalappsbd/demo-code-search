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
  TextInput,
  NumberInput,
  Alert, 
  Code
} from '@mantine/core';
import { IconCode, IconRefresh, IconAlertCircle } from '@tabler/icons-react';
import useStructureGeneration from '@/hooks/useStructureGeneration';

export const StructureGeneration = () => {
  const [targetDir, setTargetDir] = useState('');
  const [pattern, setPattern] = useState('**/*.py');
  const [maxLines, setMaxLines] = useState(500);
  const [force, setForce] = useState(false);
  
  const { 
    status, 
    loading, 
    error, 
    startGeneration, 
    reset, 
    isRunning,
    isCompleted,
    isFailed
  } = useStructureGeneration();
  
  const handleGenerateStructures = () => {
    startGeneration({
      target_dir: targetDir,
      pattern,
      max_lines: maxLines,
      force
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
      <Title order={3} mb="md">Code Structure Generation</Title>
      
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
              {status.status === 'running' ? 'Generating code structures...' : 'Structure generation complete'}
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
                Processing {status.processed || 0} of {status.total} files
              </Text>
            )}
          </Group>
          
          <Text size="sm" mt="md" c="dimmed">
            <Code>{status.message}</Code>
          </Text>
        </Box>
      )}
      
      <Box>
        <TextInput
          label="Target Directory"
          description="Leave empty to use the parent directory of the project"
          placeholder="e.g., /path/to/code"
          value={targetDir}
          onChange={(event) => setTargetDir(event.currentTarget.value)}
          disabled={isRunning}
          mb="md"
        />
        
        <TextInput
          label="File Pattern"
          description="Glob pattern for files to include"
          placeholder="e.g., **/*.py"
          value={pattern}
          onChange={(event) => setPattern(event.currentTarget.value)}
          disabled={isRunning}
          mb="md"
        />
        
        <NumberInput
          label="Max Lines"
          description="Maximum lines per code block"
          value={maxLines}
          onChange={(value) => setMaxLines(typeof value === 'number' ? value : 500)}
          min={10}
          max={2000}
          disabled={isRunning}
          mb="md"
        />
        
        <Switch
          label="Force regeneration"
          description="Generate structures even if they already exist"
          checked={force}
          onChange={(event) => setForce(event.currentTarget.checked)}
          disabled={isRunning}
          mb="md"
        />
      </Box>
      
      <Group mt="md">
        <Button
          leftSection={<IconCode size={16} />}
          onClick={handleGenerateStructures}
          loading={loading}
          disabled={isRunning}
          color="blue"
        >
          Generate Structures
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

export default StructureGeneration; 