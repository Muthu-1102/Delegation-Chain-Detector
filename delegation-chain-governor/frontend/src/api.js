import axios from "axios";

const client = axios.create({ baseURL: "/api" });

export async function login(username, password) {
  const { data } = await client.post("/auth/login", { username, password });
  return data;
}

export async function submitQuery(query) {
  const { data } = await client.post("/query", { query });
  return data;
}

export async function getWorkflowStatus(requestId) {
  const { data } = await client.get(`/workflow/${requestId}`);
  return data;
}

export async function getAuditTrail(requestId) {
  const { data } = await client.get(`/audit/${requestId}`);
  return data;
}

export async function getExecutionLogs() {
  const { data } = await client.get("/logs");
  return data;
}

export async function resolveEscalation(requestId, decision) {
  const { data } = await client.post(`/workflow/${requestId}/resolve`, { decision });
  return data;
}