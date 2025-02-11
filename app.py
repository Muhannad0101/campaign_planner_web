from wtforms import BooleanField, SubmitField, HiddenField,IntegerField, DecimalField, SelectField, StringField
from forms import CampaignDetailsForm, PlatformForm, InfluencerForm,NewsAccountForm, OptionalServicesForm, SaveCampaignForm
from flask import Flask, render_template, request, redirect,url_for, flash, session, flash, make_response, jsonify
from models import AdditionalService, DigitalPricing, Influencer, NewsAccount, AdminUser, SavedCampaign
from wtforms.validators import DataRequired, NumberRange, Optional
from extensions import db, migrate, bcrypt, login_manager
from flask_wtf.csrf import CSRFProtect, generate_csrf
from logging.handlers import RotatingFileHandler
from typing import Callable, Any, Tuple, Dict
from decimal import Decimal, ROUND_HALF_UP
from gevent.pywsgi import WSGIServer
from flask_wtf import FlaskForm
from dotenv import load_dotenv
from flask import Blueprint
from flask import jsonify
from flask_login import current_user
import werkzeug.serving
import pandas as pd
import functools
import requests
import decimal
import logging
import pdfkit
import json
import re
import os
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect, generate_csrf
from admin import admin_bp  
from jinja2 import Environment


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.jinja_env.globals.update(getattr=getattr)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True  
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SECURE'] = True


db.init_app(app)
migrate.init_app(app, db)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'admin.login'
login_manager.login_message_category = 'info'

csrf = CSRFProtect(app)
app.register_blueprint(admin_bp)

# Initialize Talisman
Talisman(app, content_security_policy=None)

wkhtmltopdf_path = os.getenv('WKHTMLTOPDF_PATH')

if not wkhtmltopdf_path:
    raise ValueError("WKHTMLTOPDF_PATH is not set in the environment variables.")
pdfkit_config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)


@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())

@app.template_filter('getattr')
def getattr_filter(obj, attr):
    return getattr(obj, attr, '')


def load_data():
    try:
        pricing_table = DigitalPricing.query.all()
        influencers_table = Influencer.query.all()
        news_accounts_table = NewsAccount.query.all()
        additional_services_table = AdditionalService.query.all()
    except Exception as e:
        app.logger.error(f"Error loading data from MySQL: {e}")
        raise e

    pricing_df = pd.DataFrame([{
        'id': p.id,
        'cost': float(p.cost),
        'quantity': p.quantity,
        'indicator': p.indicator,
        'field': p.field,
        'description': p.description,
        'item': p.item,
        'channel': p.channel
    } for p in pricing_table])

    influencers_df = pd.DataFrame([{
        'id': i.id,
        'indicator': i.indicator,
        'publication': i.publication,
        'coverage_in_person': i.coverage_in_person,
        'coverage_remote': i.coverage_remote,
        'region': i.region,
        'platform': i.platform,
        'field': i.field,
        'followers': i.followers,
        'identifier': i.identifier,
        'account': i.account
    } for i in influencers_table])

    news_accounts_df = pd.DataFrame([{
        'id': n.id,
        'indicator': n.indicator,
        'publication': n.publication,
        'coverage_in_person': n.coverage_in_person,
        'coverage_remote': n.coverage_remote,
        'region': n.region,
        'platform': n.platform,
        'field': n.field,
        'followers': n.followers,
        'identifier': n.identifier,
        'account': n.account
    } for n in news_accounts_table])

    additional_services_df = pd.DataFrame([{
        'id': a.id,
        'service_type': a.service_type,
        'price': float(a.price) if a.price else None
    } for a in additional_services_table])

    return pricing_df, influencers_df, news_accounts_df, additional_services_df

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/campaign_details', methods=['GET', 'POST'])
def campaign_details():
    form = CampaignDetailsForm()
    _, influencers_table, _, _ = load_data()
    regions = influencers_table['region'].dropna().unique()
    form.region.choices = [(region, region) for region in regions]

    # If we have data in session, populate the form fields
    if request.method == 'GET' and 'campaign_details' in session:
        cd = session['campaign_details']
        form.title.data = cd.get('title', '')
        form.region.data = cd.get('region', '')
        form.field.data = cd.get('field', '')
        form.budget.data = cd.get('budget', 0)
        form.management_fee.data = cd.get('management_fee', '')
        form.miscellaneous_cost.data = cd.get('miscellaneous_cost', '')
        form.contingency_fund.data = cd.get('contingency_fund', '')
        form.platform_fees.data = cd.get('platform_fees', '')
        form.advertising_fees.data = cd.get('advertising_fees', '')

    if form.validate_on_submit():
        session['campaign_details'] = {
            'title': form.title.data,
            'region': form.region.data,
            'field': form.field.data,
            'budget': int(form.budget.data),
            'management_fee': int(form.management_fee.data),
            'miscellaneous_cost': int(form.miscellaneous_cost.data or 0),
            'contingency_fund': int(form.contingency_fund.data or 0),
            'platform_fees': int(form.platform_fees.data or 0),
            'advertising_fees': int(form.advertising_fees.data or 0),
        }
        return redirect(url_for('platforms_indicators'))

    return render_template(
        'campaign_details.html',
        form=form,
        back_url=url_for('index')
    )


