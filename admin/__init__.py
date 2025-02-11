from flask import Blueprint

admin_bp = Blueprint(
    'admin',
    __name__,
    template_folder='templates',  
    static_folder='static/admin',
    url_prefix='/admin'
)

from . import routes 


