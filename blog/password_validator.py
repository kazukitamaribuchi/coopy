from django.core.exceptions import (
    ValidationError
)
from django.utils.translation import gettext as _
import re


class MyCommonPasswordValidator:
    """
    カスタムバリデーター
        - 英数字8文字以上で大文字、小文字、数字が含まれているかチェック
    """

    def validate(self, password, user=None):
        pattern = r'(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,50}$'
        result = re.match(pattern, password)

        if result:
            return password
        else:
            raise ValidationError('パスワードは英数字8文字以上かつ大文字,小文字,数字を含めてください。')

    def get_help_text(self):
        return _('パスワードは英数字8文字以上かつ大文字,小文字,数字を含めてください。')
