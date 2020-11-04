import pytest

from aiogram.utils.deprecated import DeprecatedReadOnlyClassVar


def test_DeprecatedReadOnlyClassVarCD():
    assert DeprecatedReadOnlyClassVar.__slots__ == ("_new_value_getter", "_warning_message")

    new_value_of_deprecated_cls_cd = "mpa"
    deprecated_cd = DeprecatedReadOnlyClassVar("mopekaa", lambda owner: new_value_of_deprecated_cls_cd)

    with pytest.warns(DeprecationWarning):
        pseudo_owner_cls = type("OpekaCla$$", (), {})
        assert deprecated_cd.__get__(None, pseudo_owner_cls) == new_value_of_deprecated_cls_cd
