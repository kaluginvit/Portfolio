import client, { DEMO_MODE } from "./client";
import * as fx from "./fixtures";
import type { Dataset, DatasetCreate, PlanResponse, CollectResponse, DataRecord, AuditRun, QueryResponse } from "../types";

const DEMO_WRITE_ERROR = "Demo Mode — запись недоступна. Данные предзагружены.";

export const getDatasets = (): Promise<Dataset[]> =>
  DEMO_MODE
    ? Promise.resolve(fx.DATASETS)
    : client.get<Dataset[]>("/datasets").then((r) => r.data);

export const getDataset = (id: string): Promise<Dataset> =>
  DEMO_MODE
    ? Promise.resolve(fx.DATASETS.find((d) => d.id === id) ?? fx.DATASETS[0])
    : client.get<Dataset>(`/datasets/${id}`).then((r) => r.data);

export const createDataset = (_data: DatasetCreate): Promise<Dataset> =>
  DEMO_MODE
    ? Promise.reject(new Error(DEMO_WRITE_ERROR))
    : client.post<Dataset>("/datasets", _data).then((r) => r.data);

export const planAndCollect = (_query: string, _datasetId: string): Promise<PlanResponse> =>
  DEMO_MODE
    ? Promise.resolve(fx.DEMO_PLAN_RESPONSE)
    : client.post<PlanResponse>("/ai/plan_and_collect", { query: _query, dataset_id: _datasetId }).then((r) => r.data);

export const collectDataset = (_datasetId: string, _agentRunId: string): Promise<CollectResponse> =>
  DEMO_MODE
    ? Promise.reject(new Error(DEMO_WRITE_ERROR))
    : client.post<CollectResponse>(`/datasets/${_datasetId}/collect`, { agent_run_id: _agentRunId }).then((r) => r.data);

export const getRecords = (datasetId: string): Promise<DataRecord[]> =>
  DEMO_MODE
    ? Promise.resolve(fx.RECORDS[datasetId] ?? [])
    : client.get<DataRecord[]>(`/datasets/${datasetId}/records`).then((r) => r.data);

export const getAudit = (): Promise<AuditRun[]> =>
  DEMO_MODE
    ? Promise.resolve(fx.AUDIT)
    : client.get<AuditRun[]>("/audit").then((r) => r.data);

export const queryDataset = (datasetId: string, question: string): Promise<QueryResponse> =>
  DEMO_MODE
    ? Promise.resolve(fx.resolveQuery(datasetId, question))
    : client.post<QueryResponse>("/ai/query", { dataset_id: datasetId, question }).then((r) => r.data);
