"""Feature calculation modules for cross-sectional equity research."""

from features.combination import (
    correlation_discounted_composite,
    equal_weighted_composite,
    ic_weighted_composite,
    icir_weighted_composite,
    walk_forward_correlation_discounted_composite,
    walk_forward_icir_weighted_composite,
)
from features.cross_validation import (
    PurgedGroupTimeSeriesSplit,
    combinatorial_purged_cross_validation_pbo,
)
from features.interaction import (
    conditional_factor_rank,
    factor_product_interaction,
    factor_quadrant_interaction,
)
from features.ml_combination import walk_forward_ml_factor_composite
from features.neutralize import (
    cross_sectional_demean,
    cross_sectional_group_neutralize,
    cross_sectional_neutralize,
)

__all__ = [
    "combinatorial_purged_cross_validation_pbo",
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
    "PurgedGroupTimeSeriesSplit",
    "walk_forward_correlation_discounted_composite",
    "walk_forward_icir_weighted_composite",
    "walk_forward_ml_factor_composite",
]
