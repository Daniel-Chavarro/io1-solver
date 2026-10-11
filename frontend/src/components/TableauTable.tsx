import type { TableauData } from "../types";

// Renders one tableau snapshot plus, during a step, the decision taken on
// it: entering column and leaving row tinted, pivot cell circled in red pen,
// and the minimum-ratio column next to RHS. Cells are canonical strings
// ("3/4", "-M-30") shown as-is. Dimension-agnostic: any R x C scrolls with
// the "Basica" and "RHS" columns pinned.
interface Props {
  tableau: TableauData;
  entering?: string | null;
  leaving?: string | null;
  ratios?: string[] | null;
  ties?: string[] | null;
}

export function TableauTable({ tableau, entering, leaving, ratios, ties }: Props) {
  const bodyCols = tableau.columns.slice(0, -1); // the last column is RHS
  const enteringIdx = entering ? bodyCols.indexOf(entering) : -1;
  const showRatios = !!ratios && ratios.length > 0;
  const tiedRows = new Set(ties ?? []);

  return (
    <div className="overflow-x-auto rounded-md border border-rule/70">
      <table className="tnum border-separate border-spacing-0 font-display text-sm">
        <thead>
          <tr>
            <th
              scope="col"
              className="sticky left-0 z-10 border-b border-l-2 border-r border-rule/70 bg-paper px-3 py-1.5 text-left font-sans text-xs font-medium text-ink-soft"
            >
              Básica
            </th>
            {bodyCols.map((col, j) => (
              <th
                key={col}
                scope="col"
                className={`whitespace-nowrap border-b border-r border-rule/70 px-3 py-1.5 text-center font-sans text-xs font-medium ${
                  enteringIdx === j ? "bg-rule-wash text-ink" : "text-ink-soft"
                }`}
              >
                {col}
              </th>
            ))}
            {showRatios && (
              <th
                scope="col"
                className="whitespace-nowrap border-b border-r border-rule/70 bg-paper px-3 py-1.5 text-center font-sans text-xs font-medium text-ink-soft"
              >
                razón mín
              </th>
            )}
            <th
              scope="col"
              className="sticky right-0 z-10 border-b border-l-2 border-r-2 border-rule/70 bg-paper px-3 py-1.5 text-center font-sans text-xs font-semibold text-ink"
            >
              RHS
            </th>
          </tr>
        </thead>
        <tbody>
          {tableau.rows.map((row, i) => {
            const isZ = i === 0;
            const isLeaving = row.basic === leaving;
            const bodyCells = row.cells.slice(0, -1);
            const rhs = row.cells[row.cells.length - 1];
            // Textbook convention: a double rule under the z row.
            const zBorder = isZ
              ? "border-b-[3px] border-double border-rule-strong/70"
              : "border-b border-rule/60";
            const stickyBg = isLeaving ? "bg-rule-wash" : "bg-paper";
            return (
              <tr key={i}>
                <th
                  scope="row"
                  className={`sticky left-0 z-10 border-l-2 border-r ${zBorder} ${stickyBg} px-3 py-1.5 text-left font-sans text-xs ${
                    isZ ? "font-bold text-ink" : "font-medium text-ink"
                  }`}
                >
                  <span className="inline-flex items-center gap-1.5">
                    {row.basic}
                    {tiedRows.has(row.basic) && (
                      <span className="rounded-sm bg-warn-wash px-1 py-px font-sans text-[10px] font-medium text-warn">
                        empate
                      </span>
                    )}
                  </span>
                </th>
                {bodyCells.map((cell, j) => {
                  const isPivot = isLeaving && j === enteringIdx;
                  const wash = isPivot
                    ? "bg-pen-wash"
                    : isLeaving || j === enteringIdx
                      ? "bg-rule-wash"
                      : "";
                  return (
                    <td
                      key={j}
                      className={`whitespace-nowrap border-r ${zBorder} ${wash} px-3 py-1.5 text-center ${
                        isZ ? "font-semibold" : ""
                      }`}
                    >
                      {isPivot ? (
                        <span className="relative inline-flex items-center justify-center px-1">
                          {cell}
                          {/* El esfero rojo del docente sobre el pivote. */}
                          <span
                            aria-hidden
                            className="pointer-events-none absolute -inset-x-2 -inset-y-1 rounded-[50%] border-2 border-pen"
                          />
                        </span>
                      ) : (
                        cell
                      )}
                    </td>
                  );
                })}
                {showRatios && (
                  <td
                    className={`border-r ${zBorder} ${isLeaving ? "bg-rule-wash" : ""} px-3 py-1.5 text-center ${
                      isLeaving ? "font-semibold text-pen" : isZ ? "text-ink-soft" : ""
                    }`}
                  >
                    {isZ ? "—" : (ratios?.[i - 1] ?? "—")}
                  </td>
                )}
                <td
                  className={`sticky right-0 z-10 border-l-2 border-r-2 ${zBorder} ${stickyBg} px-3 py-1.5 text-center ${
                    isZ ? "font-bold" : "font-semibold"
                  }`}
                >
                  {rhs}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
