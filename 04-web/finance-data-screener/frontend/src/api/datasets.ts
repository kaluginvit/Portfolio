import client from "./client";
import type { Dataset, DatasetCreate, PlanResponse, CollectResponse, DataRecord, AuditRun, QueryResponse } from "../types";

export const getDatasets = () =>
  client.get<Dataset[]>("/datasets").then((r) => r.data);

export const getDataset = (id: string) =>
  client.get<Dataset>(`/datasets/${id}`).then((r) => r.data);

export const createDataset = (data: DatasetCreate) =>
  client.post<Dataset>("/datasets", data).then((r) => r.data);

export const planAndCollect = (query: string, datasetId: string) =>
  client
    .post<PlanResponse>("/ai/plan_and_collect", { query, dataset_id: datasetId })
    .then((r) => r.data);

export const collectDataset = (datasetId: string, agentRunId: string) =>
  client
    .post<CollectResponse>(`/datasets/${datasetId}/collect`, { agent_run_id: agentRunId })
    .then((r) => r.data);

export const getRecords = (datasetId: string) =>
  client.get<DataRecord[]>(`/datasets/${datasetId}/records`).then((r) => r.data);

export const getAudit = () =>
  client.get<AuditRun[]>("/audit").then((r) => r.data);

export const queryDataset = (datasetId: string, question: string) =>
  client
    .post<QueryResponse>("/ai/query", { dataset_id: datasetId, question })
    .then((r) => r.data);
