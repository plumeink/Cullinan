from typing import Annotated, Final, Optional, Union

import pytest
from cullinan import Provider
from cullinan.core import ApplicationContext


class Foo:
    pass


class Bar:
    pass


def test_parse_runtime_annotation_supports_wrappers():
    optional_annotation = ApplicationContext._parse_runtime_annotation(Optional[Foo])
    annotated_annotation = ApplicationContext._parse_runtime_annotation(Annotated[Foo, "meta"])
    final_annotation = ApplicationContext._parse_runtime_annotation(Final[Foo])
    provider_annotation = ApplicationContext._parse_runtime_annotation(Provider[Foo])
    collection_annotation = ApplicationContext._parse_runtime_annotation(tuple[Foo, ...])
    union_annotation = ApplicationContext._parse_runtime_annotation(Union[Foo, Bar])

    assert optional_annotation.kind == "single"
    assert optional_annotation.optional is True
    assert optional_annotation.targets[0].display_name == "Foo"

    assert annotated_annotation.kind == "single"
    assert annotated_annotation.targets[0].display_name == "Foo"

    assert final_annotation.kind == "single"
    assert final_annotation.targets[0].display_name == "Foo"

    assert provider_annotation.kind == "provider"
    assert provider_annotation.targets[0].display_name == "Foo"

    assert collection_annotation.kind == "collection"
    assert collection_annotation.collection_kind == "tuple"
    assert collection_annotation.targets[0].display_name == "Foo"

    assert union_annotation.kind == "union"
    assert {target.display_name for target in union_annotation.targets} == {"Foo", "Bar"}


def test_parse_string_annotation_supports_type_checking_wrappers():
    optional_annotation = ApplicationContext._parse_string_annotation('Optional["Foo"]')
    annotated_annotation = ApplicationContext._parse_string_annotation('Annotated["Foo", "meta"]')
    final_annotation = ApplicationContext._parse_string_annotation('Final["Foo"]')
    provider_annotation = ApplicationContext._parse_string_annotation('Provider["Foo"]')
    collection_annotation = ApplicationContext._parse_string_annotation('list["Foo"]')
    union_annotation = ApplicationContext._parse_string_annotation('"Foo" | "Bar"')

    assert optional_annotation.kind == "single"
    assert optional_annotation.optional is True
    assert optional_annotation.targets[0].display_name == "Foo"

    assert annotated_annotation.kind == "single"
    assert annotated_annotation.targets[0].display_name == "Foo"

    assert final_annotation.kind == "single"
    assert final_annotation.targets[0].display_name == "Foo"

    assert provider_annotation.kind == "provider"
    assert provider_annotation.targets[0].display_name == "Foo"

    assert collection_annotation.kind == "collection"
    assert collection_annotation.collection_kind == "list"
    assert collection_annotation.targets[0].display_name == "Foo"

    assert union_annotation.kind == "union"
    assert {target.display_name for target in union_annotation.targets} == {"Foo", "Bar"}


def test_parse_string_annotation_rejects_ambiguous_nested_combinations():
    with pytest.raises(ValueError):
        ApplicationContext._parse_string_annotation('list["Foo" | "Bar"]')
