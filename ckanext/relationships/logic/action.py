import ckan.logic
import logging
from .schema import default_create_relationship_schema

log = logging.getLogger(__name__)

ValidationError = ckan.logic.ValidationError
NotFound = ckan.logic.NotFound
_check_access = ckan.logic.check_access
_get_or_bust = ckan.logic.get_or_bust
_get_action = ckan.logic.get_action


def package_relationship_create(context, data_dict):
    '''Create a relationship between two datasets (packages).

    You must be authorized to edit both the subject and the object datasets.

    :param subject: the id or name of the dataset that is the subject of the
        relationship
    :type subject: string
    :param object: the id or name of the dataset that is the object of the
        relationship
    :param type: the type of the relationship, one of ``'depends_on'``,
        ``'dependency_of'``, ``'derives_from'``, ``'has_derivation'``,
        ``'links_to'``, ``'linked_from'``, ``'child_of'`` or ``'parent_of'``
    :type type: string
    :param comment: a comment about the relationship (optional)
    :type comment: string

    :returns: the newly created package relationship
    :rtype: dictionary

    '''
    model = context['model']
    user = context['user']
    schema = context.get('schema') or default_create_relationship_schema()

    # TODO: do we need it?
    api = context.get('api_version')
    ref_package_by = 'id' if api == 2 else 'name'

    id1, id2, rel_type = _get_or_bust(data_dict, ['subject', 'object', 'type'])
    comment = data_dict.get('comment', u'')

    pkg1 = model.Package.get(id1)
    pkg2 = model.Package.get(id2)
    if not pkg1:
        raise NotFound(f'Subject package {id1} was not found.')
    if not pkg2:
        return NotFound(f'Object package {id2} was not found.')

    data, errors = _validate(data_dict, schema, context)
    if errors:
        model.Session.rollback()
        raise ValidationError(errors)

    _check_access('package_relationship_create', context, data_dict)

    # Create a Package Relationship.
    existing_rels = pkg1.get_relationships_with(pkg2, rel_type)
    if existing_rels:
        return _update_package_relationship(existing_rels[0],
                                            comment, context)
    rel = pkg1.add_relationship(rel_type, pkg2, comment=comment)
    if not context.get('defer_commit'):
        model.repo.commit_and_remove()
    context['relationship'] = rel

    relationship_dicts = rel.as_dict(ref_package_by=ref_package_by)
    return relationship_dicts


def package_relationship_delete(context, data_dict):
    '''Delete a dataset (package) relationship.

    You must be authorised to delete dataset relationships, and to edit both
    the subject and the object datasets.

    :param subject: the id or name of the dataset that is the subject of the
        relationship
    :type subject: string
    :param object: the id or name of the dataset that is the object of the
        relationship
    :type object: string
    :param type: the type of the relationship
    :type type: string

    '''
    model = context['model']
    user = context['user']
    id1, id2, rel = _get_or_bust(data_dict, ['subject', 'object', 'type'])

    pkg1 = model.Package.get(id1)
    pkg2 = model.Package.get(id2)
    if not pkg1:
        raise NotFound(f'Subject package {id1} was not found.')
    if not pkg2:
        return NotFound(f'Object package {id2} was not found.')

    existing_rels = pkg1.get_relationships_with(pkg2, rel)
    if not existing_rels:
        raise NotFound

    relationship = existing_rels[0]
    revisioned_details = 'Package Relationship: %s %s %s' % (id1, rel, id2)

    context['relationship'] = relationship
    _check_access('package_relationship_delete', context, data_dict)

    relationship.delete()
    model.repo.commit()


def package_relationships_list(context, data_dict):
    '''Return a dataset (package)'s relationships.

    :param id: the id or name of the first package
    :type id: string
    :param id2: the id or name of the second package
    :type id2: string
    :param rel: relationship as string see
        :py:func:`~ckan.logic.action.create.package_relationship_create` for
        the relationship types (optional)

    :rtype: list of dictionaries

    '''
    # TODO needs to work with dictization layer
    model = context['model']
    api = context.get('api_version')

    id1 = _get_or_bust(data_dict, "id")
    id2 = data_dict.get("id2")
    rel = data_dict.get("rel")
    ref_package_by = 'id' if api == 2 else 'name'
    pkg1 = model.Package.get(id1)
    pkg2 = None
    if not pkg1:
        raise NotFound('First package named in request was not found.')
    if id2:
        pkg2 = model.Package.get(id2)
        if not pkg2:
            raise NotFound('Second package named in address was not found.')

    if rel == 'relationships':
        rel = None

    _check_access('package_relationships_list', context, data_dict)

    # TODO: How to handle this object level authz?
    # Currently we don't care
    relationships = pkg1.get_relationships(with_package=pkg2, type=rel)

    if rel and not relationships:
        raise NotFound('Relationship "%s %s %s" not found.'
                       % (id1, rel, id2))

    relationship_dicts = [
        rel.as_dict(pkg1, ref_package_by=ref_package_by)
        for rel in relationships]

    return relationship_dicts


def _update_package_relationship(relationship, comment, context):
    model = context['model']
    api = context.get('api_version')
    ref_package_by = 'id' if api == 2 else 'name'
    is_changed = relationship.comment != comment
    if is_changed:
        relationship.comment = comment
        if not context.get('defer_commit'):
            model.repo.commit_and_remove()
    rel_dict = relationship.as_dict(package=relationship.subject,
                                    ref_package_by=ref_package_by)
    return rel_dict


def package_relationship_update(context, data_dict):
    '''Update a relationship between two datasets (packages).

    The subject, object and type parameters are required to identify the
    relationship. Only the comment can be updated.

    You must be authorized to edit both the subject and the object datasets.

    :param subject: the name or id of the dataset that is the subject of the
        relationship
    :type subject: string
    :param object: the name or id of the dataset that is the object of the
        relationship
    :type object: string
    :param type: the type of the relationship, one of ``'depends_on'``,
        ``'dependency_of'``, ``'derives_from'``, ``'has_derivation'``,
        ``'links_to'``, ``'linked_from'``, ``'child_of'`` or ``'parent_of'``
    :type type: string
    :param comment: a comment about the relationship (optional)
    :type comment: string

    :returns: the updated relationship
    :rtype: dictionary

    '''
    model = context['model']
    schema = context.get('schema') \
        or schema_.default_update_relationship_schema()

    id1, id2, rel = _get_or_bust(data_dict, ['subject', 'object', 'type'])

    pkg1 = model.Package.get(id1)
    pkg2 = model.Package.get(id2)
    if not pkg1:
        raise NotFound(f'Subject package {id1} was not found.')
    if not pkg2:
        return NotFound(f'Object package {id2} was not found.')

    data, errors = _validate(data_dict, schema, context)
    if errors:
        model.Session.rollback()
        raise ValidationError(errors)

    _check_access('package_relationship_update', context, data_dict)

    existing_rels = pkg1.get_relationships_with(pkg2, rel)
    if not existing_rels:
        raise NotFound('This relationship between the packages was not found.')
    entity = existing_rels[0]
    comment = data_dict.get('comment', u'')
    context['relationship'] = entity
    return _update_package_relationship(entity, comment, context)