@app.route('/delete_campaign_details')
def delete_campaign_details():
    session.clear()
    return redirect(url_for('campaign_details'))


@app.route('/platforms_indicators', methods=['GET', 'POST'])
def platforms_indicators():
    pricing_table, _, _, _ = load_data()
    if pricing_table is None:
        return redirect(url_for('index'))  # Redirect to home if data loading failed
    
    platforms = pricing_table['channel'].dropna().unique()
    
    # Initialize or retrieve the list of added platforms from the session
    if 'added_platforms' not in session:
        session['added_platforms'] = []
    
    form = PlatformForm()
    form.platform_name.choices = [('', 'اختر منصة')] + [(platform, platform) for platform in platforms]
    
    if request.method == 'POST':
        # Process form submission to add a platform
        if 'add_platform' in request.form:
            platform_name = request.form.get('platform_name')
            if not platform_name:
                flash('يرجى اختيار منصة لإضافتها.', 'danger')
            elif platform_name in [p['platform_name'] for p in session['added_platforms']]:
                flash(f'تمت إضافة منصة "{platform_name}" مسبقًا.', 'warning')
            else:
                # Retrieve indicators for the selected platform
                platform_indicators = pricing_table[pricing_table['channel'] == platform_name]['indicator'].dropna().unique()
                platform_data = {
                    'platform_name': platform_name,
                    'indicators': {}
                }
                # Iterate over indicators and collect data if provided
                for indicator in platform_indicators:
                    input_method = request.form.get(f'input_method_{platform_name}_{indicator}')
                    value = request.form.get(f'value_{platform_name}_{indicator}')
                    if input_method and value:
                        if input_method not in ['target', 'total_price']:
                            flash(f'طريقة الإدخال غير صالحة لمؤشر "{indicator}".', 'danger')
                            break  
                        try:
                            if input_method == 'target':
                                value = int(value)
                                if value < 0:
                                    raise ValueError
                            elif input_method == 'total_price':
                                value = float(value)
                                if value < 0:
                                    raise ValueError
                        except ValueError:
                            flash(f'القيمة المدخلة غير صالحة لمؤشر "{indicator}".', 'danger')
                            break  
                        
                        # Retrieve the cost for the current indicator
                        cost_row = pricing_table[
                            (pricing_table['channel'] == platform_name) & 
                            (pricing_table['indicator'] == indicator)
                        ]
                        if cost_row.empty:
                            flash(f'لم يتم العثور على تكلفة لمؤشر "{indicator}".', 'danger')
                            break
                        cost = cost_row['cost'].values[0]
                        
                        # Calculate final_total based on input_method
                        if input_method == 'target':
                            final_total = value * cost
                        elif input_method == 'total_price':
                            final_total = value / cost
                        final_total = int(round(final_total))
                        platform_data['indicators'][indicator] = {
                            'input_method': input_method,
                            'value': value,
                            'final_total': final_total  # Store the calculated final_total
                        }
                else:
                    # Only add the platform if at least one indicator is provided
                    if platform_data['indicators']:
                        session['added_platforms'].append(platform_data)
                        session.modified = True
                        flash(f'تمت إضافة منصة "{platform_name}" بنجاح!', 'success')
                        return redirect(url_for('platforms_indicators'))
                    else:
                        flash('يرجى إدخال بيانات لمؤشر واحد على الأقل.', 'danger')
    
    # Pass pricing_table as list of dictionaries for JavaScript
    pricing_table_json = pricing_table.to_dict(orient='records') if pricing_table is not None else []
    
    return render_template(
        'platforms_indicators.html',
        form=form,
        platforms=platforms,
        pricing_table=pricing_table_json,
        added_platforms=session['added_platforms'],
        back_url=url_for('campaign_details')
    )


@app.route('/remove_platform', methods=['POST'])
def remove_platform():
    data = request.get_json()
    platform_name = data.get('platform_name')

    if not platform_name:
        return jsonify({'status': 'error', 'message': 'لم يتم توفير اسم المنصة.'}), 400

    added_platforms = session.get('added_platforms', [])
    updated_platforms = [p for p in added_platforms if p['platform_name'] != platform_name]

    if len(added_platforms) == len(updated_platforms):
        return jsonify({'status': 'error', 'message': 'لم يتم العثور على المنصة المحددة.'}), 404

    session['added_platforms'] = updated_platforms
    session.modified = True

    return jsonify({'status': 'success', 'message': f'تمت إزالة منصة "{platform_name}" بنجاح.'})


