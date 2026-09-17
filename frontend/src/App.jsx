import { useEffect, useState } from "react";
import "./App.css";

import {
  getAuditLogs,
  getPendingApprovals,
  approveRequest,
  rejectRequest,
  submitRefundRequest,
} from "./api";


function App() {
  const [auditLogs, setAuditLogs] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [loading, setLoading] = useState(true);

  const [customerId, setCustomerId] = useState("");
  const [orderId, setOrderId] = useState("");
  const [refundAmount, setRefundAmount] = useState("");
  const [reason, setReason] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");


  const loadData = async () => {
    try {
      const [auditResponse, approvalResponse] = await Promise.all([
        getAuditLogs(),
        getPendingApprovals(),
      ]);

      setAuditLogs(auditResponse.data);
      setPendingApprovals(approvalResponse.data);

    } catch (error) {
      console.error("Failed to load dashboard data:", error);

    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    loadData();
  }, []);


  const handleSubmitRefund = async (event) => {
    event.preventDefault();

    setSubmitting(true);
    setMessage("");

    try {
      const response = await submitRefundRequest({
        customer_id: Number(customerId),
        order_id: Number(orderId),
        refund_amount: Number(refundAmount),
        reason: reason,
      });

      const result = response.data;

      if (result.decision === "ALLOW") {
        setMessage("Refund approved and processed successfully.");
      } else if (result.decision === "HUMAN_APPROVAL") {
        setMessage(
          `Refund requires human approval. Approval ID: ${result.approval.approval_id}`
        );
      } else {
        setMessage("Refund request was blocked.");
      }

      setCustomerId("");
      setOrderId("");
      setRefundAmount("");
      setReason("");

      await loadData();

    } catch (error) {
      console.error("Refund request failed:", error);

      setMessage(
        error.response?.data?.detail ||
        "Failed to submit refund request."
      );

    } finally {
      setSubmitting(false);
    }
  };


  const handleApprove = async (approvalId) => {
    try {
      await approveRequest(approvalId);
      await loadData();

    } catch (error) {
      console.error("Approval failed:", error);
    }
  };


  const handleReject = async (approvalId) => {
    try {
      await rejectRequest(approvalId);
      await loadData();

    } catch (error) {
      console.error("Rejection failed:", error);
    }
  };


  const allowedCount = auditLogs.filter(
    (log) => log.decision === "ALLOW"
  ).length;


  const approvalCount = auditLogs.filter(
    (log) => log.decision === "HUMAN_APPROVAL"
  ).length;


  const blockedCount = auditLogs.filter(
    (log) => log.decision === "BLOCK"
  ).length;


  if (loading) {
    return (
      <div className="dashboard">
        <h2>Loading Control Tower...</h2>
      </div>
    );
  }


  return (
    <div className="dashboard">

      <header className="header">
        <h1>AgentOps Control Tower</h1>
        <p>
          AI Agent Governance & Monitoring Dashboard
        </p>
      </header>


      {/* Refund Request */}

      <section className="section">

        <h2>Submit Refund Request</h2>

        <form onSubmit={handleSubmitRefund}>

          <input
            type="number"
            placeholder="Customer ID"
            value={customerId}
            onChange={(event) =>
              setCustomerId(event.target.value)
            }
            required
          />

          <input
            type="number"
            placeholder="Order ID"
            value={orderId}
            onChange={(event) =>
              setOrderId(event.target.value)
            }
            required
          />

          <input
            type="number"
            placeholder="Refund Amount"
            value={refundAmount}
            onChange={(event) =>
              setRefundAmount(event.target.value)
            }
            required
          />

          <input
            type="text"
            placeholder="Reason"
            value={reason}
            onChange={(event) =>
              setReason(event.target.value)
            }
            required
          />

          <button
            type="submit"
            disabled={submitting}
          >
            {submitting
              ? "Processing..."
              : "Submit Refund"}
          </button>

        </form>

        {message && (
          <p>{message}</p>
        )}

      </section>


      {/* Overview */}

      <section className="section">

        <h2>Overview</h2>

        <div className="kpi-grid">

          <div className="kpi-card">
            <h3>Total Requests</h3>
            <p>{auditLogs.length}</p>
          </div>

          <div className="kpi-card">
            <h3>Allowed</h3>
            <p>{allowedCount}</p>
          </div>

          <div className="kpi-card">
            <h3>Human Approval</h3>
            <p>{approvalCount}</p>
          </div>

          <div className="kpi-card">
            <h3>Blocked</h3>
            <p>{blockedCount}</p>
          </div>

        </div>

      </section>


      {/* Pending Approvals */}

      <section className="section">

        <h2>Pending Approvals</h2>

        {pendingApprovals.length === 0 ? (

          <div className="empty-state">
            No pending approvals.
          </div>

        ) : (

          <div className="table-container">

            <table>

              <thead>
                <tr>
                  <th>ID</th>
                  <th>Customer</th>
                  <th>Order</th>
                  <th>Amount</th>
                  <th>Reason</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>

                {pendingApprovals.map((approval) => (

                  <tr key={approval.id}>

                    <td>{approval.id}</td>

                    <td>{approval.customer_id}</td>

                    <td>{approval.order_id}</td>

                    <td>
                      ₹{approval.amount}
                    </td>

                    <td>
                      {approval.reason}
                    </td>

                    <td>

                      <div className="actions">

                        <button
                          className="approve-btn"
                          onClick={() =>
                            handleApprove(approval.id)
                          }
                        >
                          Approve
                        </button>

                        <button
                          className="reject-btn"
                          onClick={() =>
                            handleReject(approval.id)
                          }
                        >
                          Reject
                        </button>

                      </div>

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </section>


      {/* Audit Logs */}

      <section className="section">

        <h2>Audit Logs</h2>

        <div className="table-container">

          <table>

            <thead>

              <tr>
                <th>ID</th>
                <th>Customer</th>
                <th>Order</th>
                <th>Refund Amount</th>
                <th>Decision</th>
                <th>Reason</th>
              </tr>

            </thead>

            <tbody>

              {auditLogs.map((log) => (

                <tr key={log.id}>

                  <td>{log.id}</td>

                  <td>{log.customer_id}</td>

                  <td>{log.order_id}</td>

                  <td>
                    ₹{log.refund_amount}
                  </td>

                  <td>

                    <span
                      className={`status ${
                        log.decision === "ALLOW"
                          ? "status-allow"
                          : log.decision === "HUMAN_APPROVAL"
                          ? "status-human"
                          : "status-block"
                      }`}
                    >
                      {log.decision}
                    </span>

                  </td>

                  <td>
                    {log.reason}
                  </td>

                </tr>

              ))}

            </tbody>

          </table>

        </div>

      </section>

    </div>
  );
}


export default App;