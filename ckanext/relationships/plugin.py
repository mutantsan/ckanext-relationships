import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckanext.relationships.logic.action as action
import ckanext.relationships.logic.auth as auth
import ckanext.relationships.interfaces as interfaces

from ckan.logic.schema import default_create_package_schema
from .views import get_blueprints
from ckanext.relationships.logic.schema import default_relationship_schema


class RelationshipsPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IBlueprint)
    p.implements(p.IActions)
    p.implements(p.IAuthFunctions)
    # p.implements(p.IDatasetForm)
    p.implements(interfaces.IRelationships, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        tk.add_template_directory(config_, 'templates')
        tk.add_public_directory(config_, 'public')
        tk.add_resource('fanstatic', 'relationships')

    # IActions

    def get_actions(self):
        return {
            'package_relationship_create': action.package_relationship_create,
            'package_relationship_delete': action.package_relationship_delete,
            'package_relationships_list': action.package_relationships_list,
            'package_relationship_update': action.package_relationship_update
        }

    # IAuthFunctions

    def get_auth_functions(self):
        return {
            'package_relationship_create': auth.package_relationship_create,
            'package_relationship_delete': auth.package_relationship_delete,
            'package_relationships_list': auth.package_relationships_list,
            'package_relationship_update': auth.package_relationship_update
        }
    # IDatasetForm

    def create_package_schema(self):
        schema = default_create_package_schema()
        schema.update(
            relationships_as_object=default_relationship_schema(),
            relationships_as_subject=default_relationship_schema(),
        )
        return schema

    def is_fallback(self):
        return True

    def package_types(self):
        return []

    # IBlueprint

    def get_blueprint(self):
        return get_blueprints()

    # IClick

    def get_commands(self):
        return get_commands()
