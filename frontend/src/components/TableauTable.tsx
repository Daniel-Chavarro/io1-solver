import type { ReactNode } from "react";
import type { TableauData } from "../types";

// Classic hand-drawn C_j - Z_j tableau: a C_j row over the variable columns,
// header V_B | C_B | variables | b_j, one row per constraint, and Z_j /
// C_j - Z_j footer rows labelled in the C_B column. During a step the
// entering column and leaving row are tinted, the pivot cell is circled in
// red pen, and a "razón mín" column follows b_j. Cells are canonical strings
// ("3/4", "-M-30") shown as-is. Dimension-agnostic: V_B and C_B are pinned
// left; the right-most column (razón mín, or b_j without ratios) is pinned
// right.
interface Props {
  tableau: TableauData;
  entering?: string | null;
  leaving?: string | null;
  ratios?: string[] | null;
  ties?: string[] | null;
}

// "s1" -> s<sub>1</sub>; free-form names ("pandesal") stay untouched.
function Name({ text }: { text: string }) {
  const m = /^([A-Za-z]+)(\d+)$/.exec(text);
  if (!m) return <>{text}</>;
  return (
    <>
      {m[1]}
      <sub>{m[2]}</sub>
    </>
  );
}

const box = (top: boolean, left: boolean) =>
  `border-b border-r border-ink${top ? " border-t" : ""}${left ? " border-l" : ""}`;

