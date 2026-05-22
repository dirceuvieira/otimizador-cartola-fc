## ADDED Requirements

### Requirement: Calculate opponent defensive strength from historical data
The system SHALL calculate the average number of goals conceded (gols sofridos) by each opponent team from the last 5 rounds of historical match data.

#### Scenario: Calculate defensive strength for opponent with sufficient history
- **WHEN** `get_team_stats(clube_id=287, metric='defense', rounds=5)` is called
- **THEN** system returns average gols_sofridos (e.g., 1.2 goals/round) for team 287 across last 5 completed rounds

#### Scenario: Handle opponent with fewer than 5 completed rounds
- **WHEN** `get_team_stats(clube_id=999, metric='defense', rounds=5)` is called and team has only 3 completed rounds
- **THEN** system returns average gols_sofridos calculated from available 3 rounds

#### Scenario: Handle opponent with no historical data
- **WHEN** `get_team_stats(clube_id=999, metric='defense', rounds=5)` is called and team has 0 completed rounds
- **THEN** system returns global average gols_sofridos across all teams as fallback

### Requirement: Calculate opponent offensive strength from historical data
The system SHALL calculate the average number of goals scored (gols marcados) by each opponent team from the last 5 rounds of historical match data.

#### Scenario: Calculate offensive strength for opponent with sufficient history
- **WHEN** `get_team_stats(clube_id=264, metric='offense', rounds=5)` is called
- **THEN** system returns average gols_marcados (e.g., 1.8 goals/round) for team 264 across last 5 completed rounds

#### Scenario: Offensive strength with incomplete history
- **WHEN** `get_team_stats(clube_id=264, metric='offense', rounds=5)` is called and team has only 2 rounds
- **THEN** system returns average gols_marcados calculated from available 2 rounds

### Requirement: Calculate opponent shooting pressure from historical data
The system SHALL calculate the average number of shots conceded (finalizacoes_sofridas / FS scout) by each opponent team from the last 5 rounds.

#### Scenario: Calculate shot pressure for opponent
- **WHEN** `get_team_stats(clube_id=280, metric='finalizacoes', rounds=5)` is called
- **THEN** system returns average finalizacoes_sofridas (e.g., 4.5 shots/round) for team 280

### Requirement: Map athlete to opponent for next matchday
The system SHALL look up the opponent team ID for each athlete based on the `/partidas` endpoint data for the current/next round.

#### Scenario: Find opponent for athlete in home team
- **WHEN** athlete with clube_id=276 is processed and `/partidas` shows team 276 vs team 263
- **THEN** system maps opponent_clube_id=263 for that athlete

#### Scenario: Find opponent for athlete in away team
- **WHEN** athlete with clube_id=263 is processed and `/partidas` shows team 276 vs team 263
- **THEN** system maps opponent_clube_id=276 for that athlete

#### Scenario: Opponent not found in matches
- **WHEN** athlete's clube_id is not found in any `/partidas` entry
- **THEN** system sets opponent_clube_id=0 and opponent stats to global average (no match scheduled)

### Requirement: Enrich athlete dataset with matchup features
The system SHALL add three feature columns to each athlete record: `defesa_adversaria`, `ataque_adversario`, `finalizacoes_sofridas_adv`.

#### Scenario: Enrichment for complete athlete record
- **WHEN** athlete DataFrame contains [atleta_id, clube_id, posicao_id, ...] and opponent mapping is available
- **THEN** each row gains columns: defesa_adversaria (opponent's avg goals conceded), ataque_adversario (opponent's avg goals scored), finalizacoes_sofridas_adv (opponent's avg shots conceded)

#### Scenario: Enrichment with missing opponent data
- **WHEN** athlete's opponent_clube_id=0 (no match found)
- **THEN** matchup features are set to global averages (non-null, valid for training)

### Requirement: Handle edge cases in team stats calculation
The system SHALL handle missing or invalid scout data gracefully without raising exceptions.

#### Scenario: Scout data missing specific metrics
- **WHEN** historical data lacks "GS" scout (goals sofridos) for some records
- **THEN** system treats missing metrics as 0 and continues calculation

#### Scenario: Empty or malformed historical DataFrame
- **WHEN** historical data is empty or has no valid team records
- **THEN** system returns global statistics (computed from all available data across all teams) as default
