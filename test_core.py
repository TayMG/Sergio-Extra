"""Testes unitários da lógica pura em ``core.py``."""

from __future__ import annotations

import pytest

from core import (
    DEFAULT_SEED,
    DEFAULT_SIZE,
    DEFAULT_TAIL_CAPACITY,
    InsertStatus,
    SearchLocation,
    binary_search,
    contains_key,
    generate_sorted_region,
    insert_key,
    merge_sorted,
    search_key,
    sequential_search,
)


# ---------------------------------------------------------------------------
# Geração
# ---------------------------------------------------------------------------
def test_generate_sorted_region_is_reproducible() -> None:
    first = generate_sorted_region()
    second = generate_sorted_region()

    assert first == second
    assert len(first) == DEFAULT_SIZE
    assert first == sorted(first)
    assert len(set(first)) == DEFAULT_SIZE


def test_generate_sorted_region_accepts_custom_size_and_seed() -> None:
    first = generate_sorted_region(size=50, seed=7)
    second = generate_sorted_region(size=50, seed=7)
    different = generate_sorted_region(size=50, seed=8)

    assert first == second
    assert first != different
    assert len(first) == 50
    assert first == sorted(first)
    assert len(set(first)) == 50


def test_generate_sorted_region_default_seed_is_42() -> None:
    assert generate_sorted_region(seed=DEFAULT_SEED) == generate_sorted_region(seed=42)


def test_generate_sorted_region_rejects_negative_size() -> None:
    with pytest.raises(ValueError):
        generate_sorted_region(size=-1)


def test_generate_sorted_region_handles_empty_size() -> None:
    assert generate_sorted_region(size=0) == []


# ---------------------------------------------------------------------------
# Busca binária
# ---------------------------------------------------------------------------
def test_binary_search_counts_iterations_when_found() -> None:
    values = [10, 20, 30, 40, 50]

    middle = binary_search(values, 30)
    assert middle.found is True
    assert middle.index == 2
    assert middle.iterations == 1

    first = binary_search(values, 10)
    assert first.found is True
    assert first.index == 0
    assert first.iterations == 2

    last = binary_search(values, 50)
    assert last.found is True
    assert last.index == 4
    assert last.iterations == 3


def test_binary_search_counts_iterations_when_missing() -> None:
    values = [10, 20, 30, 40, 50]

    result = binary_search(values, 35)
    assert result.found is False
    assert result.index is None
    assert result.iterations == 2


def test_binary_search_empty_and_single_element() -> None:
    empty = binary_search([], 10)
    assert empty.found is False
    assert empty.index is None
    assert empty.iterations == 0

    single_found = binary_search([10], 10)
    assert single_found.found is True
    assert single_found.index == 0
    assert single_found.iterations == 1

    single_missing = binary_search([10], 11)
    assert single_missing.found is False
    assert single_missing.index is None
    assert single_missing.iterations == 1


# ---------------------------------------------------------------------------
# Busca sequencial
# ---------------------------------------------------------------------------
def test_sequential_search_counts_iterations() -> None:
    values = [5, 7, 9]

    first = sequential_search(values, 5)
    assert first.found is True
    assert first.index == 0
    assert first.iterations == 1

    middle = sequential_search(values, 7)
    assert middle.found is True
    assert middle.index == 1
    assert middle.iterations == 2

    last = sequential_search(values, 9)
    assert last.found is True
    assert last.index == 2
    assert last.iterations == 3


def test_sequential_search_missing_and_empty() -> None:
    missing = sequential_search([5, 7, 9], 3)
    assert missing.found is False
    assert missing.index is None
    assert missing.iterations == 3

    empty = sequential_search([], 3)
    assert empty.found is False
    assert empty.index is None
    assert empty.iterations == 0


# ---------------------------------------------------------------------------
# Busca combinada
# ---------------------------------------------------------------------------
def test_search_key_finds_in_ordered_region_without_touching_tail() -> None:
    ordered = [10, 30, 50]
    tail = [20, 40]

    report = search_key(ordered, tail, 30)

    assert report.found is True
    assert report.location is SearchLocation.ORDERED
    assert report.index == 1
    assert report.binary_iterations == 1
    assert report.sequential_iterations == 0
    assert report.total_iterations == 1


def test_search_key_falls_back_to_tail() -> None:
    ordered = [10, 30, 50]
    tail = [20, 40]

    report = search_key(ordered, tail, 20)

    assert report.found is True
    assert report.location is SearchLocation.TAIL
    assert report.index == 0
    assert report.binary_iterations == 2
    assert report.sequential_iterations == 1
    assert report.total_iterations == 3


