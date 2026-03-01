## Problem Statement

The goal is to implement a viral score calculation module that evaluates YouTube videos based on their potential to go viral. The score is computed using a weighted sum of several normalized metrics: view velocity, Reddit score, like ratio, comment velocity, and recency factor.

## Functional Requirements

1. **FR-1**: Implement the `ViralScorer` class in `src/discovery/scorer.py`.
2. **FR-2**: The `ViralScorer` class must be initialized with scoring weights from the configuration.
3. **FR-3**: Implement the `calculate_score` method that computes the weighted sum of normalized metrics.
4. **FR-4**: Normalize each metric to a 0-1 range before applying weights.
5. **FR-5**: Implement normalization functions for view velocity, Reddit score, comment velocity, and recency factor.
6. **FR-6**: Calculate the like ratio as (likes / views) and normalize it.
7. **FR-7**: Ensure that videos with zero views, likes, or comments receive a score of 0.0 without errors.

## Non-Functional Requirements

1. **NFR-1**: The module must handle large datasets efficiently.
2. **NFR-2**: The scoring algorithm must be reliable and not crash on unexpected input.
3. **NFR-3**: The code must be maintainable, with clear separation of concerns.
4. **NFR-4**: The module must adhere to security best practices.

## Constraints

1. **C-1**: All weights must sum exactly to 1.0.
2. **C-2**: Division by zero must be handled gracefully.
3. **C-3**: Recency factor decay must use exponential, not linear, scaling.
4. **C-4**: No emojis may appear in logs or outputs.

## Success Criteria

- [ ] All normalization functions return values between 0.0 and 1.0.
- [ ] Weights are correctly loaded from the configuration.
- [ ] The calculated score is within the range of 0.0 to 1.0.
- [ ] Videos with zero views, likes, or comments receive a score of 0.0 without errors.
- [ ] Comprehensive tests cover all normalization functions and edge cases.

## Out of Scope

- Data fetching from YouTube or Reddit APIs.
- Video storage or processing.
- Displaying scores in a user interface.
- Configuration validation beyond ensuring weights sum to 1.0.

## Open Questions

- How should extremely large values be handled during normalization?
- What is the default ceiling for view velocity normalization?
- Should the recency factor decay curve be configurable?