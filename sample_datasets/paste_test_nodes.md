# Paste Test Nodes — for the "Paste Nodes (CSV or SQL text)" box

These are **dummy nodes for testing the Paste Nodes feature** on the dashboard.
Both blocks below contain the **same 6 nodes** (ids `PT-01` … `PT-06`), so you can test either format.

The 6 nodes deliberately cover every class so the whole dashboard lights up:

| ids | Expected class | Why |
|-----|----------------|-----|
| `PT-01`, `PT-02` | 🔴 DERIVABLE | General textbook facts the AI already knows |
| `PT-03`, `PT-04` | 🟢 NON_DERIVABLE | Org-specific (Supra, a doctor, a date, an incident, a policy) |
| `PT-05`, `PT-06` | 🟡 PARTIALLY_DERIVABLE | General knowledge + a small org-specific detail |

### How to use

1. **Copy one block below** (just the lines inside the code box — CSV *or* SQL).
2. On the dashboard, paste it into the **Paste Nodes** box.
3. Pick the format (**Auto** works too) and click **Save to Database**.
4. Click **Rescore All** to score them.
5. To remove them later: paste the **same block** again and click **Delete by Text**.

> Both blocks use the same content, so **Delete by Text** works with either one — even if you saved using
> the other format. Your original seed nodes are never affected.

---

## 📋 CSV format

Copy everything inside this box (the first line is the header row):

```csv
id,org_id,type,title,content,importance,expected_derivability,expected_score_range,department,tokens_full,tokens_delta
PT-01,supra,FACT,What is Hypertension,"Hypertension, also called high blood pressure, is a chronic condition where the blood pressure in the arteries is persistently elevated. Normal blood pressure is below 120/80 mmHg. Common risk factors include obesity, high salt intake, and physical inactivity.",0.35,DERIVABLE,0.85-0.95,medicine,52,0
PT-02,supra,FACT,What is Pneumonia,"Pneumonia is an infection that inflames the air sacs in one or both lungs, which may fill with fluid. Typical symptoms include cough, fever, chills, and difficulty breathing. It can be caused by bacteria, viruses, or fungi.",0.35,DERIVABLE,0.88-0.96,medicine,48,0
PT-03,supra,DECISION,Cardiac Unit Lead Decision,"Supra Hospital decided in March 2024 that Dr. Mehta will lead the new cardiac care unit, after reviewing the 12 readmission cases recorded in the previous quarter.",0.80,NON_DERIVABLE,0.05-0.20,cardiology,38,38
PT-04,supra,CONSTRAINT,Blood Transfusion Approval Policy,"As per Supra Hospital policy, all blood transfusions above 2 units require written approval from the HOD on duty. This rule was added after a near-miss incident in 2023.",0.90,NON_DERIVABLE,0.05-0.25,medicine,36,36
PT-05,supra,FACT,DVT Prophylaxis Protocol,"DVT prophylaxis for surgical patients includes early mobilization and anticoagulants such as enoxaparin. At Supra Hospital, the standard enoxaparin dose is fixed by the formulary committee and logged in the auto-alert system.",0.60,PARTIALLY_DERIVABLE,0.40-0.60,ortho,50,22
PT-06,supra,FACT,Surgical Safety Checklist,"The WHO surgical safety checklist is a standard pre-operative verification tool used worldwide. Supra Hospital extended it with an extra step requiring Dr. Rao to sign off on all orthopedic implants.",0.55,PARTIALLY_DERIVABLE,0.40-0.60,ortho,44,20
```

---

## 🗄️ SQL format

Copy everything inside this box (it is **parsed, not executed** — totally safe):

```sql
INSERT INTO knowledge_nodes (id, org_id, type, title, content, importance, expected_derivability, expected_score_range, department, tokens_full, tokens_delta) VALUES
('PT-01', 'supra', 'FACT', 'What is Hypertension', 'Hypertension, also called high blood pressure, is a chronic condition where the blood pressure in the arteries is persistently elevated. Normal blood pressure is below 120/80 mmHg. Common risk factors include obesity, high salt intake, and physical inactivity.', 0.35, 'DERIVABLE', '0.85-0.95', 'medicine', 52, 0),
('PT-02', 'supra', 'FACT', 'What is Pneumonia', 'Pneumonia is an infection that inflames the air sacs in one or both lungs, which may fill with fluid. Typical symptoms include cough, fever, chills, and difficulty breathing. It can be caused by bacteria, viruses, or fungi.', 0.35, 'DERIVABLE', '0.88-0.96', 'medicine', 48, 0),
('PT-03', 'supra', 'DECISION', 'Cardiac Unit Lead Decision', 'Supra Hospital decided in March 2024 that Dr. Mehta will lead the new cardiac care unit, after reviewing the 12 readmission cases recorded in the previous quarter.', 0.80, 'NON_DERIVABLE', '0.05-0.20', 'cardiology', 38, 38),
('PT-04', 'supra', 'CONSTRAINT', 'Blood Transfusion Approval Policy', 'As per Supra Hospital policy, all blood transfusions above 2 units require written approval from the HOD on duty. This rule was added after a near-miss incident in 2023.', 0.90, 'NON_DERIVABLE', '0.05-0.25', 'medicine', 36, 36),
('PT-05', 'supra', 'FACT', 'DVT Prophylaxis Protocol', 'DVT prophylaxis for surgical patients includes early mobilization and anticoagulants such as enoxaparin. At Supra Hospital, the standard enoxaparin dose is fixed by the formulary committee and logged in the auto-alert system.', 0.60, 'PARTIALLY_DERIVABLE', '0.40-0.60', 'ortho', 50, 22),
('PT-06', 'supra', 'FACT', 'Surgical Safety Checklist', 'The WHO surgical safety checklist is a standard pre-operative verification tool used worldwide. Supra Hospital extended it with an extra step requiring Dr. Rao to sign off on all orthopedic implants.', 0.55, 'PARTIALLY_DERIVABLE', '0.40-0.60', 'ortho', 44, 20);
```
