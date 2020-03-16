import ckan.plugins as p
from ckan.logic.schema import validator_args

get_validator = p.toolkit.get_validator

not_empty = get_validator('not_empty')
ignore_missing = get_validator('ignore_missing')
empty = get_validator('empty')
one_of = get_validator('one_of')
default = get_validator('default')


@validator_args
def default_relationship_schema(
        ignore_missing, unicode_safe, not_empty, one_of, ignore):
    return {
        'id': [ignore_missing, unicode_safe],
        'subject': [ignore_missing, unicode_safe],
        'object': [ignore_missing, unicode_safe],
        'type': [not_empty,
                 one_of(ckan.model.PackageRelationship.get_all_types())],
        'comment': [ignore_missing, unicode_safe],
        'state': [ignore],
    }


@validator_args
def default_create_relationship_schema(
        empty, not_empty, unicode_safe, package_id_or_name_exists):
    schema = default_relationship_schema()
    schema['id'] = [empty]
    schema['subject'] = [not_empty, unicode_safe, package_id_or_name_exists]
    schema['object'] = [not_empty, unicode_safe, package_id_or_name_exists]

    return schema


@validator_args
def default_update_relationship_schema(
        ignore_missing, package_id_not_changed):
    schema = default_relationship_schema()
    schema['id'] = [ignore_missing, package_id_not_changed]

    # Todo: would like to check subject, object & type haven't changed, but
    # no way to do this in schema
    schema['subject'] = [ignore_missing]
    schema['object'] = [ignore_missing]
    schema['type'] = [ignore_missing]

    return schema
