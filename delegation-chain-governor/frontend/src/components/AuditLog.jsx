export default function AuditLog({ chain, decisions }) {
  return (
    <div>
      <h3 className="audit-log__subtitle">Token Chain — reconstructed from token payloads</h3>
      {!chain || chain.length === 0 ? (
        <p className="audit-log__empty">No tokens minted yet.</p>
      ) : (
        <table className="audit-log">
          <thead>
            <tr>
              <th>Depth</th><th>Agent</th><th>Delegated From</th>
              <th>Scope</th><th>Max Scope (ceiling)</th><th>Expires</th>
            </tr>
          </thead>
          <tbody>
            {chain.map((e, i) => (
              <tr key={i}>
                <td>{e.depth}</td>
                <td>{e.agent}</td>
                <td>{e.parent_agent ?? "—"}</td>
                <td>{e.scope.join(", ")}</td>
                <td>{e.max_scope.join(", ")}</td>
                <td>{new Date(e.expires_at).toLocaleTimeString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h3 className="audit-log__subtitle">Delegation Decisions</h3>
      {!decisions || decisions.length === 0 ? (
        <p className="audit-log__empty">No delegation decisions logged yet.</p>
      ) : (
        <table className="audit-log">
          <thead>
            <tr><th>Parent Agent</th><th>Child Agent</th><th>Scope</th><th>Status</th><th>Timestamp</th></tr>
          </thead>
          <tbody>
            {decisions.map((e, i) => (
              <tr key={i}>
                <td>{e.parent_agent}</td>
                <td>{e.child_agent}</td>
                <td>{e.delegated_scope}</td>
                <td className={`audit-log__status audit-log__status--${e.status}`}>{e.status}</td>
                <td>{e.timestamp}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}