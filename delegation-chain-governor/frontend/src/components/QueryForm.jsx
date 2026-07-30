import { useState } from "react";

export default function QueryForm({ onSubmit, isRunning }) {
  const [query, setQuery] = useState("Generate financial report");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) onSubmit(query.trim());
  };

  return (
    <form className="query-form" onSubmit={handleSubmit}>
      <input
        className="query-form__input"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask the agent system something..."
      />
      <button className="query-form__button" type="submit" disabled={isRunning}>
        {isRunning ? "Running..." : "Submit"}
      </button>
    </form>
  );
}
