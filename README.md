# Lista ordenada com cauda de inserções

Aplicação didática em **Python + Streamlit** para demonstrar, em uma única
página:

- geração reprodutível de **1.024 inteiros distintos** em ordem crescente;
- busca binária na região ordenada;
- busca sequencial em uma **cauda de até 10 chaves** inseridas sem ordenação;
- contagem de iterações de cada busca;
- inserção com rejeição de duplicatas;
- ordenação e intercalação automática da cauda na 10ª inserção;
- persistência do estado entre reruns com `st.session_state`.

A lógica de negócio fica isolada em `core.py` e a interface em `app.py`.

**Repositório GitHub:** https://github.com/TayMG/Sergio-Extra

---

## Link público

> **Pendente de deploy do app.** O código já está publicado no GitHub:
> https://github.com/TayMG/Sergio-Extra
>
> O Streamlit Community Cloud exige autenticação na conta do autor do
> repositório, então o link público do app ainda não foi criado. O projeto
> está pronto para o deploy.
>
> Depois de publicar (passo a passo abaixo), o endereço terá o formato:
>
> `https://<seu-usuario>-<seu-repositorio>-<app>.streamlit.app`
>
> Cole o link final nesta seção do README.

---

## Demonstração rápida

1. A página inicia com **1.024 chaves ordenadas** e a cauda vazia.
2. Digite uma chave existente e clique em **Buscar**: a busca binária encontra
   a chave e mostra as iterações.
3. Digite uma chave nova e clique em **Inserir**: ela vai para o fim da cauda,
   sem ordenação.
4. Busque essa chave nova: a busca binária não a encontra, mas a busca
   sequencial na cauda sim. A interface mostra as duas contagens e o total.
5. Repita inserções até a cauda chegar a **10 chaves**. Nesse momento a cauda é
   ordenada, intercalada na região ordenada e esvaziada.
6. Tente inserir uma chave repetida: a aplicação mostra um erro e não altera a
   estrutura.
7. O botão **Reiniciar estrutura** volta ao estado inicial com a semente 42.

---

## Arquitetura

```text
lista-ordenada-cauda/
├── core.py              # lógica pura: geração, buscas, inserção, merge
├── app.py               # somente interface Streamlit
├── test_core.py         # testes unitários da lógica
├── test_app.py          # testes de fumaça/integração com AppTest
├── requirements.txt     # dependências de produção
├── requirements-dev.txt # dependências de desenvolvimento/testes
└── README.md
```

### `core.py`

Não importa Streamlit. Expõe funções e dataclasses:

| Símbolo | Responsabilidade |
|---|---|
| `generate_sorted_region(size, seed)` | Gera chaves distintas e ordenadas com RNG local. |
| `binary_search(values, key)` | Busca binária com contagem de iterações. |
| `sequential_search(values, key)` | Busca sequencial com contagem de iterações. |
| `contains_key(ordered, tail, key)` | Verifica duplicatas nas duas regiões. |
| `merge_sorted(left, right)` | Intercalação manual O(n + m), sem reordenar a lista inteira. |
| `insert_key(ordered, tail, key, capacity)` | Insere na cauda ou dispara o merge; devolve novo estado. |
| `search_key(ordered, tail, key)` | Executa a busca binária e, se necessário, a sequencial. |
| `SearchReport` | Resultado consolidado de uma busca. |
| `InsertOutcome` | Resultado de uma inserção e o novo estado. |

As funções de inserção e merge **não alteram as listas recebidas**: elas
trabalham com cópias e devolvem o novo estado. Isso torna os testes simples e
evita efeitos colaterais.

### `app.py`

Apenas interface:

1. Inicializa o estado com `st.session_state.setdefault(...)`.
2. Lê a chave e os cliques dos botões.
3. Chama `search_key` ou `insert_key`.
4. Atualiza o estado da sessão.
5. Desenha métricas, feedback e tabelas.

O estado não precisa de configuração manual: na primeira execução, a região
ordenada é gerada automaticamente com a semente 42 e a cauda começa vazia.

---

## Componentes Streamlit utilizados

