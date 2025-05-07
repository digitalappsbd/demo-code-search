import { Box, Button, Text } from "@mantine/core";
import classes from "./DemoSearch.module.css";
import { IconPointerSearch } from "@tabler/icons-react";
import React, { useState } from 'react';
import { TextInput, Group, Paper, Title } from '@mantine/core';
import { IconFolder } from '@tabler/icons-react';

type DemoSearchProps = {
    handleDemoSearch: (query: string) => void;
};

export default function DemoSearch({ handleDemoSearch }: DemoSearchProps) {


  return (
    <Box className={classes.wrapper}>
      <Text className={classes.demoText} style={{marginTop: '15px'}}>Hybrid Search:</Text>
      <Button
        variant="outline"
        leftSection={<IconPointerSearch  size={"1.3rem"}/>}
        className={classes.demoBtn}
        onClick={() => handleDemoSearch("advanced_range_slider")}
      >
        advanced_range_slider
      </Button>
      <Button
        variant="outline"
        leftSection={<IconPointerSearch  size={"1.3rem"}/>}
        className={classes.demoBtn}
        onClick={() => handleDemoSearch("function initState")}
      >
        function initState
      </Button>
      <Button
        variant="outline"
        leftSection={<IconPointerSearch  size={"1.3rem"}/>}
        className={classes.demoBtn}
        onClick={() => handleDemoSearch("core/external_libs")}
      >
        core/external_libs
      </Button>
    </Box>
  );
}

interface CodebasePathProps {
  codebasePath: string | undefined;
  onUpdateCodebasePath: (path: string | undefined) => void;
}

export const CodebasePath: React.FC<CodebasePathProps> = ({ 
  codebasePath, 
  onUpdateCodebasePath 
}) => {
  const [inputPath, setInputPath] = useState(codebasePath || '');
  
  const handleSubmit = () => {
    onUpdateCodebasePath(inputPath.trim() || undefined);
  };
  
  return (
    <Paper p="md" withBorder mb="md">
      <Title order={4} mb="xs">Codebase Path</Title>
      <Text size="sm" color="dimmed" mb="md">
        Enter the absolute path to your codebase directory:
      </Text>
      
      <Box mb="md">
        <Group>
          <TextInput
            placeholder="/path/to/your/codebase"
            value={inputPath}
            onChange={(e) => setInputPath(e.currentTarget.value)}
            style={{ flexGrow: 1 }}
            leftSection={<IconFolder size={16} />}
          />
          <Button 
            onClick={handleSubmit}
          >
            Set Path
          </Button>
        </Group>
      </Box>
      
      {codebasePath && (
        <Text size="sm" color="dimmed">
          Current codebase path: <strong>{codebasePath}</strong>
        </Text>
      )}
    </Paper>
  );
};
