"""New synthetic adversarial checks; baseline expectations are not weakened."""
from fractions import Fraction

import numpy as np
import pandas as pd
import pytest

def test_snapshot_mixed_uint64_float_preserves_integer_identity():
    from backtest.portfolio import _snapshot_source_cells
    dates=pd.date_range('2020-01-01',periods=2)
    source=pd.DataFrame({'large':np.array([2**63+1,2**63+3],dtype=np.uint64),'real':[1.5,-0.0]},index=dates)
    cells=_snapshot_source_cells(source)
    assert cells[0][0].kind=='integer'
    assert cells[0][0].payload==(str(2**63+1),)
    assert cells[1][0].payload==(str(2**63+3),)
    assert cells[1][1].payload==('-0x0.0p+0',)

def test_snapshot_mixed_complex_does_not_retype_real_column():
    from backtest.portfolio import _snapshot_source_cells
    source=pd.DataFrame({'real':[1.0],'complex':[1+0j]},index=pd.date_range('2020-01-01',periods=1))
    cells=_snapshot_source_cells(source)
    assert [c.kind for c in cells[0]]==['real_float','complex']

def test_snapshot_nullable_and_fraction_semantics():
    from backtest.portfolio import _snapshot_source_cells
    source=pd.DataFrame({'integer':pd.array([1,None],dtype='Int64'),'fraction':[Fraction(1,3),None]},index=pd.date_range('2020-01-01',periods=2))
    cells=_snapshot_source_cells(source)
    assert cells[0][0].kind=='integer'
    assert cells[0][1].payload==('1','3')
    assert cells[1][0].kind=='missing_other'
    assert cells[1][1].kind=='missing_other'


@pytest.mark.parametrize('method',['pearson','spearman'])
def test_diagnostics_sparse_tied_constant_and_nonfinite_boundary(method):
    from features.diagnostics import factor_information_coefficient
    dates=pd.date_range('2020-01-01',periods=4)
    left=pd.DataFrame([[1,2,3,4],[1,1,1,1],[np.nan,2,np.nan,4],[1,1,2,2]],index=dates)
    right=pd.DataFrame([[4,3,2,1],[2,3,4,5],[1,np.nan,3,4],[1,1,2,2]],index=dates)
    result=factor_information_coefficient(left,right,method=method,min_periods=2)
    assert result.iloc[0]==pytest.approx(-1,abs=1e-12)
    assert np.isnan(result.iloc[1]) and np.isnan(result.iloc[2])
    assert result.iloc[3]==pytest.approx(1,abs=1e-12)
    left.iloc[0,0]=np.inf
    with pytest.raises(ValueError):
        factor_information_coefficient(left,right,method=method)

def test_labels_only_eligible_endpoints_and_sparse_series():
    from features.validation import make_train_validation_test_split,make_price_forward_return_labels
    dates=pd.bdate_range('2020-01-01',periods=30)
    split=make_train_validation_test_split(dates,train_start=dates[2],train_end=dates[9],validation_start=dates[10],validation_end=dates[19],test_start=dates[20],test_end=dates[27],label_kind='price_forward_return',label_derivation='adjusted_close_row_forward_return_v1',label_horizon_rows=3,embargo_rows=1,feature_warm_up_rows=2)
    values=pd.Series(np.arange(30)+100.,index=dates)
    before=make_price_forward_return_labels(values,split)
    values.iloc[28:]=[1e300,np.nan]
    after=make_price_forward_return_labels(values,split)
    pd.testing.assert_series_equal(before,after,check_exact=True)
    assert after.iloc[[7,8,9,17,18,19,25,26,27,28,29]].isna().all()

def test_split_frozen_dataclass_nested_frame_mutation_is_rejected():
    from features.validation import make_train_validation_test_split,make_price_forward_return_labels
    dates=pd.bdate_range('2020-01-01',periods=9)
    split=make_train_validation_test_split(dates,train_start=dates[0],train_end=dates[2],validation_start=dates[3],validation_end=dates[5],test_start=dates[6],test_end=dates[8],label_kind='price_forward_return',label_derivation='adjusted_close_row_forward_return_v1',label_horizon_rows=1,embargo_rows=0,feature_warm_up_rows=0)
    split.label_ledger.loc[2,'is_eligible']=True
    with pytest.raises(ValueError,match='canonical contract'):
        make_price_forward_return_labels(pd.Series(np.arange(9)+100.,index=dates),split)


def test_untracked_source_edit_is_rejected_before_controlled_mutation():
    from backtest.portfolio import (
        BacktestValidationError,
        apply_tracked_backtest_source_mutation,
        capture_backtest_source_provenance,
    )

    dates = pd.bdate_range("2020-01-01", periods=3)
    prices = pd.DataFrame({"asset": [100.0, 101.0, 102.0]}, index=dates)
    signals = pd.DataFrame({"asset": [1.0, 1.0, 1.0]}, index=dates)
    provenance = capture_backtest_source_provenance(prices, signals)
    prices.iloc[0, 0] = 200.0
    with pytest.raises(BacktestValidationError) as caught:
        apply_tracked_backtest_source_mutation(
            prices, signals, provenance, source_role="signals",
            row_position=2, column_position=0, value=2.0,
        )
    assert caught.value.reason == "source_provenance_invalid"
