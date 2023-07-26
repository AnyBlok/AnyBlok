# This file is a part of the AnyBlok project
#
#    Copyright (C) 2014 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2017 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2018 Jean-Sebastien SUZANNE <jssuzanne@anybox.fr>
#    Copyright (C) 2019 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#    Copyright (C) 2020 Jean-Sebastien SUZANNE <js.suzanne@gmail.com>
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file,You can
# obtain one at http://mozilla.org/MPL/2.0/.
import datetime
import enum
import time
from decimal import Decimal as D
from os import urandom
from uuid import uuid1

import pytest
import pytz
from sqlalchemy import Integer as SA_Integer
from sqlalchemy import String as SA_String
from sqlalchemy import text
from sqlalchemy.exc import StatementError

from anyblok import Declarations
from anyblok.column import (
    URL,
    UUID,
    BigInteger,
    Boolean,
    Color,
    Column,
    CompareType,
    Country,
    Date,
    DateTime,
    Decimal,
    Email,
    Enum,
    Float,
    Integer,
    Interval,
    Json,
    LargeBinary,
    ModelFieldSelection,
    ModelSelection,
    Password,
    PhoneNumber,
    Selection,
    Sequence,
    String,
    Text,
    Time,
    TimeStamp,
    add_timezone_on_datetime,
    convert_string_to_datetime,
    field_validator_all,
    field_validator_is_column,
    field_validator_is_field,
    field_validator_is_from_types,
    field_validator_is_named,
    field_validator_is_not_column,
    field_validator_is_not_field,
    field_validator_is_not_relationship,
    field_validator_is_relationship,
    fieldToModelAttribute,
    merge_validators,
    model_validator_all,
    model_validator_in_namespace,
    model_validator_is_not_sql,
    model_validator_is_not_view,
    model_validator_is_sql,
    model_validator_is_view,
)
from anyblok.config import Configuration
from anyblok.field import FieldException
from anyblok.mapper import ModelAttribute
from anyblok.relationship import Many2One
from anyblok.testing import sgdb_in, tmp_configuration

from .conftest import init_registry, reset_db

time_params = [DateTime]

if not sgdb_in(["MsSQL"]):
    time_params.append(TimeStamp)


@pytest.fixture(params=time_params)
def dt_column_type(request):
    return request.param


class MyTestEnum(enum.Enum):
    test = "test"
    other = "other"


COLUMNS = [
    pytest.param(
        (Selection, "test", {"selections": {"test": "test"}}),
        id="Selection",
    ),
    pytest.param(
        (Enum, "test", {"enum_cls": MyTestEnum}),
        id="Enum",
    ),
    pytest.param(
        (Boolean, True, {}),
        id="Boolean",
    ),
    pytest.param(
        (Boolean, False, {}),
        id="Boolean",
    ),
    pytest.param(
        (String, "test", {}),
        id="String",
    ),
    pytest.param(
        (BigInteger, 1, {}),
        id="BigInteger",
    ),
    pytest.param(
        (Text, "Test", {}),
        id="Text",
    ),
    pytest.param(
        (Date, datetime.date.today(), {}),
        id="Date",
    ),
    pytest.param(
        (
            DateTime,
            datetime.datetime.now().replace(
                tzinfo=pytz.timezone(time.tzname[0])
            ),
            {},
        ),
        id="DateTime",
    ),
    pytest.param(
        (Time, datetime.time(), {}),
        id="Time",
    ),
    pytest.param(
        (Float, 1.0, {}),
        id="Float",
    ),
    pytest.param(
        (Integer, 1, {}),
        id="Integer",
    ),
    pytest.param(
        (Integer, 1, {"sequence": "foo"}),
        id="Integer with sequence foo",
    ),
    pytest.param(
        (Email, "jhon@doe.com", {}),
        id="Email",
    ),
    pytest.param(
        (LargeBinary, urandom(100), {}),
        id="LargeBinary",
    ),
    pytest.param(
        (Interval, datetime.timedelta(days=6), {}),
        id="Interval",
    ),
    pytest.param(
        (Decimal, D("1"), {}),
        id="Decimal",
    ),
    pytest.param(
        (Json, {"name": "test"}, {}),
        id="Json",
    ),
    pytest.param(
        (ModelSelection, "Model.System.Blok", {}),
        id="ModelSelection",
    ),
    pytest.param(
        (ModelFieldSelection, "Model.System.Blok => name", {}),
        id="ModelFieldSelection",
    ),
]

if not sgdb_in(["MySQL", "MariaDB"]):
    COLUMNS.append(pytest.param((UUID, uuid1(), {}), id="UUID"))

if not sgdb_in(["MsSQL"]):
    COLUMNS.append(
        pytest.param(
            (
                TimeStamp,
                datetime.datetime.now().replace(
                    tzinfo=pytz.timezone(time.tzname[0])
                ),
                {},
            ),
            id="TimeStamp",
        )
    )


try:
    import cryptography  # noqa

    has_cryptography = True
except Exception:
    has_cryptography = False

try:
    import passlib  # noqa

    has_passlib = True
except Exception:
    has_passlib = False

try:
    import colour

    has_colour = True
    COLUMNS.append(
        pytest.param((Color, colour.Color("#123456"), {}), id="Color")
    )
except Exception:
    has_colour = False

try:
    import furl  # noqa

    has_furl = True
    COLUMNS.append(
        pytest.param((URL, furl.furl("http://doc.anyblok.org"), {}), id="URL")
    )
except Exception:
    has_furl = False


try:
    import phonenumbers  # noqa

    has_phonenumbers = True
    from sqlalchemy_utils import PhoneNumber as PN

    COLUMNS.append(
        pytest.param(
            (PhoneNumber, PN("+120012301", None), {}),
            id="PhoneNumber",
        )
    )
except Exception:
    has_phonenumbers = False

try:
    import pycountry  # noqa

    has_pycountry = True
    COLUMNS.append(
        pytest.param(
            (Country, pycountry.countries.get(alpha_2="FR"), {}), id="Country"
        )
    )
except Exception:
    has_pycountry = False


Model = Declarations.Model
register = Declarations.register


@pytest.fixture(params=COLUMNS)
def column_definition(request, bloks_loaded):
    return request.param


class OneColumn(Column):
    sqlalchemy_type = SA_Integer


class TestColumn:
    def test_forbid_instance(self):
        with pytest.raises(FieldException):
            Column()

    def test_without_label(self):
        column = OneColumn()
        column.get_sqlalchemy_mapping(None, None, "a_column", None)
        assert column.label == "A column"


def simple_column(ColumnType=None, **kwargs):
    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        col = ColumnType(**kwargs)

        @classmethod
        def meth_secretkey(cls):
            return "secretkey"


def column_with_foreign_key():
    @register(Model)
    class Test:
        name = String(primary_key=True)

    @register(Model)
    class Test2:
        id = Integer(primary_key=True)
        test = String(foreign_key=Model.Test.use("name"))


def column_with_foreign_key_with_schema():
    @register(Model)
    class Test:
        __db_schema__ = "test_db_fk_schema"

        name = String(primary_key=True)

    @register(Model)
    class Test2:
        __db_schema__ = "test_db_fk_schema"

        id = Integer(primary_key=True)
        test = String(foreign_key=Model.Test.use("name"))


def column_with_foreign_key_with_diff_schema1():
    @register(Model)
    class Test:
        __db_schema__ = "test_db_fk_schema"

        name = String(primary_key=True)

    @register(Model)
    class Test2:
        __db_schema__ = "test_db_fk_schema2"

        id = Integer(primary_key=True)
        test = String(foreign_key=Model.Test.use("name"))