| Componente | Para que serve | Trecho correspondente |
|---|---|---|
| `st.title` | Título principal. | `st.title("🔎 Lista ordenada com cauda de inserções")` |
| `st.write` | Texto introdutório. | `st.write("Demonstração de busca binária em uma região ordenada...")` |
| `st.markdown` | Seções, instruções e explicação didática. | `st.markdown("### Visão geral")` |
| `st.metric` | Iterações, total, local e visão geral. | `metric_cols[2].metric("Total de iterações", report.total_iterations)` |
| `st.dataframe` | Região ordenada com rolagem e cauda. | `st.dataframe({"Índice": ..., "Chave": ordered}, height=340, hide_index=True)` |
| `st.number_input` | Entrada da chave inteira. | `key = st.number_input("Chave inteira", value=0, step=1, format="%d")` |
| `st.button` | Acionar busca, inserção e reset. | `search_clicked = st.button("🔍 Buscar", type="primary", key="btn_search")` |
| `st.columns` | Layout lado a lado. | `input_col, search_col, insert_col = st.columns([2, 1, 1])` |
| `st.session_state` | Persistir listas, resultados e contadores. | `st.session_state.setdefault("ordered", generate_sorted_region(...))` |
| `st.success` | Confirmar busca/inserção. | `st.success(f"Chave {report.key} encontrada...")` |
| `st.error` | Rejeitar duplicata. | `st.error(outcome.message)` |
| `st.warning` | Chave não encontrada ou cauda quase cheia. | `st.warning("A cauda está com 9/10 chaves...")` |
| `st.info` | Cauda vazia e aviso pós-merge. | `st.info("Cauda vazia. A próxima inserção será a primeira.")` |
| `st.progress` | Ocupação da cauda. | `st.progress(len(tail) / 10, text="Ocupação: 3/10")` |
| `st.expander` | Explicação algorítmica opcional. | `with st.expander("Como a busca e a intercalação funcionam"):` |
| `st.sidebar` | Reset e informações da configuração. | `with st.sidebar: ...` |
| `st.caption` | Legendas e médias acumuladas. | `st.caption("A cauda não é mantida ordenada...")` |

### Onde cada componente aparece no código

- **Textos:** `st.title`, `st.write` e `st.markdown` abrem a página e explicam
  o problema. O `st.markdown` também é usado nos títulos das seções.
- **Métricas:** a seção “Visão geral” usa quatro `st.metric`; a última busca
  usa outros quatro para iterações binárias, sequenciais, total e local.
- **Tabelas:** a região ordenada é exibida em um `st.dataframe` com
  `height=340`, o que cria a rolagem vertical. A cauda tem sua própria tabela,
  menor, e um `st.progress` com a ocupação.
- **Entrada e ações:** um `st.number_input` recebe a chave; dois `st.button`
  acionam busca e inserção; o `st.sidebar` contém o botão de reset.
- **Feedback:** `st.success` para operações aceitas, `st.error` para
  duplicatas, `st.warning` para busca sem resultado/cauda quase cheia e
  `st.info` para estados informativos.
- **Layout:** `st.columns` organiza entrada, botões, métricas e as duas tabelas.
- **Persistência:** `st.session_state.setdefault` inicializa `ordered`, `tail`,
  `last_search`, `last_insert` e os contadores uma única vez por sessão.

---

## Como a contagem de iterações funciona

### Busca binária

```python
while low <= high:
    iterations += 1
    mid = low + (high - low) // 2
    current = values[mid]
    if current == key:
        return SearchStepResult(True, mid, iterations)
    if key < current:
        high = mid - 1
    else:
        low = mid + 1
```

Cada execução do `while` é **uma comparação com o elemento central**. O valor
retornado é exatamente o número de iterações do laço. Para 1.024 chaves, o
máximo é 10 iterações.

### Busca sequencial

```python
iterations = 0
for index, current in enumerate(values):
    iterations += 1
    if current == key:
        return SearchStepResult(True, index, iterations)
return SearchStepResult(False, None, iterations)
```

Cada elemento visitado incrementa `iterations`. Não usamos `list.index()`
porque ele não informa quantas comparações foram feitas.

### Total e local

`search_key` sempre executa a busca binária. A busca sequencial só é executada
quando a chave **não** está na região ordenada:

| Situação | Iterações binárias | Iterações sequenciais | Total | Local |
|---|---:|---:|---:|---|
| Chave na região ordenada | k | 0 | k | Região ordenada |
| Chave na cauda | k | t | k + t | Cauda |
| Chave inexistente | k | tamanho da cauda | k + tamanho da cauda | Não encontrada |

Exemplo com região ordenada `[10, 30, 50]` e cauda `[20, 40]`:

- buscar `30`: 1 iteração binária, 0 sequenciais, total 1;
- buscar `20`: 2 binárias, 1 sequencial, total 3;
- buscar `99`: 2 binárias, 2 sequenciais, total 4.

Os índices retornados por `core.py` são **0-based**. A tabela da região
ordenada exibe uma coluna “Índice” 1-based apenas para leitura humana; o
relatório da busca informa explicitamente que o índice interno é 0-based.

---

## Algoritmo de intercalação

A região ordenada nunca é reordenada por completo. O fluxo é:

1. A chave nova é acrescentada ao **fim da cauda**, sem ordenação.
2. Antes de inserir, `contains_key` rejeita duplicatas:
   - `bisect_left` na região ordenada, O(log n);
   - varredura simples na cauda, O(10).
3. Quando a cauda chega a 10 chaves:
   - apenas a cauda é ordenada, O(10 log 10);
   - `merge_sorted` intercala a cauda com a região ordenada usando dois
     ponteiros, O(n + 10);
   - a cauda é esvaziada;
   - novas inserções continuam permitidas.
4. `merge_sorted` também trata valores iguais acrescentando apenas uma cópia,
   mas a checagem de duplicatas já impede que isso ocorra pela interface.

Complexidades:

