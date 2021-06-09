from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin

db = SQLAlchemy()
users_to_roles = db.Table(
    'users_to_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    email = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=users_to_roles, backref=db.backref('users', lazy='dynamic'))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(30))
    description = db.Column(db.String(255))


class Address(db.Model):
    __tablename__ = "addresses"
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('addresses.id'))
    parent_address = db.relationship('Address', remote_side=[id])
    type = db.Column(db.String)

    def __repr__(self):
        full_address_name = FullNameToAddress.query.filter_by(address=self).order_by(
            -1 * FullNameToAddress.id
        ).first()

        if full_address_name:
            return '<Address %r>' % full_address_name.full_name
        else:
            return '<Address %r %r>' % (self.type, self.id)


class Item(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'))
    address = db.relationship('Address')

    def __repr__(self):
        return '<Item %r>' % self.name


class NameToAddress(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'))
    address = db.relationship('Address')


class FullNameToAddress(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    full_name = db.Column(db.String)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'))
    address = db.relationship('Address')