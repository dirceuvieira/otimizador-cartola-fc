## ADDED Requirements

### Requirement: Persist matchup features to database
The system SHALL insert or update matchup feature records in the `features_matchup` table with a unique constraint on (atleta_id, rodada) to prevent duplicates.

#### Scenario: Insert new feature record
- **WHEN** matchup features are calculated for athlete_id=12345, rodada=15 (not previously stored)
- **THEN** system inserts row into features_matchup with all feature values and timestamp_criacao=NOW()

#### Scenario: Update existing feature record
- **WHEN** matchup features are recalculated for athlete_id=12345, rodada=15 (already in database)
- **THEN** system upserts (updates) the existing row with new feature values, preserving original timestamp_criacao

#### Scenario: Batch persistence of multiple athletes
- **WHEN** features for 100+ athletes for the same rodada are ready to persist
- **THEN** system performs batch upsert (not individual row-by-row inserts) for efficiency

### Requirement: Support efficient feature retrieval by athlete
The system SHALL create an index on atleta_id to enable fast queries for athlete-specific features.

#### Scenario: Retrieve features for single athlete
- **WHEN** UI queries `SELECT * FROM features_matchup WHERE atleta_id=12345 ORDER BY rodada DESC LIMIT 1`
- **THEN** query completes within acceptable time (<100ms) using idx_features_matchup_atleta_id index

#### Scenario: Retrieve features for round
- **WHEN** UI queries `SELECT * FROM features_matchup WHERE rodada=15`
- **THEN** query completes efficiently using idx_features_matchup_rodada index

### Requirement: Support feature audit trail
The system SHALL populate and maintain the `training_log` table with metadata about each training execution.

#### Scenario: Log successful training
- **WHEN** training completes successfully with 450 athletes processed and 450 features created
- **THEN** system inserts row into training_log with status='success', total_atletas=450, total_features_criadas=450, rodada=15, timestamp_treino=NOW()

#### Scenario: Log training error
- **WHEN** training encounters error during feature calculation or persistence (e.g., database connection lost)
- **THEN** system inserts row into training_log with status='error', error_message='<detailed error>', rodada=15

#### Scenario: Prevent duplicate training logs
- **WHEN** training is executed twice with identical timestamp_treino and rodada
- **THEN** system upserts (updates) existing log entry rather than creating duplicate

### Requirement: Schema validation before persistence
The system SHALL validate feature data before inserting into database.

#### Scenario: Validate non-null required fields
- **WHEN** matchup features contain defesa_adversaria=NULL or ataque_adversario=NULL
- **THEN** system replaces NULL with default value (0.0 or global mean) before upsert

#### Scenario: Validate numeric data types
- **WHEN** defesa_adversaria, ataque_adversario, finalizacoes_sofridas_adv contain non-numeric values
- **THEN** system coerces to float64 or rejects row with error logged

#### Scenario: Validate referential integrity
- **WHEN** attempting to insert features for non-existent atleta_id
- **THEN** system either validates against `atletas` table or logs warning (non-blocking)

### Requirement: Enable time-series queries on features
The system SHALL support retrieving feature history for an athlete or team across multiple rounds.

#### Scenario: Retrieve feature trend for single athlete
- **WHEN** UI queries `SELECT * FROM features_matchup WHERE atleta_id=12345 ORDER BY rodada`
- **THEN** system returns chronological feature values enabling trend visualization across rodadas

#### Scenario: Retrieve latest features by team
- **WHEN** UI queries `SELECT * FROM features_matchup WHERE adversario_clube_id=287 AND rodada=15`
- **THEN** system returns features for all athletes facing team 287 in rodada 15

### Requirement: Maintain data integrity with constraints
The system SHALL enforce uniqueness and temporal ordering on stored features.

#### Scenario: Unique constraint prevents duplicate athlete-round
- **WHEN** attempting to insert duplicate (atleta_id=12345, rodada=15) without upsert
- **THEN** system raises unique constraint error (prevents accidental duplicates)

#### Scenario: Timestamp defaults to now
- **WHEN** feature record is inserted without explicit timestamp_criacao
- **THEN** database DEFAULT NOW() populates current timestamp automatically
