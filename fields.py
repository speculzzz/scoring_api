import re
from datetime import datetime


class BaseField(object):
    def __init__(self, required=True, nullable=False):
        self._required = required
        self._nullable = nullable
        self._attr_name = None

    def __set_name__(self, owner, name):
        self._attr_name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self._attr_name)

    def __set__(self, instance, value):
        if value is None:
            if not self._nullable:
                raise ValueError(f"{self.__class__.__name__} cannot be None (nullable=False)")
            if self._required:
                raise ValueError(f"{self.__class__.__name__} is required (required=True)")
        elif not value:
            if not self._nullable and isinstance(value, (str, list, dict)):
                raise ValueError(f"{self.__class__.__name__} cannot be empty (nullable=False)")

        instance.__dict__[self._attr_name] = value

    def __delete__(self, instance):
        instance.__dict__.pop(self._attr_name, None)


class CharField(BaseField):
    def __init__(self, required=True, nullable=False, max_length=255):
        super().__init__(required=required, nullable=nullable)
        self._max_length = max_length

    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value is not None:
            if not isinstance(value, str):
                raise ValueError(f"Value must be a string, not {type(value).__name__}")
            if len(value) > self._max_length:
                raise ValueError(f"Value exceeds maximum length of {self._max_length} characters")


class EmailField(CharField):
    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value is not None and not self._is_valid_email(value):
            raise ValueError("Invalid email address")

    def _is_valid_email(self, email):
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(pattern, email) is not None


class PhoneField(BaseField):
    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value is not None:
            if isinstance(value, int):
                value = str(int(value))
                instance.__dict__[self._attr_name] = value
            if not isinstance(value, str):
                raise ValueError(f"{self.__class__.__name__} must be a string or number, not {type(value).__name__}")
            if len(value) != 11:
                raise ValueError(f"{self.__class__.__name__} must be 11 characters long")
            if not value.startswith("7"):
                raise ValueError(f"{self.__class__.__name__} must start with 7")


class DateField(CharField):
    def __init__(self, required=True, nullable=False):
        super().__init__(required=required, nullable=nullable, max_length=10)

    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value is not None:
            if not re.match(r"^\d{2}\.\d{2}\.\d{4}$", value):
                raise ValueError("Date must be in format DD.MM.YYYY")
            if not self._is_valid_date(value):
                raise ValueError(f"Invalid date: {value}")

    def _is_valid_date(self, date_str):
        try:
            datetime.strptime(date_str, "%d.%m.%Y")
            return True
        except ValueError:
            return False


class BirthDayField(DateField):
    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value is not None:
            today = datetime.today()
            birth_date = datetime.strptime(value, "%d.%m.%Y")
            if birth_date > today:
                raise ValueError("Birthday cannot be in the future")
            if (today - birth_date).days > 120 * 365:
                raise ValueError("Age cannot be more than 120 years")


class GenderField(BaseField):
    UNKNOWN = 0
    MALE = 1
    FEMALE = 2

    GENDERS = {
        UNKNOWN: "unknown",
        MALE: "male",
        FEMALE: "female",
    }

    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value is not None:
            if value not in self.GENDERS.keys():
                raise ValueError(f"Gender must be one of {list(self.GENDERS.keys())}")


class ClientIDsField(BaseField):
    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value is not None:
            if not isinstance(value, list):
                raise ValueError(f"Client IDs must be a list, not {type(value).__name__}")
            if not all(isinstance(item, int) and item >= 0 for item in value):
                raise ValueError("All items in Client IDs must be non-negative integers")


class ArgumentsField(BaseField):
    ALLOWED_FIELDS = {
        "phone": PhoneField,
        "email": EmailField,
        "gender": GenderField,
        "date": DateField,
        "birthday": BirthDayField,
        "client_ids": ClientIDsField,
        "first_name": CharField,
        "last_name": CharField,
    }

    def __set__(self, instance, value):
        super().__set__(instance, value)
        if value is not None:
            if not isinstance(value, dict):
                raise ValueError(f"Arguments must be a dictionary, not {type(value).__name__}")

            for key, field_value in value.items():
                if key not in self.ALLOWED_FIELDS:
                    raise ValueError(f"Invalid key: '{key}'")

                field_descriptor = self.ALLOWED_FIELDS[key]()
                try:
                    field_descriptor.__set__(instance, field_value)
                except ValueError as e:
                    raise ValueError(f"Invalid value for key '{key}': {e}")
