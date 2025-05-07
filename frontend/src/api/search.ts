import { Axios } from "./axios";
import { SEARCH_URL, MERGE_CODES_URL, GENERATE_EMBEDDINGS_URL, EMBEDDING_STATUS_URL } from "./constants";


export type SearchRequest = {
    query: string;
}

export type MergeRequest = {
    file_paths: string[];
}

export type EmbeddingRequest = {
    model: string;
    force: boolean;
    use_gpu: boolean;
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

export const generateEmbeddings = (embeddingRequest: EmbeddingRequest) => {
    return Axios().post(GENERATE_EMBEDDINGS_URL, embeddingRequest);
};

export const getEmbeddingStatus = () => {
    return Axios().get(EMBEDDING_STATUS_URL);
};
