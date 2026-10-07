const TABS = [
  { id: "resolver", label: "Resolver" },
  { id: "comparar", label: "Comparación" },
  { id: "sensibilidad", label: "Sensibilidad" },
];

export function MethodTabs({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <nav className="flex gap-2" aria-label="Secciones">
      {TABS.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`rounded px-4 py-2 text-sm font-medium ${
            value === t.id ? "bg-slate-900 text-white" : "border border-slate-300 bg-white"
          }`}
        >
          {t.label}
        </button>
      ))}
    </nav>
  );
}
