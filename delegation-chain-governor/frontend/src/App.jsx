import { useState, useRef } from "react";
import QueryForm from "./components/QueryForm.jsx";
import WorkflowGraph from "./components/WorkflowGraph.jsx";
import AuditLog from "./components/AuditLog.jsx";
import EscalationBanner from "./components/EscalationBanner.jsx";
import { submitQuery, getWorkflowStatus, getAuditTrail, resolveEscalation } from "./api.js";

const TERMINAL = ["completed", "failed", "pending_approval"];

export default function App() {
  const [workflow, setWorkflow] = useState(null);
  const [auditChain, setAuditChain] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isResolving, setIsResolving] = useState(false);
  const pollRef = useRef(null);

  const refreshAudit = async (requestId) => {
    const audit = await getAuditTrail(requestId);
    setAuditChain(audit.chain);
  };

  const pollStatus = (requestId) => {
    clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      const data = await getWorkflowStatus(requestId);
      setWorkflow(data);

      if (TERMINAL.includes(data.status)) {
        clearInterval(pollRef.current);
        setIsRunning(false);
        if (data.status !== "pending_approval") {
          await refreshAudit(requestId);
        }
      }
    }, 1200);
  };

  const handleSubmit = async (query) => {
    setIsRunning(true);
    setAuditChain([]);
    const { request_id, status } = await submitQuery(query);
    setWorkflow({ request_id, status, current_agent: "gateway_agent" });
    pollStatus(request_id);
  };

  const handleDecision = async (decision) => {
    setIsResolving(true);
    await resolveEscalation(workflow.request_id, decision);
    setIsRunning(true);
    pollStatus(workflow.request_id);
    setIsResolving(false);
  };

  return (
    <div className="app">
      <header className="app__header">
        <h1>Delegation Chain Governor</h1>
        <p>Secure multi-agent workflow orchestration</p>
      </header>

      <QueryForm onSubmit={handleSubmit} isRunning={isRunning} />

      {workflow && (
        <section className="app__section">
          <h2>Workflow</h2>
          <div className="card">
            <WorkflowGraph currentAgent={workflow.current_agent} status={workflow.status} />
            <div className="status-line">
              Request <code>{workflow.request_id}</code> ·{" "}
              <span className={`status-pill status-pill--${workflow.status}`}>
                {workflow.status.replace("_", " ")}
              </span>
            </div>

            {workflow.report_result && (
              <div className="app__report">
                <h3>Report</h3>
                <p>{workflow.report_result}</p>
              </div>
            )}

            {workflow.note && <div className="app__note">{workflow.note}</div>}

            <EscalationBanner
              escalation={workflow.escalation}
              isResolving={isResolving}
              onGrant={() => handleDecision("grant")}
              onDeny={() => handleDecision("deny")}
            />
          </div>
        </section>
      )}

      <section className="app__section">
        <h2>Delegation Audit Trail</h2>
        <div className="card">
          <AuditLog chain={auditChain} />
        </div>
      </section>
    </div>
  );
}