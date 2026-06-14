"""
General Medical Knowledge Reference Corpus.

A curated set of ~55 general-knowledge medical text entries
representing "things an AI model already knows from training data."

Used by the TF-IDF scorer to compare node content against this corpus.
High similarity = the content is general knowledge = more derivable.
"""

REFERENCE_CORPUS: list[str] = [
    # --- Medical Definitions ---
    "Total knee replacement (TKR) is a surgical procedure where damaged knee joint surfaces are replaced with artificial prosthetic components. Also called total knee arthroplasty (TKA). It is the most common joint replacement surgery performed worldwide.",
    "Deep vein thrombosis (DVT) is the formation of a blood clot (thrombus) in a deep vein, most commonly in the legs. Risk factors include surgery, prolonged immobility, cancer, pregnancy, and obesity.",
    "Sepsis is a life-threatening condition caused by the body's dysregulated immune response to an infection. It can lead to organ dysfunction, septic shock, and death if not treated promptly.",
    "Type 2 diabetes mellitus is a chronic metabolic disorder characterized by insulin resistance and relative insulin deficiency. It is the most common form of diabetes, associated with obesity and sedentary lifestyle.",
    "Osteoarthritis is a degenerative joint disease characterized by the breakdown of cartilage, the tissue that covers the ends of bones in a joint. It is the most common type of arthritis.",
    "Hypertension, also known as high blood pressure, is a chronic medical condition in which the blood pressure in the arteries is persistently elevated. Normal blood pressure is below 120/80 mmHg.",
    "A myocardial infarction, commonly known as a heart attack, occurs when blood flow to a part of the heart muscle is blocked, usually by a blood clot. This can damage or destroy part of the heart muscle.",
    "Pneumonia is an infection that inflames the air sacs in one or both lungs. The air sacs may fill with fluid or pus, causing cough with phlegm, fever, chills, and difficulty breathing.",
    "Chronic obstructive pulmonary disease (COPD) is a group of lung diseases that block airflow and make breathing difficult. Emphysema and chronic bronchitis are the two most common conditions.",
    "Stroke occurs when the blood supply to part of the brain is interrupted or reduced, preventing brain tissue from getting oxygen and nutrients. Brain cells begin to die within minutes.",

    # --- Pharmacology ---
    "Paracetamol (acetaminophen) is an analgesic and antipyretic drug used to treat pain and fever. It works by inhibiting prostaglandin synthesis in the central nervous system. Standard adult dose is 500-1000mg every 4-6 hours.",
    "Warfarin is an oral anticoagulant medication that prevents blood clots by inhibiting vitamin K-dependent clotting factors. It is monitored using the International Normalized Ratio (INR), with a typical target of 2.0-3.0.",
    "Tramadol is a centrally acting synthetic opioid analgesic used for moderate to severe pain. It works by binding to mu-opioid receptors and inhibiting serotonin and norepinephrine reuptake.",
    "Metformin is the first-line oral medication for the treatment of type 2 diabetes mellitus. It works by decreasing hepatic glucose production and increasing insulin sensitivity in peripheral tissues.",
    "Insulin is a hormone produced by the pancreas that regulates blood glucose levels. In diabetes management, insulin therapy replaces or supplements the body's natural insulin production.",
    "Enoxaparin is a low molecular weight heparin used for the prevention and treatment of deep vein thrombosis. It is administered subcutaneously and has more predictable pharmacokinetics than unfractionated heparin.",
    "Omeprazole is a proton pump inhibitor (PPI) used to reduce stomach acid production. It is used to treat gastroesophageal reflux disease (GERD), peptic ulcers, and Zollinger-Ellison syndrome.",
    "Amoxicillin is a broad-spectrum penicillin antibiotic used to treat a variety of bacterial infections. It works by inhibiting bacterial cell wall synthesis.",
    "Ibuprofen is a nonsteroidal anti-inflammatory drug (NSAID) used to treat pain, inflammation, and fever. It works by inhibiting cyclooxygenase (COX) enzymes, reducing prostaglandin synthesis.",
    "Morphine is a potent opioid analgesic used for severe pain management. It acts on mu-opioid receptors in the central nervous system to produce analgesia, sedation, and euphoria.",

    # --- Vital Signs & Clinical Parameters ---
    "Normal adult vital signs include: heart rate 60-100 beats per minute, blood pressure 120/80 mmHg, respiratory rate 12-20 breaths per minute, oxygen saturation (SpO2) greater than 95%, and body temperature 36.1-37.2 degrees Celsius.",
    "The Glasgow Coma Scale (GCS) is a neurological scale used to assess the level of consciousness. It measures eye opening (1-4), verbal response (1-5), and motor response (1-6), with a total score range of 3-15.",
    "Body Mass Index (BMI) is calculated as weight in kilograms divided by height in meters squared. Categories: underweight (<18.5), normal (18.5-24.9), overweight (25-29.9), obese (>30).",
    "The Visual Analog Scale (VAS) is a pain measurement tool where patients rate their pain on a scale of 0 to 10, with 0 being no pain and 10 being the worst pain imaginable.",

    # --- Clinical Assessment Tools ---
    "The Morse Fall Scale is a rapid and simple method of assessing a patient's likelihood of falling. It consists of six items: history of falling, secondary diagnosis, ambulatory aid, IV/heparin lock, gait, and mental status.",
    "SBAR is a structured communication tool used in healthcare: Situation (what is happening now), Background (clinical context), Assessment (what the clinician thinks), Recommendation (what should be done).",
    "The Braden Scale is used to assess pressure ulcer risk. It evaluates six factors: sensory perception, moisture, activity, mobility, nutrition, and friction/shear. Lower scores indicate higher risk.",
    "The SOFA (Sequential Organ Failure Assessment) score is used to track a patient's status during their stay in an intensive care unit. It scores six organ systems from 0 to 4.",
    "The Waterlow Score is a pressure sore risk assessment tool that considers factors such as build, skin type, sex/age, continence, mobility, appetite, and special risks.",

    # --- Standard Protocols & Guidelines ---
    "DVT prophylaxis is a standard of care for surgical patients. Methods include early mobilization, mechanical compression devices, and pharmacological prophylaxis with anticoagulants such as enoxaparin or heparin.",
    "The WHO five moments of hand hygiene are: before touching a patient, before clean/aseptic procedures, after body fluid exposure risk, after touching a patient, and after touching patient surroundings.",
    "Blood transfusion safety requires verification of patient identity, blood type compatibility, and unit identification. Two healthcare workers must independently verify the information before administration.",
    "Antibiotic stewardship involves systematic efforts to optimize antibiotic use, including empiric therapy review at 48-72 hours, de-escalation based on culture results, and monitoring of antibiotic resistance patterns.",
    "Pain management typically follows a stepwise approach: Step 1 non-opioid analgesics (paracetamol, NSAIDs), Step 2 weak opioids (tramadol, codeine), Step 3 strong opioids (morphine, fentanyl).",
    "Fall prevention in hospitals includes patient assessment using validated tools, bed alarms for high-risk patients, non-slip footwear, adequate lighting, and removal of environmental hazards.",
    "Surgical site infection prevention includes preoperative skin preparation, prophylactic antibiotics, maintaining normothermia, and proper wound care postoperatively.",
    "Contrast media allergy premedication typically involves corticosteroids and antihistamines administered before the procedure to reduce the risk of allergic reactions.",
    "Insulin sliding scale is a reactive approach to glycemic management that adjusts insulin doses based on blood glucose readings. It should be used as a supplement to basal insulin, not as sole therapy.",
    "Verbal orders in healthcare should be limited to emergency situations and require read-back verification and timely written documentation to prevent medication errors.",

    # --- Emergency & Safety ---
    "Hospital emergency codes are standardized alerts used to communicate specific emergencies. Common codes include Code Blue for cardiac arrest, Code Red for fire, and Code Pink for infant abduction.",
    "Basic Life Support (BLS) involves checking responsiveness, calling for help, opening the airway, providing rescue breathing, and performing chest compressions at a rate of 100-120 per minute.",
    "Advanced Cardiac Life Support (ACLS) builds on BLS with advanced interventions including cardiac monitoring, defibrillation, medication administration, and advanced airway management.",
    "Anaphylaxis is a severe, potentially life-threatening allergic reaction. Treatment includes intramuscular epinephrine, supplemental oxygen, IV fluids, and monitoring for biphasic reactions.",

    # --- Clinical Concepts ---
    "Informed consent is the process by which a patient is informed about the risks, benefits, and alternatives of a proposed treatment or procedure before agreeing to proceed.",
    "Patient discharge planning begins at admission and involves assessing patient needs, coordinating post-discharge care, providing patient education, and arranging follow-up appointments.",
    "Medication reconciliation is the process of comparing a patient's medication orders to all of the medications the patient has been taking to avoid errors such as omissions and duplications.",
    "Clinical pathways are structured multidisciplinary care plans that detail essential steps in the care of patients with specific clinical problems. They reduce variation and improve outcomes.",
    "Evidence-based medicine integrates clinical expertise, patient values, and the best available research evidence into the decision-making process for patient care.",

    # --- Medical Terminology ---
    "Pharmacokinetics describes the movement of drugs through the body: absorption, distribution, metabolism, and excretion (ADME). Half-life is the time for drug concentration to decrease by 50%.",
    "Pharmacodynamics describes how drugs affect the body, including mechanism of action, therapeutic effects, and side effects. Drug receptors, agonists, and antagonists are key concepts.",
    "Hemostasis is the process of blood clot formation at the site of vessel injury. It involves vascular spasm, platelet plug formation, and the coagulation cascade leading to fibrin clot formation.",
    "Electrolyte balance is crucial for normal body functions. Key electrolytes include sodium, potassium, calcium, magnesium, chloride, phosphate, and bicarbonate.",
    "Acid-base balance is maintained through buffer systems, respiratory compensation (CO2), and renal compensation (bicarbonate). Normal arterial blood pH is 7.35-7.45.",
    "Wound healing occurs in four overlapping phases: hemostasis, inflammation, proliferation, and remodeling. Factors affecting healing include nutrition, infection, blood supply, and diabetes.",
]
