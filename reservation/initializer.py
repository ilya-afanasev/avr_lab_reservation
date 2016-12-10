import configparser

from reservation import app, db
from reservation.models import Resource, ResourceType


SIMULATOR_TYPE = 'simulator'
MCU_TYPE = 'mcu'


def get_resource_config():
    resources = []
    config = configparser.ConfigParser()
    if not config.read(app.config['RESOURCE_CONFIG_PATH']):
        raise IOError("Cannot open resource config file. Path {}".format(app.config['RESOURCE_CONFIG_PATH']))
    for section in config.sections():
        resource = {'id': section}
        options = config.options(section)
        for option in options:
            try:
                resource[option] = config.get(section, option)
            except Exception as ex:
                app.logger.error(ex)
                resource[option] = None
        resources.append(resource)
    return resources


def add_type_if_not_exist(type_name):
    lower_type_name = type_name.lower()
    resource_type = ResourceType.query.filter_by(name=lower_type_name).first()
    if not resource_type:
        resource_type = ResourceType(name=lower_type_name)
        db.session.add(resource_type)
        db.session.commit()
    return resource_type.id


def init_resources():
    config = get_resource_config()
    db_resources = Resource.query.all()
    processed_resource_ids = set()

    for config_resource in config:
        current_db_resource = next(filter(lambda x: x.id == int(config_resource['id']), db_resources), None)
        if not current_db_resource:
            new_resource = Resource()
            if config_resource['type'] == MCU_TYPE:
                new_resource.path = config_resource['path']
                new_resource.model = config_resource['model']
            elif config_resource['type'] != SIMULATOR_TYPE:
                raise TypeError('Unsupported resource type {}'.format(config_resource['type']))
            new_resource.id = config_resource['id']
            new_resource.type = add_type_if_not_exist(config_resource['type'])
            new_resource.available = True

            db.session.add(new_resource)
        else:
            if config_resource['type'] == MCU_TYPE:
                current_db_resource.path = config_resource['path']
                current_db_resource.model = config_resource['model']
            elif config_resource['type'] != SIMULATOR_TYPE:
                raise TypeError('Unsupported resource type {}'.format(config_resource['type']))
            current_db_resource.type = add_type_if_not_exist(config_resource['type'])
            current_db_resource.available = True

        processed_resource_ids.add(int(config_resource['id']))

    for config_resource in db_resources:
        if config_resource.id not in processed_resource_ids:
            config_resource.available = False
    db.session.commit()