def test_search_key_not_found_sums_both_searches() -> None:
    ordered = [10, 30, 50]
    tail = [20, 40]

    report = search_key(ordered, tail, 99)

    assert report.found is False
    assert report.location is SearchLocation.NOT_FOUND
    assert report.index is None
    assert report.binary_iterations == 2
    assert report.sequential_iterations == 2
    assert report.total_iterations == 4


def test_search_key_with_empty_tail() -> None:
    report = search_key([10, 30, 50], [], 20)

    assert report.found is False
    assert report.location is SearchLocation.NOT_FOUND
    assert report.binary_iterations == 2
    assert report.sequential_iterations == 0
    assert report.total_iterations == 2


# ---------------------------------------------------------------------------
# Intercalação
# ---------------------------------------------------------------------------
def test_merge_sorted_interleaves_two_sorted_sequences() -> None:
    assert merge_sorted([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]
    assert merge_sorted([], [1, 2]) == [1, 2]
    assert merge_sorted([1, 2], []) == [1, 2]
    assert merge_sorted([], []) == []


def test_merge_sorted_does_not_duplicate_equal_values() -> None:
    assert merge_sorted([1, 2, 4], [2, 3, 5]) == [1, 2, 3, 4, 5]


# ---------------------------------------------------------------------------
# Inserção
# ---------------------------------------------------------------------------
def test_contains_key_checks_both_regions() -> None:
    ordered = [10, 30, 50]
    tail = [20, 40]

    assert contains_key(ordered, tail, 10) is True
    assert contains_key(ordered, tail, 50) is True
    assert contains_key(ordered, tail, 20) is True
    assert contains_key(ordered, tail, 99) is False


def test_insert_appends_to_tail_without_sorting_it() -> None:
    ordered = [10, 30, 50]
    tail: list[int] = []

    first = insert_key(ordered, tail, 99)
    assert first.status is InsertStatus.INSERTED
    assert first.merged is False
    assert first.ordered == [10, 30, 50]
    assert first.tail == [99]

    second = insert_key(first.ordered, first.tail, 5)
    assert second.status is InsertStatus.INSERTED
    assert second.tail == [99, 5]  # não foi ordenada

    # As entradas originais não são modificadas.
    assert ordered == [10, 30, 50]
    assert tail == []


def test_insert_rejects_duplicates_in_ordered_region_and_tail() -> None:
    ordered = [10, 20, 30]
    tail = [15, 25]

    in_ordered = insert_key(ordered, tail, 20)
    assert in_ordered.status is InsertStatus.DUPLICATE
    assert in_ordered.merged is False
    assert in_ordered.ordered == ordered
    assert in_ordered.tail == tail

    in_tail = insert_key(ordered, tail, 15)
    assert in_tail.status is InsertStatus.DUPLICATE
    assert in_tail.ordered == ordered
    assert in_tail.tail == tail

    # As entradas continuam intactas.
    assert ordered == [10, 20, 30]
    assert tail == [15, 25]


def test_tenth_insert_merges_tail_and_empties_it() -> None:
    ordered = [10, 20, 30, 40, 50]
    tail = [60, 5, 35, 15, 25, 45, 55, 65, 70]

    outcome = insert_key(ordered, tail, 1)

    assert outcome.status is InsertStatus.MERGED
    assert outcome.merged is True
    assert outcome.tail == []
    assert outcome.ordered == sorted(ordered + tail + [1])
    assert len(outcome.ordered) == 15
    assert len(set(outcome.ordered)) == 15

    # Depois do merge, novas inserções continuam permitidas.
    after_merge = insert_key(outcome.ordered, outcome.tail, 2)
    assert after_merge.status is InsertStatus.INSERTED
    assert after_merge.tail == [2]


def test_custom_capacity_triggers_merge() -> None:
    outcome = insert_key([1, 3], [2], 4, capacity=2)

    assert outcome.status is InsertStatus.MERGED
    assert outcome.ordered == [1, 2, 3, 4]
    assert outcome.tail == []


def test_insert_rejects_invalid_capacity() -> None:
    with pytest.raises(ValueError):
        insert_key([1], [], 2, capacity=0)


def test_many_insertions_keep_structural_invariants() -> None:
    ordered = generate_sorted_region(size=50, seed=1)
    tail: list[int] = []

    for key in range(10_000, 10_025):
        outcome = insert_key(ordered, tail, key)
        ordered = outcome.ordered
        tail = outcome.tail

        assert len(tail) < DEFAULT_TAIL_CAPACITY
        assert ordered == sorted(ordered)
        assert len(set(ordered)) == len(ordered)

    assert len(ordered) == 70
    assert len(tail) == 5
