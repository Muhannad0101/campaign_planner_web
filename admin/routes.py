from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from . import admin_bp
from .forms import (
    AdminLoginForm,
    AdditionalServiceForm,
    DigitalPricingForm,
    InfluencerForm,
    NewsAccountForm,
    DeleteForm  
)
from models import AdminUser, AdditionalService, DigitalPricing, Influencer, NewsAccount
from extensions import db
from functools import wraps

def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

# CRUD Operations for AdditionalService
@admin_bp.route('/additional_services')
@admin_login_required
def list_additional_services():
    services = AdditionalService.query.all()
    return render_template(
        'admin/list_entries.html',
        entries=services,
        model_name='Additional Service',
        list_endpoint='admin.list_additional_services',
        create_endpoint='admin.create_additional_service'
    )

@admin_bp.route('/additional_services/create', methods=['GET', 'POST'])
@admin_login_required
def create_additional_service():
    form = AdditionalServiceForm()
    if form.validate_on_submit():
        service = AdditionalService(
            service_type=form.service_type.data,
            price=form.price.data
        )
        try:
            db.session.add(service)
            db.session.commit()
            flash('Additional Service created successfully.', 'success')
            return redirect(url_for('admin.list_additional_services'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the service.', 'danger')
    return render_template(
        'admin/edit_entry.html',
        form=form,
        action='Create',
        model_name='Additional Service',
        list_endpoint='admin.list_additional_services'
    )

@admin_bp.route('/additional_services/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_required
def edit_additional_service(id):
    service = AdditionalService.query.get_or_404(id)
    form = AdditionalServiceForm(obj=service)
    if form.validate_on_submit():
        service.service_type = form.service_type.data
        service.price = form.price.data
        try:
            db.session.commit()
            flash('Additional Service updated successfully.', 'success')
            return redirect(url_for('admin.list_additional_services'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the service.', 'danger')
    return render_template(
        'admin/edit_entry.html',
        form=form,
        action='Edit',
        model_name='Additional Service',
        list_endpoint='admin.list_additional_services'
    )

@admin_bp.route('/additional_services/delete/<int:id>', methods=['POST'])
@admin_login_required
def delete_additional_service(id):
    service = AdditionalService.query.get_or_404(id)
    try:
        db.session.delete(service)
        db.session.commit()
        flash('Additional Service deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the service.', 'danger')
    return redirect(url_for('admin.list_additional_services'))

# CRUD Operations for DigitalPricing
@admin_bp.route('/digital_pricing')
@admin_login_required
def list_digital_pricing():
    pricings = DigitalPricing.query.all()
    return render_template(
        'admin/list_entries.html',
        entries=pricings,
        model_name='Digital Pricing',
        list_endpoint='admin.list_digital_pricing',
        create_endpoint='admin.create_digital_pricing'
    )

@admin_bp.route('/digital_pricing/create', methods=['GET', 'POST'])
@admin_login_required
def create_digital_pricing():
    form = DigitalPricingForm()
    if form.validate_on_submit():
        pricing = DigitalPricing(
            cost=form.cost.data,
            quantity=form.quantity.data,
            indicator=form.indicator.data,
            field=form.field.data,
            description=form.description.data,
            item=form.item.data,
            channel=form.channel.data
        )
        try:
            db.session.add(pricing)
            db.session.commit()
            flash('Digital Pricing entry created successfully.', 'success')
            return redirect(url_for('admin.list_digital_pricing'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the digital pricing entry.', 'danger')
    return render_template(
        'admin/edit_entry.html',
        form=form,
        action='Create',
        model_name='Digital Pricing',
        list_endpoint='admin.list_digital_pricing'
    )

@admin_bp.route('/digital_pricing/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_required
def edit_digital_pricing(id):
    pricing = DigitalPricing.query.get_or_404(id)
    form = DigitalPricingForm(obj=pricing)
    if form.validate_on_submit():
        pricing.cost = form.cost.data
        pricing.quantity = form.quantity.data
        pricing.indicator = form.indicator.data
        pricing.field = form.field.data
        pricing.description = form.description.data
        pricing.item = form.item.data
        pricing.channel = form.channel.data
        try:
            db.session.commit()
            flash('Digital Pricing entry updated successfully.', 'success')
            return redirect(url_for('admin.list_digital_pricing'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the digital pricing entry.', 'danger')
    return render_template(
        'admin/edit_entry.html',
        form=form,
        action='Edit',
        model_name='Digital Pricing',
        list_endpoint='admin.list_digital_pricing'
    )

@admin_bp.route('/digital_pricing/delete/<int:id>', methods=['POST'])
@admin_login_required
def delete_digital_pricing(id):
    pricing = DigitalPricing.query.get_or_404(id)
    try:
        db.session.delete(pricing)
        db.session.commit()
        flash('Digital Pricing entry deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the digital pricing entry.', 'danger')
    return redirect(url_for('admin.list_digital_pricing'))

# CRUD Operations for Influencer
@admin_bp.route('/influencers')
@admin_login_required
def list_influencers():
    influencers = Influencer.query.all()
    return render_template(
        'admin/list_entries.html',
        entries=influencers,
        model_name='Influencer',
        list_endpoint='admin.list_influencers',
        create_endpoint='admin.create_influencer'
    )

@admin_bp.route('/influencers/create', methods=['GET', 'POST'])
@admin_login_required
def create_influencer():
    form = InfluencerForm()
    if form.validate_on_submit():
        influencer = Influencer(
            indicator=form.indicator.data,
            publication=form.publication.data,
            coverage_in_person=form.coverage_in_person.data or 0,
            coverage_remote=form.coverage_remote.data or 0,
            region=form.region.data,
            platform=form.platform.data,
            field=form.field.data,
            followers=form.followers.data or 0,
            identifier=form.identifier.data,
            account=form.account.data
        )
        try:
            db.session.add(influencer)
            db.session.commit()
            flash('Influencer created successfully.', 'success')
            return redirect(url_for('admin.list_influencers'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the influencer.', 'danger')
    return render_template(
        'admin/edit_entry.html',
        form=form,
        action='Create',
        model_name='Influencer',
        list_endpoint='admin.list_influencers'
    )

@admin_bp.route('/influencers/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_required
def edit_influencer(id):
    influencer = Influencer.query.get_or_404(id)
    form = InfluencerForm(obj=influencer)
    if form.validate_on_submit():
        influencer.indicator = form.indicator.data
        influencer.publication = form.publication.data
        influencer.coverage_in_person = form.coverage_in_person.data or 0
        influencer.coverage_remote = form.coverage_remote.data or 0
        influencer.region = form.region.data
        influencer.platform = form.platform.data
        influencer.field = form.field.data
        influencer.followers = form.followers.data or 0
        influencer.identifier = form.identifier.data
        influencer.account = form.account.data
        try:
            db.session.commit()
            flash('Influencer updated successfully.', 'success')
            return redirect(url_for('admin.list_influencers'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the influencer.', 'danger')
    return render_template(
        'admin/edit_entry.html',
        form=form,
        action='Edit',
        model_name='Influencer',
        list_endpoint='admin.list_influencers'
    )

@admin_bp.route('/influencers/delete/<int:id>', methods=['POST'])
@admin_login_required
def delete_influencer(id):
    influencer = Influencer.query.get_or_404(id)
    try:
        db.session.delete(influencer)
        db.session.commit()
        flash('Influencer deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the influencer.', 'danger')
    return redirect(url_for('admin.list_influencers'))

# CRUD Operations for NewsAccount
@admin_bp.route('/news_accounts')
@admin_login_required
def list_news_accounts():
    accounts = NewsAccount.query.all()
    return render_template(
        'admin/list_entries.html',
        entries=accounts,
        model_name='News Account',
        list_endpoint='admin.list_news_accounts',
        create_endpoint='admin.create_news_account'
    )

@admin_bp.route('/news_accounts/create', methods=['GET', 'POST'])
@admin_login_required
def create_news_account():
    form = NewsAccountForm()
    if form.validate_on_submit():
        account = NewsAccount(
            indicator=form.indicator.data,
            publication=form.publication.data,
            coverage_in_person=form.coverage_in_person.data or 0,
            coverage_remote=form.coverage_remote.data or 0,
            region=form.region.data,
            platform=form.platform.data,
            field=form.field.data,
            followers=form.followers.data or 0,
            identifier=form.identifier.data,
            account=form.account.data
        )
        try:
            db.session.add(account)
            db.session.commit()
            flash('News Account created successfully.', 'success')
            return redirect(url_for('admin.list_news_accounts'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the news account.', 'danger')
    return render_template(
        'admin/edit_entry.html',
        form=form,
        action='Create',
        model_name='News Account',
        list_endpoint='admin.list_news_accounts'
    )

@admin_bp.route('/news_accounts/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_required
def edit_news_account(id):
    account = NewsAccount.query.get_or_404(id)
    form = NewsAccountForm(obj=account)
    if form.validate_on_submit():
        account.indicator = form.indicator.data
        account.publication = form.publication.data
        account.coverage_in_person = form.coverage_in_person.data or 0
        account.coverage_remote = form.coverage_remote.data or 0
        account.region = form.region.data
        account.platform = form.platform.data
        account.field = form.field.data
        account.followers = form.followers.data or 0
        account.identifier = form.identifier.data
        account.account = form.account.data
        try:
            db.session.commit()
            flash('News Account updated successfully.', 'success')
            return redirect(url_for('admin.list_news_accounts'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the news account.', 'danger')
    return render_template(
        'admin/edit_entry.html',
        form=form,
        action='Edit',
        model_name='News Account',
        list_endpoint='admin.list_news_accounts'
    )

@admin_bp.route('/news_accounts/delete/<int:id>', methods=['POST'])
@admin_login_required
def delete_news_account(id):
    account = NewsAccount.query.get_or_404(id)
    try:
        db.session.delete(account)
        db.session.commit()
        flash('News Account deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the news account.', 'danger')
    return redirect(url_for('admin.list_news_accounts'))

# Authentication and Dashboard Routes
@admin_bp.route('/', methods=['GET'])
def admin_root():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('admin.login'))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    form = AdminLoginForm()
    if form.validate_on_submit():
        username_or_email = form.username_or_email.data
        password = form.password.data
        user = AdminUser.query.filter(
            (AdminUser.username == username_or_email) | 
            (AdminUser.email == username_or_email)
        ).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')
    return render_template('admin/login.html', form=form)

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@admin_login_required
def dashboard():
    return render_template('admin/dashboard.html')
