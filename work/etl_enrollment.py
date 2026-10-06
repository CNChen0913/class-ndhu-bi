# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "xlrd"]
# ///
"""114-1 在學人數統計表 (.xls) -> work/enrollment_114-1.csv"""
import re
from pathlib import Path

import pandas as pd
import xlrd

ROOT = Path(__file__).resolve().parent.parent
SRC = next((ROOT / "東華大學統計資料" / "在學人數統計表").glob("114-1*.xls"))
OUT = ROOT / "work" / "enrollment_114-1.csv"

# 區段標題的編號 -> 學制
PROGRAM = {"1": "博士班", "2": "碩士班", "3": "碩士在職專班", "4": "學士班"}

# 檔案內碼是 Big5，xlrd 預設解不出中文
sheet = xlrd.open_workbook(SRC, encoding_override="cp950", formatting_info=True).sheet_by_index(0)
# 合併儲存格範圍：(列起, 列迄, 欄起, 欄迄)，迄為不含
merged = {(r, c): (r0, c0) for r0, r1, c0, c1 in sheet.merged_cells
          for r in range(r0, r1) for c in range(c0, c1)}

rows, program, college, dept = [], None, "", ""
for r in range(3, sheet.nrows):
    a, b, c, d = (str(sheet.cell_value(r, i)).strip() for i in range(4))
    if a.startswith("備註"):
        break
    m = re.search(r"合計\s*(\d)", a)
    if m:  # 區段合計列：只用來切換學制
        program = PROGRAM[m.group(1)]
        continue
    if a.startswith("總計") or not d:
        continue
    # 合併儲存格只在第一格有值，往下沿用
    college = b or college
    if c:
        dept = c
    elif (r, 2) not in merged:
        # 沒被任何合併範圍涵蓋的空白系所（例如 R21 應用物理博士班一般組），
        # 報表上實際屬於下面緊接的系所，往下找第一個有名稱的格子
        dept = next(str(sheet.cell_value(k, 2)).strip() for k in range(r, sheet.nrows)
                    if str(sheet.cell_value(k, 2)).strip())
    rows.append({
        "college": re.sub(r"[（(].*?[)）]", "", college).strip(),
        "dept_raw": dept,
        "program_raw": program,
        "female": sheet.cell_value(r, 5),
        "male": sheet.cell_value(r, 6),
    })

df = pd.DataFrame(rows)
df = df.groupby(["college", "dept_raw", "program_raw"], sort=False, as_index=False)[["female", "male"]].sum()
df = df.melt(id_vars=["college", "dept_raw", "program_raw"], value_vars=["female", "male"],
             var_name="gender", value_name="count")
df["gender"] = df["gender"].map({"female": "女", "male": "男"})
df["count"] = df["count"].astype(int)
df = df.sort_values(["college", "dept_raw", "program_raw", "gender"], kind="stable")
OUT.parent.mkdir(exist_ok=True)
df.to_csv(OUT, index=False, encoding="utf-8-sig")
print(f"{len(df)} rows, total {df['count'].sum()} -> {OUT}")
