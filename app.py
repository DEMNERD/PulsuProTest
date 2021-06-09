from json import load

from flask import Flask, url_for, redirect
from flask_admin import Admin, helpers, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_security import Security, SQLAlchemyUserDatastore, current_user
from sqlalchemy import event

from models import User, Role, Address, Item, NameToAddress, FullNameToAddress, db


with open('secrets.json') as secrets_file:
    secrets_dict = load(secrets_file)


app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)


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


def create_all_children_with_new_parent_name(new_parent_full_name):
    for child in Address.query.filter_by(parent_address=new_parent_full_name.address).all():
        for child_name in NameToAddress.query.filter_by(address=child).all():
            full_child_name = FullNameToAddress(
                address=child,
                full_name=f'{new_parent_full_name.full_name} {child.type} {child_name.name}'
            )
            db.session.add(full_child_name)
            create_all_children_with_new_parent_name(full_child_name)


@event.listens_for(NameToAddress, 'after_insert')
def create_full_name(mapper, connection, target):
    parent_full_names = FullNameToAddress.query.filter_by(address=target.address.parent_address).all()
    if not parent_full_names:
        new_parent_full_name = FullNameToAddress(
            address=target.address,
            full_name=f'{target.address.type} {target.name}'
        )
        db.session.add(new_parent_full_name)
        create_all_children_with_new_parent_name(new_parent_full_name)

    for FullParentAddressName in parent_full_names:
        new_parent_full_name = FullNameToAddress(
            address=target.address,
            full_name=f'{FullParentAddressName.full_name} {target.address.type} {target.name}'
        )
        db.session.add(new_parent_full_name)
        create_all_children_with_new_parent_name(new_parent_full_name)


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)
admin.add_view(ModelView(Item, db.session))
admin.add_view(ModelView(Address, db.session))
admin.add_view(ModelView(NameToAddress, db.session))
admin.add_view(ModelView(FullNameToAddress, db.session))


@app.before_first_request
def preparation():
    db.drop_all()
    db.create_all()
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
