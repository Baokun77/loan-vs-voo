from i18n import FED_MARGINAL_LABELS, FED_MARGINAL_RATES, I18N


def test_zh_en_same_keys():
    assert set(I18N["zh"].keys()) == set(I18N["en"].keys())


def test_fed_marginal_labels_align_with_rates():
    assert len(FED_MARGINAL_LABELS["zh"]) == len(FED_MARGINAL_RATES)
    assert len(FED_MARGINAL_LABELS["en"]) == len(FED_MARGINAL_RATES)
