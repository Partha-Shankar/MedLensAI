/**
 * RxGuard Patient Mapping Utility
 * 
 * Maps MedLens prescription data and frontend patient profile to RxGuard schema.
 * 
 * RxGuard Schema (from chatbot/app/models.py):
 * - ChatRequest: { query: string, patient: PatientProfile, language: string, history: ChatMessage[] }
 * - PatientProfile: {
 *     name: string,
 *     age: int,
 *     gender: string,
 *     weight_kg: float,
 *     conditions: string[],
 *     allergies: string[],
 *     medications: Medication[],
 *     renal_impairment: boolean,
 *     pregnant: boolean,
 *     notes: string
 *   }
 * - Medication: { name: string, dose: string, frequency: string, indication: string }
 * - ChatMessage: { role: string, content: string }
 */

export function mapPrescriptionToRxGuard(prescription: any, patientProfile: any): any {
  const name = patientProfile?.name || prescription?.PatientName || "Patient";
  const age = parseInt(patientProfile?.age || prescription?.Age || "0", 10);
  const gender = patientProfile?.sex === "M" ? "Male" : patientProfile?.sex === "F" ? "Female" : "Other";
  const weight_kg = 70.0; // Default
  const conditions = patientProfile?.conditions || [];
  const allergies = typeof patientProfile?.allergies === "string"
    ? patientProfile.allergies.split(",").map((s: string) => s.trim()).filter(Boolean)
    : patientProfile?.allergies || [];

  const medications = prescription?.Medications?.map((med: any) => ({
    name: med.DrugName || "",
    dose: `${med.DoseValue || ""}${med.DoseUnit || ""}`.trim(),
    frequency: med.Frequency || "",
    indication: med.AdminInstructions || ""
  })) || [];

  const renal_impairment = patientProfile?.conditions?.includes("Kidney Disease") || false;
  const pregnant = patientProfile?.conditions?.includes("Pregnancy") || false;

  const date = prescription?.prescription_date || prescription?.Date || "recently";
  const notes = prescription?.id ? `from history, date:${date}` : "";

  console.log(`[RXGUARD_MAPPER] Mapped ${medications.length} medications, ${conditions.length} conditions`);

  return {
    name,
    age,
    gender,
    weight_kg,
    conditions,
    allergies,
    medications,
    renal_impairment,
    pregnant,
    notes
  };
}
