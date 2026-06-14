-- ============================================================
-- SAMPLE DATASET (SQL) — Cardiology & Pulmonology
-- 15 dummy knowledge nodes for testing the upload feature.
-- Upload via the dashboard "Upload Nodes" box, or run in Supabase
-- SQL Editor, then click "Rescore All".
--
-- NOTE: The /api/upload-nodes parser reads these VALUES — it does
-- NOT execute the SQL. Duplicate ids are auto-renamed on upload.
-- ============================================================

INSERT INTO knowledge_nodes (id, org_id, type, title, content, importance, expected_derivability, expected_score_range, department, tokens_full, tokens_delta) VALUES

-- ============================================================
-- CLEARLY DERIVABLE (5 nodes) — general textbook knowledge
-- Expected score: 0.70-0.99
-- ============================================================

('CP-D-01', 'supra', 'FACT', 'What is Atrial Fibrillation',
 'Atrial fibrillation is a common cardiac arrhythmia characterized by rapid and irregular beating of the atrial chambers. It increases the risk of stroke and heart failure.',
 0.35, 'DERIVABLE', '0.88-0.96', 'cardiology', 48, 0),

('CP-D-02', 'supra', 'FACT', 'Beta-Blocker Mechanism of Action',
 'Beta-blockers reduce heart rate and blood pressure by blocking the effects of adrenaline on beta-adrenergic receptors. Commonly used for hypertension, angina, and arrhythmias.',
 0.35, 'DERIVABLE', '0.88-0.95', 'cardiology', 50, 0),

('CP-D-03', 'supra', 'FACT', 'Normal Spirometry Values',
 'Normal spirometry shows an FEV1/FVC ratio above 0.70. FEV1 and FVC are compared to predicted values based on age, sex, and height. A reduced ratio indicates obstructive lung disease.',
 0.30, 'DERIVABLE', '0.85-0.94', 'pulmonology', 52, 0),

('CP-D-04', 'supra', 'FACT', 'What is Asthma',
 'Asthma is a chronic inflammatory airway disease causing reversible airflow obstruction, wheezing, and shortness of breath. It is commonly triggered by allergens, exercise, and respiratory infections.',
 0.35, 'DERIVABLE', '0.87-0.95', 'pulmonology', 50, 0),

('CP-D-05', 'supra', 'FACT', 'Troponin in Myocardial Infarction',
 'Troponin is a cardiac biomarker released when heart muscle is damaged. Elevated troponin levels are a standard diagnostic indicator of myocardial infarction.',
 0.35, 'DERIVABLE', '0.86-0.94', 'cardiology', 45, 0),

-- ============================================================
-- CLEARLY NON-DERIVABLE (5 nodes) — Supra-specific
-- Expected score: 0.01-0.30
-- ============================================================

('CP-N-01', 'supra', 'DECISION', 'Supra Cardiology Statin Protocol',
 'Supra Cardiology uses Atorvastatin 40mg as first-line statin for post-MI patients. Escalate to Rosuvastatin if the LDL target is not met. Decision by Dr. Suresh Nair, February 2025.',
 0.88, 'NON_DERIVABLE', '0.02-0.10', 'cardiology', 70, NULL),

('CP-N-02', 'supra', 'CONSTRAINT', 'Patient Meena Beta-Blocker Ban',
 'ABSOLUTE CONTRAINDICATION: No beta-blockers for patient Meena due to severe asthma and prior bronchospasm. Use calcium channel blockers instead. 3 documented adverse reactions.',
 0.97, 'NON_DERIVABLE', '0.01-0.05', 'cardiology', 62, NULL),

('CP-N-03', 'supra', 'DECISION', 'Philips ECG Machine Standard',
 'Supra Cardiology standardized on Philips ECG machines across all 4 cath labs. Decision based on integration with the hospital EMR, reviewed in 2024 by Dr. Suresh Nair.',
 0.70, 'NON_DERIVABLE', '0.02-0.08', 'cardiology', 60, NULL),

