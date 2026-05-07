# 🚀 Como Executar o Cartola FC Optimizer

## Configuração Inicial

### 1. Configure as Credenciais do Supabase

Abra o arquivo `.streamlit/secrets.toml` e atualize com suas credenciais:

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_KEY = "sua-chave-anon-public"
```

Para obter essas informações:
1. Vá para [Supabase Dashboard](https://supabase.com/dashboard)
2. Abra seu projeto
3. Vá para **Settings** → **API**
4. Copie a **URL** e a **anon public** key

### 2. Execute o Pipeline de Treinamento

Antes de rodar o app, execute o pipeline de ML para popular o Supabase:

```bash
python train_local.py
```

Isso vai:
- ✅ Carregar dados históricos
- ✅ Buscar o mercado atual via API
- ✅ Treinar o modelo RandomForest
- ✅ Salvar 747 atletas na tabela `atletas`
- ✅ Salvar previsões na tabela `previsoes`

## Executar a Aplicação

### No Windows (Recomendado)

Execute o arquivo em lote:
```powershell
.\run_app.bat
```

Ou via terminal:
```powershell
streamlit run app.py
```

### No Linux/macOS

```bash
bash run_app.sh
```

Ou:
```bash
streamlit run app.py
```

## Usando a Aplicação

### 1. Sincronizar Dados
- Clique em **"🔄 Sincronizar"** na sidebar
- Isso carrega os atletas prováveis (status_id = 7) do Supabase
- O app mostra quantos atletas foram carregados

### 2. Visualizar Mercado
- Clique em **"📊 Mercado"** para ver todos os 747 atletas
- A tabela é interativa e pode ser ordenada

### 3. Configurar Otimização
- **💰 Orçamento**: Escolha o valor total em Cartoletas (50-200)
- **🎯 Esquema Tático**: Selecione 4-3-3, 3-4-3, 4-4-2 ou 3-5-2
- **🤖 Estratégia da IA**:
  - `Mito`: Maximiza o XP previsto (mais agressivo)
  - `Consistência`: Melhor relação performance/preço (mais seguro)

### 4. Otimizar Escalação
- Clique em **"🎯 Otimizar Escalação"**
- O app vai gerar a melhor escalação de 11 titulares + 1 técnico
- Mostra:
  - 💰 Custo total
  - ⭐ XP total previsto
  - 💵 Orçamento restante
- Você pode **baixar a escalação em CSV**

## Exemplo de Uso

1. Orçamento: **100 Cartoletas**
2. Esquema: **4-3-3**
3. Estratégia: **Mito**
4. Clique em "🎯 Otimizar Escalação"
5. Recebe 11 atletas com maior XP previsto

## Estrutura das Tabelas

### Tabela `atletas`
- `atleta_id`: ID único do atleta
- `apelido`: Nome do jogador
- `posicao_id`: Posição (1=GOL, 2=LAT, 3=ZAG, 4=MEI, 5=ATA, 6=TEC)
- `preco`: Preço em Cartoletas
- `status_id`: Status (7=Provável, 6=Dúvida, etc.)
- `media_num`: Média histórica de pontuação

### Tabela `previsoes`
- `atleta_id`: ID do atleta
- `xp_previsto`: Pontuação prevista pelo modelo ML

## Troubleshooting

### Erro: "Connection refused"
- Verifique se o Supabase está online
- Confirme que SUPABASE_URL e SUPABASE_KEY estão corretos

### Erro: "Table not found"
- Execute `python train_local.py` para popular as tabelas
- Ou execute `python setup_supabase.py` para criar as tabelas

### Nenhum atleta carregado
- Clique em "🔄 Sincronizar"
- Verifique se existem atletas com status_id = 7 no Supabase

### App lento
- A primeira carga pode ser lenta (carregando 747 atletas)
- As sincronizações subsequentes são mais rápidas

## Próximos Passos

1. **Automatizar treinamento**: Configure um cron job para rodar `train_local.py` diariamente
2. **Adicionar mais dados históricos**: Implemente scraping dos scouts históricos
3. **Deploy online**: Host a aplicação no Streamlit Cloud
4. **Notificações**: Envie alertas quando houver boas oportunidades de otimização

---

**Dúvidas?** Verifique o arquivo `PROJETO_CARTOLA_IA.md` para mais detalhes técnicos.