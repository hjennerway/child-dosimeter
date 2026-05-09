# Child Medication Dosage for Home Assistant

Custom Home Assistant integration and Lovelace card for tracking rolling 24-hour
paracetamol and ibuprofen administration for a child.

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
- Provides a `child_medication_dosage.give_dose` service.
- Provides a dashboard card with:
  - child name, age, and weight
  - configurable paracetamol and ibuprofen rows
  - last dose time and time since last dose for each medicine
  - per-medicine record and reset buttons
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
4. To add another child later, open the integration options and add another
   child.

After adding another child, Home Assistant reloads the integration so the new
sensor entities are created.

## Add The Card

The card is bundled inside the integration and served by Home Assistant after
the integration is loaded. Register the dashboard resource:

```yaml
lovelace:
  resources:
    - url: /child_medication_dosage/child-dosage-card.js?v=3
      type: module
```

Do not use a `/hacsfiles/...` URL for this repository. HACS installs this as an
integration, not as a frontend/plugin repository, so the `/hacsfiles` path is
not created. If you previously used `/local/child-dosage-card.js`, remove that
resource and use the integration-served URL above.

Home Assistant and browsers can cache custom card modules. After updating the
card, increment the `v=` value in the resource URL and refresh the dashboard.

Then add a manual card:

```yaml
type: custom:child-dosage-card
title: Medication
child_name: Child Name
```

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

Each medication row includes a 24-hour dose graph showing doses administered
against the maximum allowed doses for the medicine. Hide a whole medication row
with `show_paracetamol` or `show_ibuprofen`; hide individual row elements with
the other `show_*` options.

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

## Files

- `custom_components/child_medication_dosage`: Home Assistant custom integration.
- `custom_components/child_medication_dosage/frontend/child-dosage-card.js`:
  bundled Lovelace custom card served by the integration.
