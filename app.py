from flask import Flask, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, helpers, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, current_user
from flask_security.utils import hash_password
from json import load


with open('secrets.json') as secrets_file:
    secrets_dict = load(secrets_file)

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)


class ModelViewWithLogin(AdminIndexView):
    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated)

    def is_visible(self):
        return False

    def _handle_view(self, name):
        if not self.is_accessible():
            return redirect(url_for('security.login'))


admin = Admin(app, 'Administrator panel', index_view=ModelViewWithLogin())

users_to_roles = db.Table(
    'users_to_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=users_to_roles, backref=db.backref('users', lazy='dynamic'))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(30), unique=True)
    description = db.Column(db.String(255))


class Address(db.Model):
    __tablename__ = "addresses"
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    address = db.Column(db.String)

    def __repr__(self):
        return '<Address %r>' % self.address


class Item(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'))
    address = db.relationship('Address')

    def __repr__(self):
        return '<Item %r>' % self.name


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)
admin.add_view(ModelView(Item, db.session))
admin.add_view(ModelView(Address, db.session))


@app.before_first_request
def preparation():
    db.drop_all()
    db.create_all()
    user_datastore.create_user(username=secrets_dict['admin_username'],
                               password=hash_password(secrets_dict['admin_password']))
    db.session.commit()


@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=helpers,
        get_url=url_for
    )


@app.route('/')
def redirect_to_admin():
    return redirect('/admin')


if __name__ == '__main__':
    app.run()
