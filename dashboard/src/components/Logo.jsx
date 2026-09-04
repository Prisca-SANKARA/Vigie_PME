export default function Logo({ withName = true }) {
  return (
    <div className="brand">
      <svg
        className="brand-mark"
        width="28"
        height="28"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M12 2 L21 5.5 V11 C21 16.5 17.2 20.8 12 22 C6.8 20.8 3 16.5 3 11 V5.5 Z"
          fill="currentColor"
          fillOpacity="0.15"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
        <path
          d="M8.5 12 L11 14.5 L16 9"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {withName && <span className="brand-name">Vigie_PME</span>}
    </div>
  );
}
