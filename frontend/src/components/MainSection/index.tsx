import {
  Button,
  Container,
  TextInput,
  Box,
  Image,
  Title,
  Text,
  Loader,
  Group,
  Tooltip,
  Notification,
} from "@mantine/core";
import { IconSearch, IconCopy, IconFileCode } from "@tabler/icons-react";
import useMountedState from "@/hooks/useMountedState";
import { useGetSearchResult } from "@/hooks/useGetSearchResult";
import { getHotkeyHandler, useHotkeys } from "@mantine/hooks";
import { FileTree } from "../FIleTree";
import { CodeContainer } from "../CodeContainer";
import classes from "./Main.module.css";
import DemoSearch from "../DemoSearch";
import { useSearchParams } from "react-router-dom";
import { useEffect } from "react";
import { copyToClipboard } from "@/utils/clipboard";
import { mergeCodes } from "@/api/search";

export default function Main() {
  const [query, setQuery] = useMountedState("");
  const { data, getSearch, loading, error, resetData } = useGetSearchResult();
  const [searchParams, setSearchParams] = useSearchParams();
  const [clipboardNotification, setClipboardNotification] = useMountedState<{
    visible: boolean;
    message: string;
  }>({ visible: false, message: "" });

  useHotkeys([
    [
      "/",
      () => {
        const input = document.querySelector("input");
        input?.focus();
      },
    ],
  ]);
  const handleSubmit = () => {
    resetData();
    if (query) {
      getSearch(query);
      setSearchParams({ query });
    }
  };

  const handleDemoSearch = (query: string) => {
    resetData();
    if (query) {
      setSearchParams({ query: query });
      setQuery(query);
      getSearch(query);
    }
  };

  useEffect(() => {
    if (searchParams.get("query")&&searchParams.get("query")!==query) {
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
    
    try {
      const response = await mergeCodes({ file_paths: filePaths });
      if (response.data?.result) {
        const success = await copyToClipboard(response.data.result);
        if (success) {
          setClipboardNotification({
            visible: true,
            message: "Success! Merged code copied to clipboard",
          });
        }
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
        pt={data || loading ? "1rem" : "5rem"}
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
      />

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
          <DemoSearch handleDemoSearch={handleDemoSearch} />
          <Box
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Image
              src="/landing.gif"
              alt="Qdrant Landing"
              maw={400}
              h={400}
              fit="contain"
            />
            <Title order={3} className={classes.heading}>
              Qdrant{" "}
              <span className={classes.headingHighlight}>Code Search</span>{" "}
              Unleashing Semantic Power
            </Title>
            <Text className={classes.subHeading}>
              Qdrant Code Explorer: Empowering Semantic Searching in Qdrant
              Repository with Advanced Code Analysis
            </Text>
          </Box>
        </>
      )}
      {loading && (
        <Box className={classes.loader}>
          <Loader type="bars" />
        </Box>
      )}
      {error && (
        <Box>
          <Image src="/error.gif" alt="Error" h={400} fit="contain" />

          <Text className={classes.subHeading}>
            Something went wrong, {error}
          </Text>
        </Box>
      )}
    </Container>
  );
}
