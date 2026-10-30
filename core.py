"""Núcleo da aplicação: geração, busca, inserção e intercalação.

Este módulo não importa Streamlit. Ele concentra a lógica de negócio e pode
ser testado de forma isolada com pytest. As funções que recebem listas não
alteram os argumentos: elas criam cópias antes de modificar qualquer coisa.
"""

from __future__ import annotations

import bisect
import random
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

# Valores usados pela aplicação. Também ficam aqui para que os testes possam
# importar a mesma configuração usada pela interface.
DEFAULT_SIZE = 1024
DEFAULT_SEED = 42
DEFAULT_TAIL_CAPACITY = 10


class SearchLocation(str, Enum):
    """Local em que uma busca terminou."""

    ORDERED = "Região ordenada"
    TAIL = "Cauda"
    NOT_FOUND = "Não encontrada"


class InsertStatus(str, Enum):
    """Resultado de uma tentativa de inserção."""

    INSERTED = "Inserida na cauda"
    MERGED = "Inserida e intercalada"
    DUPLICATE = "Duplicada (rejeitada)"


@dataclass(frozen=True)
class SearchStepResult:
    """Resultado de uma busca individual.

    ``index`` é sempre relativo à sequência em que a busca foi feita:
    posição na região ordenada ou posição na cauda. O índice é 0-based.
    """

    found: bool
    index: int | None
    iterations: int


@dataclass(frozen=True)
class SearchReport:
    """Resultado consolidado de uma busca na estrutura completa."""

    key: int
    binary_iterations: int
    sequential_iterations: int
    total_iterations: int
    found: bool
    location: SearchLocation
    index: int | None


@dataclass
class InsertOutcome:
    """Resultado de uma inserção e o novo estado da estrutura."""

    status: InsertStatus
    key: int
    ordered: list[int]
    tail: list[int]
    merged: bool
    message: str


def generate_sorted_region(
    size: int = DEFAULT_SIZE,
    seed: int = DEFAULT_SEED,
) -> list[int]:
    """Gera ``size`` inteiros distintos e devolve-os em ordem crescente.

    Usamos uma instância local de ``random.Random(seed)`` em vez de mexer no
    gerador global com ``random.seed``. Assim a geração é reprodutível e não
    interfere em outras partes do programa que eventualmente usem ``random``.

    ``random.sample`` garante que não há repetições. O universo é dez vezes
    maior que a quantidade solicitada, o que mantém a geração simples e
    confortável para o tamanho padrão de 1.024 chaves.
    """

    if size < 0:
        raise ValueError("O tamanho da região ordenada deve ser maior ou igual a zero.")

    rng = random.Random(seed)
    values = rng.sample(range(1, size * 10 + 1), size)
    values.sort()
    return values


def contains_key(ordered: Sequence[int], tail: Sequence[int], key: int) -> bool:
    """Verifica se ``key`` já existe na região ordenada ou na cauda.

    Na região ordenada usamos ``bisect_left`` (O(log n)); na cauda, uma
    varredura simples é suficiente porque ela tem no máximo 10 elementos.
    A região ordenada precisa estar ordenada, o que é uma invariante da
    estrutura.
    """

    position = bisect.bisect_left(ordered, key)
    if position < len(ordered) and ordered[position] == key:
        return True
    return key in tail


def binary_search(values: Sequence[int], key: int) -> SearchStepResult:
    """Busca ``key`` em uma sequência ordenada com busca binária.

    A contagem de iterações é feita dentro do laço: cada execução do
    ``while`` representa uma comparação entre a chave e o elemento central.
    O retorno inclui o índice 0-based quando a chave é encontrada.
    """

    low = 0
    high = len(values) - 1
    iterations = 0

    while low <= high:
        iterations += 1
        mid = low + (high - low) // 2
        current = values[mid]

        if current == key:
            return SearchStepResult(found=True, index=mid, iterations=iterations)
        if key < current:
            high = mid - 1
        else:
            low = mid + 1

    return SearchStepResult(found=False, index=None, iterations=iterations)


def sequential_search(values: Sequence[int], key: int) -> SearchStepResult:
    """Busca ``key`` sequencialmente e conta as comparações realizadas.

    Não usamos ``list.index`` porque ele não expõe quantas comparações
    foram necessárias. Cada elemento visitado incrementa ``iterations``.
    """

    iterations = 0
    for index, current in enumerate(values):
        iterations += 1
        if current == key:
            return SearchStepResult(found=True, index=index, iterations=iterations)

    return SearchStepResult(found=False, index=None, iterations=iterations)