@app.route('/optional_services', methods=['GET', 'POST'])
def optional_services_route():
    campaign_details = session.get('campaign_details')
    if not campaign_details:
        return redirect(url_for('campaign_details'))

    _, _, _, additional_services_table = load_data()
    optional_services = {}
    service_available = {}

    for _, row in additional_services_table.iterrows():
        service_type = row['service_type']
        price = row['price']
        try:
            price_val = float(price)
            if price_val > 0:
                optional_services[service_type] = int(price_val)
                service_available[service_type] = True
            else:
                service_available[service_type] = False
        except (ValueError, TypeError):
            service_available[service_type] = False

    class DynamicOptionalServicesForm(FlaskForm):
        submit = SubmitField('التالي')

    for service in optional_services:
        service_field = f'service_{service}'
        quantity_field = f'quantity_{service}'
        setattr(DynamicOptionalServicesForm, service_field, BooleanField(service))
        setattr(DynamicOptionalServicesForm, quantity_field, IntegerField('الكمية', validators=[Optional(), NumberRange(min=0)]))

    for service, available in service_available.items():
        if not available:
            service_field = f'service_{service}'
            quantity_field = f'quantity_{service}'
            setattr(DynamicOptionalServicesForm, service_field, BooleanField(service, default=False, render_kw={'disabled': True}))
            setattr(DynamicOptionalServicesForm, quantity_field, IntegerField('الكمية', validators=[Optional(), NumberRange(min=0)], render_kw={'disabled': True}))

    form = DynamicOptionalServicesForm()

    # If GET and session data exists, populate the form
    if request.method == 'GET' and 'optional_services' in session:
        saved_services = session['optional_services']
        for service in service_available:
            service_field = f'service_{service}'
            quantity_field = f'quantity_{service}'
            if service in saved_services:
                getattr(form, service_field).data = True
                getattr(form, quantity_field).data = saved_services[service]
            else:
                getattr(form, service_field).data = False

    if form.validate_on_submit():
        services_selected = {}
        for service in service_available:
            if service_available[service]:
                include_service = form.data.get(f'service_{service}')
                quantity = form.data.get(f'quantity_{service}') or 0
                if include_service and quantity > 0:
                    services_selected[service] = quantity
        session['optional_services'] = services_selected
        return redirect(url_for('influencers'))

    return render_template(
        'optional_services.html',
        form=form,
        optional_services=optional_services,
        service_available=service_available,
        back_url=url_for('platforms_indicators')
    )

@app.route('/delete_optional_services')
def delete_optional_services():
    session.pop('optional_services', None)
    return redirect(url_for('optional_services_route'))


@app.route('/influencers', methods=['GET', 'POST'])
def influencers():
    _, influencers_table, _, _ = load_data()

    influencers_table = influencers_table.fillna('غير معروف')

    regions = influencers_table['region'].dropna().unique().tolist()
    platforms = influencers_table['platform'].dropna().unique().tolist()

    # Handle filters
    selected_region = request.args.get('region_filter', default=None)
    selected_platform = request.args.get('platform_filter', default=None)

    # Apply filters to the influencers table
    filtered_influencers = influencers_table.copy()
    if selected_region and selected_region != 'all':
        filtered_influencers = filtered_influencers[filtered_influencers['region'] == selected_region]
    if selected_platform and selected_platform != 'all':
        filtered_influencers = filtered_influencers[filtered_influencers['platform'] == selected_platform]

    # List of valid influencer names
    influencer_names = influencers_table['identifier'].dropna().unique().tolist()

    form = InfluencerForm(influencer_names)

    added_influencers = session.get('added_influencers', [])

    # Check if the user wants to remove an influencer
    if request.method == 'POST' and 'remove_influencer' in request.form:
        index_to_remove = int(request.form.get('remove_influencer'))
        added_influencers = session.get('added_influencers', [])
        if 0 <= index_to_remove < len(added_influencers):
            removed_influencer = added_influencers.pop(index_to_remove)
            session['added_influencers'] = added_influencers
            flash(f"تمت إزالة المؤثر: {removed_influencer['name']} - {removed_influencer['coverage_type']}", 'success')
        return redirect(url_for('influencers'))
    

    if form.validate_on_submit():
        name = form.name.data.strip()
        in_person = form.in_person.data
        remote = form.remote.data

        # Ensure counts are integers and default to 0 if None
        in_person_count = form.in_person_count.data if in_person else 0
        in_person_count = int(in_person_count) if in_person_count else 0

        remote_count = form.remote_count.data if remote else 0
        remote_count = int(remote_count) if remote_count else 0

        # Fetch influencer data
        influencer = influencers_table[influencers_table['identifier'] == name].iloc[0]

        if in_person and in_person_count > 0:
            coverage_type = 'حضوري'
            coverage_count = in_person_count
            coverage_price = influencer.get('coverage_in_person', 0.0)
            if pd.isna(coverage_price) or coverage_price == 'غير معروف':
                coverage_price = 0.0
            coverage_price = float(coverage_price)
            influencer_entry = {
                'name': name,
                'coverage_type': coverage_type,
                'coverage_count': coverage_count,
                'coverage_price': coverage_price
            }
            added_influencers.append(influencer_entry)

        if remote and remote_count > 0:
            coverage_type = 'عن بعد'
            coverage_count = remote_count
            coverage_price = influencer.get('coverage_remote', 0.0)
            if pd.isna(coverage_price) or coverage_price == 'غير معروف':
                coverage_price = 0.0
            coverage_price = float(coverage_price)
            influencer_entry = {
                'name': name,
                'coverage_type': coverage_type,
                'coverage_count': coverage_count,
                'coverage_price': coverage_price
            }
            added_influencers.append(influencer_entry)

        session['added_influencers'] = added_influencers
        flash('تمت إضافة المؤثر بنجاح!', 'success')
        return redirect(url_for('influencers'))

    return render_template(
        'influencers.html',
        form=form,
        added_influencers=added_influencers,
        influencers=filtered_influencers.to_dict(orient='records'),
        regions=regions,
        platforms=platforms,
        selected_region=selected_region,
        selected_platform=selected_platform,
        back_url=url_for('optional_services_route') 
    )


