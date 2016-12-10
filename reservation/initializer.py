import configparser

from sqlalchemy.exc import SQLAlchemyError
from reservation import app, db
from reservation.models import Resource, ResourceType


def get_resource_config():
    resources = []
    config = configparser.ConfigParser()
    if not config.read(app.config['RESOURCE_CONFIG_PATH']):
        raise IOError("Cannot open resource config file. Path {}".format(app.config['RESOURCE_CONFIG']))
    for section in config.sections():
        resource = {}
        options = config.options(section)
        for option in options:
            try:
                resource[option] = config.get(section, option)
            except Exception as ex:
                app.logger.error(ex)
                resource[option] = None
        resources.append(resource)


def add_type_if_not_exist(type_name):
    lower_type_name = type_name.lower()
    resource_type = ResourceType.query.filter_by(name=lower_type_name).first()
    if not resource_type:
        resource_type = ResourceType(name=lower_type_name)
        db.session.add(resource_type)
    return resource_type.id


def init_resources():
    try:
        config = get_resource_config()
        resources = Resource.query.all()
        processed_resources = set()

        for resource in config:
            in_database = any(map(lambda x: x.name == resource['name'], resources))
            if not in_database:
                new_resource = Resource()
                if resource['type'] != 'simulator':
                    new_resource.path = resource['path']
                    new_resource.model = resource['model']
                new_resource.name = resource['name']
                new_resource.type = add_type_if_not_exist(resource['type'])
                new_resource.available = True

                db.session.add(new_resource)
            else:
                if resource['type'] != 'simulator':
                    resource.path = resource['path']
                    resource.model = resource['model']
                resource.type = add_type_if_not_exist(resource['type'])
                resource.available = True

            processed_resources.add(resource['name'])

        for resource in resources:
            if resource.name not in processed_resources:
                resource.available = False
        db.session.commit()
    except IOError as ex:
        app.logger.error(ex)
    except SQLAlchemyError as ex:
        app.logger.error(ex)