def merge_sorted(left: Sequence[int], right: Sequence[int]) -> list[int]:
    """Intercala duas sequências ordenadas em tempo O(len(left)+len(right)).

    A intercalação usa dois ponteiros. Quando os valores são iguais, apenas
    uma cópia é acrescentada e os dois ponteiros avançam. Essa proteção extra
    evita duplicatas mesmo se a função for chamada diretamente com entradas
    sobrepostas; na aplicação, a inserção já rejeita duplicatas antes.
    """

    merged: list[int] = []
    i = 0
    j = 0

    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            merged.append(left[i])
            i += 1
        elif right[j] < left[i]:
            merged.append(right[j])
            j += 1
        else:
            merged.append(left[i])
            i += 1
            j += 1

    # Um dos lados pode ter sobrado; como já está ordenado, basta concatenar.
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged


def insert_key(
    ordered: Sequence[int],
    tail: Sequence[int],
    key: int,
    capacity: int = DEFAULT_TAIL_CAPACITY,
) -> InsertOutcome:
    """Insere ``key`` na cauda ou rejeita a operação se ela for duplicada.

    Regras:
    - a chave é acrescentada ao final da cauda, sem ordenar a cauda;
    - duplicatas na região ordenada ou na cauda são rejeitadas;
    - quando a cauda atinge ``capacity`` chaves, ela é ordenada, intercalada
      na região ordenada e esvaziada.

    A função não modifica as listas recebidas. Ela devolve o novo estado,
    o que facilita os testes e evita efeitos colaterais inesperados.
    """

    if capacity < 1:
        raise ValueError("A capacidade da cauda deve ser maior ou igual a um.")

    ordered_copy = list(ordered)
    tail_copy = list(tail)

    if contains_key(ordered_copy, tail_copy, key):
        return InsertOutcome(
            status=InsertStatus.DUPLICATE,
            key=key,
            ordered=ordered_copy,
            tail=tail_copy,
            merged=False,
            message=(
                f"A chave {key} já existe na região ordenada ou na cauda "
                "e foi rejeitada."
            ),
        )

    tail_copy.append(key)

    if len(tail_copy) >= capacity:
        # Só a cauda (no máximo 10 itens) é ordenada. A região ordenada não
        # é reordenada: o merge de duas sequências ordenadas é O(n + 10).
        tail_copy.sort()
        ordered_copy = merge_sorted(ordered_copy, tail_copy)
        tail_copy = []
        return InsertOutcome(
            status=InsertStatus.MERGED,
            key=key,
            ordered=ordered_copy,
            tail=tail_copy,
            merged=True,
            message=(
                f"A cauda atingiu {capacity} chaves: ela foi ordenada, "
                "intercalada na região ordenada e esvaziada."
            ),
        )

    return InsertOutcome(
        status=InsertStatus.INSERTED,
        key=key,
        ordered=ordered_copy,
        tail=tail_copy,
        merged=False,
        message=(
            f"Chave {key} inserida no fim da cauda ({len(tail_copy)}/{capacity})."
        ),
    )


def search_key(
    ordered: Sequence[int],
    tail: Sequence[int],
    key: int,
) -> SearchReport:
    """Busca primeiro na região ordenada e, se necessário, na cauda.

    A busca binária sempre é executada. A busca sequencial só é executada
    quando a chave não aparece na região ordenada. Por isso, quando a chave
    é encontrada na região ordenada, ``sequential_iterations`` é zero.

    O total é a soma das iterações efetivamente realizadas. Quando a chave
    não é encontrada, o total inclui a busca binária completa e a varredura
    completa da cauda.
    """

    binary_result = binary_search(ordered, key)

    if binary_result.found:
        return SearchReport(
            key=key,
            binary_iterations=binary_result.iterations,
            sequential_iterations=0,
            total_iterations=binary_result.iterations,
            found=True,
            location=SearchLocation.ORDERED,
            index=binary_result.index,
        )

    sequential_result = sequential_search(tail, key)
    total_iterations = binary_result.iterations + sequential_result.iterations

    if sequential_result.found:
        return SearchReport(
            key=key,
            binary_iterations=binary_result.iterations,
            sequential_iterations=sequential_result.iterations,
            total_iterations=total_iterations,
            found=True,
            location=SearchLocation.TAIL,
            index=sequential_result.index,
        )

    return SearchReport(
        key=key,
        binary_iterations=binary_result.iterations,
        sequential_iterations=sequential_result.iterations,
        total_iterations=total_iterations,
        found=False,
        location=SearchLocation.NOT_FOUND,
        index=None,
    )


__all__ = [
    "DEFAULT_SEED",
    "DEFAULT_SIZE",
    "DEFAULT_TAIL_CAPACITY",
    "InsertOutcome",
    "InsertStatus",
    "SearchLocation",
    "SearchReport",
    "SearchStepResult",
    "binary_search",
    "contains_key",
    "generate_sorted_region",
    "insert_key",
    "merge_sorted",
    "search_key",
    "sequential_search",
]
