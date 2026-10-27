const TABS = [
  { id: "resolver", label: "Resolver" },
  { id: "comparar", label: "Comparación" },
  { id: "sensibilidad", label: "Sensibilidad" },
] as const;

export type TabId = (typeof TABS)[number]["id"];

export function MethodTabs({
  value,
  onChange,
}: {
  value: TabId;
  onChange: (v: TabId) => void;
}) {
  return (
    <nav className="flex gap-1 border-b border-rule/70" aria-label="Secciones">
      {TABS.map((t) => (
        <button
          key={t.id}
          role="tab"
          aria-selected={value === t.id}
          onClick={() => onChange(t.id)}
          className={`-mb-px rounded-t-md border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
            value === t.id
              ? "border-pen text-ink"
              : "border-transparent text-ink-soft hover:text-ink"
          }`}
        >
          {t.label}
        </button>
      ))}
    </nav>
  );
}
