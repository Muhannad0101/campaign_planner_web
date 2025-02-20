from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DecimalField, IntegerField, TextAreaField, SelectField, HiddenField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from models import AdditionalService, DigitalPricing, Influencer, NewsAccount

class AdminLoginForm(FlaskForm):
    username_or_email = StringField('Username', validators=[DataRequired(), Length(min=3, max=120)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AdditionalServiceForm(FlaskForm):
    service_type = StringField('Service Type', validators=[DataRequired(), Length(max=100)])
    price = DecimalField('Price', validators=[DataRequired()], places=2)
    submit = SubmitField('Submit')

class DigitalPricingForm(FlaskForm):
    cost = DecimalField('Cost', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    indicator = StringField('Indicator', validators=[DataRequired(), Length(max=255)])
    field = StringField('Field', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Description', validators=[DataRequired()])
    item = StringField('Item', validators=[DataRequired(), Length(max=255)])
    channel = StringField('Channel', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Submit')

class InfluencerForm(FlaskForm):
    indicator = StringField('Indicator', validators=[DataRequired(), Length(max=255)])
    publication = StringField('Publication', validators=[Optional(), Length(max=255)])
    coverage_in_person = IntegerField('Coverage In-Person', validators=[Optional(), NumberRange(min=0)])
    coverage_remote = IntegerField('Coverage Remote', validators=[Optional(), NumberRange(min=0)])
    region = StringField('Region', validators=[Optional(), Length(max=255)])
    platform = StringField('Platform', validators=[DataRequired(), Length(max=255)])
    field = StringField('Field', validators=[DataRequired(), Length(max=255)])
    followers = IntegerField('Followers', validators=[Optional(), NumberRange(min=0)])
    identifier = StringField('Identifier', validators=[DataRequired(), Length(max=255)])
    account = StringField('Account', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Submit')

class NewsAccountForm(FlaskForm):
    indicator = StringField('Indicator', validators=[DataRequired(), Length(max=255)])
    publication = StringField('Publication', validators=[Optional(), Length(max=255)])
    coverage_in_person = IntegerField('Coverage In-Person', validators=[Optional(), NumberRange(min=0)])
    coverage_remote = IntegerField('Coverage Remote', validators=[Optional(), NumberRange(min=0)])
    region = StringField('Region', validators=[Optional(), Length(max=255)])
    platform = StringField('Platform', validators=[DataRequired(), Length(max=255)])
    field = StringField('Field', validators=[DataRequired(), Length(max=255)])
    followers = IntegerField('Followers', validators=[Optional(), NumberRange(min=0)])
    identifier = StringField('Identifier', validators=[DataRequired(), Length(max=255)])
    account = StringField('Account', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Submit')


class DeleteForm(FlaskForm):
    id = HiddenField('ID', validators=[DataRequired()])
    submit = SubmitField('Delete')

