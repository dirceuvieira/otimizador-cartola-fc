## Context

The current ML pipeline (`train_local.py`) trains a RandomForest model with 8 features:
- Individual metrics: `media_movel` (5-game average), `indice_risco` (variance)
- Price and position context: `preco`, `posicao_id`
- Team context: `mando_campo` (home/away), `scouts_cedidos_adv` (opponent avg points ceded), `forca_mandante` (home strength)
- Engagement: `finalizacoes_acumuladas` (rolling sum of shots)

Features are calculated in `train_local.py:add_engineered_features()` and merged into the prediction dataset before model training. The model then predicts `xp_previsto` (expected points) for each likely athlete.

**Current Gap**: No opponent-specific features. All athletes from a given team receive identical contextual features, regardless of their opponent. For next matchday, opponent identity is not factored.

## Goals / Non-Goals

**Goals:**
- Calculate opponent-aware features (defensive pressure, offensive pressure) from last 5 rounds
- Map each athlete to their opponent using `/partidas` endpoint
- Persist features to database for UI display and audit trail
- Integrate features into training pipeline (RandomForest learns weights)
- Store features with athlete/round combo as unique key for later retrieval
- Support posit-dependent logic (attackers vs defenders care about different aspects)

**Non-Goals:**
- Real-time feature updates mid-round (features calculated once per training cycle)
- Per-position weighted aggregation (let RandomForest learn weights)
- Manual feature adjustment UI (analysis only, not user-configurable)
- Backfill historical matchup features for past rounds (start fresh from current round)

## Decisions

### Decision 1: Source Team Stats from Last 5 Rounds
**Option A** (Chosen): Query `/atletas/pontuados/<rodada>` for rodadas N-5 to N-1, aggregate scouts by team
**Option B**: Pull from historical CSV (faster but stale)

**Rationale**: 
- Fresh data reflects current form
- 5-round window balances recency with statistical stability
- Fallback to global average if insufficient history

### Decision 2: Position-Agnostic Features (Let Model Learn)
**Option A** (Chosen): Single feature per metric (defesa_adversaria, ataque_adversario, finalizacoes_sofridas_adv) for all athletes
**Option B**: Create position-conditional features (e.g., defesa_adversaria only for attackers)

**Rationale**:
- Simpler implementation (no branch logic in feature calc)
- RandomForest handles interactions automatically
- More data (all positions) for model to learn from
- Can be improved later with explicit position masking if needed

### Decision 3: Persist to New Table vs Extend Existing
**Option A** (Chosen): New table `features_matchup(atleta_id, rodada, defesa_adversaria, ataque_adversario, finalizacoes_sofridas_adv)`
**Option B**: Add columns to existing `atletas` or `previsoes` table

**Rationale**:
- Separation of concerns (matchup features are derived, not raw)
- Easier to version or A/B test feature sets
- Can be queried independently for UI display
- Audit trail (training_log tracks when features were calculated)

### Decision 4: Team Stats Aggregation Method
**Option A** (Chosen): Mean across last 5 rounds (including incomplete rounds if <5 available)
**Option B**: Only use complete rounds, error if <5 available
**Option C**: Weighted recency (recent rounds weighted higher)

**Rationale**:
- Mean is simple, interpretable, works with partial history
- Fallback to global mean if team has no history
- Weighted recency adds complexity; mean sufficient for MVP

### Decision 5: Handling Missing Opponent Data
**Option A** (Chosen): Use global mean (all teams) for opponent if lookup fails or opponent missing
**Option B**: Use 0 (neutral)
**Option C**: Skip athlete

**Rationale**:
- Global mean preserves information (better than 0)
- Model won't be misled by false low values
- Allows model to complete training even with missing matches

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Insufficient historical data on first execution | Fallback to global mean; graceful degradation |
| Team stats don't reflect recent roster changes | 5-round window is a trade-off; can shorten to 3 if needed |
| Feature leakage (future knowledge in training) | Features calculated from past matches only (N-5 to N-1) |
| Opponent lookup fails for next round | Use global mean; log error for monitoring |
| Database bloat (many athletes × many rodadas) | Unique constraint prevents duplicates; pruning strategy later if needed |
| Model sensitivity to new feature | Start with low weight in ensemble; monitor prediction drift |

## Migration Plan

**Deployment Steps:**
1. **Database**: Run migration script to create `features_matchup` and `training_log` tables
2. **Code**: Add `CartolaAPI.get_team_stats()` and `train_local.add_matchup_features()` functions
3. **Integration**: Update `train_model_use_case.execute()` to call matchup enrichment
4. **Testing**: Train model with new features, verify predictions still reasonable (no NaNs, output in expected range)
5. **Persistence**: Add upsert to `features_matchup` after prediction phase
6. **Monitoring**: Inspect `training_log` for errors; sample athlete details in UI

**Rollback:**
- If features cause instability: Remove matchup features from feature_cols in `train_model()`, retrain
- Data stays in database (safe to keep); can be ignored

## Open Questions

1. Should team stats be recalculated every training cycle or cached?
   - **Proposal**: Recalculate (ensures freshness); performance impact acceptable if not run hourly
   
2. How to handle teams with no match scheduled (cup matches, bye)?
   - **Proposal**: Use global mean; flag in training_log for manual review
   
3. Should feature names/semantics be versioned in database?
   - **Proposal**: Add optional `feature_version` column to training_log for future A/B testing