@app.route('/news_accounts', methods=['GET', 'POST'])
def news_accounts():
    _, _, news_accounts_table, _ = load_data()
    
    news_accounts_table = news_accounts_table.fillna('غير معروف')

    # Get unique regions and platforms for filters
    regions = news_accounts_table['region'].dropna().unique().tolist()
    platforms = news_accounts_table['platform'].dropna().unique().tolist()

    # Handle filters
    selected_region = request.args.get('region_filter', default=None)
    selected_platform = request.args.get('platform_filter', default=None)

    # Apply filters to the influencers table
    filtered_news_accounts = news_accounts_table.copy()
    if selected_region and selected_region != 'all':
        filtered_news_accounts = filtered_news_accounts[filtered_news_accounts['region'] == selected_region]
    if selected_platform and selected_platform != 'all':
        filtered_news_accounts = filtered_news_accounts[filtered_news_accounts['platform'] == selected_platform]

    news_accounts_names = news_accounts_table['identifier'].dropna().unique().tolist()
    form = NewsAccountForm(news_accounts_names)

    added_news_accounts = session.get('added_news_accounts', [])

    # Handle removal of news accounts
    if request.method == 'POST' and 'remove_news_account' in request.form:
        index_to_remove = int(request.form.get('remove_news_account'))
        if 0 <= index_to_remove < len(added_news_accounts):
            removed_account = added_news_accounts.pop(index_to_remove)
            session['added_news_accounts'] = added_news_accounts
            flash(f"تمت إزالة الحساب الإخباري: {removed_account['name']} - {removed_account['coverage_type']}", 'success')
        return redirect(url_for('news_accounts'))

    # Handle form submission
    if form.validate_on_submit():
        name = form.name.data.strip()
        in_person = form.in_person.data
        remote = form.remote.data

        # Ensure counts are integers and default to 0 if None
        in_person_count = form.in_person_count.data if in_person else 0
        in_person_count = int(in_person_count) if in_person_count else 0

        remote_count = form.remote_count.data if remote else 0
        remote_count = int(remote_count) if remote_count else 0

        # Fetch news account data
        news_account = news_accounts_table[news_accounts_table['identifier'] == name].iloc[0]

        if in_person and in_person_count > 0:
            coverage_type = 'حضوري'
            coverage_count = in_person_count
            coverage_price = news_account.get('coverage_in_person', 0.0)
            if pd.isna(coverage_price) or coverage_price == 'غير معروف':
                coverage_price = 0.0
            coverage_price = float(coverage_price)
            news_account_entry = {
                'name': name,
                'coverage_type': coverage_type,
                'coverage_count': coverage_count,
                'coverage_price': coverage_price
            }
            added_news_accounts.append(news_account_entry)

        if remote and remote_count > 0:
            coverage_type = 'عن بعد'
            coverage_count = remote_count
            coverage_price = news_account.get('coverage_remote', 0.0)
            if pd.isna(coverage_price) or coverage_price == 'غير معروف':
                coverage_price = 0.0
            coverage_price = float(coverage_price)
            news_account_entry = {
                'name': name,
                'coverage_type': coverage_type,
                'coverage_count': coverage_count,
                'coverage_price': coverage_price
            }
            added_news_accounts.append(news_account_entry)

        session['added_news_accounts'] = added_news_accounts
        flash('تمت إضافة الحساب الإخباري بنجاح!', 'success')
        return redirect(url_for('news_accounts'))

    # Pass data to the template
    return render_template(
        'news_accounts.html',
        form=form,
        added_news_accounts=added_news_accounts,
        news_accounts=filtered_news_accounts.to_dict(orient='records'),
        regions=regions,
        platforms=platforms,
        selected_region=selected_region,
        selected_platform=selected_platform,
        back_url=url_for('influencers')  
    )


def get_unit_price(pricing_table, platform, indicator):
    option = pricing_table[
        (pricing_table['channel'] == platform) &
        (pricing_table['indicator'] == indicator)
    ]
    if not option.empty:
        return float(option.iloc[0]['cost'])
    return 0.0


def normalize_indicator(indicator):
    # Remove leading/trailing whitespace
    indicator = indicator.strip()
    # Replace multiple spaces with a single space
    indicator = re.sub(r'\s+', ' ', indicator)
    # Convert to lowercase
    indicator = indicator.lower()
    return indicator


