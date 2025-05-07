import { Axios } from "./axios";
import { 
    SEARCH_URL, 
    MERGE_CODES_URL, 
    GENERATE_EMBEDDINGS_URL, 
    EMBEDDING_STATUS_URL,
    GENERATE_STRUCTURES_URL,
    STRUCTURE_STATUS_URL
} from "./constants";


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
    batch_size?: number;
}

export type StructureRequest = {
    target_dir: string;
    pattern: string;
    max_lines: number;
    force: boolean;
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

export const generateStructures = (structureRequest: StructureRequest) => {
    return Axios().post(GENERATE_STRUCTURES_URL, structureRequest);
};

export const getStructureStatus = () => {
    return Axios().get(STRUCTURE_STATUS_URL);
};
