import { StatusCodes } from "http-status-codes";
import useMountedState from "./useMountedState";
import { getFileResult } from "@/api/file";

export type searchResponse = {
  result: {
    code: string[];
    endline: number;
    startline: number;
    path: string;
    content?: string;
    file_name?: string;
    line_count?: number;
    lines?: { content: string; line_number: number }[];
  }[];
};

export const useGetFile = () => {
  const [data, setData] = useMountedState<searchResponse | null>(null);
  const [error, setError] = useMountedState<string | null>(null);
  const [loading, setLoading] = useMountedState<boolean>(false);
  const [codebasePath, setCodebasePath] = useMountedState<string | undefined>(undefined);

  const getFile = async (path: string, codebase_path?: string) => {
    try {
      setLoading(true);
      setError(null);
      
      // If codebase_path is provided, update state
      if (codebase_path) {
        setCodebasePath(codebase_path);
      }
      
      const res = await getFileResult({ 
        path,
        codebase_path: codebase_path || codebasePath
      });

      switch (res.status) {
        case StatusCodes.OK: {
          const searchRes = res.data;
          setData(searchRes);
          break;
        }
        default: {
          setError("Failed to get the file");
        }
      }
    } catch (err) {
      console.error("Error getting file:", err);
      setError("Failed to get the file");
    } finally {
      setLoading(false);
    }
  };

  const resetData = () => {
    setData(null);
  };

  const updateCodebasePath = (path: string | undefined) => {
    setCodebasePath(path);
  };

  return { data, error, loading, getFile, resetData, codebasePath, updateCodebasePath };
};
