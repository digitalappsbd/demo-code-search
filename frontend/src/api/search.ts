import { Axios } from "./axios";
import { SEARCH_URL, MERGE_CODES_URL } from "./constants";


export type SearchRequest = {
    query: string;
}

export type MergeRequest = {
    file_paths: string[];
}

export const getSearchResult = (searchRequest:SearchRequest) => {
    const params = {
        query: searchRequest.query,
    }
    return Axios().get(SEARCH_URL, { params });
};

export const mergeCodes = (mergeRequest: MergeRequest) => {
    return Axios().post(MERGE_CODES_URL, mergeRequest);
};
