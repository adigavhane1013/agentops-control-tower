import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

export const getAuditLogs = () => {
  return API.get("/audit/logs");
};

export const getPendingApprovals = () => {
  return API.get("/approvals/pending");
};

export const approveRequest = (approvalId) => {
  return API.post(`/approvals/${approvalId}/approved`);
};

export const rejectRequest = (approvalId) => {
  return API.post(`/approvals/${approvalId}/rejected`);
};

export const submitRefundRequest = (refundData) => {
  return API.post("/refunds/request", refundData);
};