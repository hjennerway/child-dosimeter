# Child Medication Dosage for Home Assistant

Custom Home Assistant integration and Lovelace card for tracking rolling 24-hour
medication administration for a child.

# DISCLAIMER
This is a home tracker, not medical advice. Confirm dose amounts, intervals, and
medicine suitability with the medicine label, pharmacist, GP, NHS 111, or your
clinician, especially for children under 3 months, unusual weights, other
conditions, or medicines with overlapping ingredients.

## Why
 - Forget when you last gave your child medicine?
 - Not sure if your partner gave some medicine in the night and wondering if you can give more?

## Features
 - Tracking of 24 hour dosage of paracetamol/ibuprofen based on child age and weight
 - Tracking custom doses based on dose size, max doses in 24h and size of each dose
 - Visual gauge of how much they've had
 - Log of doses administered when tapping the bar gauge

## Setup
1. Go to **Settings > Devices & services > Add integration**.
2. Search for **Child Medication Dosage**.
3. Enter the child name, date of birth, and weight in kg.
4. Optionally enable **Configure custom medications**.
5. For each custom medication, fill in the separate fields for medicine name,
   max doses in 24h, max amount in 24h, and dose size. Enable **Add another
   custom medication** to keep adding more.

   Custom medications are stored for that child and get the same sensors,
   dashboard controls, 24-hour totals, history popup, reset, and single-dose
   removal behavior as the built-in medicines.
6. To add another child later, open the integration options and add another
   child.

### Add The Card

The card is bundled inside the integration and served by Home Assistant after
the integration is loaded. Register the dashboard resource:

```yaml
lovelace:
  resources:
    - url: /child_medication_dosage/child-dosage-card.js?v=4
      type: module
```

Do not use a `/hacsfiles/...` URL for this repository. HACS installs this as an
integration, not as a frontend/plugin repository, so the `/hacsfiles` path is
not created. If you previously used `/local/child-dosage-card.js`, remove that
resource and use the integration-served URL above.

Home Assistant and browsers can cache custom card modules. After updating the
card, increment the `v=` value in the resource URL and refresh the dashboard.

Then add the card from the dashboard UI, or add a manual card:

```yaml
type: custom:child-dosage-card
title: Medication
child_name: Child Name
```

## Dosage

When you give the child paracetamol/ibuprofen, tab the green button. If the button turns orange, it's because the last dose was given less than 4 hours ago

The dose rules are based on:

- Paracetamol uses the age bands shown at https://www.nhs.uk/medicines/paracetamol-for-children/ and assumes up to four
  doses in 24 hours.
- Ibuprofen uses the weight table shown at https://www.nhs.uk/medicines/ibuprofen-for-children/ and a maximum of
  `30 mg/kg/day`, split into up to four doses.
- Where a range is given, the integration uses the lower value.


You can also use the stable `child_id` instead of `child_name`. Find the
`child_id` in the attributes of one of the created medication sensors.

### Card Options

All display options are optional and default to `true`.

```yaml
type: custom:child-dosage-card
title: Medication
child_name: Child Name
show_child_name: true
show_child_age_weight: true
show_paracetamol: true
show_ibuprofen: true
show_last_dose_time: true
show_time_since_last_dose: true
show_amount_in_last24h: true
show_dose_button: true
show_reset_button: true
custom_medications:
  - Antibiotic
paracetamol_dose_size: auto
ibuprofen_dose_size: auto
```

| Option | Default | Description |
| --- | --- | --- |
| `title` | `Medication dosage` | Card title. |
| `child_name` | required if `child_id` is not set | Child name to match against the medication sensor attributes. |
| `child_id` | required if `child_name` is not set | Stable child ID to match against the medication sensor attributes. |
| `show_child_name` | `true` | Show the child's name in the card header. |
| `show_child_age_weight` | `true` | Show the child's age and weight in the card header. |
| `show_paracetamol` | `true` | Show the paracetamol medication row. |
| `show_ibuprofen` | `true` | Show the ibuprofen medication row. |
| `show_last_dose_time` | `true` | Show the last recorded dose time in each medication row. |
| `show_time_since_last_dose` | `true` | Show the time since the last recorded dose in each medication row. |
| `show_amount_in_last24h` | `true` | Show the rolling 24-hour amount used against the allowed amount in each medication row. |
| `show_dose_button` | `true` | Show the button to record a dose in each medication row. |
| `show_reset_button` | `true` | Show the button to reset that medication's rolling 24-hour history in each medication row. |
| `custom_medications` | `[]` | Custom medication names to show. Use a YAML list or a comma-separated string. If omitted, all discovered custom medication sensors for the child are shown. |
| `paracetamol_dose_size` | `auto` | Paracetamol dose recorded when the button is pressed. Options: `auto`, `120mg/5ml liquid`, `250mg/5ml liquid`, `250mg tablet`. `auto` uses `120mg/5ml liquid` for ages 0-5 and `250mg/5ml liquid` for ages 6+. |
| `ibuprofen_dose_size` | `auto` | Ibuprofen dose recorded when the button is pressed. Options: `auto`, `2.5ml/50mg`, `5ml/100mg`, `7.5ml/150mg`, `10ml/200mg`, `15ml/300mg`. `auto` uses `2.5ml/50mg` for 3-11 months, `5ml/100mg` for 1-3 years, `7.5ml/150mg` for 4-6 years, `10ml/200mg` for 7-9 years, and `15ml/300mg` for 10 years+. |

Each medication row includes a 24-hour dose graph showing doses administered
against the maximum allowed doses for the medicine. Hide a whole medication row
with `show_paracetamol`, `show_ibuprofen`, or by omitting a custom name from
`custom_medications`; hide individual row elements with the other `show_*`
options.

## Services

To call the services from your own card/UI, use these

Record the recommended dose for the selected medicine:

```yaml
service: child_medication_dosage.give_dose
data:
  child_id: replace_with_child_id
  medicine: paracetamol
```

Record a custom dose amount:

```yaml
service: child_medication_dosage.give_dose
data:
  child_id: replace_with_child_id
  medicine: ibuprofen
  dose_mg: 100
```

Clear history for one child:

```yaml
service: child_medication_dosage.clear_history
data:
  child_id: replace_with_child_id
```

Clear history for one child and medicine:

```yaml
service: child_medication_dosage.clear_history
data:
  child_id: replace_with_child_id
  medicine: paracetamol
```

Clear all history:

```yaml
service: child_medication_dosage.clear_history
```

Remove one recorded dose:

```yaml
service: child_medication_dosage.remove_dose
data:
  child_id: replace_with_child_id
  medicine: paracetamol
  given_at: "2026-05-10T12:00:00+00:00"
  dose_mg: 120
```

## Files

- `custom_components/child_medication_dosage`: Home Assistant custom integration.
- `custom_components/child_medication_dosage/frontend/child-dosage-card.js`:
  bundled Lovelace custom card served by the integration.
- `icon.svg`: original baby-themed project icon, released as CC0-1.0.

# Unit tests
Run the tests with
`python -m unittest discover -s tests`
