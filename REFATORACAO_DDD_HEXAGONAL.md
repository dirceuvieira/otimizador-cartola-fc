# Refatoração para DDD com Arquitetura Hexagonal

## Objetivo

Documentar o passo a passo da migração incremental do app Cartola FC para uma arquitetura orientada a domínio (DDD) e hexagonal. O objetivo foi separar responsabilidades, isolar regras de negócio e manter compatibilidade com a aplicação existente, sem reescrever tudo de uma vez.

## 1. Entendimento da arquitetura existente

Antes da refatoração, o app concentrava:
- regras de negócio no `app.py` e em helpers de treinamento
- acesso a dados diretamente na aplicação principal
- lógica de otimização misturada com UI e persistência

A migração buscou criar fronteiras claras entre:
- Domínio (regras de negócio)
- Aplicação (use cases)
- Infraestrutura (adaptadores)
- Interface (Streamlit)

## 2. Criar a camada de domínio

### 2.1. Entidades

Criar objetos que representam conceitos do negócio:
- `domain/entities/atleta.py`
  - representa um atleta com atributos como `atleta_id`, `posicao_id`, `preco`, `xp_previsto`, `capitao`, etc.

### 2.2. Value Objects

Separar conceitos imutáveis e de validação:
- `domain/value_objects/tactical_scheme.py`
  - representa um esquema tático (4-3-3, 3-4-3, etc.)

### 2.3. Serviços de Domínio

Extrair regras centrais de otimização:
- `domain/services/escalacao_optimizer.py`
  - contém lógica de seleção dos 11 jogadores, respeito a orçamento, posições e capitão

## 3. Definir portas de persistência

Criar contratos abstratos para acesso a dados, sem depender da implementação concreta:
- `domain/repositories/athlete_repository.py`
  - interface para leitura e atualização de atletas
- `domain/repositories/prediction_repository.py`
  - interface para leitura e gravação de previsões e timestamp

### Por que isso é importante?

Portas permitem que o domínio seja independente de Supabase, arquivos locais ou qualquer outro banco.

## 4. Implementar adaptadores de infraestrutura

Criar implementações concretas dos repositórios:
- `adapters/supabase_repository.py`
  - `SupabaseAthleteRepository`
  - `SupabasePredictionRepository`

Esses adaptadores fazem a ponte entre:
- o domínio/application e
- o Supabase como fonte de dados

## 5. Criar os casos de uso na camada de aplicação

Agrupar orquestração e dependências em use cases:
- `application/use_cases/get_probable_atletas_use_case.py`
  - busca atletas prováveis via `AthleteRepository`
- `application/use_cases/get_all_atletas_use_case.py`
  - busca todos os atletas do mercado
- `application/use_cases/get_timestamp_treino_use_case.py`
  - lê o timestamp do último treinamento
- `application/use_cases/train_model_use_case.py`
  - orquestra o pipeline de treinamento e persiste resultados

### O papel da camada de aplicação

Ela não contém regras de domínio complexas, mas:
- consome portas do domínio
- chama helpers de infraestrutura quando necessário
- retorna dados prontos para a interface

## 6. Manter compatibilidade com a aplicação existente

Para evitar reescrever o app inteiro de uma vez, foi criado um wrapper de compatibilidade:
- `core/optimizer.py`
  - função `otimizar_escalacao(...)`
  - converte o DataFrame da UI em entidades de domínio
  - delega a otimização para `EscalacaoOptimizer`

Esse wrapper permite que `app.py` continue chamando uma API similar à original.

## 7. Refatorar a UI para usar use cases

Atualizar `app.py` para que ela:
- instancie `SupabaseAthleteRepository` e `SupabasePredictionRepository`
- use `GetProbableAtletasUseCase`, `GetAllAtletasUseCase` e `GetTimestampTreinoUseCase`
- mantenha apenas lógica de apresentação e interação com o usuário

Assim, `app.py` não conhece detalhes de persistência ou treinamento.

## 8. Refatorar o pipeline de treinamento

Atualizar `train_local.py` para usar o caso de uso de treinamento:
- instanciar `TrainModelUseCase`
- delegar a orquestração do fluxo de dados e a persistência

Isso deixa o script de treinamento responsável apenas por iniciar o fluxo, não por coordenar cada detalhe.

## 9. Adicionar testes de unidade específicos

Criar testes que validem as novas fronteiras:
- `test_train_model_use_case.py`
  - usa repositórios fake para verificar comportamento do use case
- `test_domain_optimizer.py`
  - valida a otimização de escalação com entidades do domínio

### Benefícios

- maior cobertura de regras de negócio
- isolamento de dependências externas
- possibilidade de trocar o banco e a interface sem quebrar o domínio

## 10. Benefícios da migração incremental

- mantém o app em produção enquanto a arquitetura evolui
- reduz risco de regressão
- permite validar cada camada separadamente
- facilita futuras melhorias, como troca de banco ou adição de APIs

## Estrutura final esperada

```
app.py
train_local.py
core/
  optimizer.py
application/
  use_cases/
    get_probable_atletas_use_case.py
    get_all_atletas_use_case.py
    get_timestamp_treino_use_case.py
    train_model_use_case.py
adapters/
  supabase_repository.py
domain/
  entities/
    atleta.py
  value_objects/
    tactical_scheme.py
  services/
    escalacao_optimizer.py
  repositories/
    athlete_repository.py
    prediction_repository.py
```

## Conclusão

Esta refatoração transforma o projeto de um monólito acoplado em um sistema com bordas claras:
- domínio isolado
- aplicação orquestrando casos de uso
- adaptadores cuidando da infra
- interface apenas exibindo resultados

O próximo passo natural é continuar a migração de outras operações e ampliar os casos de uso para novas funcionalidades.
