const AGENTS = ["gateway_agent", "planner_agent", "finance_agent", "report_agent"];

export default function WorkflowGraph({ currentAgent, status }) {
  const currentIndex = AGENTS.indexOf(currentAgent);
  const isTerminalBad = status === "failed" || status === "pending_approval";

  return (
    <div className="workflow-graph">
      {AGENTS.map((agent, idx) => {
        let className = "workflow-graph__node";

        if (status === "completed") {
          className += " workflow-graph__node--done";
        } else if (idx < currentIndex) {
          className += " workflow-graph__node--done";
        } else if (idx === currentIndex) {
          className += isTerminalBad
            ? " workflow-graph__node--warn"
            : " workflow-graph__node--active";
        }

        return (
          <div key={agent} className="workflow-graph__node-wrapper">
            <div className={className}>{agent.replace("_", " ")}</div>
            {idx < AGENTS.length - 1 && <div className="workflow-graph__arrow">→</div>}
          </div>
        );
      })}
    </div>
  );
}