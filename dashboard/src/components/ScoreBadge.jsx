function riskLevel(score) {
  if (score >= 90) return { label: "Bon", className: "badge badge-good" };
  if (score >= 70) return { label: "Correct", className: "badge badge-ok" };
  if (score >= 40) return { label: "Risque", className: "badge badge-warn" };
  return { label: "Critique", className: "badge badge-critical" };
}

export default function ScoreBadge({ score }) {
  const { label, className } = riskLevel(score);
  return (
    <span className={className}>
      {score}/100 — {label}
    </span>
  );
}
