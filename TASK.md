# Task: Implement viral score calculation module

Priority: 3
Status: pending
Created: 2026-02-28T02:07:00Z
Depends-On: agent/task-20260228020100-fix-conftest-imports
Scope: src/discovery/scorer.py, tests/test_scorer.py

## Description
Implement the viral scoring algorithm from SPEC.md Section 4.1.

Create src/discovery/scorer.py:
- ViralScorer class initialized with scoring weights from config
- calculate_score(video_data: dict) -> float
  Computes: w1*view_velocity + w2*reddit_score + w3*like_ratio +
  w4*comment_velocity + w5*recency_factor
  All components are normalized to 0-1 range before weighting.
- normalize_view_velocity(velocity: float) -> float
  (log-scale normalization, configurable ceiling)
- normalize_reddit_score(score: int) -> float
  (log-scale, capped)
- calculate_like_ratio(likes: int, views: int) -> float
- normalize_comment_velocity(comments_per_hour: float) -> float
- calculate_recency_factor(published_at: datetime, now: datetime) -> float
  (1.0 if just published, decays to 0 over lookback_hours window)

## Acceptance Criteria
- [ ] All normalization functions return values in 0.0-1.0 range
- [ ] Weights come from config (discovery.scoring.weight_*)
- [ ] Score is a weighted sum in 0.0-1.0 range
- [ ] Videos with zero views/likes/comments get score 0.0 without errors
- [ ] tests/test_scorer.py tests: each normalization function, edge cases (zero values,
      very large values), weight application, recency decay curve

## Critical Constraints
- All weights must sum to 1.0 (validate in __init__)
- Handle division by zero gracefully
- Recency factor uses exponential decay, not linear
- No emojis

## Reference Files
- SPEC.md (Section 4.1 scoring algorithm)
- src/config.py (DiscoveryConfig with scoring weight fields)
