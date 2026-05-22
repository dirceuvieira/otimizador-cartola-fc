## Why

Currently, the ML model predicts athlete performance based on individual statistics and aggregate team performance, but doesn't account for matchup context (who is the opponent this round?). Including head-to-head opponent analysis improves prediction accuracy: attackers benefit from weak opposing defenses, defenders are pressured by strong opposing offenses. This is a critical feature engineering gap that directly impacts recommendation quality.

## What Changes

- **Feature Enrichment**: Calculate and add matchup-aware features (opponent defense strength, opponent offensive pressure) derived from last 5 rounds of historical data
- **Opponent Lookup**: Map each athlete to their opponent for the next matchday using partida data
- **Database Schema**: Create new `features_matchup` table to persist calculated matchup features for each athlete/round combination
- **Model Integration**: Include matchup features in training pipeline - RandomForest will learn appropriate weight for each feature
- **UI Foundation**: Store features in database so frontend can display opponent context and feature breakdown when analyzing athlete recommendations

## Capabilities

### New Capabilities
- `matchup-feature-calculation`: Calculate opponent defensive pressure (avg gols sofridos) and offensive pressure (avg gols marcados) from historical data aggregated by team across last 5 rounds
- `matchup-feature-persistence`: Persist calculated matchup features to Supabase `features_matchup` table for retrieval and display in UI

### Modified Capabilities
- `athlete-prediction`: Extend ML model training to include matchup features in feature set used by RandomForest

## Impact

**Code Modified:**
- `train_local.py`: Add `add_matchup_features()` function and integrate into training pipeline
- `data/cartola_api.py`: Add `get_team_stats()` method to calculate team-level performance metrics
- `adapters/supabase_repository.py`: Add method to upsert features to `features_matchup` table

**Database:**
- New table: `features_matchup` with columns for defesa_adversaria, ataque_adversario, finalizacoes_sofridas_adv
- New table: `training_log` for audit trail of training executions

**Dependencies:**
- Requires last 5 rounds of `/atletas/pontuados/<rodada>` API data
- Requires `/partidas` endpoint to map opponents
- No new external dependencies (pandas, numpy already available)

**Breaking Changes:** None - additive feature, backward compatible