| Operação | Custo |
|---|---|
| Busca binária | O(log n) |
| Busca sequencial na cauda | O(t), com t ≤ 10 |
| Inserção normal | O(log n) para checar duplicata + O(1) para append |
| Ordenação da cauda | O(10 log 10) |
| Intercalação | O(n + 10) |
| Memória | O(n) para a região ordenada + O(10) para a cauda |

---

## Execução local

Pré-requisito: Python 3.11 ou superior (o Streamlit atual exige 3.11+).

```bash
git clone <URL-DO-SEU-REPOSITORIO>
cd lista-ordenada-cauda

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements-dev.txt
streamlit run app.py
```

O navegador abre em `http://localhost:8501`. A aplicação já inicia com a
semente 42 e a cauda vazia; não há configuração manual de estado.

Para rodar apenas a aplicação:

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Testes

```bash
pytest -q
```

Os testes cobrem:

- `test_core.py`
  - reprodutibilidade da geração com a mesma semente;
  - tamanho 1.024, ordem crescente e ausência de duplicatas;
  - contagem de iterações da busca binária (encontrada, ausente, vazia);
  - contagem de iterações da busca sequencial;
  - busca combinada: região ordenada, cauda, não encontrada e cauda vazia;
  - inserção no fim da cauda sem ordenar;
  - rejeição de duplicatas nas duas regiões;
  - intercalação na 10ª inserção e esvaziamento da cauda;
  - novas inserções após o merge;
  - invariantes após várias inserções.
- `test_app.py` (Streamlit `AppTest`)
  - fumaça: a página inicia, os controles existem e o estado inicial está
    correto;
  - busca de chave existente com métricas na tela;
  - busca de chave inexistente com aviso;
  - busca de chave que está na cauda;
  - inserção e rejeição de duplicata;
  - 10 inserções pela interface, merge e cauda vazia.

---

## Deploy no Streamlit Community Cloud

1. Crie um repositório no GitHub e envie os arquivos deste projeto.
2. Acesse [share.streamlit.io](https://share.streamlit.io) e entre com a conta
   do GitHub.
3. Clique em **New app**.
4. Selecione o repositório, a branch (`main`) e o arquivo principal `app.py`.
5. Clique em **Deploy**.
6. Copie a URL gerada, que terá um formato parecido com
   `https://seu-usuario-seu-repo-app.streamlit.app`.
7. Atualize a seção “Link público” deste README com a URL.

Não é necessário configurar segredos, banco de dados ou variáveis de
ambiente. O `requirements.txt` instala o Streamlit e suas dependências, e o
estado inicial é criado automaticamente por `st.session_state.setdefault`.

---

## Roteiro para a apresentação

1. **Abertura:** mostre o título, a explicação e a região ordenada com 1.024
   chaves. Destaque que a tabela tem rolagem.
2. **Busca binária:** busque uma chave existente. Mostre as métricas de
   iterações binárias, sequenciais (zero), total e local.
3. **Inserção:** insira uma chave nova. Mostre que ela foi para o fim da cauda
   e que a cauda não está ordenada.
4. **Busca na cauda:** busque a chave recém-inserida. Mostre que a binária não
   encontrou, a sequencial encontrou e o total é a soma das duas.
5. **Cauda cheia:** insira até a cauda ter 9 chaves e mostre o `st.warning`.
   Insira a 10ª e mostre o `st.success`, a cauda vazia e a região ordenada
   maior.
6. **Duplicata:** tente inserir uma chave existente e mostre o `st.error`.
7. **Reset:** use o botão da barra lateral para voltar à semente 42.
8. **Código:** mostre `core.py` (funções puras e contagem de iterações),
   `app.py` (somente interface) e `test_app.py` (AppTest).

---

## Decisões de projeto

- **RNG local:** `random.Random(seed)` é usado em vez de `random.seed(seed)`
  para não alterar o estado global do módulo `random`. O resultado é
  reprodutível para a mesma semente.
- **Funções sem efeitos colaterais:** inserção e merge devolvem novas listas.
  A interface é quem decide quando substituir o estado da sessão.
- **Cauda pequena:** a busca sequencial é aceitável porque a cauda tem no
  máximo 10 elementos; isso mantém o código simples e didático.
- **Sem reordenar a lista inteira:** apenas a cauda é ordenada; a região
  ordenada é intercalada em O(n + 10).
- **Índices internos 0-based:** é o padrão de Python e das funções de busca.
  A interface avisa isso e usa 1-based apenas na coluna visual da tabela.
- **Sem dependências extras:** além de `streamlit`, o projeto usa apenas a
  biblioteca padrão; `pytest` é usado somente em desenvolvimento.

---

## Limitações e observações

- O estado é por sessão do navegador. Uma nova sessão recomeça com a semente
  42; o botão de reset faz o mesmo dentro da sessão atual.
- O link público depende da conta do Streamlit Community Cloud. Veja a seção
  de deploy para publicar e preencher a URL.
- A região ordenada é exibida inteira em um `st.dataframe` com rolagem. Para
  demonstrar posições específicas, use a busca e o índice informado.