('CP-N-04', 'supra', 'FACT', 'Cath Lab Capacity',
 'Supra Cath Lab: 4 labs with a 30 procedures/day capacity. Current utilization 82%. Peak demand on Monday mornings. Overflow cases scheduled to the partner facility.',
 0.55, 'NON_DERIVABLE', '0.05-0.15', 'cardiology', 55, NULL),

('CP-N-05', 'supra', 'DECISION', 'Pulmonology Budget 2026',
 'FY 2026 Pulmonology budget: Rs 2.8 Cr. Ventilators 35%, Staffing 30%, Diagnostics 20%, Training 15%. New bronchoscopy suite approved in Q2.',
 0.68, 'NON_DERIVABLE', '0.01-0.05', 'pulmonology', 52, NULL),

-- ============================================================
-- AMBIGUOUS EDGE CASES (5 nodes) — general protocol + Supra specifics
-- Expected: PARTIALLY_DERIVABLE
-- ============================================================

('CP-E-01', 'supra', 'CONSTRAINT', 'Anticoagulation in Atrial Fibrillation',
 'All AFib patients are assessed with the CHA2DS2-VASc score. A score of 2 or more warrants anticoagulation. Supra protocol: Apixaban preferred, warfarin only under cost constraint. Document bleeding risk using HAS-BLED.',
 0.90, 'PARTIALLY_DERIVABLE', '0.40-0.58', 'cardiology', 78, 22),

('CP-E-02', 'supra', 'DECISION', 'COPD Inhaler Step-Up',
 'COPD management follows the GOLD guidelines: SABA, then LAMA/LABA, then triple therapy. Supra steps up to triple therapy after 2 exacerbations per year, and pulmonary rehab referral is mandatory.',
 0.82, 'PARTIALLY_DERIVABLE', '0.40-0.55', 'pulmonology', 70, 20),

('CP-E-03', 'supra', 'CONSTRAINT', 'Sepsis Bundle for Cardiac Patients',
 'The Surviving Sepsis bundle requires blood cultures before antibiotics and lactate measurement early. Supra tightened the lactate window to within 1 hour and auto-alerts the cardiology consultant for cardiac patients.',
 0.92, 'PARTIALLY_DERIVABLE', '0.38-0.55', 'cardiology', 72, 22),

('CP-E-04', 'supra', 'ANTI_PATTERN', 'Abrupt Beta-Blocker Withdrawal',
 'Do NOT stop beta-blockers abruptly because of the risk of rebound tachycardia and ischemia. Supra incident 2023: a patient developed unstable angina after self-discontinuation. Taper over 1 to 2 weeks.',
 0.88, 'PARTIALLY_DERIVABLE', '0.35-0.50', 'cardiology', 68, 18),

('CP-E-05', 'supra', 'CONSTRAINT', 'Oxygen Therapy Targets',
 'Target SpO2 is 94-98% for most patients and 88-92% for COPD patients with CO2 retention. Supra uses colour-coded oxygen alert cards at every bed, and exceeding the target is a reportable event.',
 0.86, 'PARTIALLY_DERIVABLE', '0.45-0.60', 'pulmonology', 66, 18)

ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- Org-specific delta for the PARTIAL (edge) nodes
-- ============================================================

UPDATE knowledge_nodes SET non_derivable_portion = 'Supra protocol: Apixaban preferred, warfarin only under cost constraint.' WHERE id = 'CP-E-01';
UPDATE knowledge_nodes SET non_derivable_portion = 'Supra steps up to triple therapy after 2 exacerbations/year; pulmonary rehab referral mandatory.' WHERE id = 'CP-E-02';
UPDATE knowledge_nodes SET non_derivable_portion = 'Supra: lactate within 1 hour; auto-alert cardiology consultant for cardiac patients.' WHERE id = 'CP-E-03';
UPDATE knowledge_nodes SET non_derivable_portion = 'Supra incident 2023: unstable angina after self-discontinuation.' WHERE id = 'CP-E-04';
UPDATE knowledge_nodes SET non_derivable_portion = 'Supra: colour-coded oxygen alert cards at every bed; exceeding target is reportable.' WHERE id = 'CP-E-05';