export function TableauTable({ tableau, entering, leaving, ratios, ties }: Props) {
  const varCols = tableau.columns.slice(0, -1); // the last column is b_j
  const n = varCols.length;
  const enteringIdx = entering ? varCols.indexOf(entering) : -1;
  const showRatios = !!ratios && ratios.length > 0;
  const tiedRows = new Set(ties ?? []);

  const stickyBg = (tint: boolean) => (tint ? "bg-rule-wash" : "bg-paper");
  const tintBg = (tint: boolean) => (tint ? "bg-rule-wash" : "");
  const pinB = showRatios ? "" : "sticky right-0 z-10 ";
  const pinR = showRatios ? "sticky right-0 z-10 " : "";

  const vbPin = "sticky left-0 z-10 w-14 min-w-14 ";
  const cbPin = "sticky left-14 z-10 ";
  const label = "whitespace-nowrap px-3 py-1.5 text-center italic";

  const blankVB = <td className={`${vbPin}bg-paper`} />;
  const blankB = <td className={`${pinB}${showRatios ? "" : "bg-paper"}`} />;
  const blankR = showRatios ? <td className={`${pinR}bg-paper`} /> : null;

  return (
    <div className="overflow-x-auto rounded-md border border-rule/70 bg-paper p-2">
      <table className="tnum border-separate border-spacing-0 font-display text-sm text-ink">
        <thead>
          <tr>
            {blankVB}
            <td className={`${cbPin}bg-paper ${label}`}>
              C<sub>j</sub>
            </td>
            {varCols.map((col, j) => (
              <td
                key={col}
                className={`${box(true, j === 0)} ${tintBg(j === enteringIdx)} whitespace-nowrap px-3 py-1.5 text-center`}
              >
                {tableau.cj[j] ?? ""}
              </td>
            ))}
            {blankB}
            {blankR}
          </tr>
          <tr>
            <th
              scope="col"
              className={`${vbPin}${box(true, true)} bg-paper ${label} font-normal`}
            >
              V<sub>B</sub>
            </th>
            <th
              scope="col"
              className={`${cbPin}${box(true, false)} bg-paper ${label} font-normal`}
            >
              C<sub>B</sub>
            </th>
            {varCols.map((col, j) => (
              <th
                key={col}
                scope="col"
                className={`${box(false, false)} ${tintBg(j === enteringIdx)} whitespace-nowrap px-3 py-1.5 text-center font-normal italic`}
              >
                <Name text={col} />
              </th>
            ))}
            <th
              scope="col"
              className={`${pinB}${box(true, false)} bg-paper ${label} font-normal`}
            >
              b<sub>j</sub>
            </th>
            {showRatios && (
              <th
                scope="col"
                className={`${pinR}${box(true, false)} bg-paper whitespace-nowrap px-3 py-1.5 text-center font-sans text-xs font-medium not-italic text-ink-soft`}
              >
                razón mín
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {tableau.rows.map((row, i) => {
            const isLeaving = row.basic === leaving;
            const bodyCells = row.cells.slice(0, -1);
            const bj = row.cells[row.cells.length - 1];
            return (
              <tr key={i}>
                <th
                  scope="row"
                  className={`${vbPin}${box(false, true)} ${stickyBg(isLeaving)} px-3 py-1.5 text-center font-medium`}
                >
                  <span className="inline-flex items-center gap-1.5 italic">
                    <span>
                      <Name text={row.basic} />
                    </span>
                    {tiedRows.has(row.basic) && (
                      <span className="rounded-sm bg-warn-wash px-1 py-px font-sans text-[10px] font-medium not-italic text-warn">
                        empate
                      </span>
                    )}
                  </span>
                </th>
                <td
                  className={`${cbPin}${box(false, false)} ${stickyBg(isLeaving)} whitespace-nowrap px-3 py-1.5 text-center`}
                >
                  {row.cb}
                </td>
                {bodyCells.map((cell, j) => {
                  const isPivot = isLeaving && j === enteringIdx;
                  const wash = isPivot
                    ? "bg-pen-wash"
                    : tintBg(isLeaving || j === enteringIdx);
                  let content: ReactNode = cell;
                  if (isPivot) {
                    content = (
                      <span className="relative inline-flex items-center justify-center px-1">
                        {cell}
                        {/* El esfero rojo del docente sobre el pivote. */}
                        <span
                          aria-hidden
                          className="pointer-events-none absolute -inset-x-2 -inset-y-1 rounded-[50%] border-2 border-pen"
                        />
                      </span>
                    );
                  }
                  return (
                    <td
                      key={j}
                      className={`${box(false, false)} ${wash} whitespace-nowrap px-3 py-1.5 text-center`}
                    >
                      {content}
                    </td>
                  );
                })}
                <td
                  className={`${pinB}${box(false, false)} ${stickyBg(isLeaving)} whitespace-nowrap px-3 py-1.5 text-center font-semibold`}
                >
                  {bj}
                </td>
                {showRatios && (
                  <td
                    className={`${pinR}${box(false, false)} ${stickyBg(isLeaving)} whitespace-nowrap px-3 py-1.5 text-center ${
                      isLeaving ? "font-semibold text-pen" : ""
                    }`}
                  >
                    {ratios?.[i] ?? ""}
                  </td>
                )}
              </tr>
            );
          })}
          <tr>
            {blankVB}
            <td
              className={`${cbPin}${box(false, true)} bg-paper ${label}`}
            >
              Z<sub>j</sub>
            </td>
            {varCols.map((col, j) => (
              <td
                key={col}
                className={`${box(false, false)} ${tintBg(j === enteringIdx)} whitespace-nowrap px-3 py-1.5 text-center`}
              >
                {tableau.zj[j] ?? ""}
              </td>
            ))}
            <td
              className={`${pinB}${box(false, false)} bg-paper whitespace-nowrap px-3 py-1.5 text-center font-semibold`}
            >
              {tableau.zj[n] ?? ""}
            </td>
            {blankR}
          </tr>
          <tr>
            {blankVB}
            <td
              className={`${cbPin}${box(false, true)} bg-paper ${label}`}
            >
              C<sub>j</sub> − Z<sub>j</sub>
            </td>
            {varCols.map((col, j) => (
              <td
                key={col}
                className={`${box(false, false)} ${tintBg(j === enteringIdx)} whitespace-nowrap px-3 py-1.5 text-center ${
                  j === enteringIdx ? "font-bold" : ""
                }`}
              >
                {tableau.cj_zj[j] ?? ""}
              </td>
            ))}
            {blankB}
            {blankR}
          </tr>
        </tbody>
      </table>
    </div>
  );
}
