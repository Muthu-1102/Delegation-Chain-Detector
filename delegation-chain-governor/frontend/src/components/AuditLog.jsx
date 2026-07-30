export default function AuditLog({ chain }) {
  if (!chain || chain.length === 0) {
    return <p className="audit-log__empty">No delegation events yet.</p>;
  }

  return (
    <table className="audit-log">
      <thead>
        <tr>
          <th>Parent Agent</th>
          <th>Child Agent</th>
          <th>Scope</th>
          <th>Status</th>
          <th>Timestamp</th>
        </tr>
      </thead>
      <tbody>
        {chain.map((entry, idx) => (
          <tr key={idx}>
            <td>{entry.parent_agent}</td>
            <td>{entry.child_agent}</td>
            <td>{entry.delegated_scope}</td>
            <td className={`audit-log__status audit-log__status--${entry.status}`}>
              {entry.status}
            </td>
            <td>{entry.timestamp}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