def compute_campaign_data():
    # Retrieve all data from session
    campaign_details = session.get('campaign_details')
    added_platforms = session.get('added_platforms', [])
    added_influencers = session.get('added_influencers', [])
    added_news_accounts = session.get('added_news_accounts', [])
    optional_services_selected = session.get('optional_services', {})

    if not campaign_details:
        return None  

    # Load data
    pricing_table, influencers_table, news_accounts_table, additional_services_table = load_data()

    # Process additional services
    optional_services = {}
    for _, row in additional_services_table.iterrows():
        service_type = row['service_type']
        price = row['price']
        optional_services[service_type] = price

    # Perform budget calculations
    campaign_budget = campaign_details['budget']
    management_fee_percentage = campaign_details['management_fee'] / 100

    # Initialize variables for KPIs
    total_impressions = 0
    total_views = 0 
    total_clicks = 0
    total_engagements = 0
    total_app_installs = 0 

    # Define the mapping between indicators and KPIs
    indicator_to_kpi = {
        'الظهور': 'impressions',
        'مشاهدات': 'views',
        'المشاهدات': 'views',
        'تحميل التطبيق': 'app_installs', 
        'النقرات': 'clicks',
        'نقرة': 'clicks',
        'تفاعل': 'engagements',
        'engagement': 'engagements',
        # Add any other indicators as needed
    }

    # Optional Services Cost
    optional_services_cost = 0
    campaign_items = []
    for service, quantity in optional_services_selected.items():
        unit_price = optional_services.get(service, 0)
        total_item_price = unit_price * quantity
        campaign_items.append({
            'البند': service,
            'الوصف': f"خدمة {service}",
            'المستهدف': 'لايوجد',
            'الوحدة': 'لايوجد',
            'العدد': quantity,
            'السعر الفردي': int(unit_price) if isinstance(unit_price, (int, float)) else unit_price,
            'السعر الإجمالي': int(total_item_price) if isinstance(total_item_price, (int, float)) else total_item_price
        })
        optional_services_cost += total_item_price

    # Platforms cost
    platforms_cost = 0
    for platform in added_platforms:
        platform_name = platform['platform_name']
        indicators = platform.get('indicators', {})
        for indicator, data in indicators.items():
            input_method = data.get('input_method')
            value = data.get('value')

            unit_price = get_unit_price(pricing_table, platform_name, indicator)

            if input_method == 'target' and value:
                try:
                    target = int(value)
                    if target < 0:
                        raise ValueError
                except ValueError:
                    flash(f'Invalid target value for indicator "{indicator}" in platform "{platform_name}".', 'danger')
                    continue
                total_item_price = unit_price * target if unit_price else 0
                total_price = total_item_price
            elif input_method == 'total_price' and value:
                try:
                    total_price = float(value)
                    if total_price < 0:
                        raise ValueError
                except ValueError:
                    flash(f'Invalid total price value for indicator "{indicator}" in platform "{platform_name}".', 'danger')
                    continue
                target = total_price / unit_price if unit_price else 0
                total_item_price = total_price
            else:
                continue  # Skip if no valid input method and value

            # Retrieve additional data from the pricing table
            option = pricing_table[
                (pricing_table['channel'] == platform_name) &
                (pricing_table['indicator'] == indicator)
            ]
            if not option.empty:
                option = option.iloc[0]
                description = option.get('description', 'لا يوجد وصف')
                item_name = option.get('item', indicator)
                quantity = option.get('quantity', 'لايوجد')
            else:
                description = 'لا يوجد وصف'
                item_name = indicator
                quantity = 'لايوجد'

            campaign_items.append({
                'البند': item_name,
                'الوصف': description,
                'المستهدف': int(target),
                'الوحدة': indicator,
                'العدد': quantity,
                'السعر الفردي': unit_price,
                'السعر الإجمالي': int(total_item_price) if isinstance(total_item_price, (int, float)) else total_item_price
            })
            platforms_cost += total_item_price

            # Normalize the indicator
            normalized_indicator = normalize_indicator(indicator)

            # Get KPI from mapping
            kpi = indicator_to_kpi.get(normalized_indicator)
            if kpi == 'impressions':
                total_impressions += target or 0
            elif kpi == 'views':
                total_views += target or 0
            elif kpi == 'clicks':
                total_clicks += target or 0
            elif kpi == 'engagements':
                total_engagements += target or 0
            elif kpi == 'app_installs':
                total_app_installs += target or 0
            else:
                app.logger.warning(f"Unknown KPI: {kpi} for indicator {indicator}")

    # Influencers cost
    influencers_cost = 0
    for influencer in added_influencers:
        coverage_count = influencer.get('coverage_count', 0)
        coverage_price = influencer.get('coverage_price', 0.0)

        if coverage_count and coverage_price:
            total_influencer_cost = coverage_count * coverage_price
            influencers_cost += total_influencer_cost
        else:
            total_influencer_cost = 0.0

        campaign_items.append({
            'البند': f'الإعلان عبر المؤثرين - {influencer.get("coverage_type", "لايوجد")}',
            'الوصف': influencer.get('name', 'لايوجد'),
            'المستهدف': f'عدد التغطيات: {coverage_count}',
            'الوحدة': f'تغطية {influencer.get("coverage_type", "لايوجد")}',
            'العدد': coverage_count,
            'السعر الفردي': int(coverage_price) if isinstance(coverage_price, (int, float)) else coverage_price,
            'السعر الإجمالي': int(total_influencer_cost) if isinstance(total_influencer_cost, (int, float)) else total_influencer_cost
        })

    # News Accounts cost
    news_accounts_cost = 0
    for account in added_news_accounts:
        coverage_count = account.get('coverage_count', 0)
        coverage_price = account.get('coverage_price', 0.0)

        if coverage_count and coverage_price:
            total_account_cost = coverage_count * coverage_price
            news_accounts_cost += total_account_cost
        else:
            total_account_cost = 0.0

        campaign_items.append({
            'البند': f'الإعلان عبر الحسابات الإخبارية - {account.get("coverage_type", "لايوجد")}',
            'الوصف': account.get('name', 'لايوجد'),
            'المستهدف': f'عدد التغطيات: {coverage_count}',
            'الوحدة': f'تغطية {account.get("coverage_type", "لايوجد")}',
            'العدد': coverage_count,
            'السعر الفردي': int(coverage_price) if isinstance(coverage_price, (int, float)) else coverage_price,
            'السعر الإجمالي': int(total_account_cost) if isinstance(total_account_cost, (int, float)) else total_account_cost
        })

    # Retrieve Optional Cost Accounts from session
    miscellaneous_cost = campaign_details.get('miscellaneous_cost', 0)
    contingency_fund = campaign_details.get('contingency_fund', 0)
    platform_fees = campaign_details.get('platform_fees', 0)
    advertising_fees = campaign_details.get('advertising_fees', 0)

    # Add additional costs to campaign_items
    # if miscellaneous_cost > 0:
    #     campaign_items.append({
    #         'البند': 'تكاليف متنوعة',
    #         'الوصف': 'تكاليف غير متوقعة أو غير مصنفة تحت الفئات الأخرى.',
    #         'المستهدف': 'لايوجد',
    #         'الوحدة': 'لايوجد',
    #         'العدد': 'لايوجد',
    #         'السعر الفردي': 'لايوجد',
    #         'السعر الإجمالي': int(miscellaneous_cost) if isinstance(miscellaneous_cost, (int, float)) else miscellaneous_cost
    #     })