def column_with_foreign_key_with_diff_schema2():
    @register(Model)
    class Test:
        __db_schema__ = "test_db_fk_schema"

        name = String(primary_key=True)

    @register(Model)
    class Test2:
        id = Integer(primary_key=True)
        test = String(foreign_key=Model.Test.use("name"))


@pytest.mark.column
class TestColumns:
    @pytest.fixture(autouse=True)
    def close_registry(self, request, bloks_loaded):
        def close():
            if hasattr(self, "registry"):
                self.registry.close()

        request.addfinalizer(close)

    def init_registry(self, *args, **kwargs):
        reset_db()
        self.registry = init_registry(*args, **kwargs)
        return self.registry

    def test_insert_columns(self, column_definition):
        column, value, kwargs = column_definition
        registry = self.init_registry(
            simple_column, ColumnType=column, **kwargs
        )
        test = registry.Test.insert(col=value)
        assert test.col == value

    def test_column_with_type_in_kwargs(self):
        self.init_registry(simple_column, ColumnType=Integer, type_=Integer)

    def test_column_with_db_column_name_in_kwargs(self):
        registry = self.init_registry(
            simple_column, ColumnType=Integer, db_column_name="another_name"
        )
        test = registry.Test.insert(col=1)
        assert test.col == 1
        res = registry.execute(text("select id from test where another_name=1"))
        assert res.fetchone()[0] == test.id
        ma = ModelAttribute("Model.Test", "col")
        assert ma.get_column_name(registry) == "another_name"

    def test_column_with_foreign_key(self):
        registry = self.init_registry(column_with_foreign_key)
        registry.Test.insert(name="test")
        registry.Test2.insert(test="test")
        assert (
            ModelAttribute("Model.Test2", "test").get_fk_remote(registry)
            == "test.name"
        )

    def test_column_with_foreign_key_with_schema(self, db_schema):
        registry = self.init_registry(column_with_foreign_key_with_schema)
        registry.Test.insert(name="test")
        registry.Test2.insert(test="test")

    def test_column_with_foreign_key_with_diff_schema1(self, db_schema):
        registry = self.init_registry(column_with_foreign_key_with_diff_schema1)
        registry.Test.insert(name="test")
        registry.Test2.insert(test="test")

    def test_column_with_foreign_key_with_diff_schema2(self, db_schema):
        registry = self.init_registry(column_with_foreign_key_with_diff_schema2)
        registry.Test.insert(name="test")
        registry.Test2.insert(test="test")

    def test_integer_str_foreign_key(self):
        registry = self.init_registry(
            simple_column, ColumnType=Integer, foreign_key="Model.Test=>id"
        )
        test = registry.Test.insert()
        test2 = registry.Test.insert(col=test.id)
        assert test2.col == test.id

    def test_setter_decimal(self):
        registry = self.init_registry(simple_column, ColumnType=Decimal)
        test = registry.Test.insert()
        test.col = "1.0"
        assert test.col == D("1.0")

    def test_boolean_with_default(self):
        registry = self.init_registry(
            simple_column, ColumnType=Boolean, default=False
        )
        test = registry.Test.insert()
        assert test.col is False

    def test_string_with_False(self):
        registry = self.init_registry(simple_column, ColumnType=String)
        test = registry.Test.insert(col=False)
        assert test.col is False
        self.registry.flush()
        self.registry.expire(test, ["col"])
        assert test.col == ""

    def test_string_set_False(self):
        registry = self.init_registry(simple_column, ColumnType=String)
        test = registry.Test.insert()
        test.col = False
        assert test.col is False
        self.registry.flush()
        self.registry.expire(test, ["col"])
        assert test.col == ""

    def test_string_query_False(self):
        registry = self.init_registry(simple_column, ColumnType=String)
        Test = registry.Test
        test = Test.insert()
        Test.execute_sql_statement(
            Test.update_sql_statement()
            .where(Test.id == test.id)
            .values(col=False)
        )
        self.registry.expire(test, ["col"])
        assert test.col == ""

    @pytest.mark.skipif(
        not has_cryptography, reason="cryptography is not installed"
    )
    def test_string_with_encrypt_key_defined_by_configuration(self):
        Configuration.set("default_encrypt_key", "secretkey")
        registry = self.init_registry(
            simple_column, ColumnType=String, encrypt_key=True
        )
        test = registry.Test.insert(col="col")
        registry.session.commit()
        assert test.col == "col"
        res = registry.execute(
            text("select col from test where id = %s" % test.id)
        )
        res = res.fetchall()[0][0]
        assert res != "col"
        del Configuration.configuration["default_encrypt_key"]

    @pytest.mark.skipif(
        not has_cryptography, reason="cryptography is not installed"
    )
    def test_string_with_encrypt_key_by_class_method(self):
        registry = self.init_registry(
            simple_column, ColumnType=String, encrypt_key="meth_secretkey"
        )
        test = registry.Test.insert(col="col")
        registry.session.commit()
        assert test.col == "col"
        res = registry.execute(
            text("select col from test where id = %s" % test.id)
        )
        res = res.fetchall()[0][0]
        assert res != "col"

    def test_string_with_size(self):
        registry = self.init_registry(
            simple_column, ColumnType=String, size=100
        )
        test = registry.Test.insert(col="col")
        assert test.col == "col"

    @pytest.mark.skipif(not has_passlib, reason="passlib is not installed")
    def test_password(self):
        registry = self.init_registry(
            simple_column,
            ColumnType=Password,
            crypt_context={"schemes": ["md5_crypt"]},
        )
        test = registry.Test.insert(col="col")
        assert test.col == "col"
        assert (
            registry.execute(text("Select col from test")).fetchone()[0]
            != "col"
        )

    @pytest.mark.skipif(not has_passlib, reason="passlib is not installed")
    def test_password_with_foreign_key(self):
        with pytest.raises(FieldException):
            self.init_registry(
                simple_column,
                ColumnType=Password,
                crypt_context={"schemes": ["md5_crypt"]},
                foreign_key="Model.System.Blok=>name",
            )

    def test_text_with_False(self):
        registry = self.init_registry(simple_column, ColumnType=Text)
        test = registry.Test.insert(col=False)
        assert test.col is False
        self.registry.flush()
        self.registry.expire(test, ["col"])
        assert test.col == ""

    def test_text_set_False(self):
        registry = self.init_registry(simple_column, ColumnType=Text)
        test = registry.Test.insert()
        test.col = False
        assert test.col is False
        self.registry.flush()
        self.registry.expire(test, ["col"])
        assert test.col == ""

    def test_text_query_False(self):
        registry = self.init_registry(simple_column, ColumnType=Text)
        Test = registry.Test
        test = Test.insert()
        Test.execute_sql_statement(
            Test.update_sql_statement()
            .where(Test.id == test.id)
            .values(col=False)
        )
        self.registry.expire(test, ["col"])
        assert test.col == ""

    def test_datetime_without_auto_update_1(self, dt_column_type):
        def add_in_registry():
            from anyblok import Declarations

            @Declarations.register(Declarations.Model)
            class Test:
                id = Integer(primary_key=True)
                update_at = DateTime()
                val = String()

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert(val="first add")
        assert test.update_at is None
        test.val = "other"
        registry.flush()
        assert test.update_at is None

    def test_datetime_without_auto_update_2(self, dt_column_type):
        def add_in_registry():
            from anyblok import Declarations

            @Declarations.register(Declarations.Model)
            class Test:
                id = Integer(primary_key=True)
                update_at = DateTime(auto_update=False)
                val = String()

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert(val="first add")
        assert test.update_at is None
        test.val = "other"
        registry.flush()
        assert test.update_at is None

    def test_datetime_with_auto_update(self, dt_column_type):
        def add_in_registry():
            from anyblok import Declarations

            @Declarations.register(Declarations.Model)
            class Test:
                id = Integer(primary_key=True)
                update_at = DateTime(auto_update=True)
                val = String()

        registry = self.init_registry(add_in_registry)
        test = registry.Test.insert(val="first add")
        assert test.update_at is None
        test.val = "other"
        registry.flush()
        assert test.update_at is not None

    def test_datetime_with_default_timezone_tz(self, dt_column_type):
        import datetime

        import pytz

        timezone = pytz.timezone("Asia/Tokyo")
        now = datetime.datetime.now()
        registry = self.init_registry(
            simple_column, ColumnType=dt_column_type, default_timezone=timezone
        )
        field = registry.loaded_namespaces_first_step["Model.Test"]["col"]
        assert field.default_timezone is timezone

        test = registry.Test.insert(col=now)
        assert test.col.tzinfo.zone is timezone.zone

    def test_datetime_with_default_timezone_str(self, dt_column_type):
        import datetime

        import pytz

        timezone = pytz.timezone("Asia/Tokyo")
        now = datetime.datetime.now()
        registry = self.init_registry(
            simple_column,
            ColumnType=dt_column_type,
            default_timezone="Asia/Tokyo",
        )
        field = registry.loaded_namespaces_first_step["Model.Test"]["col"]
        assert field.default_timezone == timezone

        test = registry.Test.insert(col=now)
        assert test.col.tzinfo.zone == timezone.zone

    def test_datetime_with_default_global_timezone_str(self, dt_column_type):
        import datetime

        import pytz

        timezone = pytz.timezone("Asia/Tokyo")
        now = datetime.datetime.now()
        with tmp_configuration(default_timezone="Asia/Tokyo"):
            registry = self.init_registry(
                simple_column, ColumnType=dt_column_type
            )

        field = registry.loaded_namespaces_first_step["Model.Test"]["col"]
        assert field.default_timezone is timezone

        test = registry.Test.insert(col=now)
        assert test.col.tzinfo.zone is timezone.zone

    def test_selection(self):
        SELECTIONS = [("admin", "Admin"), ("regular-user", "Regular user")]

        registry = self.init_registry(
            simple_column, ColumnType=Selection, selections=SELECTIONS
        )
        test = registry.Test.insert(col=SELECTIONS[0][0])
        assert test.col == SELECTIONS[0][0]
        assert test.col.label == SELECTIONS[0][1]
        test = registry.Test.query().first()
        assert test.col == SELECTIONS[0][0]
        assert test.col.label == SELECTIONS[0][1]
        with pytest.raises(FieldException):
            test.col = "bad value"

    def test_selection_with_only_one_value(self):
        SELECTIONS = [
            ("admin", "Admin"),
        ]

        registry = self.init_registry(
            simple_column, ColumnType=Selection, selections=SELECTIONS
        )
        test = registry.Test.insert(col=SELECTIONS[0][0])
        assert test.col == SELECTIONS[0][0]
        assert test.col.label == SELECTIONS[0][1]
        test = registry.Test.query().first()
        assert test.col == SELECTIONS[0][0]
        assert test.col.label == SELECTIONS[0][1]
        with pytest.raises(FieldException):
            test.col = "bad value"

    def test_selection_without_value(self):
        self.init_registry(simple_column, ColumnType=Selection, selections=[])

    def test_selection_autodoc(self):
        SELECTIONS = [
            ("admin", "Admin"),
        ]

        registry = self.init_registry(
            simple_column, ColumnType=Selection, selections=SELECTIONS
        )
        description = registry.Test.fields_description("col")["col"]
        assert description == {
            "id": "col",
            "label": "Col",
            "model": None,
            "nullable": True,
            "primary_key": False,
            "selections": [
                ("admin", "Admin"),
            ],
            "type": "Selection",
        }

    def test_selection_with_none_value(self):
        SELECTIONS = [("admin", "Admin"), ("regular-user", "Regular user")]

        registry = self.init_registry(
            simple_column, ColumnType=Selection, selections=SELECTIONS
        )
        t = registry.Test.insert()
        assert t.col is None

    @pytest.mark.skipif(
        sgdb_in(["MySQL", "MariaDB", "MsSQL"]), reason="ISSUE #90"
    )
    def test_selection_change_by_query(self):
        SELECTIONS = [("admin", "Admin"), ("regular-user", "Regular user")]

        registry = self.init_registry(
            simple_column, ColumnType=Selection, selections=SELECTIONS
        )
        registry.Test.insert(col=SELECTIONS[0][0])
        with pytest.raises(StatementError):
            registry.execute(
                registry.Test.update_sql_statement().values(
                    {"col": "bad value"}
                )
            )

    def test_selection_like_comparator(self):
        SELECTIONS = [("admin", "Admin"), ("regular-user", "Regular user")]

        registry = self.init_registry(
            simple_column, ColumnType=Selection, selections=SELECTIONS
        )
        Test = registry.Test
        t = Test.insert(col=SELECTIONS[0][0])
        t1 = Test.query().filter(Test.col.like("%admin%")).one()
        assert t is t1

    def test_selection_key_other_than_str(self):
        SELECTIONS = [(0, "Admin"), (1, "Regular user")]

        with pytest.raises(FieldException):
            self.init_registry(
                simple_column, ColumnType=Selection, selections=SELECTIONS
            )

    def test_selection_comparator(self):
        SELECTIONS = [("admin", "Admin"), ("regular-user", "Regular user")]

        registry = self.init_registry(
            simple_column, ColumnType=Selection, selections=SELECTIONS
        )
        registry.Test.insert(col=SELECTIONS[0][0])
        registry.Test.query().filter(
            registry.Test.col.in_(["admin", "regular-user"])
        ).first()

    def test_selection_use_method(self):
        SELECTIONS = [("admin", "Admin"), ("regular-user", "Regular user")]

        def add_selection():
            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                col = Selection(selections="get_selection")

                @classmethod
                def get_selection(cls):
                    return SELECTIONS

        registry = self.init_registry(add_selection)
        registry.Test.insert(col=SELECTIONS[0][0])
        registry.Test.query().filter(
            registry.Test.col.in_(["admin", "regular-user"])
        ).first()

    def test_json_update(self):
        registry = self.init_registry(simple_column, ColumnType=Json)
        test = registry.Test.insert(col={"a": "test"})
        test.col["b"] = "test"
        assert test.col == {"a": "test", "b": "test"}

    @pytest.mark.skipif(
        sgdb_in(["MariaDB", "MsSQL"]),
        reason="JSON is not existing in this SGDB",
    )
    def test_json_simple_filter(self):
        registry = self.init_registry(simple_column, ColumnType=Json)
        Test = registry.Test
        Test.insert(col={"a": "test"})
        Test.insert(col={"a": "test"})
        Test.insert(col={"b": "test"})
        assert (
            Test.query()
            .filter(Test.col["a"].cast(SA_String) == '"test"')
            .count()
            == 2
        )

    def test_json_null(self):
        registry = self.init_registry(simple_column, ColumnType=Json)
        Test = registry.Test
        Test.insert(col=None)
        Test.insert(col=None)
        Test.insert(col={"a": "test"})
        assert Test.query().filter(Test.col.is_(None)).count() == 2
        assert Test.query().filter(Test.col.isnot(None)).count() == 1

    def test_add_default_classmethod(self):
        val = "test"

        def add_in_registry():
            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                val = String(default="get_val")

                @classmethod
                def get_val(cls):
                    return val

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        assert t.val == val

    def test_add_default_without_classmethod(self):
        value = "test"

        def add_in_registry():
            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                val = String(default="get_val")

                def get_val(cls):
                    return value

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        assert t.val == "get_val"

    def test_add_default_by_var(self):
        value = "test"

        def add_in_registry():
            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                val = String(default=value)

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        assert t.val == value

    def test_add_default(self):
        def add_in_registry():
            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                val = String(default="value")

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        assert t.val == "value"

    def test_add_field_as_default(self):
        def add_in_registry():
            @register(Model)
            class Test:
                id = Integer(primary_key=True)
                val = String(default="val")

        registry = self.init_registry(add_in_registry)
        t = registry.Test.insert()
        assert t.val == "val"

    @pytest.mark.skipif(
        sgdb_in(["MySQL", "MariaDB", "MsSQL"]), reason="ISSUE #89"
    )
    def test_sequence(self):
        registry = self.init_registry(simple_column, ColumnType=Sequence)
        assert registry.Test.insert().col == "1"
        assert registry.Test.insert().col == "2"
        assert registry.Test.insert().col == "3"
        assert registry.Test.insert().col == "4"
        Seq = registry.System.Sequence
        assert Seq.query().filter(Seq.code == "Model.Test=>col").count() == 1

    @pytest.mark.skipif(
        sgdb_in(["MySQL", "MariaDB", "MsSQL"]), reason="ISSUE #89"
    )
    def test_sequence_with_primary_key(self):
        registry = self.init_registry(
            simple_column, ColumnType=Sequence, primary_key=True
        )
        assert registry.Test.insert().col == "1"
        assert registry.Test.insert().col == "2"

    @pytest.mark.skipif(
        sgdb_in(["MySQL", "MariaDB", "MsSQL"]), reason="ISSUE #89"
    )
    def test_sequence_with_code_and_formater(self):
        registry = self.init_registry(
            simple_column,
            ColumnType=Sequence,
            code="SO",
            formater="{code}-{seq:06d}",
        )
        try:
            with registry.begin_nested():
                assert registry.Test.insert().col == "SO-000001"
                assert registry.Test.insert().col == "SO-000002"
                assert registry.Test.insert().col == "SO-000003"
                raise Exception("test")

        except Exception:
            pass

        assert registry.Test.insert().col == "SO-000004"
        registry.flush()
        Seq = registry.System.Sequence
        assert Seq.query().filter(Seq.code == "SO").one()

    def test_sequence_with_foreign_key(self):
        with pytest.raises(FieldException):
            self.init_registry(
                simple_column,
                ColumnType=Sequence,
                foreign_key=Model.System.Blok.use("name"),
            )

    def test_sequence_with_default(self):
        with pytest.raises(FieldException):
            self.init_registry(
                simple_column, ColumnType=Sequence, default="default value"
            )

    def test_sequence_with_nogap(self):
        registry = self.init_registry(
            simple_column,
            ColumnType=Sequence,
            code="SO-NO-GAP",
            formater="{code}-{seq:06d}",
            no_gap=True,
        )
        try:
            with registry.begin_nested():
                assert registry.Test.insert().col == "SO-NO-GAP-000001"
                assert registry.Test.insert().col == "SO-NO-GAP-000002"
                assert registry.Test.insert().col == "SO-NO-GAP-000003"
                raise Exception("test")

        except Exception:
            pass

        assert registry.Test.insert().col == "SO-NO-GAP-000001"
        Seq = registry.System.Sequence
        seq = Seq.query().filter(Seq.code == "SO-NO-GAP").one()
        assert seq.number == 1

    @pytest.mark.skipif(not has_colour, reason="colour is not installed")
    def test_color(self):
        color = "#F5F5F5"
        registry = self.init_registry(simple_column, ColumnType=Color)
        test = registry.Test.insert(col=color)
        assert test.col.hex == colour.Color(color).hex

    @pytest.mark.skipif(not has_colour, reason="colour is not installed")
    def test_setter_color(self):
        color = "#F5F5F5"
        registry = self.init_registry(simple_column, ColumnType=Color)
        test = registry.Test.insert()
        test.col = color
        assert test.col.hex == colour.Color(color).hex

    def test_uuid_binary_3(self):
        from uuid import NAMESPACE_DNS, uuid3

        uuid = uuid3(NAMESPACE_DNS, "python.org")
        registry = self.init_registry(simple_column, ColumnType=UUID)
        test = registry.Test.insert(col=uuid)
        assert test.col is uuid

    def test_uuid_binary_4(self):
        from uuid import uuid4

        uuid = uuid4()
        registry = self.init_registry(simple_column, ColumnType=UUID)
        test = registry.Test.insert(col=uuid)
        assert test.col is uuid

    def test_uuid_binary_5(self):
        from uuid import NAMESPACE_DNS, uuid5

        uuid = uuid5(NAMESPACE_DNS, "python.org")
        registry = self.init_registry(simple_column, ColumnType=UUID)
        test = registry.Test.insert(col=uuid)
        assert test.col is uuid

    def test_uuid_char32(self):
        uuid = uuid1()
        registry = self.init_registry(
            simple_column, ColumnType=UUID, binary=False
        )
        test = registry.Test.insert(col=uuid)
        assert test.col is uuid

    @pytest.mark.skipif(not has_furl, reason="furl is not installed")
    def test_setter_URL(self):
        f = "http://doc.anyblok.org"
        registry = self.init_registry(simple_column, ColumnType=URL)
        test = registry.Test.insert()
        test.col = f
        assert test.col.url == f

    @pytest.mark.skipif(not has_furl, reason="furl is not installed")
    def test_URL_2(self):
        f = "http://doc.anyblok.org"
        registry = self.init_registry(simple_column, ColumnType=URL)
        test = registry.Test.insert(col=f)
        assert test.col.url == f

    @pytest.mark.skipif(not has_furl, reason="furl is not installed")
    def test_URL_3(self):
        f = "http://doc.anyblok.org"
        registry = self.init_registry(simple_column, ColumnType=URL)
        registry.Test.insert(col=f)
        Test = registry.Test
        test = Test.query().filter(Test.col == f).one()
        assert test.col.url == f

    @pytest.mark.skipif(not has_furl, reason="furl is not installed")
    def test_URL_4(self):
        f = furl.furl("http://doc.anyblok.org")
        registry = self.init_registry(simple_column, ColumnType=URL)
        registry.Test.insert(col=f)
        Test = registry.Test
        test = Test.query().filter(Test.col == f).one()
        assert test.col.url == f.url

    @pytest.mark.skipif(
        not has_phonenumbers, reason="phonenumbers is not installed"
    )
    def test_phonenumbers_at_insert(self):
        registry = self.init_registry(simple_column, ColumnType=PhoneNumber)
        test = registry.Test.insert(col="+120012301")
        assert test.col.national == "20012301"
        getted = registry.execute(text("Select col from test")).fetchone()[0]
        assert getted == "+120012301"

    @pytest.mark.skipif(
        not has_phonenumbers, reason="phonenumbers is not installed"
    )
    def test_phonenumbers_at_setter(self):
        registry = self.init_registry(simple_column, ColumnType=PhoneNumber)
        test = registry.Test.insert()
        test.col = "+120012301"
        assert test.col.national == "20012301"
        registry.flush()
        getted = registry.execute(text("Select col from test")).fetchone()[0]
        assert getted == "+120012301"

    @pytest.mark.skipif(
        not has_phonenumbers, reason="phonenumbers is not installed"
    )
    def test_phonenumbers_obj_at_insert(self):
        registry = self.init_registry(simple_column, ColumnType=PhoneNumber)
        col = PN("+120012301", None)
        test = registry.Test.insert(col=col)
        assert test.col == col
        getted = registry.execute(text("Select col from test")).fetchone()[0]
        assert getted == "+120012301"

    @pytest.mark.skipif(
        not has_phonenumbers, reason="phonenumbers is not installed"
    )
    def test_phonenumbers_obj_at_setter(self):
        registry = self.init_registry(simple_column, ColumnType=PhoneNumber)
        test = registry.Test.insert()
        test.col = PN("+120012301", None)
        assert test.col.national == "20012301"
        registry.flush()
        getted = registry.execute(text("Select col from test")).fetchone()[0]
        assert getted == "+120012301"

    @pytest.mark.skipif(
        not has_phonenumbers, reason="phonenumbers is not installed"
    )
    def test_phonenumbers_obj_at_setter_with_empty_value(self):
        registry = self.init_registry(simple_column, ColumnType=PhoneNumber)
        test = registry.Test.insert()
        test.col = ""
        assert test.col == ""
        registry.flush()
        assert (
            registry.execute(text("Select col from test")).fetchone()[0] == ""
        )

    def test_email_at_setter(self):
        registry = self.init_registry(simple_column, ColumnType=Email)
        test = registry.Test.insert()
        test.col = "John.Smith@foo.com"
        assert test.col == "john.smith@foo.com"
        assert (
            registry.Test.query().filter_by(col="John.Smith@foo.com").count()
            == 1
        )

    @pytest.mark.skipif(not has_pycountry, reason="pycountry is not installed")
    def test_pycoundtry_at_insert(self):
        registry = self.init_registry(simple_column, ColumnType=Country)
        test = registry.Test.insert(col="FR")
        assert test.col is pycountry.countries.get(alpha_2="FR")
        assert test.col.name == "France"
        assert (
            registry.execute(text("Select col from test")).fetchone()[0]
            == "FRA"
        )

    @pytest.mark.skipif(not has_pycountry, reason="pycountry is not installed")
    def test_pycoundtry_at_insert_with_obj(self):
        registry = self.init_registry(simple_column, ColumnType=Country)
        fr = pycountry.countries.get(alpha_2="FR")
        test = registry.Test.insert(col=fr)
        assert test.col is pycountry.countries.get(alpha_2="FR")
        assert test.col.name == "France"
        assert (
            registry.execute(text("Select col from test")).fetchone()[0]
            == "FRA"
        )

    @pytest.mark.skipif(not has_pycountry, reason="pycountry is not installed")
    def test_pycoundtry_at_insert_with_alpha_3(self):
        registry = self.init_registry(
            simple_column, ColumnType=Country, mode="alpha_3"
        )
        test = registry.Test.insert(col="FRA")
        assert test.col is pycountry.countries.get(alpha_2="FR")
        assert test.col.name == "France"
        assert (
            registry.execute(text("Select col from test")).fetchone()[0]
            == "FRA"
        )

    @pytest.mark.skipif(not has_pycountry, reason="pycountry is not installed")
    def test_pycoundtry_at_insert_with_object(self):
        registry = self.init_registry(simple_column, ColumnType=Country)
        fr = pycountry.countries.get(alpha_2="FR")
        test = registry.Test.insert(col=fr)
        assert test.col is fr
        assert test.col.name == "France"
        assert (
            registry.execute(text("Select col from test")).fetchone()[0]
            == "FRA"
        )

    @pytest.mark.skipif(not has_pycountry, reason="pycountry is not installed")
    def test_pycoundtry_at_update(self):
        registry = self.init_registry(simple_column, ColumnType=Country)
        test = registry.Test.insert()
        test.col = "FR"
        registry.flush()
        assert test.col is pycountry.countries.get(alpha_2="FR")
        assert test.col.name == "France"
        assert (
            registry.execute(text("Select col from test")).fetchone()[0]
            == "FRA"
        )

    @pytest.mark.skipif(not has_pycountry, reason="pycountry is not installed")
    def test_pycoundtry_at_update_with_alpha_3(self):
        registry = self.init_registry(
            simple_column, ColumnType=Country, mode="alpha_3"
        )
        test = registry.Test.insert()
        test.col = "FRA"
        registry.flush()
        assert test.col is pycountry.countries.get(alpha_2="FR")
        assert test.col.name == "France"
        assert (
            registry.execute(text("Select col from test")).fetchone()[0]
            == "FRA"
        )

    @pytest.mark.skipif(not has_pycountry, reason="pycountry is not installed")
    def test_pycoundtry_at_update_with_object(self):
        registry = self.init_registry(simple_column, ColumnType=Country)
        fr = pycountry.countries.get(alpha_2="FR")
        test = registry.Test.insert()
        test.col = fr
        registry.flush()
        assert test.col is fr
        assert test.col.name == "France"
        assert (
            registry.execute(text("Select col from test")).fetchone()[0]
            == "FRA"
        )

    @pytest.mark.skipif(not has_pycountry, reason="pycountry is not installed")
    def test_pycoundtry_query_is_with_object(self):
        registry = self.init_registry(simple_column, ColumnType=Country)
        Test = registry.Test
        fr = pycountry.countries.get(alpha_2="FR")
        Test.insert(col="FR")
        assert Test.query().filter(Test.col == fr).count() == 1

    @pytest.mark.skipif(not has_pycountry, reason="pycountry is not installed")
    def test_pycoundtry_query_is_with_alpha_3(self):
        registry = self.init_registry(simple_column, ColumnType=Country)
        Test = registry.Test
        Test.insert(col="FR")
        assert Test.query().filter(Test.col == "FRA").count() == 1

    @pytest.mark.skipif(not has_pycountry, reason="pycountry is not installed")
    def test_pycoundtry_query_insert_wrong(self):
        registry = self.init_registry(simple_column, ColumnType=Country)
        with pytest.raises(LookupError):
            registry.Test.insert(col="WG")

    @pytest.mark.skipif(not has_pycountry, reason="pycountry is not installed")
    @pytest.mark.skipif(
        sgdb_in(["MySQL", "MariaDB", "MsSQL"]), reason="ISSUE #90"
    )
    def test_pycoundtry_query_insert_by_wrong_query(self):
        registry = self.init_registry(simple_column, ColumnType=Country)
        with pytest.raises(Exception):
            registry.execute(text("insert into test (col) values ('WG2')"))

    @pytest.mark.skipif(
        not has_cryptography, reason="cryptography is not installed"
    )
    def test_insert_encrypt_key_columns(self, column_definition):
        column, value, kwargs = column_definition
        registry = self.init_registry(
            simple_column, ColumnType=column, encrypt_key="secretkey", **kwargs
        )
        test = registry.Test.insert(col=value)
        registry.session.commit()
        if column is Enum:
            assert test.col.value == value
        else:
            assert test.col == value

        res = registry.execute(
            text("select col from test where id = %s" % test.id)
        )
        res = res.fetchall()[0][0]
        assert res != test.col

    def test_foreign_key_on_mapper_issue_112(self):
        def add_in_registry():
            @Declarations.register(Declarations.Model)
            class Template:
                code = String(primary_key=True, db_column_name="ProductId")

            @Declarations.register(Declarations.Model)
            class Item:
                id = Integer(primary_key=True, db_column_name="ProductDetailId")
                template_code = String(
                    db_column_name="ProductId",
                    foreign_key=Model.Template.use("code"),
                )

        registry = self.init_registry(add_in_registry)
        registry.Template.insert(code="test")
        registry.Item.insert(template_code="test")

        with pytest.raises(Exception):
            registry.Item.insert(template_code="other")

    def test_foreign_key_on_mapper_issue_112_with_schema(self, db_schema):
        def add_in_registry():
            @Declarations.register(Declarations.Model)
            class Template:
                __db_schema__ = "test_db_column_schema"

                code = String(primary_key=True, db_column_name="ProductId")

            @Declarations.register(Declarations.Model)
            class Item:
                __db_schema__ = "test_db_column_schema"

                id = Integer(primary_key=True, db_column_name="ProductDetailId")
                template_code = String(
                    db_column_name="ProductId",
                    foreign_key=Model.Template.use("code"),
                )

        registry = self.init_registry(add_in_registry)
        registry.Template.insert(code="test")
        registry.Item.insert(template_code="test")

        with pytest.raises(Exception):
            registry.Item.insert(template_code="other")

    @pytest.mark.parametrize("cls", [Float, Decimal])
    def test_decimal_as_primary_key_should_raises(self, cls):
        with pytest.raises(FieldException) as ex:
            self.init_registry(simple_column, ColumnType=cls, primary_key=True)

        assert (
            f"{cls} column `Model.Test.col` are not " f"allowed as primary key"
        ) == str(ex.value), "Column name should be part of raised message"


