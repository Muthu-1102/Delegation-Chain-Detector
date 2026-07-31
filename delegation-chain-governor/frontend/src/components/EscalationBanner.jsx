export default function EscalationBanner({ escalation, onGrant, onDeny, isResolving }) {
  if (!escalation) return null;

  return (
    <div className="escalation">
      <div className="escalation__title">⚠ Delegation blocked by the Governor</div>
      <div className="escalation__body">
        <strong>{escalation.parent_agent}</strong> tried to hand off to{" "}
        <strong>{escalation.child_agent}</strong> with more scope than it currently
        holds. This is exactly the kind of privilege escalation the Governor
        exists to catch. Choose how to proceed:
      </div>

      <div className="escalation__scopes">
        <div className="escalation__scope-group">
          <h4>Requested</h4>
          {escalation.requested_scope.map((s) => (
            <span key={s} className="escalation__scope-chip">{s}</span>
          ))}
        </div>
        <div className="escalation__scope-group">
          <h4>Currently held</h4>
          {escalation.available_scope.length > 0 ? (
            escalation.available_scope.map((s) => (
              <span key={s} className="escalation__scope-chip">{s}</span>
            ))
          ) : (
            <span className="escalation__scope-chip">none</span>
          )}
        </div>
      </div>

      <div className="escalation__actions">
        <button
          className="escalation__button escalation__button--grant"
          onClick={onGrant}
          disabled={isResolving}
        >
          Retrict the Extra Access and Continue
        </button>
        <button
          className="escalation__button escalation__button--deny"
          onClick={onDeny}
          disabled={isResolving}
        >
          Abort the Process
        </button>
      </div>
    </div>
  );
}