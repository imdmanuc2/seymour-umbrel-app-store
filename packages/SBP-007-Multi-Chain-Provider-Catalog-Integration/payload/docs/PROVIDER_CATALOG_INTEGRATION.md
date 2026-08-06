# Umbrel Provider Catalog Integration

The frozen SBR Version 1.0 catalog contains nine providers.

For SBP-007:

- Bitcoin Cash is `live` and selectable.
- Every other provider is `planned` and not selectable.
- A selectable provider must have:
  - a production image;
  - supported architecture metadata;
  - default ports;
  - a disk estimate;
  - `availability: live`.

The catalog feeds the future Seymour Umbrel blockchain-selection interface.
It does not replace the existing BCH application in this package.
