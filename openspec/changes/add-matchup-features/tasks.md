## 1. Database Schema

- [x] 1.1 Create `features_matchup` table with columns: id, atleta_id, rodada, adversario_clube_id, defesa_adversaria, ataque_adversario, finalizacoes_sofridas_adv, timestamp_criacao
- [x] 1.2 Create `training_log` table with columns: id, timestamp_treino, rodada, total_atletas, total_features_criadas, status, error_message
- [x] 1.3 Add unique constraint on features_matchup(atleta_id, rodada)
- [x] 1.4 Create indices: idx_features_matchup_atleta_id, idx_features_matchup_rodada, idx_features_matchup_adversario, idx_features_matchup_timestamp
- [x] 1.5 Create indices: idx_training_log_rodada, idx_training_log_timestamp
- [x] 1.6 Run migration SQL on Supabase (or via run_migration.py if available)

## 2. CartolaAPI Enhancement

- [x] 2.1 Add `CartolaAPI.get_team_stats(clube_id, rounds=5, metric='defense')` method
- [x] 2.2 Implement team stats calculation: aggregate gols_marcados (metric='offense') from last N rounds
- [x] 2.3 Implement team stats calculation: aggregate gols_sofridos (metric='defense') from last N rounds
- [x] 2.4 Implement team stats calculation: aggregate finalizacoes_sofridas (metric='finalizacoes') from last N rounds
- [x] 2.5 Add fallback to global average when team has insufficient history
- [x] 2.6 Add error handling for missing/malformed scout data
- [x] 2.7 Add method docstring with examples and parameter description

## 3. Feature Calculation in train_local.py

- [x] 3.1 Create `build_team_stats_cache(df_hist, rounds=5)` function to pre-calculate all team stats for efficiency
- [x] 3.2 Create `add_matchup_features(df_market, df_partidas, team_stats_cache)` function
- [x] 3.3 Implement opponent lookup: map each athlete's clube_id to opponent via df_partidas
- [x] 3.4 Implement feature calculation: defesa_adversaria = opponent's gols_sofridos_media
- [x] 3.5 Implement feature calculation: ataque_adversario = opponent's gols_marcados_media
- [x] 3.6 Implement feature calculation: finalizacoes_sofridas_adv = opponent's finalizacoes_sofridas_media
- [x] 3.7 Handle edge case: opponent_clube_id=0 → use global average for all features
- [x] 3.8 Validate output: ensure no NaN values, all features in reasonable range

## 4. Model Integration

- [x] 4.1 Update `prepare_training_data()` in train_local.py to call `add_matchup_features()`
- [x] 4.2 Add matchup feature columns to feature_cols list in `train_model()`: defesa_adversaria, ataque_adversario, finalizacoes_sofridas_adv
- [x] 4.3 Update `build_prediction_dataset()` to include matchup features in prediction-time dataset
- [x] 4.4 Verify RandomForest model still trains with extended feature set (no errors, output valid)
- [x] 4.5 Test prediction output: xp_previsto values reasonable (not NaN, in expected range)

## 5. Feature Persistence

- [x] 5.1 Add method `upsert_matchup_features(client, df_features)` to SupabaseRepository
- [x] 5.2 Add method `log_training_execution(client, rodada, total_atletas, total_features, status, error_msg)` to SupabaseRepository
- [x] 5.3 Update `TrainModelUseCase.execute()` to upsert features to Supabase after prediction
- [x] 5.4 Update `TrainModelUseCase.execute()` to log training execution to training_log
- [x] 5.5 Add error handling: catch and log any Supabase upsert failures, don't crash training
- [x] 5.6 Verify unique constraint behavior: second training run updates existing features, doesn't duplicate

## 6. Testing & Validation

- [x] 6.1 Manual test: Run `train_model_use_case.execute()` and verify no errors
- [x] 6.2 Verify `features_matchup` table populated with correct athlete/rodada combinations
- [x] 6.3 Sample verification: Manually check 3-5 athletes' matchup features are sensible (e.g., defesa_adversaria > 0)
- [x] 6.4 Query `training_log`: Verify training execution logged with correct counts
- [x] 6.5 Verify model output (xp_previsto): Compare predictions before/after feature addition (should not be drastically different)
- [x] 6.6 Check for errors in any logs or console output during training
- [x] 6.7 Document result: Note if model improves, predictions stable, no data quality issues

## 7. Documentation

- [x] 7.1 Add docstring to `build_team_stats_cache()` with parameter description and example output
- [x] 7.2 Add docstring to `add_matchup_features()` with before/after example
- [x] 7.3 Update [PROJETO_CARTOLA_IA.md](../PROJETO_CARTOLA_IA.md) with new features explanation
- [x] 7.4 Document matchup feature columns in README or data model docs
- [x] 7.5 Add schema comments to Supabase tables (COMMENT ON COLUMN ...) - included in migration