# 
    # if contingency_fund > 0:
    #     campaign_items.append({
    #         'البند': 'صندوق الطوارئ',
    #         'الوصف': 'ميزانية مخصصة للتعامل مع النفقات غير المتوقعة خلال الحملة.',
    #         'المستهدف': 'لايوجد',
    #         'الوحدة': 'لايوجد',
    #         'العدد': 'لايوجد',
    #         'السعر الفردي': 'لايوجد',
    #         'السعر الإجمالي': int(contingency_fund) if isinstance(contingency_fund, (int, float)) else contingency_fund
    #     })
# 
    # if platform_fees > 0:
    #     campaign_items.append({
    #         'البند': 'رسوم المنصات',
    #         'الوصف': 'تكاليف إضافية أو رسوم خدمة تفرضها المنصات المستخدمة في الحملة.',
    #         'المستهدف': 'لايوجد',
    #         'الوحدة': 'لايوجد',
    #         'العدد': 'لايوجد',
    #         'السعر الفردي': 'لايوجد',
    #         'السعر الإجمالي': int(platform_fees) if isinstance(platform_fees, (int, float)) else platform_fees
    #     })
# 
    # if advertising_fees > 0:
    #     campaign_items.append({
    #         'البند': 'رسوم الإعلان',
    #         'الوصف': 'تكاليف شراء مساحة إعلانية إضافية أو خدمات تسويقية.',
    #         'المستهدف': 'لايوجد',
    #         'الوحدة': 'لايوجد',
    #         'العدد': 'لايوجد',
    #         'السعر الفردي': 'لايوجد',
    #         'السعر الإجمالي': int(advertising_fees) if isinstance(advertising_fees, (int, float)) else advertising_fees
    #     })
# 
    total_cost_excl_tax = (
        platforms_cost +
        optional_services_cost +
        influencers_cost +
        news_accounts_cost +
        miscellaneous_cost +
        contingency_fund +
        platform_fees +
        advertising_fees
    )

    vat = Decimal(total_cost_excl_tax) * Decimal('0.15')
    management_fees = Decimal(total_cost_excl_tax) * Decimal(management_fee_percentage)
    grand_total = Decimal(total_cost_excl_tax) + vat + management_fees
    surplus = Decimal(campaign_budget) - grand_total

    # Calculate additional KPIs
    ctr = (total_clicks / total_impressions * 100) if total_impressions else 0
    engagement_rate = (total_engagements / total_impressions * 100) if total_impressions else 0
    cpm = (platforms_cost / total_impressions * 1000) if total_impressions else 0
    cpc = (platforms_cost / total_clicks) if total_clicks else 0
    cr = (total_app_installs / total_clicks * 100) if total_clicks else 0
    cpa = (platforms_cost / total_app_installs) if total_app_installs else 0

    # Prepare KPI data
    kpi_data = {
        'إجمالي مرات الظهور': total_impressions,
        'إجمالي المشاهدات': total_views,
        'إجمالي النقرات': total_clicks,
        'إجمالي التفاعلات': total_engagements,
        'إجمالي تحميلات التطبيق': total_app_installs,
        'نسبة النقر إلى الظهور (CTR%)': round(ctr, 2),
        'معدل التفاعل (Engagement Rate%)': round(engagement_rate, 2),
        'نسبة التحويل (CR%)': round(cr, 2),
        'تكلفة الألف ظهور (CPM)': round(cpm, 2),
        'تكلفة النقرة (CPC)': round(cpc, 2),
        'تكلفة الاكتساب (CPA)': round(cpa, 2),
    }

    # Prepare summary
    budget_expected = campaign_budget

    # Return all computed data
    campaign_data = {
        'budget_expected': int(budget_expected),
        'total_cost_excl_tax': int(total_cost_excl_tax),
        'surplus': int(surplus),
        'vat': int(vat),
        'management_fees': int(management_fees),
        'grand_total': int(grand_total),
        'campaign_items': campaign_items,
        'campaign_details': campaign_details,
        'platforms_cost': platforms_cost,
        'optional_services_cost': optional_services_cost,
        'influencers_cost': influencers_cost,
        'news_accounts_cost': news_accounts_cost,
        'miscellaneous_cost': int(miscellaneous_cost) if isinstance(miscellaneous_cost, (int, float)) else miscellaneous_cost,
        'contingency_fund': int(contingency_fund) if isinstance(contingency_fund, (int, float)) else contingency_fund,
        'platform_fees': int(platform_fees) if isinstance(platform_fees, (int, float)) else platform_fees,
        'advertising_fees': int(advertising_fees) if isinstance(advertising_fees, (int, float)) else advertising_fees,
        'kpi_data': kpi_data,
    }

    return campaign_data


