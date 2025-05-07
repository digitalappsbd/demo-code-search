import { Axios } from "./axios";
import { FILE_URL } from "./constants";

export type PathRequest = {
  path: string;
  codebase_path?: string;
};

export const getFileResult = (PathRequest: PathRequest) => {
  const params = {
    path: PathRequest.path,
    codebase_path: PathRequest.codebase_path,
  };
  return Axios().get(FILE_URL, { params });
};
