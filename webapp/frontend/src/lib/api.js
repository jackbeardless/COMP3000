import axios from "axios";
import { supabase } from "./supabase";

const API = axios.create({ baseURL: import.meta.env.VITE_API_URL });

// Attach the Supabase JWT to every request automatically
API.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Cases ──────────────────────────────────────────────────────────────────
export const getCases      = ()             => API.get("/cases").then(r => r.data);
export const getCase       = (id)           => API.get(`/cases/${id}`).then(r => r.data);
export const createCase    = (body)         => API.post("/cases", body).then(r => r.data);
export const updateCase    = (id, body)     => API.patch(`/cases/${id}`, body).then(r => r.data);
export const deleteCase    = (id)           => API.delete(`/cases/${id}`);

// ── Scans ──────────────────────────────────────────────────────────────────
export const getScans      = (caseId)       => API.get(`/cases/${caseId}/scans`).then(r => r.data);
export const getScan       = (id)           => API.get(`/scans/${id}`).then(r => r.data);
export const createScan    = (caseId, body) => API.post(`/cases/${caseId}/scans`, body).then(r => r.data);

// ── Clusters ───────────────────────────────────────────────────────────────
export const getClusters   = (scanId, params) =>
  API.get(`/scans/${scanId}/clusters`, { params }).then(r => r.data);

export const annotateClusters = (clusterId, body) =>
  API.patch(`/clusters/${clusterId}/annotation`, body).then(r => r.data);
