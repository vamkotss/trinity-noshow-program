# Data Handling Note — PHI and De-identification

**Scope:** This note documents how patient health information (PHI) is handled in
the Trinity No-Show analysis. The data is synthetic, but it is treated as if it
were real, because that is the habit worth demonstrating.

## What was present

The raw operational export contained direct identifiers typical of a real
scheduling system: patient names, dates of birth, and phone numbers, keyed by
medical record number (MRN).

## What we did, and why

We apply the **HIPAA Safe Harbor** approach: remove the 18 categories of direct
identifier so the working dataset cannot reasonably be tied to an individual.

| Field | Action | Reason |
|---|---|---|
| First / last name | **Dropped** | Direct identifier; no analytical value |
| Phone | **Dropped** | Direct identifier |
| Date of birth | **Generalised to age band** | A birth date is identifying; an age band preserves the analytical signal (age relates to no-show behaviour) without the exposure. Ages 90+ are bucketed together, as Safe Harbor requires |
| MRN | **Hashed to a stable pseudonym** | We need a consistent patient key to link appointments to patients. The MRN is hashed with a secret salt: the same patient always maps to the same key, and the original MRN is not recoverable without the salt |
| Appointment / visit dates | **Kept** | These are operational event dates, not identity-linked dates like a DOB. The entire analysis is about appointment timing |

## An honest limitation

Hashing the MRN is **pseudonymisation, not anonymisation.** Our MRNs are
sequential and therefore enumerable; anyone holding the salt could reverse the
mapping by brute force. In production the salt lives in a secrets manager, the
MRN-to-key mapping is never exported, and access is logged. We state this plainly
because overstating a privacy guarantee is its own kind of harm.

## What never leaves the secure boundary

- The salt.
- The MRN-to-key mapping.
- The original name, DOB, and phone columns.

The de-identified dataset — patient key, age band, home clinic — is what every
downstream step operates on.
