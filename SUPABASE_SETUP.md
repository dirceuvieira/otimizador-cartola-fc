# Configuração do Supabase para Cartola FC Optimizer

## Tabelas Necessárias

O projeto utiliza duas tabelas principais no Supabase:

### 1. `atletas`
Armazena dados dos jogadores do Cartola FC.

**Colunas:**
- `atleta_id` (INTEGER, PRIMARY KEY) - ID único do atleta
- `apelido` (TEXT) - Nome/apelido do jogador
- `posicao_id` (INTEGER) - Posição (1=GOL, 2=LAT, 3=ZAG, 4=MEI, 5=ATA, 6=TEC)
- `preco` (NUMERIC) - Preço do jogador
- `status_id` (INTEGER) - Status (7=Provável, 6=Dúvida, etc.)
- `xp_previsto` (NUMERIC) - Pontuação prevista (calculada pelo ML)
- `media_num` (NUMERIC) - Média histórica de pontuação

### 2. `previsoes`
Armazena as previsões de pontuação geradas pelo modelo de ML.

**Colunas:**
- `atleta_id` (INTEGER, PRIMARY KEY) - ID do atleta
- `xp_previsto` (NUMERIC) - Pontuação prevista

## Como Criar as Tabelas

### Opção 1: Via SQL Editor do Supabase (Recomendado)

1. Acesse seu projeto no [Supabase Dashboard](https://supabase.com/dashboard)
2. Vá para **SQL Editor** no menu lateral
3. Execute o script `supabase_setup.sql` que está na raiz do projeto
4. Clique em **Run** para executar

### Opção 2: Via Interface do Supabase

1. Acesse seu projeto no Supabase Dashboard
2. Vá para **Table Editor** no menu lateral

**Criando tabela `atletas`:**
1. Clique em **New table**
2. Nome: `atletas`
3. Adicione as colunas:
   - atleta_id: int8, Primary Key, Not null
   - apelido: text, Not null
   - posicao_id: int4, Not null
   - preco: numeric, Default: 0
   - status_id: int4, Default: 1
   - xp_previsto: numeric
   - media_num: numeric, Default: 0

**Criando tabela `previsoes`:**
1. Clique em **New table**
2. Nome: `previsoes`
3. Adicione as colunas:
   - atleta_id: int8, Primary Key, Not null
   - xp_previsto: numeric, Not null

## Configuração das Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com:

```env
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon-public
```

Para obter essas informações:
1. No Supabase Dashboard, vá para **Settings** > **API**
2. Copie a **URL** e a **anon public** key

## Verificação

Após criar as tabelas, execute o teste:

```bash
python train_local.py
```

Se tudo estiver configurado corretamente, você verá:
- Modelo treinado com sucesso
- Previsões salvas no Supabase
- Mensagem "Treinamento local concluído com sucesso"

## Troubleshooting

**Erro: "Could not find the table 'public.previsoes'"**
- Verifique se executou o script SQL corretamente
- Confirme que está usando o banco correto no Supabase

**Erro: "SUPABASE_URL e SUPABASE_KEY devem estar definidos"**
- Verifique se o arquivo `.env` existe e contém as variáveis corretas
- Certifique-se de que o `python-dotenv` está instalado

**Erro de conexão**
- Verifique se a URL e chave do Supabase estão corretas
- Confirme que o projeto Supabase está ativo