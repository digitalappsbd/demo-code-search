import {
  Button,
  Container,
  TextInput,
  Box,
  Title,
  Text,
  Loader,
  Group,
  Tooltip,
  Notification,
  Tabs,
  Select
} from "@mantine/core";
import { IconSearch, IconCopy, IconFileCode, IconBrain, IconCode, IconSettings } from "@tabler/icons-react";
import useMountedState from "@/hooks/useMountedState";
import { useGetSearchResult } from "@/hooks/useGetSearchResult";
import { getHotkeyHandler, useHotkeys } from "@mantine/hooks";
import { FileTree } from "../FIleTree";
import { CodeContainer } from "../CodeContainer";
import classes from "./Main.module.css";
import DemoSearch from "../DemoSearch";
import { useSearchParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { copyToClipboard } from "@/utils/clipboard";
import { mergeCodes } from "@/api/search";
import EmbeddingGeneration from "../EmbeddingGeneration";
import StructureGeneration from "../StructureGeneration";
import CodebaseSettings from "../CodebaseSettings";
import { getAvailableEmbeddings } from "@/api/search";

export default function Main() {
  const [query, setQuery] = useMountedState("");
  const { data, getSearch, loading, error, resetData } = useGetSearchResult();
  const [searchParams, setSearchParams] = useSearchParams();
  const [clipboardNotification, setClipboardNotification] = useMountedState<{
    visible: boolean;
    message: string;
  }>({ visible: false, message: "" });
  const [embeddingModels, setEmbeddingModels] = useState<{value: string, label: string}[]>([]);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [loadingModels, setLoadingModels] = useState(false);

  useHotkeys([
    [
      "/",
      () => {
        const input = document.querySelector("input");
        input?.focus();
      },
    ],
  ]);
  
  // Fetch available embedding models
  useEffect(() => {
    const fetchEmbeddingModels = async () => {
      setLoadingModels(true);
      try {
        const response = await getAvailableEmbeddings();
        if (response.data && response.data.models) {
          setEmbeddingModels(response.data.models);
        }
      } catch (err) {
        console.error("Error fetching embedding models:", err);
      } finally {
        setLoadingModels(false);
      }
    };
    
    fetchEmbeddingModels();
  }, []);

  const handleSubmit = () => {
    resetData();
    if (query) {
      getSearch(query, selectedModel || undefined);
      setSearchParams({ 
        query,
        ...(selectedModel && { model: selectedModel })
      });
    }
  };

  const handleDemoSearch = (query: string) => {
    resetData();
    if (query) {
      setSearchParams({ 
        query, 
        ...(selectedModel && { model: selectedModel })
      });
      setQuery(query);
      getSearch(query, selectedModel || undefined);
    }
  };

  useEffect(() => {
    if (searchParams.get("query") && searchParams.get("query") !== query) {
      const modelParam = searchParams.get("model");
      if (modelParam) {
        setSelectedModel(modelParam);
      }
      handleDemoSearch(searchParams.get("query") ?? "");
    }
  }, [searchParams.get("query")]);

  useEffect(() => {
    if (query === "") {
      resetData();
      window.history.replaceState({}, "", "/");
    }
  }, [query]);

  // Show notification for 3 seconds
  useEffect(() => {
    if (clipboardNotification.visible) {
      const timer = setTimeout(() => {
        setClipboardNotification({ visible: false, message: "" });
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [clipboardNotification.visible]);

  // Function to copy all file paths to clipboard
  const handleCopyFilePaths = async () => {
    if (!data?.result.length) return;
    
    // Extract unique file paths
    const filePaths = [...new Set(data.result.map(item => item.context.file_path))];
    const pathsText = filePaths.join('\n');
    
    const success = await copyToClipboard(pathsText);
    if (success) {
      setClipboardNotification({
        visible: true,
        message: "Success! File paths copied to clipboard",
      });
    }
  };

  // Function to merge code from all search results
  const handleMergeCodes = async () => {
    if (!data?.result.length) return;
    
    // Extract unique file paths
    const filePaths = [...new Set(data.result.map(item => item.context.file_path))];
    console.log("File paths for merge:", filePaths);
    
    try {
      const response = await mergeCodes({ file_paths: filePaths });
      console.log("Merge response:", response);
      if (response.data?.result) {
        console.log("Merged content length:", response.data.result.length);
        console.log("Content preview:", response.data.result.substring(0, 100) + "...");
        
        const success = await copyToClipboard(response.data.result);
        console.log("Clipboard copy result:", success);
        if (success) {
          setClipboardNotification({
            visible: true,
            message: "Success! Merged code copied to clipboard",
          });
        } else {
          console.error("Failed to copy to clipboard");
          setClipboardNotification({
            visible: true,
            message: "Failed to copy to clipboard",
          });
        }
      } else {
        console.error("No result data in response");
        setClipboardNotification({
          visible: true,
          message: "Failed to merge code: Empty response",
        });
      }
    } catch (error) {
      console.error("Error merging code:", error);
      setClipboardNotification({
        visible: true, 
        message: "Failed to merge code"
      });
    }
  };

  return (
    <Container size="lg">
      <Group pb="xs" align="flex-end">
        <TextInput
          radius={4}
          size="md"
          leftSection={<IconSearch color="#102252" />}
          placeholder="Enter a query"
          rightSection={
            <Button
              radius={4}
              w={"100%"}
              size={"md"}
              variant="filled"
              color="Primary.2"
              onClick={handleSubmit}
            >
              Search
            </Button>
          }
          rightSectionWidth={"6rem"}
          value={query}
          required
          onChange={(event: any) => setQuery(event.currentTarget.value)}
          onKeyDown={getHotkeyHandler([["Enter", handleSubmit]])}
          classNames={{ input: classes.input }}
          style={{
            position: "sticky",
            top: 56,
            zIndex: 100,
            backgroundColor: "#fff",
          }}
          ref={(input) => input && input.focus()}
          w="70%"
        />
        
        <Select
          label="Search using embeddings"
          description="Select which embedding model to use for searching"
          placeholder="Select embedding model"
          data={embeddingModels}
          value={selectedModel}
          onChange={setSelectedModel}
          w="30%"
          disabled={loadingModels}
        />
      </Group>

      {selectedModel && (
        <Text size="xs" c="dimmed" mt="-xs" mb="xs">
          Current search will use: <strong>{embeddingModels.find(m => m.value === selectedModel)?.label}</strong>
        </Text>
      )}

      {clipboardNotification.visible && (
        <Notification
          color="green"
          title="Success"
          withCloseButton={false}
          style={{ position: "fixed", top: "70px", right: "20px", zIndex: 1000 }}
        >
          {clipboardNotification.message}
        </Notification>
      )}

      {data && (
        <>
          <Group justify="flex-end" mt="md" mb="sm">
            <Tooltip label="Copy all file paths">
              <Button
                variant="outline"
                leftSection={<IconCopy size="1rem" />}
                onClick={handleCopyFilePaths}
                color="blue"
              >
                Copy Paths
              </Button>
            </Tooltip>
            <Tooltip label="Merge code and copy to clipboard">
              <Button
                variant="outline"
                leftSection={<IconFileCode size="1rem" />}
                onClick={handleMergeCodes}
                color="blue"
              >
                Merge Code
              </Button>
            </Tooltip>
          </Group>

          <Box
            style={{
              display: "flex",
              flexDirection: "row",
              alignItems: "flex-start",
              justifyContent: "space-between",
            }}
          >
            <Box className={classes.navbar}>
              <FileTree data={data} />
            </Box>
            <Box pt={"md"} className={classes.codeDisplayArea}>
              {data?.result.map((item) => (
                <CodeContainer
                  {...item}
                  key={`${item.context.snippet} ${item.line_from} ${item.line_to}`}
                />
              ))}
            </Box>
          </Box>
        </>
      )}
      
      {!data && !loading && !error && (
        <>
          <Tabs defaultValue="search" mt="xl">
            <Tabs.List>
              <Tabs.Tab value="search" leftSection={<IconSearch size="0.8rem" />}>
                Search Examples
              </Tabs.Tab>
              <Tabs.Tab value="structures" leftSection={<IconCode size="0.8rem" />}>
                Structure Generation
              </Tabs.Tab>
              <Tabs.Tab value="embeddings" leftSection={<IconBrain size="0.8rem" />}>
                Embedding Generation
              </Tabs.Tab>
              <Tabs.Tab value="settings" leftSection={<IconSettings size="0.8rem" />}>
                Codebase Settings
              </Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="search" pt="xl">
              <DemoSearch handleDemoSearch={handleDemoSearch} />
            </Tabs.Panel>
            
            <Tabs.Panel value="structures" pt="xl">
              <StructureGeneration />
            </Tabs.Panel>
            
            <Tabs.Panel value="embeddings" pt="xl">
              <EmbeddingGeneration />
            </Tabs.Panel>
            
            <Tabs.Panel value="settings" pt="xl">
              <CodebaseSettings />
            </Tabs.Panel>
          </Tabs>
          
          <Box
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Title
              order={1}
              size="h2"
              style={{ fontWeight: 900, marginTop: 20 }}
            >
              Code Search
            </Title>
            <Text size="lg" c="#555" ta="center" mt={10} mb={30}>
              Search through your codebase semantically
            </Text>
          </Box>
        </>
      )}

      {loading && (
        <Box
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            marginTop: "3rem",
          }}
        >
          <Title order={4} mb={"sm"}>
            Searching...
          </Title>
          <Loader size={"lg"} color="#3d5afe" />
          <Text size="sm" c="dimmed" mt="xs">
            This may take a moment
          </Text>
        </Box>
      )}

      {error && (
        <Box mt="lg">
          <Text c="red" fw={600}>
            Error: {error}
          </Text>
        </Box>
      )}
    </Container>
  );
}
