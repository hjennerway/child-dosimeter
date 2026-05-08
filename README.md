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
  - `Given Paracetamol` and `Given Ibuprofen` buttons
  - last administration time for each medicine
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
    - url: /child_medication_dosage/child-dosage-card.js
      type: module
```

Do not use a `/hacsfiles/...` URL for this repository. HACS installs this as an
integration, not as a frontend/plugin repository, so the `/hacsfiles` path is
not created. The compatibility URL
`/child_medication_dosage/frontend/child-dosage-card.js` is also served.

Then add a manual card:

```yaml
type: custom:child-dosage-card
title: Medication
child_name: Child Name
```

You can also use the stable `child_id` instead of `child_name`. Find the
`child_id` in the attributes of one of the created medication sensors.

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

Clear all history:

```yaml
service: child_medication_dosage.clear_history
```

## Files

- `custom_components/child_medication_dosage`: Home Assistant custom integration.
- `custom_components/child_medication_dosage/frontend/child-dosage-card.js`:
  bundled Lovelace custom card served by the integration.
