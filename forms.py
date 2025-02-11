from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, DecimalField, IntegerField, PasswordField,
    BooleanField, SubmitField, FieldList, FormField, HiddenField
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, ValidationError

def validate_on_submit(self, extra_validators=None):
    """
    Calls validate only if the form is submitted. This is a shortcut,
    equivalent to form.is_submitted() and form.validate().
    """
    return self.is_submitted() and self.validate(extra_validators=extra_validators)

class CampaignDetailsForm(FlaskForm):
    title = StringField('عنوان الحملة', validators=[DataRequired()])
    region = SelectField('النطاق الجغرافي', choices=[], validators=[DataRequired()])
    field = StringField('المجال', validators=[DataRequired()])
    budget = DecimalField('ميزانية الحملة', validators=[DataRequired(), NumberRange(min=0)])
    management_fee = DecimalField('رسوم إدارة (%)', validators=[DataRequired(), NumberRange(min=0)])

    miscellaneous_cost = DecimalField(
        'تكاليف متنوعة (اختياري)',
        validators=[Optional(), NumberRange(min=0)],
        default=0,
        render_kw={"placeholder": "أدخل قيمة التكاليف المتنوعة إذا وجدت"}
    )
    contingency_fund = DecimalField(
        'صندوق الطوارئ (اختياري)',
        validators=[Optional(), NumberRange(min=0)],
        default=0,
        render_kw={"placeholder": "أدخل قيمة صندوق الطوارئ إذا كنت ترغب في تخصيصه"}
    )
    platform_fees = DecimalField(
        'رسوم المنصات (اختياري)',
        validators=[Optional(), NumberRange(min=0)],
        default=0,
        render_kw={"placeholder": "أدخل قيمة رسوم المنصات الإضافية إذا وجدت"}
    )
    advertising_fees = DecimalField(
        'رسوم الإعلان (اختياري)',
        validators=[Optional(), NumberRange(min=0)],
        default=0,
        render_kw={"placeholder": "أدخل قيمة رسوم الإعلان الإضافية إذا وجدت"}
    )
    
    submit = SubmitField('التالي')

class IndicatorInputForm(FlaskForm):
    indicator_name = HiddenField()
    input_method = SelectField('طريقة الإدخال', choices=[("target", "أدخل المستهدف"), ("total_price", "أدخل السعر الإجمالي")], validators=[DataRequired()])
    target = IntegerField('أدخل المستهدف', validators=[Optional(), NumberRange(min=0)])
    total_price = DecimalField('أدخل السعر الإجمالي', validators=[Optional(), NumberRange(min=0)])
    unit_price = HiddenField()


class PlatformForm(FlaskForm):
    platform_name = SelectField('اختر منصة', choices=[], validators=[DataRequired()])
    submit = SubmitField('إضافة منصة')


class InfluencerForm(FlaskForm):
    name = StringField('اسم المؤثر', validators=[DataRequired()])
    in_person = BooleanField('تغطية حضورية')
    remote = BooleanField('تغطية عن بعد')
    in_person_count = IntegerField('عدد التغطيات الحضورية', validators=[Optional(), NumberRange(min=1)])
    remote_count = IntegerField('عدد التغطيات عن بعد', validators=[Optional(), NumberRange(min=1)])
    submit = SubmitField('إضافة المؤثر')

    def __init__(self, influencer_names, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.influencer_names = influencer_names  # List of valid influencer names

    def validate_name(self, field):
        if field.data not in self.influencer_names:
            raise ValidationError('اسم المؤثر غير موجود. يرجى التأكد من إدخال الاسم الصحيح.')

    def validate(self, **kwargs):
        rv = super().validate(**kwargs)
        if not rv:
            return False

        # Must select at least one coverage type
        if not self.in_person.data and not self.remote.data:
            error_message = 'يجب اختيار نوع تغطية واحد على الأقل (حضورية أو عن بعد).'
            self.in_person.errors.append(error_message)
            self.remote.errors.append(error_message)
            return False

        # If in-person coverage is selected, in_person_count must be entered
        if self.in_person.data:
            if not self.in_person_count.data or self.in_person_count.data < 1:
                self.in_person_count.errors.append('يرجى إدخال عدد صحيح للتغطيات الحضورية.')
                return False

        # If remote coverage is selected, remote_count must be entered
        if self.remote.data:
            if not self.remote_count.data or self.remote_count.data < 1:
                self.remote_count.errors.append('يرجى إدخال عدد صحيح للتغطيات عن بعد.')
                return False

        return True


class NewsAccountForm(FlaskForm):
    name = StringField('اسم الحساب الإخباري', validators=[DataRequired()])
    in_person = BooleanField('تغطية حضورية')
    remote = BooleanField('تغطية عن بعد')
    in_person_count = IntegerField('عدد التغطيات الحضورية', validators=[Optional(), NumberRange(min=1)])
    remote_count = IntegerField('عدد التغطيات عن بعد', validators=[Optional(), NumberRange(min=1)])
    submit = SubmitField('إضافة الحساب الإخباري')

    def __init__(self, account_names, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.account_names = account_names  # List of valid news account names

    def validate_name(self, field):
        if field.data not in self.account_names:
            raise ValidationError('اسم الحساب الإخباري غير موجود. يرجى التأكد من إدخال الاسم الصحيح.')

    def validate(self, **kwargs):
        rv = super().validate(**kwargs)
        if not rv:
            return False

        # Must select at least one coverage type
        if not self.in_person.data and not self.remote.data:
            error_message = 'يجب اختيار نوع تغطية واحد على الأقل (حضورية أو عن بعد).'
            self.in_person.errors.append(error_message)
            self.remote.errors.append(error_message)
            return False

        # If in-person coverage is selected, in_person_count must be entered
        if self.in_person.data:
            if not self.in_person_count.data or self.in_person_count.data < 1:
                self.in_person_count.errors.append('يرجى إدخال عدد صحيح للتغطيات الحضورية.')
                return False

        # If remote coverage is selected, remote_count must be entered
        if self.remote.data:
            if not self.remote_count.data or self.remote_count.data < 1:
                self.remote_count.errors.append('يرجى إدخال عدد صحيح للتغطيات عن بعد.')
                return False

        return True


class OptionalServicesForm(FlaskForm):
    services = FieldList(FormField(FormField(BooleanField)))
    quantities = FieldList(FormField(FormField(IntegerField)))
    submit = SubmitField('التالي')


class AdminLoginForm(FlaskForm):
    email_or_username = StringField('Email or Username', validators=[DataRequired(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Login')

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
class SaveCampaignForm(FlaskForm):
    title = StringField('عنوان الحملة', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('حفظ الحملة')