@app.route('/campaign_plan')
def campaign_plan():
    campaign_data = compute_campaign_data()
    
    if campaign_data is None:
        return redirect(url_for('campaign_details'))  # Or handle as appropriate

    # Extract data
    budget_expected = campaign_data['budget_expected']
    total_cost_excl_tax = campaign_data['total_cost_excl_tax']
    surplus = campaign_data['surplus']
    vat = campaign_data['vat']
    management_fees = campaign_data['management_fees']
    management_fee_percentage = campaign_data['campaign_details']['management_fee']
    grand_total = campaign_data['grand_total']
    campaign_items = campaign_data['campaign_items']
    campaign_details = campaign_data['campaign_details']
    platforms_cost = campaign_data['platforms_cost']
    optional_services_cost = campaign_data['optional_services_cost']
    influencers_cost = campaign_data['influencers_cost']
    news_accounts_cost = campaign_data['news_accounts_cost']
    kpi_data = campaign_data['kpi_data']

    # Convert KPI data to JSON for JavaScript
    kpi_data_json = json.dumps(kpi_data)

    # Render the campaign plan template
    response = make_response(render_template(
        'campaign_plan.html',
        budget_expected=budget_expected,
        total_cost_excl_tax=total_cost_excl_tax,
        surplus=surplus,
        vat=vat,
        management_fees=management_fees,
        management_fee_percentage=management_fee_percentage,
        grand_total=grand_total,
        campaign_items=campaign_items,
        campaign_details=campaign_details,
        platforms_cost=platforms_cost,
        optional_services_cost=optional_services_cost,
        influencers_cost=influencers_cost,
        news_accounts_cost=news_accounts_cost,
        kpi_data=kpi_data,
        kpi_data_json=kpi_data_json,
        back_url=url_for('news_accounts')  
    ))

    return response


@app.route('/get_kpi_data')
def get_kpi_data():
    campaign_data = compute_campaign_data()
    if campaign_data is None:
        return jsonify({'error': 'No campaign data available'}), 400  

    kpi_data = campaign_data['kpi_data']
    return jsonify(kpi_data)

@app.route('/get_cost_data')
def get_cost_data():
    campaign_data = compute_campaign_data()
    if campaign_data is None:
        return jsonify({'error': 'No campaign data available'}), 400  

    cost_data = {
        'تكلفة المنصات': campaign_data['platforms_cost'],
        'تكلفة الخدمات الاختيارية': campaign_data['optional_services_cost'],
        'تكلفة المؤثرين': campaign_data['influencers_cost'],
        'تكلفة الحسابات الإخبارية': campaign_data['news_accounts_cost']
    }
    return jsonify(cost_data)

@app.route('/get_campaign_summary')
def get_campaign_summary():
    campaign_data = compute_campaign_data()
    if campaign_data is None:
        return jsonify({'error': 'No campaign data available'}), 400

    management_fee_percentage = campaign_data['campaign_details']['management_fee']
    
    return jsonify({
        'budget_expected': campaign_data['budget_expected'],
        'total_cost_excl_tax': campaign_data['total_cost_excl_tax'],
        'surplus': float(campaign_data['surplus']),
        'vat': campaign_data['vat'],
        'management_fees': campaign_data['management_fees'],
        'grand_total': campaign_data['grand_total'],
        'management_fee_percentage': management_fee_percentage,
        'platforms_cost': campaign_data['platforms_cost'],
        'optional_services_cost': campaign_data['optional_services_cost'],
        'influencers_cost': campaign_data['influencers_cost'],
        'news_accounts_cost': campaign_data['news_accounts_cost'],
        # 'miscellaneous_cost': campaign_data.get('miscellaneous_cost', 0),
        # 'contingency_fund': campaign_data.get('contingency_fund', 0),
        # 'platform_fees': campaign_data.get('platform_fees', 0),
        # 'advertising_fees': campaign_data.get('advertising_fees', 0),
    })




