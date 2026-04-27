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
export const deleteCase      = (id)         => API.delete(`/cases/${id}`);
export const getCaseProfile  = (id)         => API.get(`/cases/${id}/profile`).then(r => r.data);

// ── Scans ──────────────────────────────────────────────────────────────────
export const getScans      = (caseId)       => API.get(`/cases/${caseId}/scans`).then(r => r.data);
export const getScan       = (id)           => API.get(`/scans/${id}`).then(r => r.data);
export const createScan    = (caseId, body) => API.post(`/cases/${caseId}/scans`, body).then(r => r.data);

// ── Clusters ───────────────────────────────────────────────────────────────
export const getClusters   = (scanId, params) =>
  API.get(`/scans/${scanId}/clusters`, { params }).then(r => r.data);

export const annotateClusters = (clusterId, body) =>
  API.patch(`/clusters/${clusterId}/annotation`, body).then(r => r.data);

export const deleteScan = (id) => API.delete(`/scans/${id}`);

// ── Organisations ───────────────────────────────────────────────────────────
export const getMyOrg = () =>
  API.get("/orgs/me").then(r => r.data).catch(e => {
    if (e.response?.status === 404) return null;
    throw e;
  });

export const createOrg  = (body)           => API.post("/orgs", body).then(r => r.data);
export const getMembers = (orgId)          => API.get(`/orgs/${orgId}/members`).then(r => r.data);
export const inviteMember = (orgId, body)  => API.post(`/orgs/${orgId}/invite`, body).then(r => r.data);
export const removeMember = (orgId, memberId) => API.delete(`/orgs/${orgId}/members/${memberId}`);
export const acceptInvite = (body)         => API.post("/orgs/accept-invite", body).then(r => r.data);

export const getDeletionRequests = (orgId) =>
  API.get(`/orgs/${orgId}/deletion-requests`).then(r => r.data);

export const createDeletionRequest = (body) =>
  API.post("/orgs/deletion-requests", body).then(r => r.data);

export const approveDeletionRequest = (id) =>
  API.post(`/orgs/deletion-requests/${id}/approve`).then(r => r.data);

export const rejectDeletionRequest = (id) =>
  API.post(`/orgs/deletion-requests/${id}/reject`).then(r => r.data);