@pytest.fixture(params=time_params, scope="class")
def registry_dt(request):
    reset_db()
    registry = init_registry(simple_column, ColumnType=request.param)
    request.addfinalizer(registry.close)
    return registry


@pytest.mark.relationship
class TestColumnDT:
    @pytest.fixture(autouse=True)
    def transact(self, request, registry_dt):
        transaction = registry_dt.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_none_value(self, registry_dt):
        test = registry_dt.Test.insert(col=None)
        assert test.col is None

    def test_str_conversion_1(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = datetime.datetime.now().replace(tzinfo=timezone)
        test = registry_dt.Test.insert(
            col=now.strftime("%Y-%m-%d %H:%M:%S.%f%z")
        )
        assert test.col == now

    def test_str_conversion_2(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = timezone.localize(datetime.datetime.now())
        test = registry_dt.Test.insert(
            col=now.strftime("%Y-%m-%d %H:%M:%S.%f%Z")
        )
        assert test.col == now

    def test_str_conversion_3(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = timezone.localize(datetime.datetime.now())
        test = registry_dt.Test.insert(col=now.strftime("%Y-%m-%d %H:%M:%S.%f"))
        assert test.col == now

    def test_str_conversion_4(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = timezone.localize(datetime.datetime.now())
        test = registry_dt.Test.insert(col=now.strftime("%Y-%m-%d %H:%M:%S"))
        assert test.col == now.replace(microsecond=0)

    def test_by_property(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = datetime.datetime.now().replace(tzinfo=timezone)
        test = registry_dt.Test.insert()
        test.col = now
        assert test.col == now

    def test_by_property_none_value(self, registry_dt):
        test = registry_dt.Test.insert()
        test.col = None
        assert test.col is None

    def test_str_conversion_1_by_property(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = datetime.datetime.now().replace(tzinfo=timezone)
        test = registry_dt.Test.insert()
        test.col = now.strftime("%Y-%m-%d %H:%M:%S.%f%z")
        assert test.col == now

    def test_str_conversion_2_by_property(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = timezone.localize(datetime.datetime.now())
        test = registry_dt.Test.insert()
        test.col = now.strftime("%Y-%m-%d %H:%M:%S.%f%Z")
        assert test.col == now

    def test_str_conversion_3_by_property(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = timezone.localize(datetime.datetime.now())
        test = registry_dt.Test.insert()
        test.col = now.strftime("%Y-%m-%d %H:%M:%S.%f")
        assert test.col == now

    def test_str_conversion_4_by_property(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = timezone.localize(datetime.datetime.now())
        test = registry_dt.Test.insert()
        test.col = now.strftime("%Y-%m-%d %H:%M:%S")
        assert test.col == now.replace(microsecond=0)

    def test_by_query(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        d = datetime.datetime(2020, 7, 3, 18, 59, 0)
        d = add_timezone_on_datetime(d, timezone)
        Test = registry_dt.Test
        test = Test.insert()
        Test.execute_sql_statement(Test.update_sql_statement().values(col=d))
        registry_dt.refresh(test)
        assert test.col == d

    def test_by_query_none_value(self, registry_dt):
        Test = registry_dt.Test
        test = Test.insert()
        Test.execute_sql_statement(Test.update_sql_statement().values(col=None))
        assert test.col is None

    @pytest.mark.skipif(
        sgdb_in(["MySQL", "MariaDB", "MsSQL"]), reason="ISSUE #87"
    )
    def test_str_conversion_1_by_query(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = datetime.datetime.now().replace(tzinfo=timezone)
        Test = registry_dt.Test
        test = Test.insert()
        Test.execute_sql_statement(
            Test.update_sql_statement().values(
                col=now.strftime("%Y-%m-%d %H:%M:%S.%f%z")
            )
        )
        registry_dt.expire(test, ["col"])
        assert test.col == now

    @pytest.mark.skipif(
        sgdb_in(["MySQL", "MariaDB", "MsSQL"]), reason="ISSUE #87"
    )
    def test_str_conversion_2_by_query(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = timezone.localize(datetime.datetime.now())
        Test = registry_dt.Test
        test = Test.insert()
        Test.execute_sql_statement(
            Test.update_sql_statement().values(
                col=now.strftime("%Y-%m-%d %H:%M:%S.%f%Z")
            )
        )
        registry_dt.expire(test, ["col"])
        assert test.col == now

    @pytest.mark.skipif(
        sgdb_in(["MySQL", "MariaDB", "MsSQL"]), reason="ISSUE #87"
    )
    def test_str_conversion_3_by_query(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = timezone.localize(datetime.datetime.now())
        Test = registry_dt.Test
        test = Test.insert()
        Test.execute_sql_statement(
            Test.update_sql_statement().values(
                col=now.strftime("%Y-%m-%d %H:%M:%S.%f")
            )
        )
        registry_dt.expire(test, ["col"])
        assert test.col == now

    @pytest.mark.skipif(
        sgdb_in(["MySQL", "MariaDB", "MsSQL"]), reason="ISSUE #87"
    )
    def test_datetime_str_conversion_4_by_query(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = timezone.localize(datetime.datetime.now())
        Test = registry_dt.Test
        test = Test.insert()
        Test.execute_sql_statement(
            Test.update_sql_statement().values(
                col=now.strftime("%Y-%m-%d %H:%M:%S")
            )
        )
        registry_dt.expire(test, ["col"])
        assert test.col == now.replace(microsecond=0)

    @pytest.mark.skipif(
        sgdb_in(["MySQL", "MariaDB", "MsSQL"]), reason="ISSUE #87"
    )
    def test_datetime_by_query_filter(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = datetime.datetime.now().replace(tzinfo=timezone)
        test = registry_dt.Test.insert(col=now)
        Test = registry_dt.Test
        assert Test.query().filter(Test.col == now).one() is test

    @pytest.mark.skipif(
        sgdb_in(["MySQL", "MariaDB", "MsSQL"]), reason="ISSUE #87"
    )
    def test_datetime_str_conversion_1_by_query_filter(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = datetime.datetime.now().replace(tzinfo=timezone)
        test = registry_dt.Test.insert(col=now)
        Test = registry_dt.Test
        assert (
            Test.query()
            .filter(Test.col == now.strftime("%Y-%m-%d %H:%M:%S.%f%z"))
            .one()
            is test
        )

    @pytest.mark.skipif(
        sgdb_in(["MySQL", "MariaDB", "MsSQL"]), reason="ISSUE #87"
    )
    def test_str_conversion_2_by_query_filter(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = timezone.localize(datetime.datetime.now())
        test = registry_dt.Test.insert(col=now)
        Test = registry_dt.Test
        assert (
            Test.query()
            .filter(Test.col == now.strftime("%Y-%m-%d %H:%M:%S.%f%Z"))
            .one()
            is test
        )

    @pytest.mark.skipif(
        sgdb_in(["MySQL", "MariaDB", "MsSQL"]), reason="ISSUE #87"
    )
    def test_str_conversion_3_by_query_filter(self, registry_dt):
        timezone = pytz.timezone(time.tzname[0])
        now = timezone.localize(datetime.datetime.now())
        test = registry_dt.Test.insert(col=now)
        Test = registry_dt.Test
        assert (
            Test.query()
            .filter(Test.col == now.strftime("%Y-%m-%d %H:%M:%S.%f"))
            .one()
            is test
        )


def add_modelselection_in_registry():
    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        col = ModelSelection(validator="my_validator")
        col2 = ModelSelection(default=Model.System.Blok)

        @classmethod
        def my_validator(cls, Model):
            return Model.__registry_name__ == "Model.System.Blok"


@pytest.fixture(scope="class")
def registry_modelselection(request, bloks_loaded):
    reset_db()
    registry = init_registry(add_modelselection_in_registry)
    request.addfinalizer(registry.close)
    return registry


@pytest.mark.relationship
class TestColumnModelSelection:
    @pytest.fixture(autouse=True)
    def transact(self, request, registry_modelselection):
        transaction = registry_modelselection.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_setter_use_method(self, registry_modelselection):
        test = registry_modelselection.Test.insert()
        assert test.col is None
        assert test.col2 == "Model.System.Blok"

        with pytest.raises(FieldException):
            test.col = "Model.System"

        test.col = "Model.System.Blok"
        assert test.col.Model is registry_modelselection.System.Blok

    def test_description(self, registry_modelselection):
        description = registry_modelselection.Test.fields_description("col")[
            "col"
        ]
        assert description == {
            "id": "col",
            "label": "Col",
            "model": None,
            "nullable": True,
            "primary_key": False,
            "selections": [
                ("Model.System.Blok", "Model.System.Blok"),
            ],
            "type": "ModelSelection",
        }

    def test_description2(self, registry_modelselection):
        description = registry_modelselection.Test.fields_description(
            ["col", "col2"]
        )
        assert (
            description["col"]["selections"]
            != description["col2"]["selections"]
        )

    def test_setter_model_validator_all(self, registry_modelselection):
        assert model_validator_all(registry_modelselection.System) is True

    def test_modelselection_setter_model_validator_is_sql(
        self, registry_modelselection
    ):
        assert model_validator_is_sql(registry_modelselection.System) is False
        assert (
            model_validator_is_sql(registry_modelselection.System.Blok) is True
        )

    def test_modelselection_setter_model_validator_is_not_sql(
        self, registry_modelselection
    ):
        assert (
            model_validator_is_not_sql(registry_modelselection.System) is True
        )
        assert (
            model_validator_is_not_sql(registry_modelselection.System.Blok)
            is False
        )

    def test_modelselection_setter_model_validator_is_view(
        self, registry_modelselection
    ):
        assert model_validator_is_view(registry_modelselection.System) is False
        assert (
            model_validator_is_view(registry_modelselection.System.Blok)
            is False
        )

    def test_modelselection_setter_model_validator_is_not_view(
        self, registry_modelselection
    ):
        assert (
            model_validator_is_not_view(registry_modelselection.System) is True
        )
        assert (
            model_validator_is_not_view(registry_modelselection.System.Blok)
            is True
        )

    def test_modelselection_setter_model_validator_in_namespace(
        self, registry_modelselection
    ):
        assert (
            model_validator_in_namespace(Model.System)(
                registry_modelselection.Test
            )
            is False
        )
        assert (
            model_validator_in_namespace(Model.System)(
                registry_modelselection.System
            )
            is False
        )
        assert (
            model_validator_in_namespace(Model.System)(
                registry_modelselection.System.Blok
            )
            is True
        )

    def test_modelselection_setter_model_validator_merge(
        self, registry_modelselection
    ):
        validator = merge_validators(
            model_validator_is_sql,
            model_validator_is_not_view,
            model_validator_in_namespace(Model.System),
        )
        assert validator(registry_modelselection.Test) is False
        assert validator(registry_modelselection.System) is False
        assert validator(registry_modelselection.System.Blok) is True

    def test_search_with_str(self, registry_modelselection):
        test = registry_modelselection.Test.insert()
        test.col = "Model.System.Blok"
        registry_modelselection.flush()
        test2 = (
            registry_modelselection.Test.query()
            .filter_by(col="Model.System.Blok")
            .one()
        )
        assert test is test2

    def test_search_with_model(self, registry_modelselection):
        test = registry_modelselection.Test.insert()
        test.col = registry_modelselection.System.Blok
        registry_modelselection.flush()
        test2 = (
            registry_modelselection.Test.query()
            .filter_by(col=registry_modelselection.System.Blok)
            .one()
        )
        assert test is test2

    def test_search_with_declaration_model(self, registry_modelselection):
        test = registry_modelselection.Test.insert()
        test.col = Model.System.Blok
        registry_modelselection.flush()
        test2 = (
            registry_modelselection.Test.query()
            .filter_by(col=Model.System.Blok)
            .one()
        )
        assert test is test2


def add_modelfieldselection_in_registry():
    @register(Model)
    class Test:
        id = Integer(primary_key=True)
        col = ModelFieldSelection(
            model_validator="my_model_validator",
            field_validator="my_field_validator",
        )
        col2 = ModelFieldSelection(default=Model.System.Blok.use("name"))

        @classmethod
        def my_model_validator(cls, Model):
            return Model.__registry_name__ == "Model.System.Blok"

        @classmethod
        def my_field_validator(cls, field):
            return field.anyblok_field_name == "name"


@pytest.fixture(scope="class")
def registry_modelfieldselection(request, bloks_loaded):
    reset_db()
    registry = init_registry(add_modelfieldselection_in_registry)
    request.addfinalizer(registry.close)
    return registry


@pytest.mark.relationship
class TestColumnModelFieldSelection:
    @pytest.fixture(autouse=True)
    def transact(self, request, registry_modelfieldselection):
        transaction = registry_modelfieldselection.begin_nested()
        request.addfinalizer(transaction.rollback)
        return

    def test_setter_use_method(self, registry_modelfieldselection):
        test = registry_modelfieldselection.Test.insert()
        assert test.col is None
        assert test.col2 == "Model.System.Blok => name"

        with pytest.raises(FieldException):
            test.col = "Model.System.Blok => version"

        test.col = "Model.System.Blok => name"
        assert test.col.field == registry_modelfieldselection.System.Blok.name

    def test_description(self, registry_modelfieldselection):
        description = registry_modelfieldselection.Test.fields_description(
            "col"
        )["col"]
        assert description == {
            "id": "col",
            "label": "Col",
            "model": None,
            "nullable": True,
            "primary_key": False,
            "selections": [
                ("Model.System.Blok => name", "Model.System.Blok : name"),
            ],
            "type": "ModelFieldSelection",
        }

    def test_description2(self, registry_modelfieldselection):
        description = registry_modelfieldselection.Test.fields_description(
            ["col", "col2"]
        )
        assert (
            description["col"]["selections"]
            != description["col2"]["selections"]
        )

    def test_setter_field_validator_all(self, registry_modelfieldselection):
        assert (
            field_validator_all(registry_modelfieldselection.System.Blok.name)
            is True
        )

    def test_setter_field_validator_is_field(
        self, registry_modelfieldselection
    ):
        assert (
            field_validator_is_field(
                registry_modelfieldselection.System.Blok.logo
            )
            is True
        )

    def test_setter_field_validator_is_not_field(
        self, registry_modelfieldselection
    ):
        assert (
            field_validator_is_not_field(
                registry_modelfieldselection.System.Blok.logo
            )
            is False
        )

    def test_setter_field_validator_is_column(
        self, registry_modelfieldselection
    ):
        assert (
            field_validator_is_column(
                registry_modelfieldselection.System.Blok.name
            )
            is True
        )

    def test_setter_field_validator_is_not_column(
        self, registry_modelfieldselection
    ):
        assert (
            field_validator_is_not_column(
                registry_modelfieldselection.System.Blok.name
            )
            is False
        )

    def test_setter_field_validator_is_relationship(
        self, registry_modelfieldselection
    ):
        assert (
            field_validator_is_relationship(
                registry_modelfieldselection.System.Blok.name
            )
            is False
        )

    def test_setter_field_validator_is_not_relationship(
        self, registry_modelfieldselection
    ):
        assert (
            field_validator_is_not_relationship(
                registry_modelfieldselection.System.Blok.name
            )
            is True
        )

    def test_setter_field_validator_is_named(
        self, registry_modelfieldselection
    ):
        assert (
            field_validator_is_named("name")(
                registry_modelfieldselection.System.Blok.name
            )
            is True
        )

    def test_setter_field_validator_is_from_types(
        self, registry_modelfieldselection
    ):
        assert (
            field_validator_is_from_types(String, Many2One)(
                registry_modelfieldselection.System.Blok.name
            )
            is True
        )

    def test_modelselection_setter_validator_merge(
        self, registry_modelfieldselection
    ):
        validator = merge_validators(
            field_validator_is_column,
            field_validator_is_from_types(String),
        )
        assert validator(registry_modelfieldselection.Test.id) is False
        assert validator(registry_modelfieldselection.System.Blok.name) is True

    def test_search_with_str(self, registry_modelfieldselection):
        test = registry_modelfieldselection.Test.insert()
        test.col = "Model.System.Blok => name"
        registry_modelfieldselection.flush()
        test2 = (
            registry_modelfieldselection.Test.query()
            .filter_by(col="Model.System.Blok => name")
            .one()
        )
        assert test is test2

    def test_search_with_model(self, registry_modelfieldselection):
        test = registry_modelfieldselection.Test.insert()
        test.col = registry_modelfieldselection.System.Blok.name
        registry_modelfieldselection.flush()
        test2 = (
            registry_modelfieldselection.Test.query()
            .filter_by(
                col=fieldToModelAttribute(
                    registry_modelfieldselection.System.Blok.name
                )
            )
            .one()
        )
        assert test is test2

    def test_search_with_declaration_model(self, registry_modelfieldselection):
        test = registry_modelfieldselection.Test.insert()
        test.col = Model.System.Blok.use("name")
        registry_modelfieldselection.flush()
        test2 = (
            registry_modelfieldselection.Test.query()
            .filter_by(col=Model.System.Blok.use("name"))
            .one()
        )
        assert test is test2


class TestColumnsAutoDoc:
    def call_autodoc(self, column, **kwargs):
        col = column(**kwargs)
        col.autodoc()

    def test_autodoc(self, column_definition):
        column, _, kwargs = column_definition
        self.call_autodoc(column, **kwargs)

    @pytest.mark.skipif(
        not has_cryptography, reason="cryptography is not installed"
    )
    def test_autodoc_with_encrypt_key(self, column_definition):
        column, _, kwargs = column_definition
        self.call_autodoc(column, encrypt_key="secretkey", **kwargs)

    def test_string_with_size(self):
        self.call_autodoc(String, size=100)

    @pytest.mark.skipif(not has_passlib, reason="passlib is not installed")
    def test_password(self):
        self.call_autodoc(Password, crypt_context={"schemes": ["md5_crypt"]})

    def test_datetime_with_default_timezone_tz(self):
        timezone = pytz.timezone("Asia/Tokyo")
        self.call_autodoc(DateTime, default_timezone=timezone)

    def test_datetime_with_default_timezone_str(self):
        self.call_autodoc(DateTime, default_timezone="Asia/Tokyo")

    def test_add_default(self):
        self.call_autodoc(String, default="get_val")

    def test_add_default_by_var(self):
        value = "test"
        self.call_autodoc(String, default=value)

    def test_sequence(self):
        self.call_autodoc(Sequence)

    def test_sequence_with_primary_key(self):
        self.call_autodoc(Sequence, primary_key=True)

    def test_uuid_char32(self):
        self.call_autodoc(UUID, binary=False)

    @pytest.mark.skipif(not has_pycountry, reason="pycountry is not installed")
    def test_pycoundtry_at_insert_with_alpha_3(self):
        self.call_autodoc(Country, mode="alpha_3")

    def test_modelselection(self):
        self.call_autodoc(ModelSelection)


class Test_convert_string_to_datetime:
    def test_with_none(self):
        assert convert_string_to_datetime(None) is None

    def test_with_datetime(self):
        now = datetime.datetime.now()
        assert convert_string_to_datetime(now) is now

    def test_with_date(self):
        today = datetime.date.today()
        now = datetime.datetime.combine(today, datetime.datetime.min.time())
        assert convert_string_to_datetime(today) == now

    def test_with_other(self):
        with pytest.raises(FieldException):
            convert_string_to_datetime(1)


class TestCompareColumn:
    def same_type(self, col1, col2):
        CompareType.validate(
            ModelAttribute("Test1", "col1"),
            col1,
            ModelAttribute("Test2", "col2"),
            col2,
        )

    def diff_type(self, col1, col2):
        with pytest.raises(FieldException):
            CompareType.validate(
                ModelAttribute("Test1", "col1"),
                col1,
                ModelAttribute("Test2", "col2"),
                col2,
            )

    def test_compare_default_method_on_same_type(self):
        self.same_type(Integer(), Integer())

    def test_compare_default_method_on_different_type(self):
        self.diff_type(Integer(), BigInteger())

    def test_string_to_string_with_default_size(self):
        self.same_type(String(), String())

    def test_string_to_string_with_diff_size(self):
        self.diff_type(String(size=10), String(size=20))

    def test_string_to_selection_with_default_size(self):
        self.same_type(String(), Selection(selections={"foo": "Bar"}))

    def test_string_to_selection_with_diff_size(self):
        self.diff_type(
            String(size=10), Selection(selections={"foo": "Bar"}, size=20)
        )

    def test_string_to_sequence_with_default_size(self):
        self.same_type(String(), Sequence())

    def test_string_to_sequence_with_diff_size(self):
        self.diff_type(String(size=10), Sequence(size=20))

    @pytest.mark.skipif(not has_colour, reason="colour is not installed")
    def test_string_to_color_with_default_size(self):
        self.same_type(String(size=10), Color(size=10))

    @pytest.mark.skipif(not has_colour, reason="colour is not installed")
    def test_string_to_color_with_diff_size(self):
        self.diff_type(String(size=10), Color(size=20))