@app.route('/download_campaign_plan')
def download_campaign_plan():
    campaign_data = compute_campaign_data()
    
    if campaign_data is None:
        flash('No campaign data available to download.', 'danger')
        return redirect(url_for('campaign_details')) 
    
    # Render the Dedicated PDF Template with Campaign Data
    rendered = render_template(
        'campaign_plan_pdf.html',  
        budget_expected=campaign_data['budget_expected'],
        total_cost_excl_tax=campaign_data['total_cost_excl_tax'],
        surplus=campaign_data['surplus'],
        vat=campaign_data['vat'],
        management_fees=campaign_data['management_fees'],
        management_fee_percentage = campaign_data['campaign_details']['management_fee'],
        grand_total=campaign_data['grand_total'],
        campaign_items=campaign_data['campaign_items'],
        campaign_details=campaign_data['campaign_details'],
        platforms_cost=campaign_data['platforms_cost'],
        optional_services_cost=campaign_data['optional_services_cost'],
        influencers_cost=campaign_data['influencers_cost'],
        news_accounts_cost=campaign_data['news_accounts_cost'],
        kpi_data=campaign_data['kpi_data'],
    )
    
    # Configure PDF Generation Options
    pdf_options = {
        'page-size': 'A4',
        'encoding': 'UTF-8',
        'enable-local-file-access': None 
    }
    
    try:
        # Generate PDF from Rendered HTML
        pdf = pdfkit.from_string(rendered, False, options=pdf_options, configuration=pdfkit_config)
    except Exception as e:
        app.logger.error(f"Error generating PDF: {e}")
        flash('An error occurred while generating the PDF.', 'danger')
        return redirect(url_for('campaign_plan'))  
    
    # Create a Response Object with PDF Data
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=campaign_plan.pdf'
    
    return response


@app.route('/delete_campaign_plan')
def delete_campaign_plan():
    # Clear the session data
    session.clear()
    flash('تم حذف خطة الحملة بنجاح.', 'success')
    # Redirect to the main page
    return redirect(url_for('index'))


@app.route('/save_campaign', methods=['GET', 'POST'])
def save_campaign():
    form = SaveCampaignForm()
    if form.validate_on_submit():
        title = form.title.data.strip()
        
        # Check if a campaign with this title already exists
        existing_campaign = SavedCampaign.query.filter_by(title=title).first()
        if existing_campaign:
            flash('عنوان الحملة موجود بالفعل. يرجى اختيار عنوان آخر.', 'danger')
            return render_template('save_campaign.html', form=form)
        
        # Get campaign data from session
        campaign_details = session.get('campaign_details')
        added_platforms = session.get('added_platforms', [])
        optional_services = session.get('optional_services', {})
        added_influencers = session.get('added_influencers', [])
        added_news_accounts = session.get('added_news_accounts', [])
        additional_services = session.get('additional_services', {})
        
        if not campaign_details:
            flash('لا توجد بيانات حملة لحفظها.', 'danger')
            return redirect(url_for('campaign_details'))
        
        # Serialize the data
        platforms_indicators = added_platforms
        influencers = added_influencers
        news_accounts = added_news_accounts
        
        saved_campaign = SavedCampaign(
            title=title,
            campaign_details=campaign_details,
            platforms_indicators=platforms_indicators,
            additional_services=additional_services,
            influencers=influencers,
            news_accounts=news_accounts,
            optional_services=optional_services
        )
        
        try:
            db.session.add(saved_campaign)
            db.session.commit()
            flash('تم حفظ الحملة بنجاح!', 'success')
            return redirect(url_for('campaign_plan'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error saving campaign: {e}")
            flash('حدث خطأ أثناء حفظ الحملة. يرجى المحاولة مرة أخرى.', 'danger')
    
    return render_template('save_campaign.html', form=form)

@app.route('/saved_campaigns')
def saved_campaigns():
    campaigns = SavedCampaign.query.order_by(SavedCampaign.created_at.desc()).all()
    return render_template('saved_campaigns.html', campaigns=campaigns)

@app.route('/load_campaign/<int:campaign_id>')
def load_campaign(campaign_id):
    campaign = SavedCampaign.query.get_or_404(campaign_id)
    
    # Populate session with saved campaign data
    session['campaign_details'] = campaign.campaign_details
    session['added_platforms'] = campaign.platforms_indicators
    session['additional_services'] = campaign.additional_services
    session['added_influencers'] = campaign.influencers
    session['added_news_accounts'] = campaign.news_accounts
    session['optional_services'] = campaign.optional_services

    flash(f'تم تحميل الحملة "{campaign.title}" بنجاح! يمكنك تعديلها الآن.', 'success')
    return redirect(url_for('campaign_plan'))

@app.route('/delete_saved_campaign/<int:campaign_id>', methods=['POST', 'GET'])
def delete_saved_campaign(campaign_id):
    campaign = SavedCampaign.query.get_or_404(campaign_id)
    try:
        db.session.delete(campaign)
        db.session.commit()
        flash(f'تم حذف الحملة "{campaign.title}" بنجاح.', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting campaign: {e}")
        flash('حدث خطأ أثناء حذف الحملة. يرجى المحاولة مرة أخرى.', 'danger')
    return redirect(url_for('saved_campaigns'))


def _ansi_style_supressor(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Tuple[Any, ...], **kwargs: Dict[str, Any]) -> Any:
        if args and isinstance(args[0], str) and args[0].startswith('WARNING: This is a development server.'):
            return ''
        return func(*args, **kwargs)

    return wrapper

# Apply the suppressor to the _ansi_style function
werkzeug.serving._ansi_style = _ansi_style_supressor(werkzeug.serving._ansi_style)

if __name__ == '__main__':
    app.run(debug=True)






