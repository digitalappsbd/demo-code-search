import { getSearchResult } from "@/api/search";
import { StatusCodes } from "http-status-codes";
import useMountedState from "./useMountedState";

export type searchResponse = {
  result: {
    code_type: string;
    context: {
      file_name: string;
      file_path: string;
      module: string;
      snippet: string;
      struct_name: string;
    };
    docstring: string | null;
    line: number;
    line_from: number;
    line_to: number;
    name: string;
    signature: string;
    similarity: number;
    match_type?: string;
    matched_field?: string;
    sub_matches: {
      overlap_from: number;
      overlap_to: number;
    }[];
  }[];
};
export const useGetSearchResult = () => {
  const [data, setData] = useMountedState<searchResponse | null>(null);
  const [error, setError] = useMountedState<string | null>(null);
  const [loading, setLoading] = useMountedState<boolean>(false);

  const getSearch = async (query: string, model?: string) => {
    try {
      setLoading(true);
      setError(null);
      const res = await getSearchResult({ query, model });

      switch (res.status) {
        case StatusCodes.OK: {
          const searchRes = res.data;
          
          // Check if the backend returned an error message
          if (searchRes.error) {
            setError(searchRes.error);
            return;
          }
          
          setData(searchRes);
          break;
        }
        default: {
          setError("Failed to get Search Result");
        }
      }
    } catch (err) {
      console.error("Search error:", err);
      if (err instanceof Error) {
        setError(`Failed to get Search Result: ${err.message}`);
      } else {
        setError("Failed to get Search Result");
      }
    } finally {
      setLoading(false);
    }
  };

  const resetData = () => {
    setData(null);
  };

  return { data, error, loading, getSearch, resetData };
};
