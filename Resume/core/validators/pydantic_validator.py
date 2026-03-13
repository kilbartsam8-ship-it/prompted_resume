from pydantic import ValidationError as PydanticError

from Resume.core.exceptions import ValidationError


class PydanticValidator:
    @staticmethod
    def validate(model_class, data: dict):
        try:
            validated = model_class(**data)
            return validated.model_dump()
        except PydanticError as e:
            raise ValidationError(str(e))
