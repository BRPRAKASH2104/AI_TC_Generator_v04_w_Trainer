# 🚀 Quick Start Guide - v03 Compatible v04

**Version**: v1.7.0 | **Status**: ✅ v03-Compatible

---

## ⚡ 30-Second Verification

```bash
# Verify all fixes work
python utilities/verify_v03_compatibility.py input/your_file.reqifz

# Expected: ✅ ALL CHECKS PASSED
```

---

## 🎯 Quick Usage

```bash
# Standard mode (v03-compatible)
python main.py input/your_file.reqifz --verbose

# High-performance mode (3-5x faster)
python main.py input/your_file.reqifz --hp --max-concurrent 4 --verbose
```

---

## ✅ What's Fixed

| Issue | Status |
|-------|--------|
| Processes ALL requirements (not just those with tables) | ✅ |
| Lenient classification (fewer requirements dropped) | ✅ |
| Supports v03 AI response field names | ✅ |
| 16 columns match v03 exactly | ✅ |
| Column names: Feature Group, LinkTest | ✅ |
| Default values: RoboFit, Infotainment, SYS_DI_VALIDATION_TEST | ✅ |
| Summary format: [feature_name] | ✅ |

---

## 📊 Output Structure (Identical to v03)

```
16 Columns:
1. Issue ID               2. Summary [feature_name]
3. Test Type (RoboFit)    4. Issue Type (Test)
5. Project Key (TCTOIC)   6. Assignee (ENGG)
7. Description (empty)    8. Action (preconditions)
9. Data (test steps)      10. Expected Result
11. Planned Execution     12. Test Case Type
13. Feature Group         14. Components (Infotainment)
15. Labels (SYS_DI_VALIDATION_TEST)
16. LinkTest (requirement_id)
```

---

## 🔍 Verification Commands

```bash
# 1. Core logic check
python utilities/verify_v03_compatibility.py input/file.reqifz

# 2. Output format check (if you have v03 output)
python utilities/compare_v03_v04_output.py v03.csv v04.xlsx

# 3. Quick column check
python -c "import pandas as pd; df = pd.read_excel('output.xlsx', sheet_name='Test Cases'); print('Columns:', len(df.columns)); print(df.columns.tolist())"
```

---

## ⚠️ One Difference: CSV → XLSX

v03 outputs `.csv`, v04 outputs `.xlsx` (Excel)

**Need CSV?**
```python
import pandas as pd
df = pd.read_excel('output.xlsx', sheet_name='Test Cases')
df.to_csv('output.csv', index=False, encoding='utf-8-sig')
```

---

## 📚 Full Documentation

- `V03_COMPATIBILITY_FIXES.md` - Complete fix details
- `OUTPUT_FORMAT_COMPATIBILITY.md` - Output format guide
- `INIT_V03_COMPATIBILITY_SUMMARY.md` - Initialization summary

---

## 🎉 You're Ready!

v04 now processes requirements exactly like v03, with the same output structure, plus v04's advanced features (context-aware processing, HP mode, better formatting).

**Best of both worlds!**
