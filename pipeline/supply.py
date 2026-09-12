"""supply — the "where to buy" layer (docs/where-to-buy.md).

Responsibility: for (country, HS prefix) collect regions and clusters where the product group is made, official
registries of industrial zones and clusters, state trade fairs and export agencies, and regional output indicators
from statistics tables; assemble `supply_pages` content in the shape of web/lib/supply-content.ts.

Rules this module must never break:
  - regions and official registries only — a fact naming an individual company is dropped by the validator;
  - indicator numbers (output share, enterprises, export value) come only from statistics tables, never from the LLM;
  - no quote -> no fact; missing statistics -> value NULL and a visible "not loaded" status, never a guess.

TODO (stages 1–2): implement. Keep functions small and testable on one country + one HS prefix.
"""
