# Child Medication Dosage for Home Assistant

Custom Home Assistant integration and Lovelace card for tracking rolling 24-hour
medication administration for a child.

This is a home tracker, not medical advice. Confirm dose amounts, intervals, and
medicine suitability with the medicine label, pharmacist, GP, NHS 111, or your
clinician, especially for children under 3 months, unusual weights, other
conditions, or medicines with overlapping ingredients.

## What It Does

- Adds a child through the Home Assistant integrations UI with name, date of
  birth, and weight.
- Creates one sensor per child and medicine:
  - paracetamol rolling 24-hour total
  - ibuprofen rolling 24-hour total
  - any configured custom medication rolling 24-hour total
- Provides a `child_medication_dosage.give_dose` service.
- Provides a dashboard card with:
  - child name, age, and weight
  - configurable medication rows
  - last dose time and time since last dose for each medicine
  - per-medicine record and reset buttons
  - removal of individual recorded doses from the history popup
  - administered/maximum 24-hour dose bars

The dose rules are based on the supplied photo:

- Paracetamol uses the age bands shown in the schedule and assumes up to four
  doses in 24 hours.
- Ibuprofen uses the weight table shown in the schedule and a maximum of
  `30 mg/kg/day`, split into up to four doses.
- When the photo shows dose ranges, the integration uses the lower value.

## Install

Copy the integration folder into your Home Assistant config directory:

```text
custom_components/child_medication_dosage
```

Restart Home Assistant.

## Configure

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

After adding another child, Home Assistant reloads the integration so the new
sensor entities are created.

## Add The Card

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

You can also use the stable `child_id` instead of `child_name`. Find the
`child_id` in the attributes of one of the created medication sensors.

The card includes a visual editor in the Home Assistant dashboard card picker.
Use it to choose the child, toggle row sections, select dose-size behaviour, and
enter custom medications without editing YAML.

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
