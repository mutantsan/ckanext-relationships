# -*- coding: utf-8 -*-

import graphene
from graphql import GraphQLError
import uuid

from flask import Blueprint
from flask_graphql import GraphQLView

import ckan.logic as logic
from datetime import datetime as dt
from ckan.model.package import Package
from ckan.model import meta

relationships = Blueprint('relationships', __name__)

# <Package id=55601304-bcda-4314-9bb3-5f961378b92f
# name=abraham title=Abraham version= url= author=
# author_email= maintainer= maintainer_email= notes=
# license_id=cc-by type=dataset owner_org=c31bf3ba-a6ae-453b-9552-492c3652f0e7
# creator_user_id=None metadata_created=2020-03-10 08:35:12.329084
# metadata_modified=2020-03-10 11:59:50.715404 private=True state=active>
# (Pdb) dir(pkg_dicts[0])



class Child(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    title = graphene.String()
    url = graphene.String()
    description = graphene.String()
    private = graphene.Boolean()
    pkg_type = graphene.String()
    state = graphene.String()
    created_date = graphene.DateTime()
    modified_date = graphene.DateTime()
    license_id = graphene.String()
    owner_org = graphene.ID()

class Dataset(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    title = graphene.String()
    url = graphene.String()
    description = graphene.String()
    private = graphene.Boolean()
    pkg_type = graphene.String()
    state = graphene.String()
    created_date = graphene.DateTime()
    modified_date = graphene.DateTime()
    license_id = graphene.String()
    owner_org = graphene.ID()
    child = graphene.Field(Child)


class Query(graphene.ObjectType):
    package = graphene.List(Dataset, id=graphene.ID())
    child = graphene.List(Child, id=graphene.ID())

    def resolve_child(self, info, id):
        return [
            Package(
                id=pkg_dict['id'],
                title=pkg_dict['title']
            ) for pkg_dict in sub_pkgs.values()
        ]

    def resolve_package(self, info, id):
        # if limit > 500:
        #     raise GraphQLError('The max limit value is 500')
            
        pkg_dict = logic.get_action('package_show')(None, {'id': id})

        if not pkg_dict:
            raise GraphQLError(f"The package with id '{id}' doesn't exists")

        if pkg_dict['relationships_as_object']:
            as_object = [
                pkg['__extras']['subject_package_id']
                for pkg in pkg_dict['relationships_as_object']
            ]

        if pkg_dict['relationships_as_subject']:
            as_subject = [
                pkg['__extras']['object_package_id']
                for pkg in pkg_dict['relationships_as_subject']
            ]
        sub_pkgs = {}
        if as_object:
            for id in as_object:
                sub_pkgs[id] = logic.get_action('package_show')(None, {'id': id})

        return [
            Package(
                id=pkg_dict['id'],
                name=pkg_dict['name'],
                title=pkg_dict['title'],
                url=pkg_dict['url'],
                description=pkg_dict['notes'],
                private=pkg_dict['private'],
                pkg_type=pkg_dict['type'],
                state=pkg_dict['state'],
                created_date = pkg_dict['metadata_created'],
                modified_date = pkg_dict['metadata_modified'],
                license_id = pkg_dict['license_id'],
                owner_org = pkg_dict['owner_org'],
                child = graphene.Field(Child, default_value=sub_pkgs)
            )
        ]
class NewQuery(graphene.ObjectType):
    people = graphene.Field(Query)

    def resolve_people(self, info):
        return Query()

package_schema = graphene.Schema(query=NewQuery)


relationships.add_url_rule('/get_hierarchy',
                           view_func=GraphQLView.as_view('graphql', schema=package_schema, graphiql=True))


def get_blueprints():
    return [relationships]
