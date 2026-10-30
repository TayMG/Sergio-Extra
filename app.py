"""Camada Streamlit da demonstração.

Toda a lógica algorítmica fica em ``core.py``. Este arquivo apenas lê o
estado da sessão, chama as funções puras e desenha a interface.
"""

from __future__ import annotations

import streamlit as st

from core import (
    DEFAULT_SEED,
    DEFAULT_SIZE,
    DEFAULT_TAIL_CAPACITY,
    InsertStatus,
    generate_sorted_region,
    insert_key,
    search_key,
)

st.set_page_config(
    page_title="Lista ordenada + cauda",
    page_icon="🔎",
    layout="wide",
)


def init_state() -> None:
    """Cria o estado inicial apenas uma vez por sessão.

    ``setdefault`` é importante: em cada rerun o Streamlit executa o script
    novamente, mas não queremos gerar uma nova lista nem apagar a cauda.
    """

    st.session_state.setdefault(
        "ordered",
        generate_sorted_region(size=DEFAULT_SIZE, seed=DEFAULT_SEED),
    )
    st.session_state.setdefault("tail", [])
    st.session_state.setdefault("last_search", None)
    st.session_state.setdefault("last_insert", None)
    st.session_state.setdefault("search_count", 0)
    st.session_state.setdefault("insert_count", 0)
    st.session_state.setdefault("binary_iterations_sum", 0)
    st.session_state.setdefault("sequential_iterations_sum", 0)


def reset_state() -> None:
    """Volta ao estado inicial reproduzível (semente 42)."""

    st.session_state.ordered = generate_sorted_region(
        size=DEFAULT_SIZE,
        seed=DEFAULT_SEED,
    )
    st.session_state.tail = []
    st.session_state.last_search = None
    st.session_state.last_insert = None
    st.session_state.search_count = 0
    st.session_state.insert_count = 0
    st.session_state.binary_iterations_sum = 0
    st.session_state.sequential_iterations_sum = 0


init_state()

# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Sobre a demonstração")
    st.markdown(
        f"""
        - **Semente:** `{DEFAULT_SEED}`
        - **Região ordenada:** `{DEFAULT_SIZE}` chaves
        - **Capacidade da cauda:** `{DEFAULT_TAIL_CAPACITY}` chaves
        """
    )

    if st.button(
        "🔄 Reiniciar estrutura",
        width="stretch",
        key="btn_reset",
    ):
        reset_state()
        st.success("Estrutura reiniciada com a semente 42.")

    st.divider()
    st.caption(
        "A cauda é ordenada e intercalada automaticamente quando recebe "
        "a 10ª chave. Depois disso, novas inserções continuam permitidas."
    )

# ---------------------------------------------------------------------------
# Cabeçalho e textos
# ---------------------------------------------------------------------------
st.title("🔎 Lista ordenada com cauda de inserções")
st.write(
    "Demonstração de busca binária em uma região ordenada de "
    f"{DEFAULT_SIZE:,} chaves e de uma cauda de até "
    f"{DEFAULT_TAIL_CAPACITY} inserções sem ordenação."
)
st.markdown(
    "A busca começa sempre pela **região ordenada** (busca binária). "
    "Se a chave não estiver lá, a **cauda** é percorrida sequencialmente. "
    "Na 10ª inserção, a cauda é ordenada e intercalada na região ordenada."
)

# ---------------------------------------------------------------------------
# Entrada e botões
# ---------------------------------------------------------------------------
st.subheader("Operações")
input_col, search_col, insert_col = st.columns(
    [2, 1, 1],
    vertical_alignment="bottom",
)

with input_col:
    key = st.number_input(
        "Chave inteira",
        value=0,
        step=1,
        format="%d",
        key="input_key",
        help="Digite a chave que deseja buscar ou inserir.",
    )

with search_col:
    search_clicked = st.button(
        "🔍 Buscar",
        type="primary",
        width="stretch",
        key="btn_search",
    )

with insert_col:
    insert_clicked = st.button(
        "➕ Inserir",
        width="stretch",
        key="btn_insert",
    )

# ---------------------------------------------------------------------------
# Ações
# ---------------------------------------------------------------------------
if search_clicked:
    report = search_key(
        st.session_state.ordered,
        st.session_state.tail,
        int(key),
    )
    st.session_state.last_search = report
    st.session_state.last_insert = None
    st.session_state.search_count += 1
    st.session_state.binary_iterations_sum += report.binary_iterations
    st.session_state.sequential_iterations_sum += report.sequential_iterations

if insert_clicked:
    outcome = insert_key(
        st.session_state.ordered,
        st.session_state.tail,
        int(key),
    )
    st.session_state.ordered = outcome.ordered
    st.session_state.tail = outcome.tail
    st.session_state.last_insert = outcome
    st.session_state.last_search = None
    if outcome.status is not InsertStatus.DUPLICATE:
        st.session_state.insert_count += 1

# O estado pode ter mudado acima; recarregamos as referências para desenhar
# a interface com os valores atualizados neste mesmo rerun.
ordered = st.session_state.ordered
tail = st.session_state.tail

