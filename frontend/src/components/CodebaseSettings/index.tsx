import { useState, useEffect } from 'react';
import { 
  Box, 
  Button, 
  Group, 
  Text, 
  Title, 
  Paper, 
  Divider,
  TextInput,
  Alert
} from '@mantine/core';
import { IconDatabase, IconInfoCircle, IconRefresh } from '@tabler/icons-react';
import { useGetFile } from '@/hooks/useGetFile';

export const CodebaseSettings = () => {
  const { codebasePath, updateCodebasePath } = useGetFile();
  const [localPath, setLocalPath] = useState(codebasePath || '');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    setLocalPath(codebasePath || '');
  }, [codebasePath]);

  const handleUpdateCodebase = async () => {
    setError(null);
    setSuccess(null);
    
    if (!localPath) {
      setError('Please provide a valid path');
      return;
    }
    
    try {
      await updateCodebasePath(localPath);
      setSuccess('Codebase path updated successfully');
    } catch (err) {
      setError('Failed to update codebase path');
      console.error(err);
    }
  };

  const handleReset = () => {
    setLocalPath('');
    setError(null);
    setSuccess(null);
  };
  
  return (
    <Paper p="md" withBorder radius="md" mb="xl">
      <Title order={3} mb="md">Codebase Settings</Title>
      
      {error && (
        <Alert 
          icon={<IconInfoCircle size={16} />} 
          title="Error" 
          color="red" 
          mb="md"
        >
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert 
          icon={<IconInfoCircle size={16} />} 
          title="Success" 
          color="green" 
          mb="md"
        >
          {success}
        </Alert>
      )}
      
      <Box mb="lg">
        <TextInput
          label="Codebase Path"
          description="Enter the absolute path to your codebase"
          placeholder="/path/to/your/codebase"
          value={localPath}
          onChange={(e) => setLocalPath(e.currentTarget.value)}
          mb="md"
        />
        
        <Group mt="md">
          <Button
            leftSection={<IconDatabase size={16} />}
            onClick={handleUpdateCodebase}
            color="blue"
          >
            Update Path
          </Button>
          
          <Button
            leftSection={<IconRefresh size={16} />}
            variant="light"
            onClick={handleReset}
          >
            Reset
          </Button>
        </Group>
      </Box>
      
      <Divider my="md" />
      
      <Text size="sm" c="dimmed">
        <IconInfoCircle size={16} style={{ verticalAlign: 'middle', marginRight: '5px' }} />
        The codebase path determines where to look for files when displaying search results.
        By default, it uses the project's root directory.
      </Text>
    </Paper>
  );
};

export default CodebaseSettings; 