# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas"]
# ///
"""data/*.csv -> docs/data.js（window.BI_DATA，給 docs/index.html 用 <script> 直接載入）"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
read = lambda n: pd.read_csv(ROOT / "data" / n, encoding="utf-8-sig", keep_default_na=False)

enr, leave, mapping = read("enrollment.csv"), read("leave.csv"), read("dept_mapping.csv")

# 先加總：去掉 dept_raw、program_raw、identity 等網頁用不到的欄位
enr = enr.groupby(["semester", "college", "dept", "degree", "gender"], as_index=False)["count"].sum()
leave = leave.groupby(["semester", "college", "dept", "degree", "gender", "reason"], as_index=False)[
    ["new_leave", "on_leave_end"]].sum()

def rows(df):
    return df.astype(object).values.tolist()

data = {
    "semesters": sorted(set(enr.semester)),
    "enrollment": {"cols": list(enr.columns), "rows": rows(enr)},   # count = 在學人數
    "leave": {"cols": list(leave.columns), "rows": rows(leave)},    # new_leave = 學期間休學；on_leave_end = 學期底休學狀態
    "depts": [{"dept": r.dept, "college": r.college,
               "aliases": [a for a in r.aliases.split(";") if a]} for r in mapping.itertuples()],
}
out = ROOT / "docs" / "data.js"
out.write_text("window.BI_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")

e114 = int(enr[enr.semester == "114-1"]["count"].sum())
print(f"enrollment {len(enr)} 列, leave {len(leave)} 列, depts {len(data['depts'])} 個")
print(f"114-1 在學人數合計 {e114} {'OK' if e114 == 10035 else 'MISMATCH'}")
print(f"{out} {out.stat().st_size / 1024:.0f} KB")
