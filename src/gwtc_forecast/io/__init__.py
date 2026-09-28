"""I/O adapters and immutable analysis-ready data contracts."""

from .contracts import (
    iter_selection_contract_chunks,
    read_event_contract,
    read_hyperposterior_contract,
    read_selection_contract,
    selection_contract_summary,
    write_event_contract,
    write_hyperposterior_contract,
    write_selection_contract,
)
from .pe_summary import read_pe_summary_table

__all__ = [
    "iter_selection_contract_chunks",
    "read_event_contract",
    "read_hyperposterior_contract",
    "read_pe_summary_table",
    "read_selection_contract",
    "selection_contract_summary",
    "write_event_contract",
    "write_hyperposterior_contract",
    "write_selection_contract",
]
