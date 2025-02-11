from extensions import db, bcrypt
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

class AdminUser(db.Model, UserMixin):
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='editor')  
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<AdminUser {self.email}>"


class AdditionalService(db.Model):
    __tablename__ = 'AdditionalServices'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    service_type = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=True)

    def __repr__(self):
        return f"<AdditionalService {self.service_type}>"


class DigitalPricing(db.Model):
    __tablename__ = 'DigitalPricing'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cost = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    indicator = db.Column(db.String(255), nullable=False)
    field = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    item = db.Column(db.String(255), nullable=False)
    channel = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<DigitalPricing {self.channel} - {self.indicator}>"


class Influencer(db.Model):
    __tablename__ = 'influencers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    indicator = db.Column(db.String(255), nullable=False)
    publication = db.Column(db.String(255), nullable=True)
    coverage_in_person = db.Column(db.Integer, nullable=True)
    coverage_remote = db.Column(db.Integer, nullable=True)
    region = db.Column(db.String(255), nullable=True)
    platform = db.Column(db.String(255), nullable=False)
    field = db.Column(db.String(255), nullable=False)
    followers = db.Column(db.BigInteger, nullable=True)
    identifier = db.Column(db.String(255), nullable=False)
    account = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Influencer {self.identifier}>"


class NewsAccount(db.Model):
    __tablename__ = 'NewsAccounts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    indicator = db.Column(db.String(255), nullable=False)
    publication = db.Column(db.String(255), nullable=True)
    coverage_in_person = db.Column(db.Integer, nullable=True)
    coverage_remote = db.Column(db.Integer, nullable=True)
    region = db.Column(db.String(255), nullable=True)
    platform = db.Column(db.String(255), nullable=False)
    field = db.Column(db.String(255), nullable=False)
    followers = db.Column(db.BigInteger, nullable=True)
    identifier = db.Column(db.String(255), nullable=False)
    account = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<NewsAccount {self.identifier}>"


class SavedCampaign(db.Model):
    __tablename__ = 'saved_campaigns'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), unique=True, nullable=False)
    campaign_details = Column(JSON, nullable=False)
    platforms_indicators = Column(JSON, nullable=False)
    additional_services = Column(JSON, nullable=True)
    influencers = Column(JSON, nullable=True)
    news_accounts = Column(JSON, nullable=True)
    optional_services = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SavedCampaign {self.title}>"