import ckan.authz as authz


def package_relationship_create(context, data_dict):
    user = context.get('user')

    id1 = data_dict.get('subject')
    id2 = data_dict.get('object')

    # If we can update each package we can see the relationships
    authorized1 = authz.is_authorized_boolean(
        'package_update', context, {'id': id1})
    authorized2 = authz.is_authorized_boolean(
        'package_update', context, {'id': id2})

    if not (authorized1 and authorized2):
        return {
            'success': False,
            'msg': _(f'User {user} not authorized to edit these packages')
        }
    else:
        return {'success': True}


def package_relationship_delete(context, data_dict):
    user = context.get('user')
    relationship = context['relationship']

    # If you can create this relationship the you can also delete it
    authorized = authz.is_authorized_boolean(
        'package_relationship_create', context, data_dict)
    if not authorized:
        return {
            'success': False,
            'msg': _(f'User {user} not authorized to delete relationship {relationship.id}')
        }
    else:
        return {'success': True}


def package_relationships_list(context, data_dict):
    user = context.get('user')

    id1 = data_dict.get('subject')
    id2 = data_dict.get('object')

    # If we can see each package we can see the relationships
    authorized1 = authz.is_authorized_boolean(
            'package_show', context, {'id': id1})
    if id2:
        authorized2 = authz.is_authorized_boolean(
            'package_show', context, {'id': id2})
    else:
        authorized2 = True

    if not (authorized1 and authorized2):
        return {
            'success': False,
            'msg': _(f'User {user} not authorized to read these packages')
        }
    else:
        return {'success': True}


def package_relationship_update(context, data_dict):
    return authz.is_authorized('package_relationship_create', context, data_dict)
