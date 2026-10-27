// Mensajes de error del backend (422 en español) o de red, tal cual llegan.
// Los errores nunca cierran el programa ni borran lo capturado.
export function ErrorBanner({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  return (
    <div
      role="alert"
      className="flex items-start justify-between gap-3 rounded-lg border border-pen/40 bg-pen-wash p-4"
    >
      <p className="text-sm">{message}</p>
      <button
        type="button"
        className="btn-ghost shrink-0 text-sm"
        onClick={onDismiss}
        aria-label="Cerrar el aviso"
      >
        Cerrar
      </button>
    </div>
  );
}