# ---------------------------------------------------------------------------
# Visão geral
# ---------------------------------------------------------------------------
st.markdown("### Visão geral")
summary_cols = st.columns(4)
summary_cols[0].metric("Chaves na região ordenada", len(ordered))
summary_cols[1].metric(
    "Chaves na cauda",
    f"{len(tail)}/{DEFAULT_TAIL_CAPACITY}",
)
summary_cols[2].metric("Buscas realizadas", st.session_state.search_count)
summary_cols[3].metric("Inserções aceitas", st.session_state.insert_count)

# ---------------------------------------------------------------------------
# Feedback da última inserção
# ---------------------------------------------------------------------------
if st.session_state.last_insert is not None:
    outcome = st.session_state.last_insert

    if outcome.status is InsertStatus.DUPLICATE:
        st.error(outcome.message)
    elif outcome.status is InsertStatus.MERGED:
        st.success(outcome.message)
        st.info(
            f"A região ordenada agora tem {len(ordered):,} chaves e a cauda "
            "está vazia. Novas inserções continuam permitidas."
        )
    else:
        st.success(outcome.message)

if len(tail) == DEFAULT_TAIL_CAPACITY - 1:
    st.warning(
        f"A cauda está com {len(tail)}/{DEFAULT_TAIL_CAPACITY} chaves. "
        "A próxima inserção única vai ordená-la e intercalá-la na região "
        "ordenada."
    )

# ---------------------------------------------------------------------------
# Feedback e métricas da última busca
# ---------------------------------------------------------------------------
if st.session_state.last_search is not None:
    report = st.session_state.last_search
    st.markdown("#### Resultado da última busca")

    if report.found:
        st.success(
            f"Chave {report.key} encontrada na "
            f"{report.location.value.lower()} "
            f"(índice interno {report.index}, base 0)."
        )
    else:
        st.warning(
            f"Chave {report.key} não encontrada na região ordenada nem na cauda."
        )

    metric_cols = st.columns(4)
    metric_cols[0].metric(
        "Iterações da busca binária",
        report.binary_iterations,
    )
    metric_cols[1].metric(
        "Iterações da busca sequencial",
        report.sequential_iterations,
    )
    metric_cols[2].metric("Total de iterações", report.total_iterations)
    metric_cols[3].metric("Local do resultado", report.location.value)

    if st.session_state.search_count:
        average_binary = (
            st.session_state.binary_iterations_sum / st.session_state.search_count
        )
        average_sequential = (
            st.session_state.sequential_iterations_sum / st.session_state.search_count
        )
        st.caption(
            f"Acumulado: {st.session_state.search_count} busca(s) · "
            f"média binária {average_binary:.2f} · "
            f"média sequencial {average_sequential:.2f}."
        )

# ---------------------------------------------------------------------------
# Tabelas da estrutura
# ---------------------------------------------------------------------------
st.markdown("### Estrutura atual")
ordered_col, tail_col = st.columns([2, 1], gap="large")

with ordered_col:
    st.markdown(f"**Região ordenada** · {len(ordered):,} chaves")
    st.caption("Role a tabela para ver todas as chaves. A coluna Índice é 1-based.")
    st.dataframe(
        {
            "Índice": list(range(1, len(ordered) + 1)),
            "Chave": ordered,
        },
        height=340,
        hide_index=True,
        width="stretch",
    )

with tail_col:
    st.markdown(f"**Cauda** · {len(tail)}/{DEFAULT_TAIL_CAPACITY} chaves")
    if tail:
        st.dataframe(
            {
                "Posição": list(range(1, len(tail) + 1)),
                "Chave": tail,
            },
            height=220,
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("Cauda vazia. A próxima inserção será a primeira.")

    st.progress(
        len(tail) / DEFAULT_TAIL_CAPACITY,
        text=f"Ocupação: {len(tail)}/{DEFAULT_TAIL_CAPACITY}",
    )
    st.caption(
        "A cauda não é mantida ordenada; ela é ordenada apenas no momento "
        "da intercalação."
    )

# ---------------------------------------------------------------------------
# Explicação didática
# ---------------------------------------------------------------------------
with st.expander("Como a busca e a intercalação funcionam"):
    st.markdown(
        """
        **Busca binária (região ordenada).** A cada iteração o algoritmo
        compara a chave com o elemento central e descarta metade do intervalo.
        O custo é O(log n): para 1.024 chaves, no máximo 10 iterações. A
        contagem exibida é o número de vezes que o laço `while` executou, ou
        seja, o número de comparações com o elemento central.

        **Busca sequencial (cauda).** Se a busca binária não encontrar a
        chave, a cauda é percorrida da primeira até a última posição. Como a
        cauda tem no máximo 10 chaves, o custo é O(10). Quando a chave é
        encontrada na região ordenada, a busca sequencial nem é executada e
        suas iterações aparecem como zero.

        **Inserção.** A chave nova é acrescentada ao fim da cauda, sem
        ordenação. Antes disso, uma verificação com `bisect_left` na região
        ordenada e uma busca simples na cauda rejeitam duplicatas.

        **Intercalação.** Quando a cauda chega a 10 chaves, apenas ela é
        ordenada (`O(10 log 10)`). Depois, duas sequências já ordenadas são
        intercaladas com dois ponteiros em `O(n + 10)`. A região ordenada
        nunca é reordenada por completo. Por fim, a cauda é esvaziada.
        """
    )

st.divider()
st.caption(
    "Projeto didático: lógica pura em core.py, interface em app.py e testes "
    "com pytest + Streamlit AppTest."
)
