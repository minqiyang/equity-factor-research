"""Feature calculation modules for cross-sectional equity research."""

from features.combination import (
    correlation_discounted_composite,
    equal_weighted_composite,
    ic_weighted_composite,
    icir_weighted_composite,
    walk_forward_correlation_discounted_composite,
    walk_forward_icir_weighted_composite,
)
from features.interaction import (
    conditional_factor_rank,
    factor_product_interaction,
    factor_quadrant_interaction,
)
from features.neutralize import (
    cross_sectional_demean,
    cross_sectional_group_neutralize,
    cross_sectional_neutralize,
)

__all__ = [
    "conditional_factor_rank",
    "correlation_discounted_composite",
    "cross_sectional_demean",
    "cross_sectional_group_neutralize",
    "cross_sectional_neutralize",
    "equal_weighted_composite",
    "factor_product_interaction",
    "factor_quadrant_interaction",
    "ic_weighted_composite",
    "icir_weighted_composite",
    "walk_forward_correlation_discounted_composite",
    "walk_forward_icir_weighted_composite",
]
